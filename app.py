from flask import Flask, render_template, request, redirect, session, flash, jsonify
from datetime import datetime
from urllib.parse import urlparse, unquote
import os
import secrets
import pg8000

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "boztek-secret")
DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "saban")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "5109")
READY = False

def parse_db_url():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL yok. Render > Environment içine Neon connection string ekle.")
    u = urlparse(DATABASE_URL)
    return {
        "user": unquote(u.username or ""),
        "password": unquote(u.password or ""),
        "host": u.hostname,
        "port": u.port or 5432,
        "database": (u.path or "/neondb").lstrip("/"),
    }

def db():
    cfg = parse_db_url()
    return pg8000.connect(
        user=cfg["user"],
        password=cfg["password"],
        host=cfg["host"],
        port=cfg["port"],
        database=cfg["database"],
        ssl_context=True
    )

def rows_to_dicts(cursor, rows):
    if not rows:
        return []
    cols = [c["name"] if isinstance(c, dict) else c[0] for c in cursor.description]
    return [dict(zip(cols, r)) for r in rows]

def q(sql, params=None, fetch=False, one=False):
    conn = db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        data = None
        if fetch:
            rows = cur.fetchall()
            data = rows_to_dicts(cur, rows)
            if one:
                data = data[0] if data else None
        conn.commit()
        cur.close()
        return data
    finally:
        conn.close()

def col(table, name, definition):
    r = q("select column_name from information_schema.columns where table_name=%s and column_name=%s", (table, name), fetch=True, one=True)
    if not r:
        q(f"alter table {table} add column {definition}")

def init_db():
    global READY
    q("""create table if not exists personnel(
        id serial primary key,
        full_name text not null,
        department text not null,
        annual_leave_total integer default 14,
        annual_leave_used integer default 0,
        annual_leave_remaining integer default 14,
        salary numeric default 0,
        active integer default 1,
        username text unique,
        password text,
        token text unique
    )""")
    q("""create table if not exists advances(
        id serial primary key,
        person_id integer references personnel(id) on delete cascade,
        amount numeric not null,
        note text,
        status text default 'Beklemede'
    )""")
    q("""create table if not exists leaves(
        id serial primary key,
        person_id integer references personnel(id) on delete cascade,
        start_date text not null,
        end_date text not null,
        days_count integer default 0,
        status text default 'İzinli'
    )""")
    q("""create table if not exists attendance_logs(
        id serial primary key,
        person_id integer references personnel(id) on delete cascade,
        event_type text not null,
        event_time text not null
    )""")
    col("personnel","username","username text unique")
    col("personnel","password","password text")
    col("personnel","token","token text unique")
    col("personnel","salary","salary numeric default 0")
    col("personnel","active","active integer default 1")
    READY = True

@app.before_request
def before():
    global READY
    if not READY:
        init_db()

def admin():
    return session.get("admin_ok") == True

def val(name, default=None):
    return request.form.get(name) or request.args.get(name) or default

def days_between(a,b):
    s = datetime.strptime(a,"%Y-%m-%d").date()
    e = datetime.strptime(b,"%Y-%m-%d").date()
    return max((e-s).days+1, 1)

def summary(pid):
    p = q("select p.*, coalesce((select sum(amount) from advances a where a.person_id=p.id),0) total_advance from personnel p where id=%s", (pid,), fetch=True, one=True)
    if not p:
        return None
    salary = float(p["salary"] or 0)
    adv = float(p["total_advance"] or 0)
    return {"id":p["id"],"full_name":p["full_name"],"department":p["department"],"salary":salary,"total_advance":adv,"remaining_salary":salary-adv,"annual_leave_remaining":p["annual_leave_remaining"],"annual_leave_used":p["annual_leave_used"],"annual_leave_total":p["annual_leave_total"]}

@app.route("/")
def home():
    return redirect("/admin/dashboard") if admin() else redirect("/admin/login")

@app.route("/admin/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USERNAME and request.form.get("password") == ADMIN_PASSWORD:
            session["admin_ok"] = True
            return redirect("/admin/dashboard")
        flash("Hatalı giriş")
    return render_template("login.html")

@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect("/admin/login")

@app.route("/admin")
@app.route("/admin/dashboard")
def dash():
    if not admin():
        return redirect("/admin/login")
    personel = q("select count(*) c from personnel", fetch=True, one=True)["c"]
    avans = q("select count(*) c from advances", fetch=True, one=True)["c"]
    izin = q("select count(*) c from leaves", fetch=True, one=True)["c"]
    return render_template("dashboard.html", title="Dashboard", personel=personel, avans=avans, izin=izin)

@app.route("/admin/personnel", methods=["GET","POST"])
def personnel():
    if not admin():
        return redirect("/admin/login")
    if request.method == "POST":
        total = int(request.form.get("annual_leave_total",14))
        salary = float(request.form.get("salary",0))
        try:
            q("""insert into personnel(full_name,department,annual_leave_total,annual_leave_used,annual_leave_remaining,salary,active,username,password,token)
                 values(%s,%s,%s,0,%s,%s,1,%s,%s,%s)""",
              (request.form["full_name"], request.form["department"], total, total, salary,
               request.form.get("username") or None, request.form.get("password") or None, secrets.token_hex(24)))
            flash("Personel kalıcı olarak eklendi.")
        except Exception:
            flash("Eklenemedi. Kullanıcı adı aynı olabilir.")
    rows = q("select * from personnel order by id desc", fetch=True)
    return render_template("personnel.html", title="Personel", rows=rows)

@app.route("/admin/personnel/<int:pid>/edit", methods=["GET","POST"])
def edit(pid):
    if not admin():
        return redirect("/admin/login")
    p = q("select * from personnel where id=%s", (pid,), fetch=True, one=True)
    if not p:
        return redirect("/admin/personnel")
    if request.method == "POST":
        total = int(request.form.get("annual_leave_total",0))
        used = int(request.form.get("annual_leave_used",0))
        rem = max(total-used,0)
        token = p.get("token") or secrets.token_hex(24)
        q("""update personnel set full_name=%s,department=%s,username=%s,password=%s,
             annual_leave_total=%s,annual_leave_used=%s,annual_leave_remaining=%s,salary=%s,active=%s,token=%s where id=%s""",
          (request.form["full_name"],request.form["department"],request.form.get("username") or None,
           request.form.get("password") or None,total,used,rem,float(request.form.get("salary",0)),
           int(request.form.get("active",1)),token,pid))
        return redirect("/admin/personnel")
    return render_template("edit.html", title="Düzenle", p=p)

@app.route("/admin/personnel/<int:pid>/delete", methods=["POST"])
def delete_person(pid):
    if not admin():
        return redirect("/admin/login")
    q("delete from personnel where id=%s", (pid,))
    return redirect("/admin/personnel")

@app.route("/admin/advances", methods=["GET","POST"])
def advances():
    if not admin():
        return redirect("/admin/login")
    if request.method == "POST":
        q("insert into advances(person_id,amount,note,status) values(%s,%s,'','Beklemede')", (request.form["person_id"], request.form["amount"]))
    people = q("select * from personnel order by full_name", fetch=True)
    rows = q("select a.*,p.full_name from advances a join personnel p on p.id=a.person_id order by a.id desc", fetch=True)
    opts = "".join([f"<option value='{p['id']}'>{p['full_name']}</option>" for p in people])
    trs = "".join([f"<tr><td>{r['full_name']}</td><td>{r['amount']}</td><td>{r['status']}</td></tr>" for r in rows])
    body = f"<form method='post'><select name='person_id'>{opts}</select><input name='amount' type='number' step='0.01' required><button>Avans Ekle</button></form><table border='1' cellpadding='8'><tr><th>Personel</th><th>Tutar</th><th>Durum</th></tr>{trs}</table>"
    return render_template("table.html", title="Avanslar", body=body)

@app.route("/admin/leaves", methods=["GET","POST"])
def leaves():
    if not admin():
        return redirect("/admin/login")
    if request.method == "POST":
        pid = request.form["person_id"]
        start = request.form["start_date"]
        end = request.form["end_date"]
        count = days_between(start,end)
        p = q("select * from personnel where id=%s", (pid,), fetch=True, one=True)
        if p and p["annual_leave_remaining"] >= count:
            q("insert into leaves(person_id,start_date,end_date,days_count,status) values(%s,%s,%s,%s,'İzinli')", (pid,start,end,count))
            q("update personnel set annual_leave_used=annual_leave_used+%s, annual_leave_remaining=annual_leave_remaining-%s where id=%s", (count,count,pid))
    people = q("select * from personnel order by full_name", fetch=True)
    rows = q("select l.*,p.full_name from leaves l join personnel p on p.id=l.person_id order by l.id desc", fetch=True)
    opts = "".join([f"<option value='{p['id']}'>{p['full_name']} - Kalan {p['annual_leave_remaining']}</option>" for p in people])
    trs = "".join([f"<tr><td>{r['full_name']}</td><td>{r['start_date']} - {r['end_date']}</td><td>{r['days_count']}</td></tr>" for r in rows])
    body = f"<form method='post'><select name='person_id'>{opts}</select><input name='start_date' type='date' required><input name='end_date' type='date' required><button>İzin Ekle</button></form><table border='1' cellpadding='8'><tr><th>Personel</th><th>Tarih</th><th>Gün</th></tr>{trs}</table>"
    return render_template("table.html", title="İzinler", body=body)

@app.route("/admin/salary")
def salary_page():
    if not admin():
        return redirect("/admin/login")
    rows = q("select p.*,coalesce((select sum(amount) from advances a where a.person_id=p.id),0) total_advance from personnel p order by full_name", fetch=True)
    body = "<table border='1' cellpadding='8'><tr><th>Personel</th><th>Maaş</th><th>Avans</th><th>Kalan</th></tr>"
    for r in rows:
        s = float(r["salary"] or 0); a = float(r["total_advance"] or 0)
        body += f"<tr><td>{r['full_name']}</td><td>{s:.2f}</td><td>{a:.2f}</td><td>{s-a:.2f}</td></tr>"
    body += "</table>"
    return render_template("table.html", title="Maaşlar", body=body)

@app.route("/admin/attendance")
def attendance():
    if not admin():
        return redirect("/admin/login")
    rows = q("select a.*,p.full_name from attendance_logs a join personnel p on p.id=a.person_id order by a.id desc limit 200", fetch=True)
    body = "<table border='1' cellpadding='8'><tr><th>Personel</th><th>Tip</th><th>Zaman</th></tr>"
    for r in rows:
        body += f"<tr><td>{r['full_name']}</td><td>{r['event_type']}</td><td>{r['event_time']}</td></tr>"
    body += "</table>"
    return render_template("table.html", title="Giriş Çıkış", body=body)

@app.route("/admin/annual-leave")
def annual():
    if not admin():
        return redirect("/admin/login")
    rows = q("select * from personnel order by full_name", fetch=True)
    body = "<table border='1' cellpadding='8'><tr><th>Personel</th><th>Toplam</th><th>Kullanılan</th><th>Kalan</th></tr>"
    for r in rows:
        body += f"<tr><td>{r['full_name']}</td><td>{r['annual_leave_total']}</td><td>{r['annual_leave_used']}</td><td>{r['annual_leave_remaining']}</td></tr>"
    body += "</table>"
    return render_template("table.html", title="Yıllık İzin", body=body)

@app.route("/admin/reports")
def reports():
    return salary_page()

@app.route("/api/health")
def health():
    q("select 1", fetch=True, one=True)
    return jsonify({"status":"ok","database":"connected","driver":"pg8000"})

@app.route("/api/personnel")
def api_personnel():
    rows = q("select * from personnel where active=1 order by full_name", fetch=True)
    out = []
    m = datetime.now().strftime("%Y-%m")
    for p in rows:
        days = q("select count(distinct substring(event_time,1,10)) c from attendance_logs where person_id=%s and event_type='entry' and substring(event_time,1,7)=%s", (p["id"],m), fetch=True, one=True)["c"]
        adv = q("select coalesce(sum(amount),0) s from advances where person_id=%s", (p["id"],), fetch=True, one=True)["s"]
        out.append({"id":p["id"],"full_name":p["full_name"],"department":p["department"],"monthly_days":days,"annual_leave_remaining":p["annual_leave_remaining"],"salary":float(p["salary"] or 0),"total_advance":float(adv or 0)})
    return jsonify(out)

@app.route("/api/entry", methods=["GET","POST"])
def api_entry():
    pid = val("person_id")
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    q("insert into attendance_logs(person_id,event_type,event_time) values(%s,'entry',%s)", (pid,t))
    return jsonify({"status":"ok","event_type":"entry","person_id":int(pid),"event_time":t})

@app.route("/api/exit", methods=["GET","POST"])
def api_exit():
    pid = val("person_id")
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    q("insert into attendance_logs(person_id,event_type,event_time) values(%s,'exit',%s)", (pid,t))
    return jsonify({"status":"ok","event_type":"exit","person_id":int(pid),"event_time":t})

@app.route("/api/attendance")
def api_attendance():
    return jsonify(q("select a.id,a.person_id,p.full_name,a.event_type,a.event_time from attendance_logs a join personnel p on p.id=a.person_id order by a.id desc limit 100", fetch=True))

@app.route("/api/leaves", methods=["GET"])
def api_leaves():
    return jsonify(q("select l.id,l.person_id,p.full_name,l.start_date,l.end_date,l.days_count,l.status from leaves l join personnel p on p.id=l.person_id order by l.id desc", fetch=True))

@app.route("/api/leaves", methods=["POST"])
@app.route("/api/leave-add", methods=["GET","POST"])
def api_leave_add():
    pid = val("person_id")
    start = val("start_date")
    end = val("end_date")
    if not pid or not start or not end:
        return jsonify({"status":"error","message":"eksik alan"}), 400
    count = days_between(start,end)
    p = q("select * from personnel where id=%s", (pid,), fetch=True, one=True)
    if not p:
        return jsonify({"status":"error","message":"personel yok"}), 404
    if p["annual_leave_remaining"] < count:
        return jsonify({"status":"error","message":"yetersiz izin"}), 400
    q("insert into leaves(person_id,start_date,end_date,days_count,status) values(%s,%s,%s,%s,'İzinli')", (pid,start,end,count))
    q("update personnel set annual_leave_used=annual_leave_used+%s, annual_leave_remaining=annual_leave_remaining-%s where id=%s", (count,count,pid))
    return jsonify({"status":"ok","person_id":int(pid),"days_count":count})

@app.route("/api/employee-login", methods=["GET","POST"])
def employee_login():
    u = val("username")
    pword = val("password")
    p = q("select * from personnel where username=%s and password=%s and active=1", (u,pword), fetch=True, one=True)
    if not p:
        return jsonify({"status":"error","message":"Kullanıcı adı veya şifre hatalı"}), 401
    token = p.get("token") or secrets.token_hex(24)
    q("update personnel set token=%s where id=%s", (token,p["id"]))
    return jsonify({"status":"ok","token":token,"person":summary(p["id"])})

@app.route("/api/employee-me", methods=["GET","POST"])
def employee_me():
    token = val("token")
    p = q("select id from personnel where token=%s and active=1", (token,), fetch=True, one=True)
    if not p:
        return jsonify({"status":"error","message":"geçersiz giriş"}), 401
    return jsonify({"status":"ok","person":summary(p["id"])})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

import os, sqlite3
from datetime import datetime, date
from functools import wraps
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, g
from werkzeug.security import check_password_hash, generate_password_hash

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(APP_DIR, "kuafor.db"))
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deploying")

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(exc):
    conn = g.pop("db", None)
    if conn is not None: conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS services(id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL DEFAULT 0, duration INTEGER NOT NULL DEFAULT 30, sessions INTEGER NOT NULL DEFAULT 1, active INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS staff(id INTEGER PRIMARY KEY, name TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY, name TEXT NOT NULL, phone TEXT NOT NULL, notes TEXT DEFAULT '', created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS packages(id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id), service_id INTEGER REFERENCES services(id), title TEXT NOT NULL, total_sessions INTEGER NOT NULL, used_sessions INTEGER NOT NULL DEFAULT 0, total_price REAL NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS appointments(id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id), service_id INTEGER REFERENCES services(id), staff_id INTEGER REFERENCES staff(id), package_id INTEGER REFERENCES packages(id), starts_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Bekliyor', note TEXT DEFAULT '', public_booking INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS payments(id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id), package_id INTEGER REFERENCES packages(id), amount REAL NOT NULL, method TEXT NOT NULL DEFAULT 'Nakit', note TEXT DEFAULT '', paid_at TEXT NOT NULL);
    """)
    if not conn.execute("SELECT id FROM users LIMIT 1").fetchone():
        conn.execute("INSERT INTO users(username,password_hash) VALUES(?,?)", ("admin", generate_password_hash("Kuafor123!")))
    if not conn.execute("SELECT id FROM services LIMIT 1").fetchone():
        conn.executemany("INSERT INTO services(name,price,duration,sessions) VALUES(?,?,?,?)", [
            ("Saç kesimi", 350, 30, 1), ("Saç boyama", 1200, 90, 1), ("Cilt bakımı paketi", 2500, 60, 5), ("Lazer seans paketi", 5000, 45, 10)])
    if not conn.execute("SELECT id FROM staff LIMIT 1").fetchone():
        conn.executemany("INSERT INTO staff(name) VALUES(?)", [("Ayşe",),("Zeynep",)])
    conn.commit(); conn.close()

init_db()

STYLE = """
:root{--navy:#101b31;--navy2:#172641;--gold:#d6b36a;--cream:#f7f5ef;--ink:#202a3a;--muted:#7b8494;--line:#e5e8ee;--white:#fff}
*{box-sizing:border-box}body{margin:0;background:#f3f5f9;color:var(--ink);font:15px/1.5 Inter,system-ui,-apple-system,Segoe UI,sans-serif}
a{color:inherit;text-decoration:none}.layout{display:flex;min-height:100vh}.sidebar{width:245px;background:var(--navy);color:#e8edf5;padding:26px 18px;flex-shrink:0}.brand{font-size:21px;font-weight:800;letter-spacing:.4px;margin:4px 12px 4px}.brand span{color:var(--gold)}.subbrand{color:#9da9bc;font-size:11px;letter-spacing:2px;margin:0 12px 32px;text-transform:uppercase}.nav a{display:block;padding:12px 14px;border-radius:11px;margin:5px 0;color:#bdc7d7}.nav a:hover,.nav a.active{background:#243653;color:#fff}.nav a.active{border-left:3px solid var(--gold)}.nav .public{margin-top:24px;color:var(--gold)}.main{flex:1;min-width:0;padding:30px clamp(16px,3vw,42px)}.top{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:26px}.eyebrow{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:1.5px}.h1{font-size:28px;font-weight:800;margin:3px 0}.topright{display:flex;gap:10px;align-items:center}.pill{border:1px solid var(--line);border-radius:30px;padding:8px 12px;background:#fff;font-size:13px}.gold{color:#8d6b22}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px;margin-bottom:24px}.card,.panel{background:#fff;border:1px solid #e8ebf1;border-radius:17px;padding:20px;box-shadow:0 4px 18px #1a294008}.metric-label{font-size:13px;color:var(--muted)}.metric{font-size:28px;font-weight:800;margin:9px 0 2px}.metric-note{font-size:12px;color:var(--muted)}.section-title{display:flex;justify-content:space-between;align-items:center;margin:8px 0 14px;gap:12px}.section-title h2{font-size:17px;margin:0}.panel{margin-bottom:20px;padding:20px}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;white-space:nowrap}th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);padding:12px 10px;border-bottom:1px solid var(--line)}td{padding:14px 10px;border-bottom:1px solid #f0f2f6;font-size:14px}tr:last-child td{border-bottom:0}.btn{display:inline-flex;align-items:center;justify-content:center;background:var(--navy);color:#fff;border:0;border-radius:10px;padding:10px 15px;font-weight:700;cursor:pointer;font-size:13px}.btn.goldbtn{background:var(--gold);color:#211b10}.btn.ghost{background:#f0f2f6;color:#28344a}.btn.danger{background:#fff0ee;color:#a2392c}.btn.small{padding:7px 10px;font-size:12px}.formgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.field{display:flex;flex-direction:column;gap:6px}.field.full{grid-column:1/-1}label{font-size:12px;color:#596477;font-weight:700}input,select,textarea{width:100%;padding:11px 12px;border:1px solid #dfe4ec;border-radius:10px;background:#fff;color:var(--ink);font:inherit;outline:none}input:focus,select:focus,textarea:focus{border-color:var(--gold);box-shadow:0 0 0 3px #d6b36a22}textarea{min-height:84px;resize:vertical}.actions{display:flex;gap:8px;flex-wrap:wrap}.badge{display:inline-block;border-radius:30px;padding:5px 9px;font-size:11px;font-weight:700;background:#eef2f8;color:#43516a}.badge.ok{background:#e6f6ec;color:#237447}.badge.warn{background:#fff3d9;color:#8a641a}.badge.cancel{background:#fde9e7;color:#a53d32}.flash{padding:12px 15px;background:#fff5db;border:1px solid #f2d68d;border-radius:10px;margin-bottom:14px}.empty{padding:28px;text-align:center;color:var(--muted)}.muted{color:var(--muted)}.progress{height:7px;background:#edf0f4;border-radius:10px;overflow:hidden;margin-top:8px}.progress span{display:block;height:100%;background:var(--gold)}.auth{min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at 80% 20%,#263c60,var(--navy) 55%);padding:20px}.authbox{width:min(430px,100%);background:#fff;padding:34px;border-radius:22px;box-shadow:0 20px 80px #0003}.authbox h1{margin:0 0 6px}.publichead{background:var(--navy);color:white;padding:20px clamp(18px,5vw,70px);display:flex;justify-content:space-between;align-items:center}.publicbody{max-width:900px;margin:35px auto;padding:0 18px}.publichero{background:var(--navy);color:white;border-radius:20px;padding:28px;margin-bottom:20px}.publichero h1{margin:0 0 8px;font-size:30px}.publichero p{color:#c7d1df;margin:0}.two{display:grid;grid-template-columns:1.1fr .9fr;gap:18px}.footer{text-align:center;color:var(--muted);font-size:12px;padding:20px}@media(max-width:900px){.sidebar{width:190px}.cards{grid-template-columns:repeat(2,minmax(0,1fr))}.two{grid-template-columns:1fr}}@media(max-width:650px){.layout{display:block}.sidebar{width:100%;padding:15px}.subbrand{margin-bottom:12px}.nav{display:flex;overflow:auto;gap:4px}.nav a{white-space:nowrap;padding:9px 11px}.nav .public{margin-top:5px}.main{padding:20px 14px}.top{align-items:flex-start}.h1{font-size:23px}.cards{gap:9px}.card{padding:14px}.metric{font-size:22px}.formgrid{grid-template-columns:1fr}.field.full{grid-column:auto}.panel{padding:14px}}
"""
BASE = """
<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{ title }} · Atelier</title><style>""" + STYLE + """</style></head><body><div class="layout"><aside class="sidebar"><div class="brand">ATELIER<span>.</span></div><div class="subbrand">Salon yönetim sistemi</div><nav class="nav">
<a class="{{'active' if page=='dashboard' else ''}}" href="{{url_for('dashboard')}}">▦ &nbsp; Genel Bakış</a>
<a class="{{'active' if page=='appointments' else ''}}" href="{{url_for('appointments')}}">▣ &nbsp; Randevular</a>
<a class="{{'active' if page=='customers' else ''}}" href="{{url_for('customers')}}">♙ &nbsp; Müşteriler & Seanslar</a>
<a class="{{'active' if page=='services' else ''}}" href="{{url_for('services')}}">✧ &nbsp; Hizmet & Paketler</a>
<a class="{{'active' if page=='payments' else ''}}" href="{{url_for('payments')}}">₺ &nbsp; Tahsilatlar</a>
<a class="{{'active' if page=='staff' else ''}}" href="{{url_for('staff')}}">♧ &nbsp; Personel</a>
<a class="{{'active' if page=='reports' else ''}}" href="{{url_for('reports')}}">▤ &nbsp; Gelir Raporları</a>
<a class="public" href="{{url_for('book')}}">↗ &nbsp; Online randevu sayfası</a>
<a href="{{url_for('logout')}}">⇥ &nbsp; Çıkış yap</a>
</nav></aside><main class="main"><header class="top"><div><div class="eyebrow">Salon yönetimi / {{ section }}</div><div class="h1">{{ title }}</div></div><div class="topright"><span class="pill">✦ <span class="gold">Premium</span></span><span class="pill">{{ session.get('username','Salon') }}</span></div></header>
{% with messages = get_flashed_messages() %}{% for m in messages %}<div class="flash">{{m}}</div>{% endfor %}{% endwith %}
{{ body|safe }}<div class="footer">ATELIER · Randevu ve müşteri deneyimi</div></main></div></body></html>
"""
def page(title, section, page_name, body):
    return render_template_string(BASE, title=title, section=section, page=page_name, body=body)

def login_required(fn):
    @wraps(fn)
    def inner(*a, **kw):
        if not session.get("user_id"): return redirect(url_for("login"))
        return fn(*a, **kw)
    return inner

def money(n): return f"₺{float(n or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
app.jinja_env.globals["money"] = money

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user=db().execute("SELECT * FROM users WHERE username=?",(request.form.get("username","").strip(),)).fetchone()
        if user and check_password_hash(user["password_hash"],request.form.get("password","")):
            session.clear(); session["user_id"]=user["id"]; session["username"]=user["username"]
            return redirect(url_for("dashboard"))
        flash("Kullanıcı adı veya şifre hatalı.")
    return render_template_string("""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Atelier giriş</title><style>"""+STYLE+"""</style></head><body class="auth"><form class="authbox" method="post"><div class="brand" style="color:#101b31;margin:0 0 25px">ATELIER<span>.</span></div><div class="eyebrow">Salon yönetim sistemi</div><h1>Hoş geldiniz</h1><p class="muted">Yönetim panelinize giriş yapın.</p>{% with messages = get_flashed_messages() %}{% for m in messages %}<div class="flash">{{m}}</div>{% endfor %}{% endwith %}<div class="field" style="margin:18px 0"><label>Kullanıcı adı</label><input name="username" required autocomplete="username" placeholder="admin"></div><div class="field" style="margin-bottom:18px"><label>Şifre</label><input type="password" name="password" required autocomplete="current-password" placeholder="••••••••"></div><button class="btn goldbtn" style="width:100%;padding:13px">Giriş yap →</button><p class="muted" style="font-size:12px;margin-top:18px">İlk giriş: admin / Kuafor123!</p></form></body></html>""")

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    c=db()
    today=date.today().isoformat()
    appointments=c.execute("SELECT a.*,cu.name customer,s.name service,st.name staff FROM appointments a JOIN customers cu ON cu.id=a.customer_id LEFT JOIN services s ON s.id=a.service_id LEFT JOIN staff st ON st.id=a.staff_id WHERE substr(a.starts_at,1,10)=? ORDER BY a.starts_at",(today,)).fetchall()
    customers=c.execute("SELECT COUNT(*) n FROM customers").fetchone()["n"]
    sales=c.execute("SELECT COALESCE(SUM(amount),0) n FROM payments WHERE substr(paid_at,1,7)=?",(today[:7],)).fetchone()["n"]
    due=c.execute("SELECT COALESCE(SUM(p.total_price),0)-COALESCE((SELECT SUM(pay.amount) FROM payments pay WHERE pay.package_id=p.id),0) n FROM packages p").fetchone()["n"]
    upcoming=c.execute("SELECT COUNT(*) n FROM appointments WHERE starts_at>=? AND status='Bekliyor'",(datetime.now().strftime("%Y-%m-%dT%H:%M"),)).fetchone()["n"]
    body=render_template_string("""
    <div class="cards"><div class="card"><div class="metric-label">Bugünkü randevular</div><div class="metric">{{ ap|length }}</div><div class="metric-note">Bugün planlanan</div></div><div class="card"><div class="metric-label">Toplam müşteri</div><div class="metric">{{customers}}</div><div class="metric-note">Kayıtlı müşteri</div></div><div class="card"><div class="metric-label">Bu ay tahsilat</div><div class="metric">{{money(sales)}}</div><div class="metric-note">Kaydedilen ödemeler</div></div><div class="card"><div class="metric-label">Bekleyen bakiye</div><div class="metric">{{money(due)}}</div><div class="metric-note">Paket bazında hesaplanır</div></div></div>
    <div class="section-title"><h2>Bugünün randevuları</h2><a class="btn goldbtn" href="{{url_for('appointments')}}">+ Randevu ekle</a></div><div class="panel table-wrap"><table><thead><tr><th>Saat</th><th>Müşteri</th><th>Hizmet</th><th>Personel</th><th>Durum</th></tr></thead><tbody>{% for a in ap %}<tr><td><b>{{a.starts_at[11:16]}}</b></td><td>{{a.customer}}</td><td>{{a.service or '—'}}</td><td>{{a.staff or 'Atanmadı'}}</td><td><span class="badge {{'ok' if a.status=='Tamamlandı' else 'cancel' if a.status=='İptal' else 'warn'}}">{{a.status}}</span></td></tr>{% else %}<tr><td colspan="5" class="empty">Bugün için randevu yok. Yeni randevu ekleyebilirsiniz.</td></tr>{% endfor %}</tbody></table></div>
    <div class="section-title"><h2>Hızlı işlemler</h2></div><div class="actions"><a class="btn" href="{{url_for('customers')}}">+ Müşteri ekle</a><a class="btn ghost" href="{{url_for('payments')}}">₺ Tahsilat kaydet</a><a class="btn ghost" href="{{url_for('book')}}">Online randevuyu görüntüle ↗</a></div>
    """,ap=appointments,customers=customers,sales=sales,due=due,upcoming=upcoming,money=money)
    return page("Genel Bakış","Özet","dashboard",body)

@app.route("/customers",methods=["GET","POST"])
@login_required
def customers():
    c=db()
    if request.method=="POST":
        name=request.form.get("name","").strip(); phone=request.form.get("phone","").strip()
        if name and phone:
            cur=c.execute("INSERT INTO customers(name,phone,notes,created_at) VALUES(?,?,?,?)",(name,phone,request.form.get("notes","").strip(),datetime.now().isoformat(timespec="minutes")))
            cid=cur.lastrowid
            service_id=request.form.get("service_id") or None
            if request.form.get("package_title"):
                total=max(1,int(request.form.get("sessions") or 1)); price=max(0,float(request.form.get("price") or 0))
                c.execute("INSERT INTO packages(customer_id,service_id,title,total_sessions,total_price,created_at) VALUES(?,?,?,?,?,?)",(cid,service_id,request.form["package_title"],total,price,datetime.now().isoformat(timespec="minutes")))
            c.commit(); flash("Müşteri kaydedildi.")
        return redirect(url_for("customers"))
    rows=c.execute("""SELECT cu.*, (SELECT COUNT(*) FROM packages p WHERE p.customer_id=cu.id) package_count FROM customers cu ORDER BY cu.id DESC""").fetchall()
    sv=c.execute("SELECT * FROM services WHERE active=1 ORDER BY name").fetchall()
    body=render_template_string("""
    <div class="two"><div class="panel"><div class="section-title"><h2>Yeni müşteri ekle</h2></div><form method="post" class="formgrid"><div class="field"><label>Ad soyad *</label><input name="name" required></div><div class="field"><label>Telefon *</label><input name="phone" required type="tel"></div><div class="field full"><label>Müşteri notu</label><textarea name="notes" placeholder="Tercihler, alerji notları vb."></textarea></div><div class="field full"><label>İlk paket (isteğe bağlı)</label><input name="package_title" placeholder="Örn. Lazer 10 seans"></div><div class="field"><label>Hizmet</label><select name="service_id"><option value="">Seçiniz</option>{% for s in sv %}<option value="{{s.id}}">{{s.name}}</option>{% endfor %}</select></div><div class="field"><label>Toplam seans</label><input name="sessions" type="number" min="1" value="1"></div><div class="field full"><label>Paket tutarı (₺)</label><input name="price" type="number" min="0" step=".01" value="0"></div><div class="field full"><button class="btn goldbtn">Müşteriyi kaydet</button></div></form></div>
    <div class="panel"><div class="section-title"><h2>Müşteri kartları</h2><span class="badge">{{rows|length}} kayıt</span></div>{% for cu in rows %}<div style="padding:12px 0;border-bottom:1px solid #edf0f4"><b>{{cu.name}}</b><div class="muted" style="font-size:13px">{{cu.phone}}</div><div class="actions" style="margin-top:8px"><a class="btn small" href="{{url_for('customer_detail',cid=cu.id)}}">Kartı aç →</a></div></div>{% else %}<div class="empty">Henüz müşteri yok.</div>{% endfor %}</div></div>
    """,rows=rows,sv=sv)
    return page("Müşteriler & Seanslar","Müşteri yönetimi","customers",body)

@app.route("/customers/<int:cid>",methods=["GET","POST"])
@login_required
def customer_detail(cid):
    c=db(); cu=c.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone()
    if not cu: return redirect(url_for("customers"))
    if request.method=="POST":
        if request.form.get("action")=="package":
            sid=request.form.get("service_id") or None
            c.execute("INSERT INTO packages(customer_id,service_id,title,total_sessions,total_price,created_at) VALUES(?,?,?,?,?,?)",(cid,sid,request.form["title"],max(1,int(request.form.get("sessions") or 1)),max(0,float(request.form.get("price") or 0)),datetime.now().isoformat(timespec="minutes")))
            flash("Paket oluşturuldu.")
        elif request.form.get("action")=="payment":
            amount=max(0,float(request.form.get("amount") or 0)); pid=request.form.get("package_id") or None
            if amount>0: c.execute("INSERT INTO payments(customer_id,package_id,amount,method,note,paid_at) VALUES(?,?,?,?,?,?)",(cid,pid,amount,request.form.get("method","Nakit"),request.form.get("note",""),datetime.now().isoformat(timespec="minutes"))); flash("Tahsilat kaydedildi.")
        elif request.form.get("action")=="notes":
            c.execute("UPDATE customers SET notes=? WHERE id=?",(request.form.get("notes",""),cid)); flash("Not güncellendi.")
        c.commit(); return redirect(url_for("customer_detail",cid=cid))
    packs=c.execute("""SELECT p.*,s.name service, COALESCE((SELECT SUM(amount) FROM payments WHERE package_id=p.id),0) paid FROM packages p LEFT JOIN services s ON s.id=p.service_id WHERE p.customer_id=? ORDER BY p.id DESC""",(cid,)).fetchall()
    payments=c.execute("SELECT * FROM payments WHERE customer_id=? ORDER BY paid_at DESC",(cid,)).fetchall()
    sv=c.execute("SELECT * FROM services WHERE active=1").fetchall()
    pack_options=c.execute("SELECT * FROM packages WHERE customer_id=?",(cid,)).fetchall()
    body=render_template_string("""
    <div class="section-title"><h2>{{cu.name}}</h2><span class="pill">{{cu.phone}}</span></div><div class="two"><div>
    {% for p in packs %}<div class="panel"><div class="section-title"><h2>{{p.title}}</h2><span class="badge ok">{{p.total_sessions-p.used_sessions}} seans kaldı</span></div><div class="muted">{{p.service or 'Özel paket'}}</div><div style="display:flex;justify-content:space-between;margin-top:18px"><div><div class="metric-label">Toplam seans</div><b>{{p.total_sessions}}</b></div><div><div class="metric-label">Kullanılan</div><b>{{p.used_sessions}}</b></div><div><div class="metric-label">Kalan</div><b class="gold">{{p.total_sessions-p.used_sessions}}</b></div></div><div class="progress"><span style="width:{{(100*p.used_sessions/p.total_sessions) if p.total_sessions else 0}}%"></span></div><div style="margin-top:17px;display:flex;justify-content:space-between"><span class="muted">Paket tutarı</span><b>{{money(p.total_price)}}</b></div><div style="display:flex;justify-content:space-between"><span class="muted">Tahsilat</span><b>{{money(p.paid)}}</b></div><div style="display:flex;justify-content:space-between"><span class="muted">Kalan borç</span><b style="color:#a53d32">{{money(p.total_price-p.paid)}}</b></div></div>{% else %}<div class="panel empty">Bu müşteri için paket yok.</div>{% endfor %}
    <div class="panel"><h2 style="font-size:16px">Ödeme geçmişi</h2><table><thead><tr><th>Tarih</th><th>Tutar</th><th>Yöntem</th></tr></thead><tbody>{% for p in payments %}<tr><td>{{p.paid_at[:16].replace('T',' ')}}</td><td>{{money(p.amount)}}</td><td>{{p.method}}</td></tr>{% else %}<tr><td colspan="3" class="empty">Ödeme kaydı yok.</td></tr>{% endfor %}</tbody></table></div></div>
    <div><div class="panel"><h2 style="font-size:16px">Yeni paket oluştur</h2><form method="post" class="formgrid"><input type="hidden" name="action" value="package"><div class="field full"><label>Paket adı</label><input name="title" required placeholder="Örn. Bakım paketi"></div><div class="field full"><label>Hizmet</label><select name="service_id"><option value="">Özel paket</option>{% for s in sv %}<option value="{{s.id}}">{{s.name}}</option>{% endfor %}</select></div><div class="field"><label>Seans</label><input name="sessions" type="number" min="1" value="5"></div><div class="field"><label>Tutar ₺</label><input name="price" type="number" min="0" step=".01" required></div><div class="field full"><button class="btn goldbtn">Paketi ekle</button></div></form></div>
    <div class="panel"><h2 style="font-size:16px">Tahsilat kaydet</h2><form method="post" class="formgrid"><input type="hidden" name="action" value="payment"><div class="field full"><label>İlgili paket</label><select name="package_id"><option value="">Paketsiz / genel ödeme</option>{% for p in packs %}<option value="{{p.id}}">{{p.title}} — kalan {{money(p.total_price-p.paid)}}</option>{% endfor %}</select></div><div class="field full"><label>Tutar ₺</label><input name="amount" type="number" min=".01" step=".01" required></div><div class="field full"><label>Ödeme yöntemi</label><select name="method"><option>Nakit</option><option>Kredi/Banka kartı</option><option>Havale/EFT</option></select></div><div class="field full"><label>Not</label><input name="note"></div><div class="field full"><button class="btn">Tahsilatı kaydet</button></div></form></div>
    <div class="panel"><h2 style="font-size:16px">Müşteri notları</h2><form method="post"><input type="hidden" name="action" value="notes"><textarea name="notes">{{cu.notes}}</textarea><button class="btn ghost" style="margin-top:10px">Notu güncelle</button></form></div></div></div>
    """,cu=cu,packs=packs,payments=payments,sv=sv,money=money)
    return page("Müşteri Kartı","Müşteri yönetimi","customers",body)

@app.route("/appointments",methods=["GET","POST"])
@login_required
def appointments():
    c=db()
    if request.method=="POST":
        cid=request.form.get("customer_id")
        if request.form.get("new_name") and request.form.get("new_phone"):
            cur=c.execute("INSERT INTO customers(name,phone,created_at) VALUES(?,?,?)",(request.form["new_name"].strip(),request.form["new_phone"].strip(),datetime.now().isoformat(timespec="minutes"))); cid=cur.lastrowid
        if cid and request.form.get("starts_at"):
            c.execute("INSERT INTO appointments(customer_id,service_id,staff_id,package_id,starts_at,status,note,created_at) VALUES(?,?,?,?,?,?,?,?)",(cid,request.form.get("service_id") or None,request.form.get("staff_id") or None,request.form.get("package_id") or None,request.form["starts_at"],"Bekliyor",request.form.get("note",""),datetime.now().isoformat(timespec="minutes")))
            c.commit(); flash("Randevu kaydedildi.")
        return redirect(url_for("appointments"))
    rows=c.execute("SELECT a.*,cu.name customer,cu.phone,s.name service,st.name staff FROM appointments a JOIN customers cu ON cu.id=a.customer_id LEFT JOIN services s ON s.id=a.service_id LEFT JOIN staff st ON st.id=a.staff_id ORDER BY a.starts_at DESC LIMIT 100").fetchall()
    cust=c.execute("SELECT * FROM customers ORDER BY name").fetchall(); sv=c.execute("SELECT * FROM services WHERE active=1").fetchall(); staff_rows=c.execute("SELECT * FROM staff WHERE active=1").fetchall()
    packs=c.execute("SELECT p.*,cu.name customer FROM packages p JOIN customers cu ON cu.id=p.customer_id WHERE p.used_sessions<p.total_sessions").fetchall()
    body=render_template_string("""
    <div class="two"><div class="panel"><h2 style="font-size:16px">Randevu oluştur</h2><form method="post" class="formgrid"><div class="field full"><label>Kayıtlı müşteri</label><select name="customer_id"><option value="">Yeni müşteri ekle veya seç</option>{% for cu in cust %}<option value="{{cu.id}}">{{cu.name}} · {{cu.phone}}</option>{% endfor %}</select></div><div class="field"><label>Yeni müşteri adı</label><input name="new_name" placeholder="Ad soyad"></div><div class="field"><label>Yeni müşteri telefonu</label><input name="new_phone" type="tel" placeholder="05xx..."></div><div class="field full"><label>Tarih ve saat *</label><input type="datetime-local" name="starts_at" required></div><div class="field"><label>Hizmet</label><select name="service_id"><option value="">Seçiniz</option>{% for s in sv %}<option value="{{s.id}}">{{s.name}} · {{money(s.price)}}</option>{% endfor %}</select></div><div class="field"><label>Personel</label><select name="staff_id"><option value="">Atanmamış</option>{% for st in staff_rows %}<option value="{{st.id}}">{{st.name}}</option>{% endfor %}</select></div><div class="field full"><label>Paket / seans (isteğe bağlı)</label><select name="package_id"><option value="">Paket seçilmedi</option>{% for p in packs %}<option value="{{p.id}}">{{p.customer}} · {{p.title}} ({{p.total_sessions-p.used_sessions}} seans kaldı)</option>{% endfor %}</select></div><div class="field full"><label>Not</label><input name="note" placeholder="İsteğe bağlı"></div><div class="field full"><button class="btn goldbtn">Randevuyu kaydet</button></div></form></div>
    <div class="panel"><div class="section-title"><h2>Randevu listesi</h2><span class="badge">{{rows|length}} kayıt</span></div><div class="table-wrap"><table><thead><tr><th>Tarih / Saat</th><th>Müşteri</th><th>Hizmet / Personel</th><th>Durum</th><th>İşlem</th></tr></thead><tbody>{% for a in rows %}<tr><td>{{a.starts_at.replace('T',' ')}}</td><td><b>{{a.customer}}</b><div class="muted">{{a.phone}}</div></td><td>{{a.service or '—'}}<div class="muted">{{a.staff or '—'}}</div></td><td><span class="badge {{'ok' if a.status=='Tamamlandı' else 'cancel' if a.status=='İptal' else 'warn'}}">{{a.status}}</span></td><td><div class="actions"><form method="post" action="{{url_for('appointment_status',aid=a.id)}}"><input type="hidden" name="status" value="Tamamlandı"><button class="btn small">Tamamla</button></form><form method="post" action="{{url_for('appointment_status',aid=a.id)}}"><input type="hidden" name="status" value="İptal"><button class="btn small danger">İptal</button></form></div></td></tr>{% else %}<tr><td colspan="5" class="empty">Henüz randevu yok.</td></tr>{% endfor %}</tbody></table></div></div></div>
    """,rows=rows,cust=cust,sv=sv,staff_rows=staff_rows,packs=packs,money=money)
    return page("Randevular","Takvim ve planlama","appointments",body)

@app.route("/appointments/<int:aid>/status",methods=["POST"])
@login_required
def appointment_status(aid):
    status=request.form.get("status")
    if status not in ("Tamamlandı","İptal","Bekliyor"): return redirect(url_for("appointments"))
    c=db(); old=c.execute("SELECT * FROM appointments WHERE id=?",(aid,)).fetchone()
    if old:
        if status=="Tamamlandı" and old["status"]!="Tamamlandı" and old["package_id"]:
            p=c.execute("SELECT * FROM packages WHERE id=?",(old["package_id"],)).fetchone()
            if p and p["used_sessions"]<p["total_sessions"]:
                c.execute("UPDATE packages SET used_sessions=used_sessions+1 WHERE id=?",(p["id"],))
        if old["status"]=="Tamamlandı" and status!="Tamamlandı" and old["package_id"]:
            c.execute("UPDATE packages SET used_sessions=MAX(0,used_sessions-1) WHERE id=?",(old["package_id"],))
        c.execute("UPDATE appointments SET status=? WHERE id=?",(status,aid)); c.commit()
    flash("Randevu durumu güncellendi.")
    return redirect(url_for("appointments"))

@app.route("/services",methods=["GET","POST"])
@login_required
def services():
    c=db()
    if request.method=="POST":
        name=request.form.get("name","").strip()
        if name:
            c.execute("INSERT INTO services(name,price,duration,sessions) VALUES(?,?,?,?)",(name,max(0,float(request.form.get("price") or 0)),max(5,int(request.form.get("duration") or 30)),max(1,int(request.form.get("sessions") or 1))))
            c.commit(); flash("Hizmet/paket eklendi.")
        return redirect(url_for("services"))
    rows=c.execute("SELECT * FROM services ORDER BY active DESC,name").fetchall()
    body=render_template_string("""<div class="two"><div class="panel"><h2 style="font-size:16px">Hizmet / paket tanımla</h2><form method="post" class="formgrid"><div class="field full"><label>Hizmet adı</label><input name="name" required placeholder="Örn. Keratin bakım"></div><div class="field"><label>Fiyat (₺)</label><input name="price" type="number" min="0" step=".01" required></div><div class="field"><label>Süre (dakika)</label><input name="duration" type="number" min="5" value="30"></div><div class="field full"><label>Varsayılan seans sayısı</label><input name="sessions" type="number" min="1" value="1"></div><div class="field full"><button class="btn goldbtn">Hizmeti ekle</button></div></form></div><div class="panel"><h2 style="font-size:16px">Tanımlı hizmetler</h2><table><thead><tr><th>Hizmet</th><th>Süre</th><th>Seans</th><th>Fiyat</th></tr></thead><tbody>{% for s in rows %}<tr><td><b>{{s.name}}</b></td><td>{{s.duration}} dk</td><td>{{s.sessions}}</td><td>{{money(s.price)}}</td></tr>{% else %}<tr><td colspan="4" class="empty">Hizmet eklenmemiş.</td></tr>{% endfor %}</tbody></table></div></div>""",rows=rows,money=money)
    return page("Hizmet & Paketler","Salon ayarları","services",body)

@app.route("/payments")
@login_required
def payments():
    c=db()
    rows=c.execute("SELECT pay.*,cu.name customer,p.title package FROM payments pay JOIN customers cu ON cu.id=pay.customer_id LEFT JOIN packages p ON p.id=pay.package_id ORDER BY pay.paid_at DESC LIMIT 200").fetchall()
    total=c.execute("SELECT COALESCE(SUM(amount),0) n FROM payments").fetchone()["n"]
    body=render_template_string("""<div class="cards"><div class="card"><div class="metric-label">Toplam tahsilat</div><div class="metric">{{money(total)}}</div><div class="metric-note">Tüm kayıtlı ödemeler</div></div><div class="card"><div class="metric-label">İşlem sayısı</div><div class="metric">{{rows|length}}</div><div class="metric-note">Son 200 işlem gösterilir</div></div></div><div class="panel"><div class="section-title"><h2>Tahsilat geçmişi</h2><a class="btn goldbtn" href="{{url_for('customers')}}">Müşteri kartından tahsilat ekle</a></div><div class="table-wrap"><table><thead><tr><th>Tarih</th><th>Müşteri</th><th>Paket</th><th>Yöntem</th><th>Tutar</th><th>Not</th></tr></thead><tbody>{% for p in rows %}<tr><td>{{p.paid_at[:16].replace('T',' ')}}</td><td>{{p.customer}}</td><td>{{p.package or 'Genel ödeme'}}</td><td>{{p.method}}</td><td><b>{{money(p.amount)}}</b></td><td>{{p.note}}</td></tr>{% else %}<tr><td colspan="6" class="empty">Henüz tahsilat yok.</td></tr>{% endfor %}</tbody></table></div></div>""",rows=rows,total=total,money=money)
    return page("Tahsilatlar","Finans","payments",body)

@app.route("/staff",methods=["GET","POST"])
@login_required
def staff():
    c=db()
    if request.method=="POST":
        name=request.form.get("name","").strip()
        if name: c.execute("INSERT INTO staff(name) VALUES(?)",(name,)); c.commit(); flash("Personel eklendi.")
        return redirect(url_for("staff"))
    rows=c.execute("SELECT st.*, (SELECT COUNT(*) FROM appointments a WHERE a.staff_id=st.id AND a.status!='İptal') cnt FROM staff st ORDER BY st.active DESC,st.name").fetchall()
    body=render_template_string("""<div class="two"><div class="panel"><h2 style="font-size:16px">Personel ekle</h2><form method="post"><div class="field"><label>Ad soyad</label><input name="name" required></div><button class="btn goldbtn" style="margin-top:14px">Personeli ekle</button></form></div><div class="panel"><h2 style="font-size:16px">Personel listesi</h2><table><thead><tr><th>Personel</th><th>Randevu sayısı</th><th>Durum</th></tr></thead><tbody>{% for s in rows %}<tr><td><b>{{s.name}}</b></td><td>{{s.cnt}}</td><td><span class="badge ok">Aktif</span></td></tr>{% else %}<tr><td colspan="3" class="empty">Personel yok.</td></tr>{% endfor %}</tbody></table></div></div>""",rows=rows)
    return page("Personel","Salon ayarları","staff",body)

@app.route("/reports")
@login_required
def reports():
    c=db()
    months=c.execute("SELECT substr(paid_at,1,7) month, SUM(amount) total, COUNT(*) count FROM payments GROUP BY substr(paid_at,1,7) ORDER BY month DESC LIMIT 12").fetchall()
    services=c.execute("SELECT s.name,COUNT(a.id) cnt FROM services s LEFT JOIN appointments a ON a.service_id=s.id AND a.status='Tamamlandı' GROUP BY s.id ORDER BY cnt DESC").fetchall()
    total=c.execute("SELECT COALESCE(SUM(amount),0) n FROM payments").fetchone()["n"]
    due=c.execute("SELECT COALESCE(SUM(p.total_price),0)-COALESCE((SELECT SUM(pay.amount) FROM payments pay WHERE pay.package_id=p.id),0) n FROM packages p").fetchone()["n"]
    body=render_template_string("""<div class="cards"><div class="card"><div class="metric-label">Toplam tahsilat</div><div class="metric">{{money(total)}}</div><div class="metric-note">Tüm dönem</div></div><div class="card"><div class="metric-label">Açık paket bakiyesi</div><div class="metric">{{money(due)}}</div><div class="metric-note">Paket ödemelerine göre</div></div></div><div class="two"><div class="panel"><h2 style="font-size:16px">Aylık tahsilat</h2><table><thead><tr><th>Ay</th><th>İşlem</th><th>Toplam</th></tr></thead><tbody>{% for m in months %}<tr><td>{{m.month}}</td><td>{{m.count}}</td><td><b>{{money(m.total)}}</b></td></tr>{% else %}<tr><td colspan="3" class="empty">Rapor için ödeme kaydı gerekli.</td></tr>{% endfor %}</tbody></table></div><div class="panel"><h2 style="font-size:16px">Tamamlanan hizmetler</h2><table><thead><tr><th>Hizmet</th><th>Adet</th></tr></thead><tbody>{% for s in services %}<tr><td>{{s.name}}</td><td>{{s.cnt}}</td></tr>{% endfor %}</tbody></table><p class="muted" style="font-size:12px">Tahsilat raporu kaydedilen ödemeleri esas alır; hizmet adedi tamamlanan randevulardan hesaplanır.</p></div></div>""",months=months,services=services,total=total,due=due,money=money)
    return page("Gelir Raporları","Raporlama","reports",body)

@app.route("/book",methods=["GET","POST"])
def book():
    c=db()
    if request.method=="POST":
        name=request.form.get("name","").strip(); phone=request.form.get("phone","").strip(); starts=request.form.get("starts_at","")
        sid=request.form.get("service_id") or None; staff_id=request.form.get("staff_id") or None
        if name and phone and starts:
            try:
                datetime.fromisoformat(starts)
                cu=c.execute("SELECT * FROM customers WHERE phone=?",(phone,)).fetchone()
                if not cu:
                    cur=c.execute("INSERT INTO customers(name,phone,created_at) VALUES(?,?,?)",(name,phone,datetime.now().isoformat(timespec="minutes"))); cid=cur.lastrowid
                else: cid=cu["id"]
                c.execute("INSERT INTO appointments(customer_id,service_id,staff_id,starts_at,status,note,public_booking,created_at) VALUES(?,?,?,?,?,?,1,?)",(cid,sid,staff_id,starts,"Bekliyor",request.form.get("note",""),datetime.now().isoformat(timespec="minutes")))
                c.commit(); return render_template_string("""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>"""+STYLE+"""</style></head><body class="auth"><div class="authbox"><div class="brand" style="color:#101b31">ATELIER<span>.</span></div><h1>Talebiniz alındı ✦</h1><p>Randevu talebiniz salona iletildi. Salon tarafından onaylanması gerekir.</p><a class="btn goldbtn" href="{{url_for('book')}}">Yeni randevu oluştur</a></div></body></html>""")
            except ValueError: flash("Lütfen geçerli tarih ve saat seçin.")
    sv=c.execute("SELECT * FROM services WHERE active=1 ORDER BY name").fetchall()
    staff_rows=c.execute("SELECT * FROM staff WHERE active=1 ORDER BY name").fetchall()
    return render_template_string("""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Online Randevu · Atelier</title><style>"""+STYLE+"""</style></head><body><header class="publichead"><div class="brand">ATELIER<span>.</span></div><span class="gold">Kendinize zaman ayırın</span></header><div class="publicbody"><div class="publichero"><div class="eyebrow" style="color:#d6b36a">ONLINE RANDEVU</div><h1>Güzelliğiniz için<br>doğru zaman.</h1><p>Size uygun hizmeti ve zamanı seçerek randevu talebinizi oluşturun.</p></div>{% with messages = get_flashed_messages() %}{% for m in messages %}<div class="flash">{{m}}</div>{% endfor %}{% endwith %}<div class="panel"><h2 style="margin-top:0">Randevu talebi oluştur</h2><form method="post" class="formgrid"><div class="field"><label>Ad soyad *</label><input name="name" required></div><div class="field"><label>Telefon *</label><input name="phone" type="tel" required placeholder="05xx xxx xx xx"></div><div class="field"><label>Hizmet *</label><select name="service_id" required><option value="">Hizmet seçin</option>{% for s in sv %}<option value="{{s.id}}">{{s.name}} · {{money(s.price)}}</option>{% endfor %}</select></div><div class="field"><label>Personel tercihi</label><select name="staff_id"><option value="">Fark etmez</option>{% for st in staff_rows %}<option value="{{st.id}}">{{st.name}}</option>{% endfor %}</select></div><div class="field"><label>Tarih ve saat *</label><input type="datetime-local" name="starts_at" required min="{{min_date}}"></div><div class="field"><label>Not (isteğe bağlı)</label><input name="note" placeholder="Tercih ettiğiniz saat vb."></div><div class="field full"><button class="btn goldbtn" style="padding:13px">Randevu talebi gönder →</button></div></form><p class="muted" style="font-size:12px">Randevu talebi, salon onayından sonra kesinleşir.</p></div><div class="footer">ATELIER · Özenle sizin için</div></div></body></html>""",sv=sv,staff_rows=staff_rows,money=money,min_date=datetime.now().strftime("%Y-%m-%dT%H:%M"))

@app.route("/health")
def health(): return {"status":"ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)

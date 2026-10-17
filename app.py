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
    CREATE TABLE IF NOT EXISTS customer_accounts(id INTEGER PRIMARY KEY, customer_id INTEGER UNIQUE NOT NULL REFERENCES customers(id), username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT NOT NULL);
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
:root{--navy:#382832;--navy2:#503744;--gold:#ed9ba8;--cream:#fff6f3;--ink:#30252b;--muted:#927f88;--line:#f1dce2;--white:#fff}
*{box-sizing:border-box}body{margin:0;background:#fff8f7;color:var(--ink);font:15px/1.5 Inter,system-ui,-apple-system,Segoe UI,sans-serif}
a{color:inherit;text-decoration:none}.layout{display:flex;min-height:100vh}.sidebar{width:245px;background:var(--navy);color:#e8edf5;padding:26px 18px;flex-shrink:0}.brand{font-size:21px;font-weight:800;letter-spacing:.4px;margin:4px 12px 4px}.brand span{color:var(--gold)}.subbrand{color:#9da9bc;font-size:11px;letter-spacing:2px;margin:0 12px 32px;text-transform:uppercase}.nav a{display:block;padding:12px 14px;border-radius:11px;margin:5px 0;color:#bdc7d7}.nav a:hover,.nav a.active{background:#49343e;color:#fff}.nav a.active{border-left:3px solid var(--gold)}.nav .public{margin-top:24px;color:var(--gold)}.main{flex:1;min-width:0;padding:30px clamp(16px,3vw,42px)}.top{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:26px}.eyebrow{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:1.5px}.h1{font-size:28px;font-weight:800;margin:3px 0}.topright{display:flex;gap:10px;align-items:center}.pill{border:1px solid var(--line);border-radius:30px;padding:8px 12px;background:#fff;font-size:13px}.gold{color:#8d6b22}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px;margin-bottom:24px}.card,.panel{background:#fff;border:1px solid #e8ebf1;border-radius:17px;padding:20px;box-shadow:0 4px 18px #1a294008}.metric-label{font-size:13px;color:var(--muted)}.metric{font-size:28px;font-weight:800;margin:9px 0 2px}.metric-note{font-size:12px;color:var(--muted)}.section-title{display:flex;justify-content:space-between;align-items:center;margin:8px 0 14px;gap:12px}.section-title h2{font-size:17px;margin:0}.panel{margin-bottom:20px;padding:20px}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;white-space:nowrap}th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);padding:12px 10px;border-bottom:1px solid var(--line)}td{padding:14px 10px;border-bottom:1px solid #f0f2f6;font-size:14px}tr:last-child td{border-bottom:0}.btn{display:inline-flex;align-items:center;justify-content:center;background:var(--navy);color:#fff;border:0;border-radius:10px;padding:10px 15px;font-weight:700;cursor:pointer;font-size:13px}.btn.goldbtn{background:var(--gold);color:#211b10}.btn.ghost{background:#f0f2f6;color:#28344a}.btn.danger{background:#fff0ee;color:#a2392c}.btn.small{padding:7px 10px;font-size:12px}.formgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.field{display:flex;flex-direction:column;gap:6px}.field.full{grid-column:1/-1}label{font-size:12px;color:#596477;font-weight:700}input,select,textarea{width:100%;padding:11px 12px;border:1px solid #dfe4ec;border-radius:10px;background:#fff;color:var(--ink);font:inherit;outline:none}input:focus,select:focus,textarea:focus{border-color:var(--gold);box-shadow:0 0 0 3px #e98d9b22}textarea{min-height:84px;resize:vertical}.actions{display:flex;gap:8px;flex-wrap:wrap}.badge{display:inline-block;border-radius:30px;padding:5px 9px;font-size:11px;font-weight:700;background:#eef2f8;color:#43516a}.badge.ok{background:#e6f6ec;color:#237447}.badge.warn{background:#fff3d9;color:#8a641a}.badge.cancel{background:#fde9e7;color:#a53d32}.flash{padding:12px 15px;background:#fff5db;border:1px solid #f2d68d;border-radius:10px;margin-bottom:14px}.empty{padding:28px;text-align:center;color:var(--muted)}.muted{color:var(--muted)}.progress{height:7px;background:#edf0f4;border-radius:10px;overflow:hidden;margin-top:8px}.progress span{display:block;height:100%;background:var(--gold)}.auth{min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at 80% 20%,#704b5b,var(--navy) 55%);padding:20px}.authbox{width:min(430px,100%);background:#fff;padding:34px;border-radius:22px;box-shadow:0 20px 80px #0003}.authbox h1{margin:0 0 6px}.publichead{background:var(--navy);color:white;padding:20px clamp(18px,5vw,70px);display:flex;justify-content:space-between;align-items:center}.publicbody{max-width:900px;margin:35px auto;padding:0 18px}.publichero{background:var(--navy);color:white;border-radius:20px;padding:28px;margin-bottom:20px}.publichero h1{margin:0 0 8px;font-size:30px}.publichero p{color:#c7d1df;margin:0}.two{display:grid;grid-template-columns:1.1fr .9fr;gap:18px}.footer{text-align:center;color:var(--muted);font-size:12px;padding:20px}@media(max-width:900px){.sidebar{width:190px}.cards{grid-template-columns:repeat(2,minmax(0,1fr))}.two{grid-template-columns:1fr}}@media(max-width:650px){.layout{display:block}.sidebar{width:100%;padding:15px}.subbrand{margin-bottom:12px}.nav{display:flex;overflow:auto;gap:4px}.nav a{white-space:nowrap;padding:9px 11px}.nav .public{margin-top:5px}.main{padding:20px 14px}.top{align-items:flex-start}.h1{font-size:23px}.cards{gap:9px}.card{padding:14px}.metric{font-size:22px}.formgrid{grid-template-columns:1fr}.field.full{grid-column:auto}.panel{padding:14px}}
/* NUR BEAUTY salon theme */
.sidebar{background:linear-gradient(165deg,#35242f,#503442 70%,#30242b)}
.brand{letter-spacing:1px}.subbrand{color:#e4cbd2}
.nav a.active{background:linear-gradient(110deg,#f7c0c6,#ed9ba8);color:#35242f;border-left:0;box-shadow:0 5px 15px #ed9ba833}
.btn{background:#49313d}.btn.goldbtn{background:linear-gradient(120deg,#f5c0c6,#e98d9b);color:#382832}.card,.panel{border-color:#f2dfe3;box-shadow:0 8px 24px #6e3e4d0a}
.publichead{background:#382832;border-bottom:3px solid #ed9ba8}.publicbody{max-width:1000px;margin:24px auto 50px}
.publichero{position:relative;overflow:hidden;min-height:250px;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(90deg,rgba(56,40,50,.96),rgba(56,40,50,.78) 48%,rgba(56,40,50,.1)),url('https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=1600&q=85') center/cover;border-radius:24px;padding:clamp(24px,5vw,48px)}
.publichero h1{font-size:clamp(30px,5vw,48px);line-height:1.12;max-width:540px}.publichero p{max-width:440px;color:#f5e7eb}.publichero .eyebrow{color:#f6b8c3!important;letter-spacing:2px}
.booking-layout{display:grid;grid-template-columns:1fr .7fr;gap:18px;align-items:start}.service-visual{min-height:180px;border-radius:18px;background:linear-gradient(0deg,rgba(56,40,50,.88),rgba(56,40,50,.04)),url('https://images.unsplash.com/photo-1560066984-138dadb4c035?auto=format&fit=crop&w=1000&q=80') center/cover;color:#fff;padding:20px;display:flex;flex-direction:column;justify-content:end;margin-bottom:14px}.service-visual strong{font-size:20px}.service-chips{display:flex;flex-wrap:wrap;gap:8px}.service-chip{border:1px solid #f1dce2;border-radius:30px;background:#fff;padding:8px 11px;font-size:12px;color:#634553}
.booking-card{background:#fff;border:1px solid #f1dce2;border-radius:22px;padding:clamp(16px,3vw,26px);box-shadow:0 12px 35px #6e3e4d0d}.booking-card h2{margin:0 0 5px}.booking-intro{margin:0 0 18px;color:#927f88;font-size:13px}.booking-card input,.booking-card select,.booking-card textarea{border-color:#ead8df;background:#fffdfd;padding:13px}.booking-card .btn{width:100%;padding:14px;font-size:15px;border-radius:13px}.secure-note{display:flex;gap:8px;align-items:flex-start;background:#fff6f3;border-radius:12px;padding:12px;color:#785b68;font-size:12px;margin-top:14px}
@media(max-width:700px){.booking-layout{grid-template-columns:1fr}.publichero{min-height:230px}.publichead{padding:17px 18px}.publichead .gold{font-size:12px}.publicbody{margin-top:15px}.publichero{border-radius:18px}.booking-card{padding:17px}}
"""
BASE = """
<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{ title }} · Nur Beauty</title><style>""" + STYLE + """</style></head><body><div class="layout"><aside class="sidebar"><div class="brand">NUR BEAUTY<span>.</span></div><div class="subbrand">Salon yönetim sistemi</div><nav class="nav">
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
{{ body|safe }}<div class="footer">NUR BEAUTY · Randevu ve müşteri deneyimi</div></main></div>
<script>
// Admin browser notifications while the management panel is open.
(async function(){
 if (!location.pathname.startsWith('/login') && !location.pathname.startsWith('/customer/')) {
   let seen = new Set(JSON.parse(sessionStorage.getItem('nurSeenBookings') || '[]'));
   async function checkAdmin(){ try {
     const r=await fetch('/api/admin/new-bookings'); if(!r.ok)return; const items=await r.json();
     for(const a of items){ if(!seen.has(a.id)){ seen.add(a.id); if('Notification' in window){ if(Notification.permission==='granted') new Notification('NUR BEAUTY · Yeni randevu talebi',{body:a.customer+' · '+a.service+' · '+a.starts_at.replace('T',' ')}); else if(Notification.permission==='default') Notification.requestPermission(); } }
     }
     sessionStorage.setItem('nurSeenBookings',JSON.stringify([...seen].slice(-100)));
   }catch(e){} }
   checkAdmin(); setInterval(checkAdmin,20000);
 }
})();
</script></body></html>
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
    return render_template_string("""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Nur Beauty giriş</title><style>"""+STYLE+"""</style></head><body class="auth"><form class="authbox" method="post"><div class="brand" style="color:#292126;margin:0 0 25px">NUR BEAUTY<span>.</span></div><div class="eyebrow">Salon yönetim sistemi</div><h1>Hoş geldiniz</h1><p class="muted">Yönetim panelinize giriş yapın.</p>{% with messages = get_flashed_messages() %}{% for m in messages %}<div class="flash">{{m}}</div>{% endfor %}{% endwith %}<div class="field" style="margin:18px 0"><label>Kullanıcı adı</label><input name="username" required autocomplete="username" placeholder="admin"></div><div class="field" style="margin-bottom:18px"><label>Şifre</label><input type="password" name="password" required autocomplete="current-password" placeholder="••••••••"></div><button class="btn goldbtn" style="width:100%;padding:13px">Giriş yap →</button><p class="muted" style="font-size:12px;margin-top:18px">İlk giriş: admin / Kuafor123!</p></form></body></html>""")

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
    <div class="panel"><div class="section-title"><h2>Randevu listesi</h2><span class="badge">{{rows|length}} kayıt</span></div><div class="table-wrap"><table><thead><tr><th>Tarih / Saat</th><th>Müşteri</th><th>Hizmet / Personel</th><th>Durum</th><th>İşlem</th></tr></thead><tbody>{% for a in rows %}<tr><td>{{a.starts_at.replace('T',' ')}}</td><td><b>{{a.customer}}</b><div class="muted">{{a.phone}}</div></td><td>{{a.service or '—'}}<div class="muted">{{a.staff or '—'}}</div></td><td><span class="badge {{'ok' if a.status=='Tamamlandı' else 'cancel' if a.status=='İptal' else 'warn'}}">{{a.status}}</span></td><td><div class="actions"><form method="post" action="{{url_for('appointment_status',aid=a.id)}}"><input type="hidden" name="status" value="Onaylandı"><button class="btn small">Onayla</button></form><form method="post" action="{{url_for('appointment_status',aid=a.id)}}"><input type="hidden" name="status" value="Tamamlandı"><button class="btn small">Tamamla</button></form><form method="post" action="{{url_for('appointment_status',aid=a.id)}}"><input type="hidden" name="status" value="İptal"><button class="btn small danger">İptal</button></form></div></td></tr>{% else %}<tr><td colspan="5" class="empty">Henüz randevu yok.</td></tr>{% endfor %}</tbody></table></div></div></div>
    """,rows=rows,cust=cust,sv=sv,staff_rows=staff_rows,packs=packs,money=money)
    return page("Randevular","Takvim ve planlama","appointments",body)

@app.route("/appointments/<int:aid>/status",methods=["POST"])
@login_required
def appointment_status(aid):
    status=request.form.get("status")
    if status not in ("Tamamlandı","İptal","Bekliyor","Onaylandı"): return redirect(url_for("appointments"))
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

@app.route("/customer/register", methods=["GET", "POST"])
def customer_register():
    c = db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if not name or not phone or not username or len(password) < 8:
            flash("Tüm alanları doldurun. Şifre en az 8 karakter olmalı.")
        elif password != confirm:
            flash("Şifreler eşleşmiyor.")
        elif c.execute("SELECT id FROM customer_accounts WHERE username=?", (username,)).fetchone():
            flash("Bu kullanıcı adı kullanılıyor. Başka bir kullanıcı adı seçin.")
        else:
            now = datetime.now().isoformat(timespec="minutes")
            try:
                cur = c.execute("INSERT INTO customers(name,phone,created_at) VALUES(?,?,?)", (name, phone, now))
                cid = cur.lastrowid
                c.execute("INSERT INTO customer_accounts(customer_id,username,password_hash,created_at) VALUES(?,?,?,?)", (cid, username, generate_password_hash(password), now))
                c.commit()
                session.clear(); session["customer_id"] = cid; session["customer_username"] = username
                flash("Hesabınız oluşturuldu. Artık randevu alabilirsiniz.")
                return redirect(url_for("book"))
            except sqlite3.IntegrityError:
                c.rollback(); flash("Kayıt tamamlanamadı. Kullanıcı adınızı kontrol edin.")
    return render_template_string("""<!doctype html><html lang='tr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Üye Ol · NUR BEAUTY</title><style>"""+STYLE+"""</style></head><body class='auth'><form class='authbox' method='post'><div class='brand' style='color:#382832'>NUR BEAUTY<span>.</span></div><p class='eyebrow' style='margin-top:18px'>MÜŞTERİ HESABI</p><h1>Aramıza hoş geldiniz</h1><p class='muted'>Hesabınızı oluşturun, randevularınızı tek yerden takip edin.</p>{% with messages=get_flashed_messages() %}{% for m in messages %}<div class='flash'>{{m}}</div>{% endfor %}{% endwith %}<div class='field' style='margin:14px 0'><label>Ad soyad</label><input name='name' required autocomplete='name'></div><div class='field' style='margin:14px 0'><label>Telefon</label><input name='phone' type='tel' required autocomplete='tel' placeholder='05xx xxx xx xx'></div><div class='field' style='margin:14px 0'><label>Kullanıcı adı</label><input name='username' required minlength='3' autocomplete='username'></div><div class='field' style='margin:14px 0'><label>Şifre (en az 8 karakter)</label><input name='password' type='password' required minlength='8' autocomplete='new-password'></div><div class='field' style='margin:14px 0'><label>Şifreyi tekrar girin</label><input name='confirm' type='password' required minlength='8' autocomplete='new-password'></div><button class='btn goldbtn' style='width:100%;padding:13px'>Hesap oluştur</button><p class='muted' style='margin-top:18px'>Zaten hesabınız var mı? <a href='{{url_for("customer_login")}}'><b>Giriş yap</b></a></p></form></body></html>""")

@app.route("/customer/login", methods=["GET", "POST"])
def customer_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        account = db().execute("SELECT * FROM customer_accounts WHERE username=?", (username,)).fetchone()
        if account and check_password_hash(account["password_hash"], request.form.get("password", "")):
            session.clear(); session["customer_id"] = account["customer_id"]; session["customer_username"] = account["username"]
            return redirect(url_for("book"))
        flash("Kullanıcı adı veya şifre hatalı.")
    return render_template_string("""<!doctype html><html lang='tr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Müşteri Girişi · NUR BEAUTY</title><style>"""+STYLE+"""</style></head><body class='auth'><form class='authbox' method='post'><div class='brand' style='color:#382832'>NUR BEAUTY<span>.</span></div><p class='eyebrow' style='margin-top:18px'>MÜŞTERİ GİRİŞİ</p><h1>Tekrar hoş geldiniz</h1><p class='muted'>Randevu almak ve randevularınızı görüntülemek için giriş yapın.</p>{% with messages=get_flashed_messages() %}{% for m in messages %}<div class='flash'>{{m}}</div>{% endfor %}{% endwith %}<div class='field' style='margin:18px 0'><label>Kullanıcı adı</label><input name='username' required autocomplete='username'></div><div class='field' style='margin-bottom:18px'><label>Şifre</label><input name='password' type='password' required autocomplete='current-password'></div><button class='btn goldbtn' style='width:100%;padding:13px'>Giriş yap</button><p class='muted' style='margin-top:18px'>Hesabınız yok mu? <a href='{{url_for("customer_register")}}'><b>Üye olun</b></a></p></form></body></html>""")

@app.route("/customer/logout")
def customer_logout():
    session.pop("customer_id", None); session.pop("customer_username", None)
    return redirect(url_for("customer_login"))

@app.route("/customer/appointments")
def customer_appointments():
    if not session.get("customer_id"): return redirect(url_for("customer_login"))
    rows = db().execute("SELECT a.*,s.name service FROM appointments a LEFT JOIN services s ON s.id=a.service_id WHERE a.customer_id=? ORDER BY a.starts_at DESC", (session["customer_id"],)).fetchall()
    return render_template_string("""<!doctype html><html lang='tr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Randevularım · NUR BEAUTY</title><style>"""+STYLE+"""</style></head><body><header class='publichead'><div class='brand'>NUR BEAUTY<span>.</span></div><a class='btn goldbtn' href='{{url_for("book")}}'>+ Randevu al</a></header><main class='publicbody'><div class='publichero'><div class='eyebrow'>MÜŞTERİ PANELİ</div><h1>Randevularım</h1><p>Merhaba {{username}}, randevu geçmişinizi buradan takip edebilirsiniz.</p></div><div class='panel table-wrap'><table><thead><tr><th>Tarih</th><th>Hizmet</th><th>Durum</th></tr></thead><tbody>{% for a in rows %}<tr><td>{{a.starts_at.replace('T',' ')}}</td><td>{{a.service or '—'}}</td><td><span class='badge {{'ok' if a.status=='Tamamlandı' else 'cancel' if a.status=='İptal' else 'warn'}}'>{{a.status}}</span></td></tr>{% else %}<tr><td colspan='3' class='empty'>Henüz randevunuz yok.</td></tr>{% endfor %}</tbody></table></div><p><a href='{{url_for("customer_logout")}}'>Çıkış yap</a></p></main><script>
(async function(){ if(!('Notification' in window))return; let first=true, known={}; async function poll(){try{const r=await fetch('/api/customer/appointment-updates');if(!r.ok)return;const rows=await r.json();if(first){rows.forEach(a=>known[a.id]=a.status);first=false;return;}rows.forEach(a=>{if(known[a.id] && known[a.id]!==a.status && (a.status==='Onaylandı'||a.status==='İptal')){if(Notification.permission==='granted')new Notification('NUR BEAUTY · Randevu güncellemesi',{body:a.service+' · '+a.starts_at.replace('T',' ')+' — '+a.status});}known[a.id]=a.status;});}catch(e){}} poll();setInterval(poll,20000);document.addEventListener('click',()=>{if(Notification.permission==='default')Notification.requestPermission();},{once:true});})();
</script></body></html>""", rows=rows, username=session.get("customer_username", "Müşterimiz"))

@app.route("/book", methods=["GET", "POST"])
def book():
    """Public mobile-friendly booking page; requests are saved to the same DB as the admin panel."""
    if not session.get("customer_id"):
        flash("Randevu almak için müşteri hesabınızla giriş yapın veya üye olun.")
        return redirect(url_for("customer_login"))
    c = db()
    account_customer = c.execute("SELECT * FROM customers WHERE id=?", (session["customer_id"],)).fetchone()
    if not account_customer:
        session.pop("customer_id", None); session.pop("customer_username", None)
        return redirect(url_for("customer_login"))
    if request.method == "POST":
        name = account_customer["name"]
        phone = account_customer["phone"]
        starts = request.form.get("starts_at", "").strip()
        sid = request.form.get("service_id") or None
        staff_id = request.form.get("staff_id") or None
        note = request.form.get("note", "").strip()
        try:
            start_dt = datetime.fromisoformat(starts)
            if start_dt <= datetime.now():
                flash("Lütfen gelecekte bir tarih ve saat seçin.")
                return redirect(url_for("book"))
            if not sid:
                flash("Lütfen bir hizmet seçin.")
                return redirect(url_for("book"))
            service = c.execute("SELECT * FROM services WHERE id=? AND active=1", (sid,)).fetchone()
            if not service:
                flash("Lütfen geçerli bir hizmet seçin.")
                return redirect(url_for("book"))
            if staff_id and not c.execute("SELECT id FROM staff WHERE id=? AND active=1", (staff_id,)).fetchone():
                staff_id = None
            # Avoid overlapping bookings for the same staff member (or any staff when no preference is selected).
            from datetime import timedelta
            end_dt = start_dt + timedelta(minutes=int(service["duration"] or 30))
            existing = c.execute("""SELECT a.starts_at, COALESCE(s.duration,30) duration, a.staff_id
                FROM appointments a LEFT JOIN services s ON s.id=a.service_id
                WHERE a.status!='İptal' AND substr(a.starts_at,1,10)=?""", (start_dt.strftime("%Y-%m-%d"),)).fetchall()
            for row in existing:
                try:
                    old_start = datetime.fromisoformat(row["starts_at"])
                    old_end = old_start + timedelta(minutes=int(row["duration"] or 30))
                    same_staff = (not staff_id or not row["staff_id"] or str(row["staff_id"]) == str(staff_id))
                    if same_staff and start_dt < old_end and end_dt > old_start:
                        flash("Bu saat için uygunluk görünmüyor. Lütfen başka bir saat seçin.")
                        return redirect(url_for("book"))
                except (ValueError, TypeError):
                    continue
            cid = account_customer["id"]
            c.execute("""INSERT INTO appointments(customer_id,service_id,staff_id,starts_at,status,note,public_booking,created_at)
                VALUES(?,?,?,?,?,?,1,?)""", (cid, sid, staff_id, start_dt.isoformat(timespec="minutes"), "Bekliyor", note, datetime.now().isoformat(timespec="minutes")))
            c.commit()
            return render_template_string("""<!doctype html><html lang='tr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Talep alındı · NUR BEAUTY</title><style>""" + STYLE + """</style></head><body class='auth'><div class='authbox'><div class='brand' style='color:#382832'>NUR BEAUTY<span>.</span></div><div class='eyebrow' style='margin-top:18px'>ONLINE RANDEVU</div><h1>Talebiniz alındı ✨</h1><p>Randevu talebiniz salona iletildi. Salon tarafından onaylandığında kesinleşecektir.</p><p class='muted'><b>{{when}}</b></p><a class='btn goldbtn' style='width:100%' href='{{url_for("book")}}'>Yeni randevu oluştur</a></div></body></html>""", when=start_dt.strftime("%d.%m.%Y · %H:%M"))
        except ValueError:
            flash("Lütfen geçerli bir tarih ve saat seçin.")
            return redirect(url_for("book"))
    sv = c.execute("SELECT * FROM services WHERE active=1 ORDER BY name").fetchall()
    staff_rows = c.execute("SELECT * FROM staff WHERE active=1 ORDER BY name").fetchall()
    return render_template_string("""<!doctype html><html lang='tr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><meta name='theme-color' content='#382832'><meta name='description' content='NUR BEAUTY online randevu sayfası'><title>Online Randevu · NUR BEAUTY</title><style>""" + STYLE + """</style></head><body>
<header class='publichead'><div><div class='brand'>NUR BEAUTY<span>.</span></div><div style='font-size:10px;letter-spacing:2px;color:#e4cbd2;margin:2px 0 0 12px'>GÜZELLİK SALONU</div></div><span class='gold'>Kendinize zaman ayırın ✦</span></header>
<div class='publicbody'><div class='actions' style='justify-content:flex-end;margin-bottom:12px'><a class='btn ghost' href='{{url_for("customer_appointments")}}'>Randevularım</a><a class='btn ghost' href='{{url_for("customer_logout")}}'>Çıkış yap</a></div><section class='publichero'><div class='eyebrow'>NUR BEAUTY · ONLINE RANDEVU</div><h1>Güzelliğiniz için<br>kendinize zaman ayırın.</h1><p>Hizmetinizi ve size uygun zamanı seçin. Randevu talebinizi telefonunuzdan kolayca gönderin.</p></section>
{% with messages = get_flashed_messages() %}{% for m in messages %}<div class='flash'>{{m}}</div>{% endfor %}{% endwith %}
<div class='booking-layout'><section><div class='service-visual'><span style='font-size:11px;letter-spacing:2px'>SİZİN İÇİN ÖZENLE</span><strong>Bakımınız, sizin zamanınız.</strong><span style='font-size:12px'>NUR BEAUTY</span></div><div class='panel'><h3 style='margin:0 0 12px'>Salon hizmetleri</h3><div class='service-chips'>{% for s in sv %}<span class='service-chip'>✦ {{s.name}} · {{money(s.price)}}</span>{% endfor %}</div><p class='muted' style='font-size:12px;margin-bottom:0'>Gönderdiğiniz randevu talebi salon tarafından kontrol edilerek onaylanır.</p></div></section>
<section class='booking-card'><h2>Randevu oluştur</h2><p class='booking-intro'>Bilgilerinizi girin, size uygun zamanı seçin.</p><form method='post' class='formgrid'><div class='field full'><label>Randevu sahibi</label><div class='pill'>{{customer.name}} · {{customer.phone}}</div><p class='muted' style='font-size:12px;margin:0'>Bilgilerinizi değiştirmek için salonla iletişime geçin.</p></div><div class='field full'><label>Hizmet seçin *</label><select name='service_id' required><option value=''>Hangi hizmeti almak istiyorsunuz?</option>{% for s in sv %}<option value='{{s.id}}'>{{s.name}} · {{money(s.price)}} · {{s.duration}} dk</option>{% endfor %}</select></div><div class='field full'><label>Personel tercihi</label><select name='staff_id'><option value=''>Fark etmez</option>{% for st in staff_rows %}<option value='{{st.id}}'>{{st.name}}</option>{% endfor %}</select></div><div class='field'><label>Tarih *</label><input type='date' id='book-date' required min='{{min_day}}'></div><div class='field'><label>Saat *</label><select name='starts_at' id='book-time' required><option value=''>Önce tarih seçin</option></select></div><div class='field full'><label>Notunuz (isteğe bağlı)</label><textarea name='note' rows='2' placeholder='Varsa belirtmek istediğiniz bir konu...'></textarea></div><div class='field full'><button class='btn goldbtn'>Randevu talebi gönder&nbsp; →</button></div></form><div class='secure-note'><span>✦</span><span>Randevunuz, salon onayı gelene kadar talep durumundadır. Bilgileriniz randevu planlaması için kullanılır.</span></div></section></div><div class='footer'>NUR BEAUTY · Güzelliğiniz için, her zaman yanınızda</div></div>
<script>
const dateInput=document.getElementById('book-date'), timeSelect=document.getElementById('book-time');
function fillTimes(){timeSelect.innerHTML='<option value="">Saat seçin</option>';if(!dateInput.value)return;for(let h=9;h<=19;h++){for(let m of [0,30]){if(h===19&&m===30)continue;const value=String(h).padStart(2,'0')+':'+String(m).padStart(2,'0');const dt=new Date(dateInput.value+'T'+value);if(dt.getTime()<=Date.now())continue;const opt=document.createElement('option');opt.value=dateInput.value+'T'+value;opt.textContent=value;timeSelect.appendChild(opt)}}}
dateInput.addEventListener('change',fillTimes);fillTimes();
</script></body></html>""", sv=sv, staff_rows=staff_rows, money=money, min_day=date.today().isoformat(), customer=account_customer)


@app.route("/api/admin/new-bookings")
@login_required
def api_admin_new_bookings():
    # Returns recent online requests; browser notifications appear while the admin panel is open.
    c = db()
    rows = c.execute("""SELECT a.id,a.starts_at,cu.name customer,COALESCE(s.name,'Hizmet') service
        FROM appointments a JOIN customers cu ON cu.id=a.customer_id
        LEFT JOIN services s ON s.id=a.service_id
        WHERE a.public_booking=1 AND a.status='Bekliyor' AND a.created_at >= ?
        ORDER BY a.id DESC LIMIT 30""", ((datetime.now() - __import__("datetime").timedelta(minutes=10)).isoformat(timespec="minutes"),)).fetchall()
    return [{"id": r["id"], "starts_at": r["starts_at"], "customer": r["customer"], "service": r["service"]} for r in rows]

@app.route("/api/customer/appointment-updates")
def api_customer_appointment_updates():
    if not session.get("customer_id"):
        return {"error": "login_required"}, 401
    rows = db().execute("""SELECT a.id,a.status,a.starts_at,COALESCE(s.name,'Hizmet') service
        FROM appointments a LEFT JOIN services s ON s.id=a.service_id
        WHERE a.customer_id=? ORDER BY a.id DESC LIMIT 30""", (session["customer_id"],)).fetchall()
    return [{"id": r["id"], "status": r["status"], "starts_at": r["starts_at"], "service": r["service"]} for r in rows]

@app.route("/health")
def health(): return {"status":"ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)

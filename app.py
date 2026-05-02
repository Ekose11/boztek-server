from flask import Flask, request, jsonify
import os
import pg8000

app = Flask(__name__)
<div class="card"><form method="post" class="form-grid">
<div class="field"><label>Ad Soyad</label><input name="full_name" required></div><div class="field"><label>Bölüm</label><input name="department" required></div>
<div class="field"><label>Kullanıcı Adı</label><input name="username"></div><div class="field"><label>Şifre</label><input name="password"></div>
<div class="field"><label>Yıllık İzin</label><input name="annual_leave_total" type="number" value="14"></div><div class="field"><label>Maaş</label><input name="salary" type="number" step="0.01" value="0"></div>
<div><button class="btn">Personel Ekle</button></div></form></div>
<div class="card"><table class="table"><tr><th>İsim</th><th>Bölüm</th><th>Kullanıcı</th><th>Maaş</th><th>Kalan İzin</th><th>İşlem</th></tr>
{% for p in rows %}<tr><td><b>{{p.full_name}}</b></td><td>{{p.department}}</td><td>{{p.username or "-"}}</td><td>{{"%.2f"|format(p.salary|float)}} ₺</td><td>{{p.annual_leave_remaining}}</td><td><form method="post" action="/admin/personnel/{{p.id}}/delete" style="display:inline"><button class="btn btn-red">Sil</button></form></td></tr>{% endfor %}
</table></div>{% endblock %}

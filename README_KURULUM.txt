BOZTEK TAM SISTEM SON PAKET

GitHub'a yükleme:
1) ZIP'i çıkar.
2) İçindeki dosyaları repo ANA DİZİNE yükle.
3) app.py içine HTML yapıştırma. app.py sadece Python kodudur.
4) requirements.txt içine sadece paket isimleri yazılır.

Render ayarları:
Build Command:
pip install -r requirements.txt

Start Command:
gunicorn --workers 1 --threads 4 --timeout 120 app:app

Environment:
DATABASE_URL = Neon connection string

Deploy:
Manual Deploy > Clear build cache & deploy

Test:
https://senin-server.onrender.com/api/health

Doğru çıktı:
{"database":"connected","driver":"pg8000","mode":"final","status":"ok"}

Panel:
Kullanıcı adı: saban
Şifre: 5109

Bu paket:
- Profesyonel yeni tasarım
- Yeni font/punto düzeni
- Yeni arka plan renkleri
- Modern menü butonları
- Personel ekle/sil/düzenle
- Personel kullanıcı adı/şifre
- Avans
- Maaş/Kalan maaş
- Yıllık izin
- Aylık rapor
- Telefon uygulaması API endpointleri
- Neon kalıcı veritabanı

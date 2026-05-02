PROFESYONEL PANEL - KURULUM

1) ZIP'i çıkar.
2) İçindeki dosyaları GitHub repo ana dizinine yükle.
3) Render ayarları:
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app
   Environment: DATABASE_URL = Neon connection string

4) Manual Deploy > Clear build cache & deploy

5) Test:
   /api/health

Doğru çıktı:
{"status":"ok","database":"connected","driver":"pg8000"}

Bu sürüm çalışan pg8000 altyapısını korur, paneli profesyonel yapar.

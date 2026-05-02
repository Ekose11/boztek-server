SIFIRDAN KURULUM

1) GitHub'da yeni/temiz repo kullan.
2) ZIP'i çıkar.
3) İçindeki dosyaları repo ana dizinine yükle.
4) Render servisinde:
   - Root Directory boş
   - Build Command: pip install -r requirements.txt
   - Start Command: gunicorn app:app
   - Environment: DATABASE_URL = Neon connection string

5) Manual Deploy > Clear build cache & deploy

6) Test:
   /api/health

Doğru çıktı:
{"status":"ok","database":"connected","driver":"pg8000"}

Bu çıktı gelirse personeller deploy sonrası silinmez.

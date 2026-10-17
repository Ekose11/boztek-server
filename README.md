# ATELIER — Kuaför Randevu ve Seans Takip Paneli

Flask + SQLite ile hazırlanmış Türkçe başlangıç uygulaması. GitHub'a yüklenip Render üzerinden yayınlanacak şekilde paketlenmiştir.

## İçerik
- `app.py`: Flask web uygulaması
- `requirements.txt`: Python bağımlılıkları
- `Procfile`: Gunicorn başlatma komutu
- `render.yaml`: Render Blueprint yapılandırması
- `.gitignore`: Yerel veritabanı ve gizli dosyaları Git dışında tutar

## GitHub'a yükleme
1. ZIP'i bilgisayarında bir klasöre çıkar.
2. GitHub'da yeni bir repository oluştur.
3. Çıkarılan klasördeki dosyaları repository'ye yükle (ZIP dosyasının kendisini değil, içindeki dosyaları).
4. Repository'nin `app.py`, `requirements.txt`, `Procfile` ve `render.yaml` dosyalarını kök dizinde tuttuğunu kontrol et.

## Render'da yayınlama
1. Render hesabına giriş yap ve **New + → Blueprint** seç.
2. GitHub hesabını bağla, bu repository'yi seç.
3. Render'ın `render.yaml` dosyasını okumasını bekle ve oluşturma adımlarını onayla.
4. Dağıtım tamamlanınca Render'ın verdiği `onrender.com` adresini aç.

### Kalıcı veritabanı uyarısı
Bu sürüm SQLite kullanır ve `render.yaml`, veritabanını `/var/data/kuafor.db` konumunda tutacak 1 GB kalıcı disk tanımlar. Render'da kalıcı diskler ücretli web servis planı gerektirebilir. Kalıcı disk bağlanmadan SQLite'ı geçici dosya sisteminde kullanırsan dağıtım/yeniden başlatma sırasında kayıtlar kaybolabilir.

## İlk giriş
- Kullanıcı adı: `admin`
- Şifre: `Kuafor123!`

Bu, herkeste aynı olan demo hesabıdır. Uygulamanın mevcut sürümünde parola değiştirme ekranı bulunmadığı için **gerçek müşteri verisi koymadan ve herkese açık satışa açmadan önce** kimlik doğrulama güvenliğini tamamla; en azından varsayılan hesabı güvenli şekilde değiştiren bir mekanizma ekle. `SECRET_KEY`, Render yapılandırmasında otomatik oluşturulur; kaynak koda gerçek gizli anahtar koyma.

## Üretim öncesi eksikler
Bu paket, Render'a dağıtılabilir bir başlangıç/demonstrasyon sürümüdür; güvenlik incelemesi yapılmış ticari ürün olarak değerlendirilmemelidir. Gerçek müşteriler için yayınlamadan önce en azından şunları tamamla:
- Güvenli parola değiştirme ve parola sıfırlama
- CSRF koruması ve oturum güvenliği ayarları
- Her salonun yalnızca kendi verilerini görebileceği çok işletmeli (multi-tenant) veri izolasyonu
- Randevu saat çakışması kontrolü ve eşzamanlı seans/ödeme işlemlerinin doğrulanması
- Otomatik yedekleme ve geri yükleme testi
- Gizlilik/KVKK süreçleri, erişim kayıtları ve üretim testleri

## Yerel çalıştırma (Windows)
```bat
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py app.py
```
Tarayıcıda `http://127.0.0.1:5000` adresini aç.

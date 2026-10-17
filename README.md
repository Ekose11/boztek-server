# NUR BEAUTY — Kuaför ve Güzellik Salonu Yönetim Paneli

Türkçe arayüzlü Flask tabanlı randevu ve salon yönetim paneli. Görsel tema NUR BEAUTY markası için koyu mürdüm, pudra pembe ve krem renklerine uyarlanmıştır.

## Özellikler
- Yönetici girişi ve özet ekranı
- Randevu yönetimi ve online randevu talep sayfası (`/book`)
- Müşteri kayıtları
- Hizmet ve paket yönetimi
- Paket/seans takibi
- Tahsilat kayıtları
- Personel kayıtları
- Gelir raporları
- Mobil ekranlara uyumlu tasarım

## Yerel çalıştırma
Python 3.10+ önerilir.

```bash
pip install -r requirements.txt
python app.py
```
Ardından `http://127.0.0.1:5000` adresini açın.

## GitHub ve Render kurulumu
1. ZIP dosyasını çıkarın.
2. İçindeki proje dosyalarını GitHub deposunun kök dizinine yükleyin.
3. Render hesabında **New + → Blueprint** seçin ve GitHub deposunu bağlayın.
4. Render, `render.yaml` dosyasındaki ayarlara göre servisi kuracaktır.
5. İlk giriş bilgilerini aşağıdan alın ve dağıtımdan sonra değiştirin.

## İlk giriş
- Kullanıcı adı: `admin`
- Şifre: `Kuafor123!`

**Güvenlik:** Bu proje başlangıç/demo paketidir. Gerçek müşteri verileriyle kullanmadan önce varsayılan şifreyi değiştirin, parola değiştirme ekranı ve CSRF koruması ekleyin, `SECRET_KEY` değerini güvenli bir ortam değişkeni olarak ayarlayın ve veri yedekleme/kalıcılığını doğrulayın. SQLite ve tek yönetici hesabı mevcut haliyle yüksek trafikli veya çok salonlu ticari kullanım için yeterli değildir. Render kalıcı disk planı ücretli olabilir.

`logo.svg`, NUR BEAUTY için düzenlenebilir vektör logo taslağıdır.


## Online randevu sayfası

Yayınlandıktan sonra müşterilerin kullanacağı mobil uyumlu sayfa: `/book`. Yönetim panelindeki “Online randevu sayfası” bağlantısı da aynı sayfayı açar. Web formundan gönderilen talepler aynı veritabanındaki randevu listesine ve müşteri kayıtlarına kaydedilir; yönetici panelinden takip edilir. Randevular ilk aşamada **Bekliyor** durumunda kaydedilir ve salon onayı gerektirir.

Not: Bu proje başlangıç sürümüdür. Canlı kullanımdan önce varsayılan yönetici şifresini değiştirmek, güvenlik kontrollerini ve gerçek sunucu üzerinde randevu çakışması testlerini yapmak gerekir.

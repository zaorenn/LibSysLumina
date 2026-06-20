# LibSys Kütüphane Yönetim Sistemi 📚✨

LibSys (Lumina Kütüphane Sistemi), Python, SQLite ve CustomTkinter kullanılarak geliştirilmiş, yüksek estetik standartlara sahip modern bir kütüphane yönetim sistemidir. Kullanıcılar (üyeler) ve yöneticiler (admin) için iki ayrı arayüz sunarak güvenli, performanslı ve kullanıcı dostu bir deneyim sağlar.

![LibSys Banner](https://images.unsplash.com/photo-1507842217343-583bb7270b66?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80)

---

## 🌟 Öne Çıkan Özellikler

### 1. İki Farklı Uygulama Mimarisi
- **Kullanıcı Uygulaması (`main.py`)**: Üyelerin hesap oluşturabildiği, giriş yapabildiği, zengin kitap kataloğunu inceleyebildiği, kitapları ödünç alıp iade edebildiği, kendi profilinden iade tarihlerini ve cezalarını takip edebildiği son derece modern ve pürüzsüz (smooth) bir arayüz.
- **Yönetici Paneli (`admin_app.py`)**: Sadece `admin` yetkisine sahip kişilerin girebildiği, kitap ekleme (internetten otomatik veri çekme destekli), üye yönetimi ve ödünç/iade işlemlerinin detaylı takip edildiği gelişmiş özel kontrol paneli.

### 2. Yüksek Estetik ve Performans (Premium UI/UX)
- **Karanlık Tema (Dark Mode)**: Göz yormayan, premium hissiyatlı renk paleti (#121212, #1E1E1E) ve indigo/emerald vurgular.
- **Dinamik ve Akıcı Kitap Kartları**: Kitaplar, kapak resimleri asenkron olarak arka planda indirilerek şık bir Grid (Izgara) yapısında sergilenir. Optimize edilmiş katalog sistemi sayesinde sayfa kaydırma (scroll) işlemlerinde donma veya kasma yaşanmaz.
- **Yuvarlatılmış Hatlar ve Şeffaflık**: Tüm butonlar, kartlar ve giriş alanları modern tasarım trendlerine (glassmorphism/rounded UI) uygun olarak tasarlanmıştır.

### 3. Gelişmiş Veritabanı ve Güvenlik (SQLite & Bcrypt)
- Tüm şifreler `bcrypt` ile hash'lenerek saklanır.
- Trigger'lar (Tetikleyiciler) sayesinde stok takibi, ödünç durumu güncellemeleri ve gecikme cezası (günlük 5 TL) hesaplamaları otomatik olarak veritabanı seviyesinde gerçekleşir.

---

## 🛠️ Kurulum ve Ön Hazırlık

### Gereksinimler
Projenin sorunsuz çalışabilmesi için sisteminizde **Python 3.8 veya üzeri** bir sürüm yüklü olmalıdır.

1. Proje dizinini bilgisayarınıza indirin ve komut satırında (Terminal/CMD) bu dizine gidin:
   ```bash
   cd Proje
   ```
2. Gerekli Python kütüphanelerini yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
   *(Yüklenen bağımlılıklar: customtkinter, bcrypt, pytest, Pillow, requests)*

---

## 📖 Uygulamanın Kullanımı

LibSys sistemi 3 ana araç sunar. Bunları sırasıyla nasıl kullanacağınız aşağıda açıklanmıştır:

### 1. Veritabanını Sıfırlama ve Hazırlama (Seed DB)
Sistemi ilk kez çalıştırıyorsanız veya her şeyi sıfırlayıp **test verileri** (Admin, Örnek Kullanıcı ve Katalogda 100 adet gerçek kitap) ile doldurmak istiyorsanız, sıfırlama script'ini çalıştırmalısınız:

```bash
python seed_db.py
```
*Bu komut veritabanındaki tüm eski bilgileri siler, baştan tablo oluşturur ve sistemi hazır hale getirir. Başarı mesajını aldıktan sonra diğer uygulamalara geçebilirsiniz.*

### 2. Yönetici Paneli (Admin Dashboard)
Kütüphane görevlisi veya yöneticisi olarak sisteme girip kitap/kullanıcı eklemek için:

```bash
python admin_app.py
```

> **Varsayılan Yönetici Bilgileri:**
> Kullanıcı Adı: `admin`
> Şifre: `admin`

**Admin Olarak Neler Yapabilirsiniz?**
- **Üye Yönetimi**: Sisteme kayıtlı tüm üyeleri listeleyebilir, çift tıklayarak bir üyenin e-posta, isim, telefon ve hatta şifresini değiştirebilir veya üyeyi silebilirsiniz.
- **Kitap Yönetimi**: İnternetten Kitap Ekle butonu ile Gutenberg veya OpenLibrary entegrasyonu üzerinden saniyeler içinde yeni kitaplar bulup görselleriyle beraber kütüphaneye dahil edebilirsiniz.
- **Ödünç Takibi**: Kimin, hangi kitabı, ne zaman aldığını kontrol edebilir, süresi geçenleri listeleyebilirsiniz.

### 3. Kullanıcı Uygulaması (Member App)
Kütüphane üyelerinin veya öğrencilerin kataloğa göz atması, kitap ödünç alması ve profillerini yönetmesi için:

```bash
python main.py
```

> **Varsayılan Test Üyesi Bilgileri:**
> E-posta/Kullanıcı Adı: `uye@lumina.com` veya `uye`
> Şifre: `uye`

**Üye Olarak Neler Yapabilirsiniz?**
- **Katalogda Gezinme**: En yeni eklenen kitapları yüksek performanslı akıcı bir Grid sisteminde inceleyebilirsiniz.
- **Kitap Ödünç Alma**: Stoğu olan bir kitabı tek tıkla ödünç alabilir, süresi bitmeden önce profilinizden kolayca tek tuşla **İade Et** yapabilirsiniz.
- **Profil ve Cezalar**: Hesabınızda mevcut cezalarınızı, aktif ödünç kitaplarınızı görebilirsiniz.
- **Yeni Kayıt**: Eğer üye değilseniz, giriş ekranındaki Kayıt Ol butonuna basarak sadece saniyeler içinde kendi hesabınızı açabilirsiniz (Telefon numarası kısmına sadece rakam girilmesine izin verilmektedir).

---

## 🧪 Test Senaryoları (Unit Tests)

Uygulamanın sağlamlığını doğrulamak için `pytest` altyapısı mevcuttur. Testleri çalıştırmak için komut satırına:

```bash
pytest tests/
```
Test edilen modüller:
- Admin giriş doğrulamaları.
- Üye şifrelerinin `bcrypt` algoritması ile doğru eşleşmesi.
- Kitap stok düşüşü ve artışının ödünç/iade döngülerinde testi.

---

## 📂 Proje Dizin Yapısı
```text
Proje/
├── main.py                # Kullanıcı uygulaması başlatıcısı
├── admin_app.py           # Yönetici paneli başlatıcısı
├── seed_db.py             # Veritabanını sıfırlama ve test verisi oluşturma script'i
├── requirements.txt       # Kütüphane listesi
├── library.db             # SQLite veritabanı (otomatik oluşur)
├── controllers/           # Mantık (Giriş, Üye/Kitap yönetimi)
│   ├── auth.py
│   └── library.py
├── models/                # Tablolar, veritabanı ve trigger'lar
│   └── database.py
├── views/                 # Arayüz tasarımları (CustomTkinter)
│   ├── ui.py              # Kullanıcı arayüzleri
│   └── admin_ui.py        # Admin panel arayüzleri
└── tests/                 # Otomatik test senaryoları
```

Geliştirme sırasında performans ve kullanıcı deneyimi en üst düzeyde tutulmuştur. İyi kullanımlar! 🎉

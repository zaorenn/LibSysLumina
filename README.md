# Lumina Kütüphane Yönetim Sistemi 📚✨

Lumina, Python, SQLite ve CustomTkinter kullanılarak geliştirilmiş, yüksek estetik standartlara sahip modern bir kütüphane yönetim sistemidir. Bu proje, kullanıcılar (üyeler) ve yöneticiler (admin) için iki ayrı arayüz sunarak güvenli ve gelişmiş bir deneyim sağlar.

![Lumina Banner](https://images.unsplash.com/photo-1507842217343-583bb7270b66?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80)

## 🌟 Öne Çıkan Özellikler

### 1. İki Farklı Uygulama Mimarisi
- **Kullanıcı Uygulaması (`main.py`)**: Üyelerin kayıt olup giriş yapabileceği, kitap kataloğunu inceleyebileceği, kitapları ödünç alabileceği ve kendi profilinden iade tarihlerini/cezalarını takip edebileceği son derece modern ve animasyonlu bir arayüz.
- **Yönetici Paneli (`admin_app.py`)**: Sadece `admin` yetkisine sahip kişilerin girebildiği, kitap, üye ve ödünç işlemlerinin CRUD (Oluştur, Oku, Güncelle, Sil) operasyonlarının yapıldığı özel kontrol paneli.

### 2. Yüksek Estetik (Premium UI/UX)
- **Karanlık Tema (Dark Mode)**: Göz yormayan, premium hissiyatlı renk paleti (#121212, #1E1E1E) ve indigo/emerald vurgular.
- **Dinamik Kitap Kartları**: Kitaplar sıkıcı listeler yerine, kapak resimleri (URL üzerinden dinamik yüklenen) ile şık bir Grid (Izgara) yapısında sergilenir.
- **Yuvarlatılmış Hatlar ve Şeffaflık**: Tüm butonlar, kartlar ve giriş alanları modern tasarım trendlerine uygun olarak yuvarlatılmıştır.

### 3. Gelişmiş Veritabanı (SQLite)
- Şifreler `bcrypt` ile hash'lenerek saklanır (Güvenlik).
- Trigger'lar (Tetikleyiciler) sayesinde stok takibi ve gecikme cezası (günlük 5 TL) hesaplamaları otomatik olarak veritabanı seviyesinde yapılır.

---

## 🛠️ Kurulum ve Çalıştırma

### Gereksinimler
Projeyi çalıştırmak için bilgisayarınızda Python 3.8+ yüklü olmalıdır.

1. Proje dizinine gidin.
2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
   *(Bağımlılıklar: customtkinter, bcrypt, pytest, Pillow, requests)*

### Çalıştırma

**Admin Paneli (Veritabanı Yönetimi İçin):**
```bash
python admin_app.py
```
> **Varsayılan Yönetici Bilgileri:**
> Kullanıcı Adı: `admin`
> Şifre: `admin123`

**Kullanıcı Ana Uygulaması (Üyeler İçin):**
```bash
python main.py
```
> **Varsayılan Üye Bilgileri:**
> E-posta: `uye@lumina.com`
> Şifre: `uye123`
*(Uygulama üzerinden yeni bir hesap oluşturabilir veya bu varsayılan üye bilgileri ile doğrudan giriş yapabilirsiniz.)*

---

## 🧪 Test Senaryoları (Test Cases)
Proje, temel iş mantığını doğrulamak için `pytest` kullanılarak yazılmış test senaryoları içerir.
Testleri çalıştırmak için:
```bash
pytest tests/
```
Test edilen senaryolar:
- Admin girişi doğrulaması (Doğru ve yanlış şifre denemeleri).
- Yeni üye kaydı ve bcrypt şifre doğrulaması.
- Kitap ekleme işleminin başarılı olması.
- Kitap ödünç alma (stok düşüşü) ve iade etme (stok artışı) döngüsü.

---

## 📂 Proje Yapısı
```text
Proje/
│
├── main.py                # Kullanıcı (Üye) uygulaması başlangıç dosyası
├── admin_app.py           # Yönetici (Admin) uygulaması başlangıç dosyası
├── requirements.txt       # Python bağımlılıkları
├── library.db             # SQLite veritabanı dosyası (Otomatik oluşur)
│
├── controllers/           # İş mantığı (Business Logic)
│   ├── auth.py            # Giriş ve kimlik doğrulama işlemleri
│   └── library.py         # Kitap, üye ve ödünç alma CRUD işlemleri
│
├── models/                # Veri modelleri
│   └── database.py        # Tablo kurulumları ve Trigger'lar
│
├── views/                 # Arayüz tasarımları (CustomTkinter)
│   ├── ui.py              # Kullanıcı uygulaması arayüzü (Katalog, Profil)
│   └── admin_ui.py        # Yönetici paneli arayüzü (Tablolar, Dashboard)
│
└── tests/                 # Pytest test dosyaları
    └── test_core.py       # Temel test senaryoları
```

## 🎯 Projenin Amacı ve Hedefi
Bu proje, standart bir okul/kütüphane projesinin ötesine geçerek gerçek dünyada kullanılabilecek seviyede "modern, kullanıcı dostu ve güvenli" bir yazılım geliştirme prensiplerini sergilemeyi amaçlamaktadır. Göz alıcı tasarımıyla sıradan projelerden ayrılır.

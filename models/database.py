import sqlite3
import bcrypt
import os

# Projenin ana dizinini bularak veritabanı yolunu mutlak (absolute) hale getiriyoruz
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "library.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. ADMIN TABLOSU (Şifreler Hash'li)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT DEFAULT 'Yönetici',
        email TEXT DEFAULT 'admin@lumina.com'
    )
    ''')
    
    # 2. KİTAPLAR TABLOSU
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT UNIQUE NOT NULL,
        category TEXT,
        published_year INTEGER,
        description TEXT,
        cover_image_url TEXT,
        total_copies INTEGER NOT NULL,
        available_copies INTEGER NOT NULL
    )
    ''')
    
    # 3. ÜYELER TABLOSU (Şifre eklendi)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        password_hash TEXT NOT NULL,
        is_approved BOOLEAN DEFAULT 0,
        must_change_password BOOLEAN DEFAULT 0,
        registered_date DATE DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 4. ÖDÜNÇ ALMA TABLOSU
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS borrows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        member_id INTEGER,
        member_name_snapshot TEXT NOT NULL,
        borrow_date DATE DEFAULT CURRENT_DATE,
        return_date DATE NOT NULL,
        actual_return_date DATE,
        late_fee REAL DEFAULT 0,
        FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
        FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE SET NULL
    )
    ''')
    
    # 5. İSTEK KİTAP TABLOSU
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS book_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        member_name TEXT,
        title TEXT NOT NULL,
        author TEXT,
        isbn TEXT,
        cover_url TEXT,
        request_date DATE DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # BİLDİRİMLER TABLOSU
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT 0,
        created_at DATE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (member_id) REFERENCES members(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS profile_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        member_name TEXT,
        new_name TEXT,
        new_email TEXT,
        status TEXT DEFAULT 'PENDING',
        request_date DATE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (member_id) REFERENCES members(id)
    )
    ''')
    
    # 5. YORUMLAR TABLOSU (Kullanıcıların kitaplara yorum yapması için)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        member_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
        comment TEXT,
        review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
        FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE
    )
    ''')

    # 6. FAVORİLER (WISHLIST) TABLOSU
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wishlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        member_id INTEGER NOT NULL,
        added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
        FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE,
        UNIQUE(book_id, member_id)
    )
    ''')

    # 7. REZERVASYON TABLOSU
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        member_id INTEGER NOT NULL,
        reservation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Bekliyor',
        FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
        FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE
    )
    ''')

    # 8. AUDIT LOGS TABLOSU (İşlem Takibi)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT,
        table_name TEXT,
        record_id INTEGER,
        action_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        description TEXT
    )
    ''')

    # TRIGGER 1: Ödünç alma sonrası stok düşür ve logla
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS after_borrow_insert
    AFTER INSERT ON borrows
    BEGIN
        UPDATE books SET available_copies = available_copies - 1 WHERE id = NEW.book_id;
        INSERT INTO audit_logs (action_type, table_name, record_id, action_date, description)
        VALUES ('BORROW', 'borrows', NEW.id, datetime('now', 'localtime'), 'Kitap ödünç verildi. Üye ID: ' || NEW.member_id);
    END;
    ''')
    
    # TRIGGER 2: İade sonrası stok artır, gecikme cezası hesapla (Geciken gün x 5 TL) ve logla
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS after_borrow_update_return
    AFTER UPDATE OF actual_return_date ON borrows
    WHEN NEW.actual_return_date IS NOT NULL AND OLD.actual_return_date IS NULL
    BEGIN
        UPDATE borrows 
        SET late_fee = CASE 
            WHEN CAST(julianday(NEW.actual_return_date) - julianday(OLD.return_date) AS INTEGER) > 0 
            THEN CAST(julianday(NEW.actual_return_date) - julianday(OLD.return_date) AS INTEGER) * 5.0
            ELSE 0 
        END
        WHERE id = NEW.id;
        
        UPDATE books SET available_copies = available_copies + 1 WHERE id = NEW.book_id;
        
        INSERT INTO audit_logs (action_type, table_name, record_id, action_date, description)
        VALUES ('RETURN', 'borrows', NEW.id, datetime('now', 'localtime'), 'Kitap iade edildi.');
    END;
    ''')

    # Sütun Migrasyonları (Eski veritabanı şemalarını otomatik güncellemek için)
    try:
        cursor.execute("ALTER TABLE members ADD COLUMN is_approved BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE members ADD COLUMN must_change_password BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE admins ADD COLUMN name TEXT DEFAULT 'Yönetici'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE admins ADD COLUMN email TEXT DEFAULT 'admin@lumina.com'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE books ADD COLUMN cover_image_url TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE borrows ADD COLUMN member_name_snapshot TEXT NOT NULL DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE borrows ADD COLUMN late_fee REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE book_requests ADD COLUMN cover_url TEXT")
    except sqlite3.OperationalError:
        pass

    # Varsayılan Admin Hesabını Oluştur (admin / admin)
    cursor.execute("SELECT COUNT(*) FROM admins")
    if cursor.fetchone()[0] == 0:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(b"admin", salt).decode('utf-8')
        cursor.execute("INSERT INTO admins (username, password_hash, name, email) VALUES (?, ?, ?, ?)", ("admin", hashed, "Sistem Yöneticisi", "admin@lumina.com"))
        
    # Varsayılan Üye Hesabını Oluştur (uye@lumina.com / uye)
    cursor.execute("SELECT COUNT(*) FROM members")
    if cursor.fetchone()[0] == 0:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(b"uye", salt).decode('utf-8')
        cursor.execute("INSERT INTO members (name, email, phone, password_hash, is_approved) VALUES (?, ?, ?, ?, 1)",
                       ("Üye", "uye@lumina.com", "5551234567", hashed))

    # Varsayılan 100 Kitabı Ekle
    cursor.execute("SELECT COUNT(*) FROM books")
    if cursor.fetchone()[0] == 0:
        books_data = [
            ('Harry Potter ve Felsefe Taşı', 'J.K. Rowling', '8702113996', 'Fantastik', 1997, "Büyücülük dünyasına adım atan genç Harry'nin maceraları.", 'https://images-na.ssl-images-amazon.com/images/P/8702113996.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Yüzüklerin Efendisi: Yüzük Kardeşliği', 'J.R.R. Tolkien', '9780739409558', 'Fantastik', 1954, "Orta Dünya'yı karanlıktan kurtarmak için çıkılan destansı yolculuk.", 'https://images-na.ssl-images-amazon.com/images/P/9780739409558.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Hobbit', 'J.R.R. Tolkien', '0871294273', 'Fantastik', 1937, "Bilbo Baggins'in ejderha Smaug'un hazinesini geri alma macerası.", 'https://images-na.ssl-images-amazon.com/images/P/0871294273.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Harry Potter ve Sırlar Odası', 'J.K. Rowling', '9781006397356', 'Fantastik', 1998, "Hogwarts'ta taşlaşan öğrenciler ve Sırlar Odası'nın gizemi.", ''),
            ('Harry Potter ve Azkaban Tutsağı', 'J.K. Rowling', '9781004837936', 'Fantastik', 1999, "Azkaban hapishanesinden kaçan gizemli Sirius Black'in hikayesi.", ''),
            ('Yüzüklerin Efendisi: İki Kule', 'J.R.R. Tolkien', '9780739409558', 'Fantastik', 1954, 'Kardeşliğin dağılmasıyla başlayan amansız savaşlar ve yolculuklar.', 'https://images-na.ssl-images-amazon.com/images/P/9780739409558.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Yüzüklerin Efendisi: Kralın Dönüşü', 'J.R.R. Tolkien', '9780739409558', 'Fantastik', 1955, "Tek yüzüğün yok edilmesi ve Gondor'un yeni kralının gelişi.", 'https://images-na.ssl-images-amazon.com/images/P/9780739409558.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Rüzgarın Adı', 'Patrick Rothfuss', '9781001240982', 'Fantastik', 2007, 'Kvothe adındaki efsanevi büyücü ve müzisyenin kendi ağzından hikayesi.', ''),
            ('Bilge Adamın Korkusu', 'Patrick Rothfuss', '9781473223721', 'Fantastik', 2011, "Kvothe'un efsanesini ararken karşılaştığı yeni tehlikeler ve maceralar.", 'https://images-na.ssl-images-amazon.com/images/P/9781473223721.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Yerdeniz Büyücüsü', 'Ursula K. Le Guin', '9780812421453', 'Fantastik', 1968, "Genç büyücü Ged'in gölgesiyle yüzleşme ve olgunlaşma mücadelesi.", 'https://images-na.ssl-images-amazon.com/images/P/9780812421453.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Puslu Kıtalar Atlası', 'İhsan Oktay Anar', '9789754704723', 'Fantastik', 1995, 'Düşler ve gerçekler arasında kaybolan Osmanlı dönemi Galata hikayeleri.', 'https://images-na.ssl-images-amazon.com/images/P/9789754704723.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Aslan, Cadı ve Gardırop', 'C.S. Lewis', '9781004133770', 'Fantastik', 1950, 'Sihirli bir gardıroptan Narnia dünyasına geçen dört kardeşin serüveni.', ''),
            ('Taht Oyunları', 'George R.R. Martin', '8375068306', 'Fantastik', 1996, 'Westeros kıtasındaki yedi krallığın taht mücadeleleri ve entrikaları.', 'https://images-na.ssl-images-amazon.com/images/P/8375068306.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Kralların Çarpışması', 'George R.R. Martin', '9781004686519', 'Fantastik', 1998, 'Demir Taht için savaşan beş kralın kanlı mücadelesi.', ''),
            ('Kılıçların Fırtınası', 'George R.R. Martin', '9781007622944', 'Fantastik', 2000, "Westeros'taki savaşın derinleşmesi ve beklenmedik ittifaklar.", ''),
            ('1984', 'George Orwell', '0241436524', 'Bilim Kurgu', 1949, "Büyük Birader'in gözetiminde, düşüncenin yasaklandığı distopik bir dünya.", 'https://images-na.ssl-images-amazon.com/images/P/0241436524.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Cesur Yeni Dünya', 'Aldous Huxley', '9789756902165', 'Bilim Kurgu', 1932, 'Teknoloji ve haz odaklı, aile ve duyguların olmadığı yapay bir toplum.', 'https://images-na.ssl-images-amazon.com/images/P/9789756902165.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Fahrenheit 451', 'Ray Bradbury', '9781613832493', 'Bilim Kurgu', 1953, 'Kitap okumanın ve saklamanın yasak olduğu, itfaiyecilerin kitap yaktığı dünya.', 'https://images-na.ssl-images-amazon.com/images/P/9781613832493.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Otomatik Portakal', 'Anthony Burgess', '9780606194723', 'Bilim Kurgu', 1962, "Şiddet yanlısı bir gencin devlet eliyle 'iyi'leştirilme çabaları.", 'https://images-na.ssl-images-amazon.com/images/P/9780606194723.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Vakıf', 'Isaac Asimov', '9788960177567', 'Bilim Kurgu', 1951, 'Galaktik İmparatorluğun çöküşünü öngören psikotarih biliminin doğuşu.', 'https://images-na.ssl-images-amazon.com/images/P/9788960177567.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Vakıf ve İmparatorluk', 'Isaac Asimov', '9788402047830', 'Bilim Kurgu', 1952, "Çöken imparatorluğun Vakıf'a karşı son saldırıları ve Katır gizemi.", 'https://images-na.ssl-images-amazon.com/images/P/9788402047830.01._SCLZZZZZZZ_SX200_.jpg'),
            ('İkinci Vakıf', 'Isaac Asimov', '896017758X', 'Bilim Kurgu', 1953, "Katır'ın yükselişi karşısında gizli İkinci Vakıf'ın ortaya çıkışı.", 'https://images-na.ssl-images-amazon.com/images/P/896017758X.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Dune', 'Frank Herbert', '0450031462', 'Bilim Kurgu', 1965, "Çöl gezegeni Arrakis'te baharat savaşı ve Paul Atreides'in yükselişi.", 'https://images-na.ssl-images-amazon.com/images/P/0450031462.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Dune Mesihi', 'Frank Herbert', '9785237041484', 'Bilim Kurgu', 1969, "İmparator Paul Atreides'in din ve siyaset kıskacındaki trajedisi.", 'https://images-na.ssl-images-amazon.com/images/P/9785237041484.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Dune Çocukları', 'Frank Herbert', '2221000455', 'Bilim Kurgu', 1976, "Paul'ün çocukları Leto ve Ghanima'nın insanlığın geleceğini kurtarma planı.", 'https://images-na.ssl-images-amazon.com/images/P/2221000455.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Ben, Robot', 'Isaac Asimov', '9783641132071', 'Bilim Kurgu', 1950, 'Üç robot yasası çerçevesinde yapay zeka ve insan ilişkileri öyküleri.', 'https://images-na.ssl-images-amazon.com/images/P/9783641132071.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Zaman Makinesi', 'H.G. Wells', '9781434452399', 'Bilim Kurgu', 1895, 'Geleceğe seyahat eden bir bilim insanının Eloi ve Morlock ırklarıyla karşılaşması.', 'https://images-na.ssl-images-amazon.com/images/P/9781434452399.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Dünyalar Savaşı', 'H.G. Wells', '1613825560', 'Bilim Kurgu', 1898, 'Marslıların dünyayı işgal etme girişimi ve insanlığın çaresizliği.', 'https://images-na.ssl-images-amazon.com/images/P/1613825560.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Karanlığın Sol Eli', 'Ursula K. Le Guin', '0441478026', 'Bilim Kurgu', 1969, 'Çift cinsiyetli canlıların yaşadığı kış gezegeninde bir elçinin hikayesi.', 'https://images-na.ssl-images-amazon.com/images/P/0441478026.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Mülksüzler', 'Ursula K. Le Guin', '9780060504007', 'Bilim Kurgu', 1974, 'Anarşist Anarres ile kapitalist Urras gezegenleri arasındaki bilim insanı.', 'https://images-na.ssl-images-amazon.com/images/P/9780060504007.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Suç ve Ceza', 'Fyodor Dostoyevski', '9786257907637', 'Klasik', 1866, 'Vicdan azabı ve ahlak felsefesi üzerine yazılmış ölümsüz bir başyapıt.', 'https://images-na.ssl-images-amazon.com/images/P/9786257907637.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Sefiller', 'Victor Hugo', '6057936485', 'Klasik', 1862, "Jean Valjean'ın adalet, merhamet ve toplumsal eşitsizlik mücadelesi.", 'https://images-na.ssl-images-amazon.com/images/P/6057936485.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Gurur ve Önyargı', 'Jane Austen', '6257310377', 'Klasik', 1813, 'Elizabeth Bennet ile Bay Darcy arasındaki önyargı ve gurur savaşı.', 'https://images-na.ssl-images-amazon.com/images/P/6257310377.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Bülbülü Öldürmek', 'Harper Lee', '9789999589604', 'Klasik', 1960, "Güney Amerika'da ırkçılık ve adalet kavramını çocuk gözünden anlatan başyapıt.", 'https://images-na.ssl-images-amazon.com/images/P/9789999589604.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Don Kişot', 'Miguel de Cervantes', '9781539524342', 'Klasik', 1605, "Şövalye hikayeleriyle aklını yitiren Don Kişot'un yel değirmenleriyle savaşı.", 'https://images-na.ssl-images-amazon.com/images/P/9781539524342.01._SCLZZZZZZZ_SX200_.jpg'),
            ('İlahi Komedya', 'Dante Alighieri', '6052491612', 'Klasik', 1320, "Dante'nin Cehennem, Araf ve Cennet'e yaptığı manevi yolculuk.", 'https://images-na.ssl-images-amazon.com/images/P/6052491612.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Odysseia', 'Homeros', '9780451600219', 'Klasik', -800, "Truva Savaşı'ndan sonra evine dönmeye çalışan Kral Odysseus'un serüvenleri.", 'https://images-na.ssl-images-amazon.com/images/P/9780451600219.01._SCLZZZZZZZ_SX200_.jpg'),
            ('İlyada', 'Homeros', '605980070X', 'Klasik', -800, "Truva Savaşı'nın son dönemlerini ve Aşil'in öfkesini anlatan destan.", 'https://images-na.ssl-images-amazon.com/images/P/605980070X.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Devlet', 'Platon', '0008480095', 'Klasik', -375, 'İdeal devlet yönetimi ve adalet kavramının tartışıldığı diyaloglar.', 'https://images-na.ssl-images-amazon.com/images/P/0008480095.01._SCLZZZZZZZ_SX200_.jpg'),
            ("Sokrates'in Savunması", 'Platon', '9781006969882', 'Klasik', -399, "Sokrates'in ölüme mahkum edilmeden önce yaptığı tarihi savunma.", ''),
            ('Savaş ve Barış', 'Lev Tolstoy', '9781000864640', 'Klasik', 1869, 'Napolyon döneminde Rus toplumunun ve aristokrasisinin yaşamı.', ''),
            ('Anna Karenina', 'Lev Tolstoy', '9781007988948', 'Klasik', 1877, 'Yasak aşkın pençesinde yok olan soylu bir kadının trajedisi.', ''),
            ('Karamazov Kardeşler', 'Fyodor Dostoyevski', '9781004442993', 'Klasik', 1880, 'Baba katilliği ekseninde inanç, ahlak ve insan doğası sorgulaması.', ''),
            ('Budala', 'Fyodor Dostoyevski', '9752899528', 'Klasik', 1869, "Saf ve iyi yürekli Prens Mışkin'in bencil ve hırslı sosyetedeki dramı.", 'https://images-na.ssl-images-amazon.com/images/P/9752899528.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Babalar ve Oğullar', 'Ivan Turgenyev', '9786054840014', 'Klasik', 1862, 'Nihilist Bazarov üzerinden kuşaklar arası fikir çatışmaları.', 'https://images-na.ssl-images-amazon.com/images/P/9786054840014.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Simyacı', 'Paulo Coelho', '9781009933740', 'Roman', 1988, 'Endülüslü bir çobanın kendi kişisel menkıbesini bulma yolculuğu.', ''),
            ('Küçük Prens', 'Antoine de Saint-Exupéry', '9781002194134', 'Roman', 1943, 'Bir çocuğun gözünden büyüklere sevgi, dostluk ve yaşam dersleri.', ''),
            ('Şeker Portakalı', 'José Mauro de Vasconcelos', '9781003422104', 'Roman', 1968, "Küçük Zezé'nin acıları, hayalleri ve şeker portakalı ağacıyla dostluğu.", ''),
            ('Satranç', 'Stefan Zweig', '9780241305164', 'Roman', 1941, "Nazi esaretinde akıl sağlığını satranç oynayarak koruyan Dr. B'nin öyküsü.", 'https://images-na.ssl-images-amazon.com/images/P/9780241305164.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Dönüşüm', 'Franz Kafka', '9781003358655', 'Roman', 1915, "Gregor Samsa'nın bir sabah uyandığında kendini dev bir böceğe dönüşmüş bulması.", ''),
            ('Uçurtma Avcısı', 'Khaled Hosseini', '9780385660068', 'Roman', 2003, "Afganistan'daki çocukluk arkadaşlığı, ihanet ve kefaret arayışı.", 'https://images-na.ssl-images-amazon.com/images/P/9780385660068.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Kürk Mantolu Madonna', 'Sabahattin Ali', '9786052972120', 'Roman', 1943, "Raif Efendi'nin Maria Puder'e duyduğu sessiz ve derin aşkın öyküsü.", 'https://images-na.ssl-images-amazon.com/images/P/9786052972120.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Tutunamayanlar', 'Oğuz Atay', '9781008288511', 'Roman', 1971, 'Modern Türk edebiyatının yönünü değiştiren, aydın yabancılaşması romanı.', ''),
            ('İnce Memed', 'Yaşar Kemal', '9781003764429', 'Roman', 1955, 'Çukurova köylüsünün ağalık düzenine ve haksızlıklara karşı isyanı.', ''),
            ('Saatleri Ayarlama Enstitüsü', 'Ahmet Hamdi Tanpınar', '9781009585931', 'Roman', 1961, 'Doğu ile Batı arasında sıkışan Türk toplumunun absürt hicvi.', ''),
            ('Mai ve Siyah', 'Halit Ziya Uşaklıgil', '9781008310307', 'Roman', 1897, "Ahmet Cemil'in hayalleri ve gerçek hayatın hayal kırıklıkları.", ''),
            ('Serenad', 'Zülfü Livaneli', '6050900280', 'Roman', 2011, '60 yıllık bir aşkın izinde dünya tarihi ve insanlık dramları.', 'https://images-na.ssl-images-amazon.com/images/P/6050900280.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Martı Jonathan Livingston', 'Richard Bach', '9781000641703', 'Roman', 1970, 'Uçmanın sadece yemek bulmaktan öte bir şey olduğuna inanan bir martı.', ''),
            ('Goriot Baba', 'Honoré de Balzac', '9781008623439', 'Roman', 1835, 'Kızları için her şeyini feda eden fedakar bir babanın trajedisi.', ''),
            ('Vadideki Zambak', 'Honoré de Balzac', '9786053143505', 'Roman', 1835, 'Felix ile Madam de Mortsauf arasındaki imkansız aşkın hikayesi.', 'https://images-na.ssl-images-amazon.com/images/P/9786053143505.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Böyle Buyurdu Zerdüşt', 'Friedrich Nietzsche', '9754060401', 'Felsefe', 1883, "Nietzsche'nin Üstinsan ve bengi dönüş fikirlerini anlattığı başyapıtı.", 'https://images-na.ssl-images-amazon.com/images/P/9754060401.01._SCLZZZZZZZ_SX200_.jpg'),
            ('İnsanın Anlam Arayışı', 'Viktor E. Frankl', '9781005929216', 'Felsefe', 1946, 'Toplama kampındaki deneyimler ışığında insanın yaşama anlam bulma ihtiyacı.', ''),
            ('Kelimeler', 'Jean-Paul Sartre', '9781003260172', 'Felsefe', 1963, "Varoluşçu filozof Sartre'ın kendi çocukluğu ve yazarlık serüveni.", ''),
            ('Yabancı', 'Albert Camus', '9781007836666', 'Felsefe', 1942, 'Hayatın anlamsızlığına ve toplumsal kurallara kayıtsız kalan Meursault.', ''),
            ('Sisifos Söyleni', 'Albert Camus', '9781002794225', 'Felsefe', 1942, 'Hayatın absürtlüğü karşısında intiharı reddedip başkaldırma felsefesi.', ''),
            ('Aforizmalar', 'Franz Kafka', '605223704X', 'Felsefe', 1920, "Kafka'nın yaşam, ölüm, günah ve kurtuluş üzerine derin aforizmaları.", 'https://images-na.ssl-images-amazon.com/images/P/605223704X.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Denemeler', 'Michel de Montaigne', '9786054401062', 'Felsefe', 1580, 'İnsan doğası, dostluk, okumak ve yaşam üzerine ilk denemeler.', 'https://images-na.ssl-images-amazon.com/images/P/9786054401062.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Ahlakın Soykütüğü', 'Friedrich Nietzsche', '9781005742817', 'Felsefe', 1887, 'Ahlakın kökenleri ve toplumsal değerlerin felsefi ve tarihsel analizi.', ''),
            ('Düşünceler', 'Marcus Aurelius', '9781005610994', 'Felsefe', 180, "Roma İmparatoru ve Stoa filozofu Aurelius'un kendine yazdığı notlar.", ''),
            ('Mutlu Olma Sanatı', 'Arthur Schopenhauer', '9789750741203', 'Felsefe', 1851, "Schopenhauer'ın kötümser felsefesinden sıyrılan pratik yaşam öğütleri.", 'https://images-na.ssl-images-amazon.com/images/P/9789750741203.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Sapiens', 'Yuval Noah Harari', '9781007563139', 'Tarih', 2011, 'İnsan türünün bilişsel, tarım ve bilim devrimleriyle yükseliş tarihi.', ''),
            ('Homo Deus', 'Yuval Noah Harari', '9781009985479', 'Tarih', 2015, 'Yapay zeka ve biyoteknoloji çağında insanlığın geleceği.', ''),
            ('21. Yüzyıl İçin 21 Ders', 'Yuval Noah Harari', '9781984801494', 'Tarih', 2018, 'Günümüz dünyasının teknolojik ve politik krizlerine bakış.', 'https://images-na.ssl-images-amazon.com/images/P/9781984801494.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Tüfek, Mikrop ve Çelik', 'Jared Diamond', '9781003012731', 'Tarih', 1997, 'Coğrafi faktörlerin medeniyetlerin kaderini nasıl belirlediğinin analizi.', ''),
            ('Çöküş', 'Jared Diamond', '9781101502006', 'Tarih', 2005, 'Eski toplumların ekolojik krizler nedeniyle yok oluş öyküleri.', 'https://images-na.ssl-images-amazon.com/images/P/9781101502006.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Devlet-i Aliyye', 'Halil Inalcık', '9781007503900', 'Tarih', 2009, "Büyük tarihçi Halil İnalcık'ın gözünden Osmanlı İmparatorluğu.", ''),
            ('İmparatorluğun En Uzun Yüzyılı', 'İlber Ortaylı', '9781002987692', 'Tarih', 1983, "Osmanlı'nın 19. yüzyıldaki modernleşme ve ayakta kalma çabaları.", ''),
            ('Tarihin Sınırlarına Yolculuk', 'İlber Ortaylı', '9781008263868', 'Tarih', 2007, 'Tarihsel mekanlar, şehirler ve medeniyetlerin izleri.', ''),
            ('Nutuk', 'Mustafa Kemal Atatürk', '9758980408', 'Tarih', 1927, "Kurtuluş Savaşı ve Türkiye Cumhuriyeti'nin kuruluşunun belgesi.", 'https://images-na.ssl-images-amazon.com/images/P/9758980408.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Tek Adam', 'Şevket Süreyya Aydemir', '9781006732489', 'Tarih', 1963, "Mustafa Kemal Atatürk'ün hayatı ve dönemin tarihi koşulları.", ''),
            ('Kızıl Soruşturma', 'Arthur Conan Doyle', '9781005041817', 'Gizem', 1887, "Sherlock Holmes ve Dr. Watson'ın ilk tanışması ve ilk ortak davaları.", ''),
            ('Dörtlerin İmzası', 'Arthur Conan Doyle', '9781006595615', 'Gizem', 1890, 'Kayıp bir hazine, gizemli bir cinayet ve zehirli iğneler.', ''),
            ('Doğu Ekspresinde Cinayet', 'Agatha Christie', '9781004153813', 'Gizem', 1934, "Hercule Poirot'nun lüks trende işlenen gizemli cinayeti çözmesi.", ''),
            ('Roger Ackroyd Cinayeti', 'Agatha Christie', '9780593639580', 'Gizem', 1926, 'Ters köşe sonuyla polisiye edebiyatın en ünlü dedektiflik romanı.', 'https://images-na.ssl-images-amazon.com/images/P/9780593639580.01._SCLZZZZZZZ_SX200_.jpg'),
            ('On Küçük Zenci', 'Agatha Christie', '9781004604371', 'Gizem', 1939, 'Issız bir adaya çağrılan on kişinin geçmiş günahlarıyla yüzleşmesi.', ''),
            ('Da Vinci Şifresi', 'Dan Brown', '9788497870801', 'Gizem', 2003, "Louvre Müzesi'ndeki cinayetle başlayan İsa ve Kutsal Kase sırrı.", 'https://images-na.ssl-images-amazon.com/images/P/9788497870801.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Melekler ve Şeytanlar', 'Dan Brown', '9781002916246', 'Gizem', 2000, "Vatikan'ı yok etmekle tehdit eden İlluminati örgütünün peşinde.", ''),
            ('Kayıp Sembol', 'Dan Brown', '9781008027882', 'Gizem', 2009, "Masonik gizemler ve Washington DC'de zamana karşı yarış.", ''),
            ('Cehennem', 'Dan Brown', '9789752116849', 'Gizem', 2013, "Dante'nin Cehennem tasviri üzerinden dünya nüfusunu azaltma planı.", 'https://images-na.ssl-images-amazon.com/images/P/9789752116849.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Kızıl Nehirler', 'Jean-Christophe Grangé', '9781001798729', 'Gizem', 1998, "Alpler'de işlenen vahşi cinayetleri araştıran iki dedektifin yolu.", ''),
            ('Dost Kazanma Sanatı', 'Dale Carnegie', '9781006198392', 'Kişisel Gelişim', 1936, 'İletişim becerilerini geliştirme ve popüler olma yöntemleri.', ''),
            ('Etkili İnsanların 7 Alışkanlığı', 'Stephen R. Covey', '9754346534', 'Kişisel Gelişim', 1989, 'Karakter odaklı kişisel liderlik ve verimlilik ilkeleri.', 'https://images-na.ssl-images-amazon.com/images/P/9754346534.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Düşünce Gücüyle Treat', 'Louise L. Hay', '9781000579070', 'Kişisel Gelişim', 1984, 'Pozitif düşüncenin fiziksel sağlık üzerindeki iyileştirici gücü.', ''),
            ('Bilinçaltının Gücü', 'Joseph Murphy', '6056949508', 'Kişisel Gelişim', 1963, 'Zihninizin gizli gücünü kullanarak hayatınızı dönüştürme yolları.', 'https://images-na.ssl-images-amazon.com/images/P/6056949508.01._SCLZZZZZZZ_SX200_.jpg'),
            ('Zengin Baba Yoksul Baba', 'Robert T. Kiyosaki', '9781005490445', 'Kişisel Gelişim', 1997, 'Finansal okuryazarlık ve parayı çalıştırma sanatı.', ''),
            ('Hızlı ve Yavaş Düşünme', 'Daniel Kahneman', '9781007601575', 'Kişisel Gelişim', 2011, 'Nobel ödüllü ekonomistin beynimizin iki sistemli karar mekanizması analizi.', ''),
            ('İrade Gücü', 'Roy F. Baumeister', '9781002231851', 'Kişisel Gelişim', 2011, 'Öz denetimin ve iradenin hayat başarısındaki kritik rolü.', ''),
            ('Atomik Alışkanlıklar', 'James Clear', '9781008039762', 'Kişisel Gelişim', 2018, 'Küçük değişimlerin hayatınızda nasıl devasa sonuçlar yaratacağı.', ''),
            ('Pürüzsüz Zihin', 'Göran Backlund', '9781008892512', 'Kişisel Gelişim', 2015, 'Zihinsel karmaşadan uzaklaşıp berrak düşünme yolları.', ''),
            ('Şimdinin Gücü', 'Eckhart Tolle', '9781006975751', 'Kişisel Gelişim', 1997, 'Geçmiş ve gelecek kaygısından sıyrılıp şimdiki anı yaşamak.', ''),
        ]
        
        for b in books_data:
            cover_url = b[6]
            if not cover_url or not cover_url.startswith("http"):
                cover_url = f"https://images-na.ssl-images-amazon.com/images/P/{b[2]}.01._SCLZZZZZZZ_SX200_.jpg"
            cursor.execute('''INSERT OR IGNORE INTO books 
                           (title, author, isbn, category, published_year, description, cover_image_url, total_copies, available_copies) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                           (b[0], b[1], b[2], b[3], b[4], b[5], cover_url, 5, 5))
        conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()

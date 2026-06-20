import os
import sqlite3
import bcrypt
from models.database import init_db, get_connection
from controllers.library import BookController

def seed():
    print("Veritabanı sıfırlanıyor...")
    
    # Veritabanını tamamen temizleyip yeniden ilklendirmek için init_db çağırıyoruz
    init_db()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tüm verileri sıfırla
    tables = [
        "admins", "members", "books", "borrows", "wishlist", 
        "reviews", "reservations", "book_requests", "notifications", 
        "profile_requests", "audit_logs"
    ]
    for table in tables:
        cursor.execute(f"DELETE FROM {table};")
        # Autoincrement sayaçlarını sıfırla
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")
        
    conn.commit()
    print("Tüm kullanıcılar, kitaplar ve kayıtlar sıfırlandı.")
    
    # 1. BİR ADET VARSAYILAN ADMIN OLUŞTURMA
    salt = bcrypt.gensalt()
    hashed_admin = bcrypt.hashpw(b"admin123", salt).decode('utf-8')
    cursor.execute(
        "INSERT INTO admins (username, password_hash, name, email) VALUES (?, ?, ?, ?)",
        ("admin", hashed_admin, "Sistem Yöneticisi", "admin@lumina.com")
    )
    
    # 2. BİR ADET VARSAYILAN KULLANICI (ÜYE) OLUŞTURMA (Önceden Onaylı)
    hashed_member = bcrypt.hashpw(b"uye123", salt).decode('utf-8')
    cursor.execute(
        "INSERT INTO members (name, email, phone, password_hash, is_approved) VALUES (?, ?, ?, ?, 1)",
        ("Örnek Üye", "uye@lumina.com", "5551234567", hashed_member)
    )
    
    conn.commit()
    conn.close()
    print("Varsayılan Admin (admin/admin123) ve varsayılan Üye (uye@lumina.com/uye123) oluşturuldu.")

    # 3. EN AZ 100 ADET ÖRNEK KİTAP VERİSİ
    books_data = [
        # Fantastik (15)
        ("Harry Potter ve Felsefe Taşı", "J.K. Rowling", "Fantastik", 1997, "Büyücülük dünyasına adım atan genç Harry'nin maceraları."),
        ("Yüzüklerin Efendisi: Yüzük Kardeşliği", "J.R.R. Tolkien", "Fantastik", 1954, "Orta Dünya'yı karanlıktan kurtarmak için çıkılan destansı yolculuk."),
        ("Hobbit", "J.R.R. Tolkien", "Fantastik", 1937, "Bilbo Baggins'in ejderha Smaug'un hazinesini geri alma macerası."),
        ("Harry Potter ve Sırlar Odası", "J.K. Rowling", "Fantastik", 1998, "Hogwarts'ta taşlaşan öğrenciler ve Sırlar Odası'nın gizemi."),
        ("Harry Potter ve Azkaban Tutsağı", "J.K. Rowling", "Fantastik", 1999, "Azkaban hapishanesinden kaçan gizemli Sirius Black'in hikayesi."),
        ("Yüzüklerin Efendisi: İki Kule", "J.R.R. Tolkien", "Fantastik", 1954, "Kardeşliğin dağılmasıyla başlayan amansız savaşlar ve yolculuklar."),
        ("Yüzüklerin Efendisi: Kralın Dönüşü", "J.R.R. Tolkien", "Fantastik", 1955, "Tek yüzüğün yok edilmesi ve Gondor'un yeni kralının gelişi."),
        ("Rüzgarın Adı", "Patrick Rothfuss", "Fantastik", 2007, "Kvothe adındaki efsanevi büyücü ve müzisyenin kendi ağzından hikayesi."),
        ("Bilge Adamın Korkusu", "Patrick Rothfuss", "Fantastik", 2011, "Kvothe'un efsanesini ararken karşılaştığı yeni tehlikeler ve maceralar."),
        ("Yerdeniz Büyücüsü", "Ursula K. Le Guin", "Fantastik", 1968, "Genç büyücü Ged'in gölgesiyle yüzleşme ve olgunlaşma mücadelesi."),
        ("Puslu Kıtalar Atlası", "İhsan Oktay Anar", "Fantastik", 1995, "Düşler ve gerçekler arasında kaybolan Osmanlı dönemi Galata hikayeleri."),
        ("Aslan, Cadı ve Gardırop", "C.S. Lewis", "Fantastik", 1950, "Sihirli bir gardıroptan Narnia dünyasına geçen dört kardeşin serüveni."),
        ("Taht Oyunları", "George R.R. Martin", "Fantastik", 1996, "Westeros kıtasındaki yedi krallığın taht mücadeleleri ve entrikaları."),
        ("Kralların Çarpışması", "George R.R. Martin", "Fantastik", 1998, "Demir Taht için savaşan beş kralın kanlı mücadelesi."),
        ("Kılıçların Fırtınası", "George R.R. Martin", "Fantastik", 2000, "Westeros'taki savaşın derinleşmesi ve beklenmedik ittifaklar."),
        
        # Bilim Kurgu / Distopya (15)
        ("1984", "George Orwell", "Bilim Kurgu", 1949, "Büyük Birader'in gözetiminde, düşüncenin yasaklandığı distopik bir dünya."),
        ("Cesur Yeni Dünya", "Aldous Huxley", "Bilim Kurgu", 1932, "Teknoloji ve haz odaklı, aile ve duyguların olmadığı yapay bir toplum."),
        ("Fahrenheit 451", "Ray Bradbury", "Bilim Kurgu", 1953, "Kitap okumanın ve saklamanın yasak olduğu, itfaiyecilerin kitap yaktığı dünya."),
        ("Otomatik Portakal", "Anthony Burgess", "Bilim Kurgu", 1962, "Şiddet yanlısı bir gencin devlet eliyle 'iyi'leştirilme çabaları."),
        ("Vakıf", "Isaac Asimov", "Bilim Kurgu", 1951, "Galaktik İmparatorluğun çöküşünü öngören psikotarih biliminin doğuşu."),
        ("Vakıf ve İmparatorluk", "Isaac Asimov", "Bilim Kurgu", 1952, "Çöken imparatorluğun Vakıf'a karşı son saldırıları ve Katır gizemi."),
        ("İkinci Vakıf", "Isaac Asimov", "Bilim Kurgu", 1953, "Katır'ın yükselişi karşısında gizli İkinci Vakıf'ın ortaya çıkışı."),
        ("Dune", "Frank Herbert", "Bilim Kurgu", 1965, "Çöl gezegeni Arrakis'te baharat savaşı ve Paul Atreides'in yükselişi."),
        ("Dune Mesihi", "Frank Herbert", "Bilim Kurgu", 1969, "İmparator Paul Atreides'in din ve siyaset kıskacındaki trajedisi."),
        ("Dune Çocukları", "Frank Herbert", "Bilim Kurgu", 1976, "Paul'ün çocukları Leto ve Ghanima'nın insanlığın geleceğini kurtarma planı."),
        ("Ben, Robot", "Isaac Asimov", "Bilim Kurgu", 1950, "Üç robot yasası çerçevesinde yapay zeka ve insan ilişkileri öyküleri."),
        ("Zaman Makinesi", "H.G. Wells", "Bilim Kurgu", 1895, "Geleceğe seyahat eden bir bilim insanının Eloi ve Morlock ırklarıyla karşılaşması."),
        ("Dünyalar Savaşı", "H.G. Wells", "Bilim Kurgu", 1898, "Marslıların dünyayı işgal etme girişimi ve insanlığın çaresizliği."),
        ("Karanlığın Sol Eli", "Ursula K. Le Guin", "Bilim Kurgu", 1969, "Çift cinsiyetli canlılerin yaşadığı kış gezegeninde bir elçinin hikayesi."),
        ("Mülksüzler", "Ursula K. Le Guin", "Bilim Kurgu", 1974, "Anarşist Anarres ile kapitalist Urras gezegenleri arasındaki bilim insanı."),

        # Klasikler (15)
        ("Suç ve Ceza", "Fyodor Dostoyevski", "Klasik", 1866, "Vicdan azabı ve ahlak felsefesi üzerine yazılmış ölümsüz bir başyapıt."),
        ("Sefiller", "Victor Hugo", "Klasik", 1862, "Jean Valjean'ın adalet, merhamet ve toplumsal eşitsizlik mücadelesi."),
        ("Gurur ve Önyargı", "Jane Austen", "Klasik", 1813, "Elizabeth Bennet ile Bay Darcy arasındaki önyargı ve gurur savaşı."),
        ("Bülbülü Öldürmek", "Harper Lee", "Klasik", 1960, "Güney Amerika'da ırkçılık ve adalet kavramını çocuk gözünden anlatan başyapıt."),
        ("Don Kişot", "Miguel de Cervantes", "Klasik", 1605, "Şövalye hikayeleriyle aklını yitiren Don Kişot'un yel değirmenleriyle savaşı."),
        ("İlahi Komedya", "Dante Alighieri", "Klasik", 1320, "Dante'nin Cehennem, Araf ve Cennet'e yaptığı manevi yolculuk."),
        ("Odysseia", "Homeros", "Klasik", -800, "Truva Savaşı'ndan sonra evine dönmeye çalışan Kral Odysseus'un serüvenleri."),
        ("İlyada", "Homeros", "Klasik", -800, "Truva Savaşı'nın son dönemlerini ve Aşil'in öfkesini anlatan destan."),
        ("Devlet", "Platon", "Klasik", -375, "İdeal devlet yönetimi ve adalet kavramının tartışıldığı diyaloglar."),
        ("Sokrates'in Savunması", "Platon", "Klasik", -399, "Sokrates'in ölüme mahkum edilmeden önce yaptığı tarihi savunma."),
        ("Savaş ve Barış", "Lev Tolstoy", "Klasik", 1869, "Napolyon döneminde Rus toplumunun ve aristokrasisinin yaşamı."),
        ("Anna Karenina", "Lev Tolstoy", "Klasik", 1877, "Yasak aşkın pençesinde yok olan soylu bir kadının trajedisi."),
        ("Karamazov Kardeşler", "Fyodor Dostoyevski", "Klasik", 1880, "Baba katilliği ekseninde inanç, ahlak ve insan doğası sorgulaması."),
        ("Budala", "Fyodor Dostoyevski", "Klasik", 1869, "Saf ve iyi yürekli Prens Mışkin'in bencil ve hırslı sosyetedeki dramı."),
        ("Babalar ve Oğullar", "Ivan Turgenyev", "Klasik", 1862, "Nihilist Bazarov üzerinden kuşaklar arası fikir çatışmaları."),

        # Roman (15)
        ("Simyacı", "Paulo Coelho", "Roman", 1988, "Endülüslü bir çobanın kendi kişisel menkıbesini bulma yolculuğu."),
        ("Küçük Prens", "Antoine de Saint-Exupéry", "Roman", 1943, "Bir çocuğun gözünden büyüklere sevgi, dostluk ve yaşam dersleri."),
        ("Şeker Portakalı", "José Mauro de Vasconcelos", "Roman", 1968, "Küçük Zezé'nin acıları, hayalleri ve şeker portakalı ağacıyla dostluğu."),
        ("Satranç", "Stefan Zweig", "Roman", 1941, "Nazi esaretinde akıl sağlığını satranç oynayarak koruyan Dr. B'nin öyküsü."),
        ("Dönüşüm", "Franz Kafka", "Roman", 1915, "Gregor Samsa'nın bir sabah uyandığında kendini dev bir böceğe dönüşmüş bulması."),
        ("Uçurtma Avcısı", "Khaled Hosseini", "Roman", 2003, "Afganistan'daki çocukluk arkadaşlığı, ihanet ve kefaret arayışı."),
        ("Kürk Mantolu Madonna", "Sabahattin Ali", "Roman", 1943, "Raif Efendi'nin Maria Puder'e duyduğu sessiz ve derin aşkın öyküsü."),
        ("Tutunamayanlar", "Oğuz Atay", "Roman", 1971, "Modern Türk edebiyatının yönünü değiştiren, aydın yabancılaşması romanı."),
        ("İnce Memed", "Yaşar Kemal", "Roman", 1955, "Çukurova köylüsünün ağalık düzenine ve haksızlıklara karşı isyanı."),
        ("Saatleri Ayarlama Enstitüsü", "Ahmet Hamdi Tanpınar", "Roman", 1961, "Doğu ile Batı arasında sıkışan Türk toplumunun absürt hicvi."),
        ("Mai ve Siyah", "Halit Ziya Uşaklıgil", "Roman", 1897, "Ahmet Cemil'in hayalleri ve gerçek hayatın hayal kırıklıkları."),
        ("Serenad", "Zülfü Livaneli", "Roman", 2011, "60 yıllık bir aşkın izinde dünya tarihi ve insanlık dramları."),
        ("Martı Jonathan Livingston", "Richard Bach", "Roman", 1970, "Uçmanın sadece yemek bulmaktan öte bir şey olduğuna inanan bir martı."),
        ("Goriot Baba", "Honoré de Balzac", "Roman", 1835, "Kızları için her şeyini feda eden fedakar bir babanın trajedisi."),
        ("Vadideki Zambak", "Honoré de Balzac", "Roman", 1835, "Felix ile Madam de Mortsauf arasındaki imkansız aşkın hikayesi."),

        # Felsefe (10)
        ("Böyle Buyurdu Zerdüşt", "Friedrich Nietzsche", "Felsefe", 1883, "Nietzsche'nin Üstinsan ve bengi dönüş fikirlerini anlattığı başyapıtı."),
        ("İnsanın Anlam Arayışı", "Viktor E. Frankl", "Felsefe", 1946, "Toplama kampındaki deneyimler ışığında insanın yaşama anlam bulma ihtiyacı."),
        ("Kelimeler", "Jean-Paul Sartre", "Felsefe", 1963, "Varoluşçu filozof Sartre'ın kendi çocukluğu ve yazarlık serüveni."),
        ("Yabancı", "Albert Camus", "Felsefe", 1942, "Hayatın anlamsızlığına ve toplumsal kurallara kayıtsız kalan Meursault."),
        ("Sisifos Söyleni", "Albert Camus", "Felsefe", 1942, "Hayatın absürtlüğü karşısında intiharı reddedip başkaldırma felsefesi."),
        ("Aforizmalar", "Franz Kafka", "Felsefe", 1920, "Kafka'nın yaşam, ölüm, günah ve kurtuluş üzerine derin aforizmaları."),
        ("Denemeler", "Michel de Montaigne", "Felsefe", 1580, "İnsan doğası, dostluk, okumak ve yaşam üzerine ilk denemeler."),
        ("Ahlakın Soykütüğü", "Friedrich Nietzsche", "Felsefe", 1887, "Ahlakın kökenleri ve toplumsal değerlerin felsefi ve tarihsel analizi."),
        ("Düşünceler", "Marcus Aurelius", "Felsefe", 180, "Roma İmparatoru ve Stoa filozofu Aurelius'un kendine yazdığı notlar."),
        ("Mutlu Olma Sanatı", "Arthur Schopenhauer", "Felsefe", 1851, "Schopenhauer'ın kötümser felsefesinden sıyrılan pratik yaşam öğütleri."),

        # Tarih (10)
        ("Sapiens", "Yuval Noah Harari", "Tarih", 2011, "İnsan türünün bilişsel, tarım ve bilim devrimleriyle yükseliş tarihi."),
        ("Homo Deus", "Yuval Noah Harari", "Tarih", 2015, "Yapay zeka ve biyoteknoloji çağında insanlığın geleceği."),
        ("21. Yüzyıl İçin 21 Ders", "Yuval Noah Harari", "Tarih", 2018, "Günümüz dünyasının teknolojik ve politik krizlerine bakış."),
        ("Tüfek, Mikrop ve Çelik", "Jared Diamond", "Tarih", 1997, "Coğrafi faktörlerin medeniyetlerin kaderini nasıl belirlediğinin analizi."),
        ("Çöküş", "Jared Diamond", "Tarih", 2005, "Eski toplumların ekolojik krizler nedeniyle yok oluş öyküleri."),
        ("Devlet-i Aliyye", "Halil Inalcık", "Tarih", 2009, "Büyük tarihçi Halil İnalcık'ın gözünden Osmanlı İmparatorluğu."),
        ("İmparatorluğun En Uzun Yüzyılı", "İlber Ortaylı", "Tarih", 1983, "Osmanlı'nın 19. yüzyıldaki modernleşme ve ayakta kalma çabaları."),
        ("Tarihin Sınırlarına Yolculuk", "İlber Ortaylı", "Tarih", 2007, "Tarihsel mekanlar, şehirler ve medeniyetlerin izleri."),
        ("Nutuk", "Mustafa Kemal Atatürk", "Tarih", 1927, "Kurtuluş Savaşı ve Türkiye Cumhuriyeti'nin kuruluşunun belgesi."),
        ("Tek Adam", "Şevket Süreyya Aydemir", "Tarih", 1963, "Mustafa Kemal Atatürk'ün hayatı ve dönemin tarihi koşulları."),

        # Gizem / Polisiye (10)
        ("Kızıl Soruşturma", "Arthur Conan Doyle", "Gizem", 1887, "Sherlock Holmes ve Dr. Watson'ın ilk tanışması ve ilk ortak davaları."),
        ("Dörtlerin İmzası", "Arthur Conan Doyle", "Gizem", 1890, "Kayıp bir hazine, gizemli bir cinayet ve zehirli iğneler."),
        ("Doğu Ekspresinde Cinayet", "Agatha Christie", "Gizem", 1934, "Hercule Poirot'nun lüks trende işlenen gizemli cinayeti çözmesi."),
        ("Roger Ackroyd Cinayeti", "Agatha Christie", "Gizem", 1926, "Ters köşe sonuyla polisiye edebiyatın en ünlü dedektiflik romanı."),
        ("On Küçük Zenci", "Agatha Christie", "Gizem", 1939, "Issız bir adaya çağrılan on kişinin geçmiş günahlarıyla yüzleşmesi."),
        ("Da Vinci Şifresi", "Dan Brown", "Gizem", 2003, "Louvre Müzesi'ndeki cinayetle başlayan İsa ve Kutsal Kase sırrı."),
        ("Melekler ve Şeytanlar", "Dan Brown", "Gizem", 2000, "Vatikan'ı yok etmekle tehdit eden İlluminati örgütünün peşinde."),
        ("Kayıp Sembol", "Dan Brown", "Gizem", 2009, "Masonik gizemler ve Washington DC'de zamana karşı yarış."),
        ("Cehennem", "Dan Brown", "Gizem", 2013, "Dante'nin Cehennem tasviri üzerinden dünya nüfusunu azaltma planı."),
        ("Kızıl Nehirler", "Jean-Christophe Grangé", "Gizem", 1998, "Alpler'de işlenen vahşi cinayetleri araştıran iki dedektifin yolu."),
        
        # Kişisel Gelişim (10)
        ("Dost Kazanma Sanatı", "Dale Carnegie", "Kişisel Gelişim", 1936, "İletişim becerilerini geliştirme ve popüler olma yöntemleri."),
        ("Etkili İnsanların 7 Alışkanlığı", "Stephen R. Covey", "Kişisel Gelişim", 1989, "Karakter odaklı kişisel liderlik ve verimlilik ilkeleri."),
        ("Düşünce Gücüyle Tedavi", "Louise L. Hay", "Kişisel Gelişim", 1984, "Pozitif düşüncenin fiziksel sağlık üzerindeki iyileştirici gücü."),
        ("Bilinçaltının Gücü", "Joseph Murphy", "Kişisel Gelişim", 1963, "Zihninizin gizli gücünü kullanarak hayatınızı dönüştürme yolları."),
        ("Zengin Baba Yoksul Baba", "Robert T. Kiyosaki", "Kişisel Gelişim", 1997, "Finansal okuryazarlık ve parayı çalıştırma sanatı."),
        ("Hızlı ve Yavaş Düşünme", "Daniel Kahneman", "Kişisel Gelişim", 2011, "Nobel ödüllü ekonomistin beynimizin iki sistemli karar mekanizması analizi."),
        ("İrade Gücü", "Roy F. Baumeister", "Kişisel Gelişim", 2011, "Öz denetimin ve iradenin hayat başarısındaki kritik rolü."),
        ("Atomik Alışkanlıklar", "James Clear", "Kişisel Gelişim", 2018, "Küçük değişimlerin hayatınızda nasıl devasa sonuçlar yaratacağı."),
        ("Pürüzsüz Zihin", "Göran Backlund", "Kişisel Gelişim", 2015, "Zihinsel karmaşadan uzaklaşıp berrak düşünme yolları."),
        ("Şimdinin Gücü", "Eckhart Tolle", "Kişisel Gelişim", 1997, "Geçmiş ve gelecek kaygısından sıyrılıp şimdiki anı yaşamak.")
    ]

    # En estetik ve hızlı yüklenen 15 farklı Unsplash kitap kapağı görseli
    covers = [
        "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400&q=80",
        "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400&q=80",
        "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400&q=80",
        "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400&q=80",
        "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=400&q=80",
        "https://images.unsplash.com/photo-1506880018603-83d5b814b5a6?w=400&q=80",
        "https://images.unsplash.com/photo-1495640388908-05fa85288e61?w=400&q=80",
        "https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=400&q=80",
        "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=400&q=80",
        "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=400&q=80",
        "https://images.unsplash.com/photo-1510172951991-856a654063f9?w=400&q=80",
        "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=400&q=80",
        "https://images.unsplash.com/photo-1531988042231-d39a9cc12a9a?w=400&q=80",
        "https://images.unsplash.com/photo-1509021436665-8f07dbf5bf1d?w=400&q=80",
        "https://images.unsplash.com/photo-1476275466078-4007374efbbe?w=400&q=80"
    ]

    print("Kitaplar veritabanına ekleniyor...")
    for i, b in enumerate(books_data):
        isbn = f"978{1000000000 + i}"
        cover_url = covers[i % len(covers)]
        BookController.add_book(
            title=b[0], 
            author=b[1], 
            isbn=isbn, 
            category=b[2],
            published_year=b[3], 
            description=b[4], 
            cover_image_url=cover_url, 
            total_copies=5
        )
        
    print(f"Toplam {len(books_data)} adet kitap başarıyla veritabanına yüklendi!")

if __name__ == "__main__":
    seed()

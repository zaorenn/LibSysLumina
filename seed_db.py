import os
from models.database import init_db
from controllers.library import BookController
import sqlite3

def seed():
    # Eğer veritabanı yoksa oluştur
    if not os.path.exists("library.db"):
        init_db()

    books = [
        ("Harry Potter ve Felsefe Taşı", "J.K. Rowling", "9780747532699", "Fantastik", 1997, "Büyücülük dünyasına giriş.", "https://covers.openlibrary.org/b/id/10521270-M.jpg", 5),
        ("1984", "George Orwell", "9780451524935", "Bilim Kurgu / Distopya", 1949, "Büyük Birader seni izliyor.", "https://covers.openlibrary.org/b/id/12586616-M.jpg", 4),
        ("Suç ve Ceza", "Fyodor Dostoyevski", "9780140449136", "Klasik", 1866, "Raskolnikov'un vicdan azabı.", "https://covers.openlibrary.org/b/id/12595861-M.jpg", 3),
        ("Yüzüklerin Efendisi: Yüzük Kardeşliği", "J.R.R. Tolkien", "9780544003415", "Fantastik", 1954, "Orta Dünya'da büyük yolculuk.", "https://covers.openlibrary.org/b/id/14467363-M.jpg", 6),
        ("Simyacı", "Paulo Coelho", "9780062315007", "Roman", 1988, "Hazinenin peşinde.", "https://covers.openlibrary.org/b/id/8259441-M.jpg", 5),
        ("Küçük Prens", "Antoine de Saint-Exupéry", "9780156012195", "Çocuk / Felsefe", 1943, "Çöl ve küçük gezegen.", "https://covers.openlibrary.org/b/id/12629633-M.jpg", 8),
        ("Sefiller", "Victor Hugo", "9780451419439", "Klasik", 1862, "Jean Valjean'ın hikayesi.", "https://covers.openlibrary.org/b/id/14479527-M.jpg", 3),
        ("Hayvan Çiftliği", "George Orwell", "9780451526342", "Hiciv", 1945, "Bütün hayvanlar eşittir.", "https://covers.openlibrary.org/b/id/12598375-M.jpg", 5),
        ("Gurur ve Önyargı", "Jane Austen", "9780141439518", "Klasik Romantizm", 1813, "Elizabeth Bennet'in hikayesi.", "https://covers.openlibrary.org/b/id/12582806-M.jpg", 4),
        ("Bülbülü Öldürmek", "Harper Lee", "9780060935467", "Klasik Roman", 1960, "Irkçılık ve adalet üzerine.", "https://covers.openlibrary.org/b/id/12594326-M.jpg", 4),
        ("Satranç", "Stefan Zweig", "9781590171691", "Kısa Roman", 1941, "Bir satranç dehası.", "https://covers.openlibrary.org/b/id/12693822-M.jpg", 7),
        ("Dönüşüm", "Franz Kafka", "9780553213690", "Felsefi", 1915, "Gregor Samsa'nın böceğe dönüşümü.", "https://covers.openlibrary.org/b/id/12690326-M.jpg", 6),
        ("Şeker Portakalı", "José Mauro de Vasconcelos", "9789750719363", "Roman", 1968, "Zezé'nin hikayesi.", "https://covers.openlibrary.org/b/id/10549073-M.jpg", 5),
        ("Hobbit", "J.R.R. Tolkien", "9780547928227", "Fantastik", 1937, "Bilbo Baggins'in macerası.", "https://covers.openlibrary.org/b/id/12582498-M.jpg", 5),
        ("Goriot Baba", "Honoré de Balzac", "9780199536764", "Klasik", 1835, "Paris sosyetesi ve dram.", "https://covers.openlibrary.org/b/id/12644265-M.jpg", 2),
        ("Olasılıksız", "Adam Fawer", "9780060736774", "Bilim Kurgu / Gerilim", 2005, "Şans ve ihtimaller.", "https://covers.openlibrary.org/b/id/1118318-M.jpg", 4),
        ("Uçurtma Avcısı", "Khaled Hosseini", "9781594631931", "Roman", 2003, "Afganistan'dan Amerika'ya.", "https://covers.openlibrary.org/b/id/12585250-M.jpg", 5),
        ("Fahrenheit 451", "Ray Bradbury", "9781451673319", "Distopya", 1953, "Kitap yakan itfaiyeciler.", "https://covers.openlibrary.org/b/id/12597793-M.jpg", 6),
        ("Otomatik Portakal", "Anthony Burgess", "9780393312836", "Distopya", 1962, "Şiddet ve özgür irade.", "https://covers.openlibrary.org/b/id/12613041-M.jpg", 4),
        ("Cesur Yeni Dünya", "Aldous Huxley", "9780060850524", "Distopya", 1932, "Teknolojik ve kontrol altında bir toplum.", "https://covers.openlibrary.org/b/id/12594537-M.jpg", 5),
        ("Sırça Köşk", "Sabahattin Ali", "9789750800047", "Öykü", 1947, "Sabahattin Ali'nin masalları.", "https://covers.openlibrary.org/b/id/11059383-M.jpg", 4),
        ("Kürk Mantolu Madonna", "Sabahattin Ali", "9789750826214", "Roman", 1943, "Raif Efendi'nin aşkı.", "https://covers.openlibrary.org/b/id/10515155-M.jpg", 10),
        ("Aylak Adam", "Yusuf Atılgan", "9789750801129", "Roman", 1959, "C.'nin arayışı.", "https://covers.openlibrary.org/b/id/8343719-M.jpg", 3),
        ("Tutunamayanlar", "Oğuz Atay", "9789754700114", "Roman", 1971, "Selim Işık ve Turgut Özben.", "https://covers.openlibrary.org/b/id/10549065-M.jpg", 3),
        ("İnce Memed 1", "Yaşar Kemal", "9789750807336", "Roman", 1955, "Toroslar'ın isyanı.", "https://covers.openlibrary.org/b/id/8296716-M.jpg", 4),
        ("Saatleri Ayarlama Enstitüsü", "Ahmet Hamdi Tanpınar", "9789754940503", "Roman", 1961, "Modernleşme ve zaman.", "https://covers.openlibrary.org/b/id/11186716-M.jpg", 3),
        ("Don Kişot", "Miguel de Cervantes", "9780060934347", "Klasik", 1605, "Yel değirmenlerine karşı.", "https://covers.openlibrary.org/b/id/12586710-M.jpg", 2),
        ("Mai ve Siyah", "Halit Ziya Uşaklıgil", "9789754471540", "Roman", 1897, "Ahmet Cemil'in hayalleri.", "https://covers.openlibrary.org/b/id/8165682-M.jpg", 3),
        ("Serenad", "Zülfü Livaneli", "9786050900286", "Roman", 2011, "Tarih ve aşk.", "https://covers.openlibrary.org/b/id/10530755-M.jpg", 6),
        ("Martı Jonathan Livingston", "Richard Bach", "9780743214251", "Felsefi", 1970, "Sınırları aşan bir martı.", "https://covers.openlibrary.org/b/id/12586887-M.jpg", 7)
    ]

    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM books")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        print("Kitaplar veritabanına ekleniyor...")
        for b in books:
            BookController.add_book(
                title=b[0], author=b[1], isbn=b[2], category=b[3],
                published_year=b[4], description=b[5], cover_image_url=b[6], total_copies=b[7]
            )
        print(f"{len(books)} adet kitap başarıyla eklendi!")
    else:
        print("Veritabanında halihazırda kitaplar mevcut. Seeding atlandı.")

if __name__ == "__main__":
    seed()

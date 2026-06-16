import sqlite3
import bcrypt
import os

DB_PATH = "library.db"

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
        password_hash TEXT NOT NULL
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
        registered_date DATE DEFAULT CURRENT_DATE
    )
    ''')
    
    # 4. ÖDÜNÇ ALMA TABLOSU (Foreign Keys ile İlişkisel)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS borrows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        member_id INTEGER NOT NULL,
        borrow_date DATE DEFAULT CURRENT_DATE,
        return_date DATE NOT NULL,
        actual_return_date DATE,
        late_fee REAL DEFAULT 0,
        FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
        FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE
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

    # 6. AUDIT LOGS TABLOSU (İşlem Takibi)
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

    # Varsayılan Admin Hesabını Oluştur (admin / admin123)
    cursor.execute("SELECT COUNT(*) FROM admins")
    if cursor.fetchone()[0] == 0:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(b"admin123", salt).decode('utf-8')
        cursor.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)", ("admin", hashed))
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()

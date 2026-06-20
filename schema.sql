-- Lumina Kütüphane Yönetim Sistemi - Veritabanı Şeması
-- SQLite ile uyumludur.

-- 1. ADMIN TABLOSU (Şifreler bcrypt ile hash'lenerek Python katmanında saklanır)
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT DEFAULT 'Yönetici',
    email TEXT DEFAULT 'admin@lumina.com'
);

-- 2. KİTAPLAR TABLOSU
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
);

-- 3. ÜYELER TABLOSU (Şifreler bcrypt ile hash'lenerek Python katmanında saklanır)
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    password_hash TEXT NOT NULL,
    is_approved BOOLEAN DEFAULT 0,
    must_change_password BOOLEAN DEFAULT 0,
    registered_date DATE DEFAULT CURRENT_TIMESTAMP
);

-- 4. ÖDÜNÇ ALMA TABLOSU
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
);

-- 5. İSTEK KİTAP TABLOSU
CREATE TABLE IF NOT EXISTS book_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    member_name TEXT,
    title TEXT NOT NULL,
    author TEXT,
    isbn TEXT,
    cover_url TEXT,
    request_date DATE DEFAULT CURRENT_TIMESTAMP
);

-- 6. BİLDİRİMLER TABLOSU
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT 0,
    created_at DATE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id)
);

-- 7. PROFİL GÜNCELLEME İSTEKLERİ TABLOSU
CREATE TABLE IF NOT EXISTS profile_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    member_name TEXT,
    new_name TEXT,
    new_email TEXT,
    status TEXT DEFAULT 'PENDING',
    request_date DATE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id)
);

-- 8. YORUMLAR TABLOSU
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    comment TEXT,
    review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE
);

-- 9. FAVORİLER (WISHLIST) TABLOSU
CREATE TABLE IF NOT EXISTS wishlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE,
    UNIQUE(book_id, member_id)
);

-- 10. REZERVASYON TABLOSU
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    reservation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'Bekliyor',
    FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE
);

-- 11. AUDIT LOGS TABLOSU (İşlem Takibi)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT,
    table_name TEXT,
    record_id INTEGER,
    action_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- TRIGGER 1: Ödünç alma sonrası stok düşür ve logla
CREATE TRIGGER IF NOT EXISTS after_borrow_insert
AFTER INSERT ON borrows
BEGIN
    UPDATE books SET available_copies = available_copies - 1 WHERE id = NEW.book_id;
    INSERT INTO audit_logs (action_type, table_name, record_id, action_date, description)
    VALUES ('BORROW', 'borrows', NEW.id, datetime('now', 'localtime'), 'Kitap ödünç verildi. Üye ID: ' || NEW.member_id);
END;

-- TRIGGER 2: İade sonrası stok artır, gecikme cezası hesapla (Geciken gün x 5 TL) ve logla
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

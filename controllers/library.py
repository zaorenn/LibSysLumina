from models.database import get_connection
import datetime
import bcrypt
import requests
import sqlite3

class BookController:
    @staticmethod
    def add_book(title, author, isbn, category, published_year, description, cover_image_url, total_copies):
        import random
        # Benzersiz ISBN oluştur (Sadece geçerli bir ISBN verilmediyse)
        if not isbn or isbn.strip() in ("", "000000000"):
            while True:
                conn = get_connection()
                cursor = conn.cursor()
                new_isbn = "978" + str(random.randint(1000000000, 9999999999))
                cursor.execute("SELECT id FROM books WHERE isbn = ?", (new_isbn,))
                if not cursor.fetchone():
                    isbn = new_isbn
                    conn.close()
                    break
                conn.close()
            
        if not cover_image_url:
            if isbn and isbn.strip() not in ("", "000000000"):
                cover_image_url = f"https://images-na.ssl-images-amazon.com/images/P/{isbn}.01._SCLZZZZZZZ_SX200_.jpg"
            else:
                try:
                    r = requests.get(f"http://openlibrary.org/search.json?q={title}&limit=1", timeout=5)
                    docs = r.json().get("docs", [])
                    if docs:
                        fetched_isbn = docs[0].get("isbn", [""])[0]
                        if fetched_isbn:
                            cover_image_url = f"https://images-na.ssl-images-amazon.com/images/P/{fetched_isbn}.01._SCLZZZZZZZ_SX200_.jpg"
                except:
                    pass

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO books 
                           (title, author, isbn, category, published_year, description, cover_image_url, total_copies, available_copies) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                           (title, author, isbn, category, published_year, description, cover_image_url, total_copies, total_copies))
            conn.commit()
            return True, "Kitap başarıyla eklendi."
        except sqlite3.IntegrityError:
            return False, "Veritabanı kuralı ihlali (Örn: Bu ISBN zaten var)."
        except Exception as e:
            return False, "Beklenmeyen hata: " + str(e)
        finally:
            conn.close()

    @staticmethod
    def get_all_books(search_term="", limit=20, offset=0):
        conn = get_connection()
        cursor = conn.cursor()
        like_term = f"%{search_term}%"
        cursor.execute('''SELECT id, title, author, isbn, category, published_year, description, cover_image_url, total_copies, available_copies 
                          FROM books 
                          WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ? OR category LIKE ?
                          LIMIT ? OFFSET ?''', 
                       (like_term, like_term, like_term, like_term, limit, offset))
        rows = cursor.fetchall()
        conn.close()
        return rows

    @staticmethod
    def delete_book(book_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def update_book(book_id, title, author, isbn, category, published_year, description, cover_image_url, total_copies):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT total_copies, available_copies FROM books WHERE id = ?", (book_id,))
            current_total, current_avail = cursor.fetchone()
            diff = total_copies - current_total
            new_avail = current_avail + diff
            
            if new_avail < 0:
                return False, "Mevcut kopya sayısı negatif olamaz, ödünçteki kitapları bekleyin."
                
            cursor.execute('''UPDATE books 
                              SET title=?, author=?, isbn=?, category=?, published_year=?, description=?, cover_image_url=?, total_copies=?, available_copies=? 
                              WHERE id=?''', 
                           (title, author, isbn, category, published_year, description, cover_image_url, total_copies, new_avail, book_id))
            conn.commit()
            return True, "Kitap güncellendi."
        except sqlite3.IntegrityError:
            return False, "Benzersiz bir alan (ISBN vs.) zaten kullanılıyor."
        except Exception as e:
            return False, "Bilinmeyen hata: " + str(e)
        finally:
            conn.close()


class MemberController:
    @staticmethod
    def add_member(name, email, phone, password):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            cursor.execute("INSERT INTO members (name, email, phone, password_hash) VALUES (?, ?, ?, ?)", (name, email, phone, hashed))
            conn.commit()
            return True, "Üye başarıyla eklendi."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_all_members(search_term=""):
        conn = get_connection()
        cursor = conn.cursor()
        like_term = f"%{search_term}%"
        cursor.execute("SELECT id, name, email, phone, registered_date FROM members WHERE is_approved = 1 AND (name LIKE ? OR email LIKE ?)", 
                       (like_term, like_term))
        rows = cursor.fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_pending_members():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, phone, registered_date FROM members WHERE is_approved = 0")
        rows = cursor.fetchall()
        conn.close()
        return rows

    @staticmethod
    def approve_member(member_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE members SET is_approved = 1 WHERE id = ?", (member_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def delete_member(member_id):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE borrows SET member_id = NULL WHERE member_id = ?", (member_id,))
            cursor.execute("DELETE FROM members WHERE id = ?", (member_id,))
            conn.commit()
            return True, "Üye başarıyla silindi (Ödünç geçmişi korundu)."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

class BorrowController:
    @staticmethod
    def borrow_book(book_id, member_id, days=14):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Sadece hala iade edilmemiş kitabı varsa engelle
            cursor.execute("SELECT COUNT(*) FROM borrows WHERE member_id = ? AND actual_return_date IS NULL", (member_id,))
            active_borrows = cursor.fetchone()[0]
            if active_borrows > 0:
                return False, "Zaten ödünç aldığınız bir kitap var! Yenisini almadan önce profilinizden onu iade etmelisiniz."

            cursor.execute("SELECT available_copies FROM books WHERE id = ?", (book_id,))
            res = cursor.fetchone()
            if not res or res[0] <= 0:
                return False, "Kitap stokta yok."

            cursor.execute("SELECT name FROM members WHERE id = ?", (member_id,))
            m_name = cursor.fetchone()[0]

            return_date = (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
            cursor.execute("INSERT INTO borrows (book_id, member_id, member_name_snapshot, borrow_date, return_date) VALUES (?, ?, ?, DATE('now', 'localtime'), ?)", 
                           (book_id, member_id, m_name, return_date))
            conn.commit()
            return True, "Kitap başarıyla ödünç alındı."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def return_book(borrow_id):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE borrows SET actual_return_date = DATE('now', 'localtime') WHERE id = ? AND actual_return_date IS NULL", (borrow_id,))
            if cursor.rowcount == 0:
                return False, "Zaten iade edilmiş veya geçersiz ID."
            conn.commit()
            return True, "Kitap iade alındı."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_all_borrows():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT br.id, b.title, br.member_name_snapshot, br.borrow_date, br.return_date, br.actual_return_date, br.late_fee 
            FROM borrows br
            JOIN books b ON br.book_id = b.id
            ORDER BY br.id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_member_borrows(member_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT br.id, b.title, b.author, b.cover_image_url, br.borrow_date, br.return_date, br.actual_return_date, br.late_fee 
            FROM borrows br
            JOIN books b ON br.book_id = b.id
            WHERE br.member_id = ?
            ORDER BY br.id DESC
        """, (member_id,))
        rows = cursor.fetchall()
        conn.close()
        return rows
        
    @staticmethod
    def get_active_borrowers_by_book(book_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT member_name_snapshot, borrow_date FROM borrows WHERE book_id = ? AND actual_return_date IS NULL", (book_id,))
        rows = cursor.fetchall()
        conn.close()
        return rows
        
    @staticmethod
    def get_dashboard_stats():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM books")
        total_books = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM borrows WHERE actual_return_date IS NULL")
        active_borrows = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM borrows WHERE actual_return_date IS NULL AND return_date < DATE('now', 'localtime')")
        overdue_books = cursor.fetchone()[0]
        
        conn.close()
        return total_books, active_borrows, overdue_books

class RequestController:
    @staticmethod
    def add_request(member_id, member_name, title, author, isbn, cover_url):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO book_requests 
                              (member_id, member_name, title, author, isbn, cover_url) 
                              VALUES (?, ?, ?, ?, ?, ?)''', 
                           (member_id, member_name, title, author, isbn, cover_url))
            conn.commit()
            return True, "Kitap isteği başarıyla gönderildi."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_all_requests():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, member_id, member_name, title, author, isbn, request_date, cover_url FROM book_requests ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    @staticmethod
    def delete_request(req_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM book_requests WHERE id = ?", (req_id,))
        conn.commit()
        conn.close()

class NotificationController:
    @staticmethod
    def add_notification(member_id, message):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notifications (member_id, message) VALUES (?, ?)", (member_id, message))
        conn.commit()
        conn.close()

    @staticmethod
    def get_unread_notifications(member_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, message, created_at FROM notifications WHERE member_id = ? AND is_read = 0 ORDER BY id DESC", (member_id,))
        rows = cursor.fetchall()
        conn.close()
        return rows
        
    @staticmethod
    def mark_as_read(notif_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notif_id,))
        conn.commit()
        conn.close()

class ProfileRequestController:
    @staticmethod
    def add_request(member_id, member_name, new_name, new_email):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO profile_requests (member_id, member_name, new_name, new_email) VALUES (?, ?, ?, ?)", (member_id, member_name, new_name, new_email))
            conn.commit()
            return True, "Profil güncelleme isteğiniz yöneticiye iletildi."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_pending_requests():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, member_id, member_name, new_name, new_email, request_date FROM profile_requests WHERE status = 'PENDING'")
        rows = cursor.fetchall()
        conn.close()
        return rows

    @staticmethod
    def approve_request(req_id, member_id, new_name, new_email):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE members SET name = ?, email = ? WHERE id = ?", (new_name, new_email, member_id))
        cursor.execute("UPDATE profile_requests SET status = 'APPROVED' WHERE id = ?", (req_id,))
        # Also update snapshot in borrows for history consistency (optional, but good practice if needed. we'll skip for now)
        conn.commit()
        conn.close()
        
    @staticmethod
    def reject_request(req_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE profile_requests SET status = 'REJECTED' WHERE id = ?", (req_id,))
        conn.commit()
        conn.close()

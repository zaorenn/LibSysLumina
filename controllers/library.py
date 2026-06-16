from models.database import get_connection
import datetime
import bcrypt

class BookController:
    @staticmethod
    def add_book(title, author, isbn, category, published_year, description, cover_image_url, total_copies):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO books 
                           (title, author, isbn, category, published_year, description, cover_image_url, total_copies, available_copies) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                           (title, author, isbn, category, published_year, description, cover_image_url, total_copies, total_copies))
            conn.commit()
            return True, "Kitap başarıyla eklendi."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_all_books(search_term=""):
        conn = get_connection()
        cursor = conn.cursor()
        like_term = f"%{search_term}%"
        cursor.execute('''SELECT id, title, author, isbn, category, published_year, description, cover_image_url, total_copies, available_copies 
                          FROM books 
                          WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ? OR category LIKE ?''', 
                       (like_term, like_term, like_term, like_term))
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
        cursor.execute("SELECT id, name, email, phone, registered_date FROM members WHERE name LIKE ? OR email LIKE ?", 
                       (like_term, like_term))
        rows = cursor.fetchall()
        conn.close()
        return rows

    @staticmethod
    def delete_member(member_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM members WHERE id = ?", (member_id,))
        conn.commit()
        conn.close()


class BorrowController:
    @staticmethod
    def borrow_book(book_id, member_id, days=14):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT available_copies FROM books WHERE id = ?", (book_id,))
            res = cursor.fetchone()
            if not res or res[0] <= 0:
                return False, "Kitap stokta yok."

            return_date = (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
            cursor.execute("INSERT INTO borrows (book_id, member_id, borrow_date, return_date) VALUES (?, ?, DATE('now', 'localtime'), ?)", 
                           (book_id, member_id, return_date))
            conn.commit()
            return True, "Kitap başarıyla ödünç verildi."
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
            SELECT br.id, b.title, m.name, br.borrow_date, br.return_date, br.actual_return_date, br.late_fee 
            FROM borrows br
            JOIN books b ON br.book_id = b.id
            JOIN members m ON br.member_id = m.id
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

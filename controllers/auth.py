import bcrypt
from models.database import get_connection

class AuthController:
    @staticmethod
    def login_admin(username, password):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, name, email FROM admins WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row and bcrypt.checkpw(password.encode('utf-8'), row[2].encode('utf-8')):
            return True, {"id": row[0], "username": row[1], "name": row[3], "email": row[4]}
        return False, None

    @staticmethod
    def update_admin_profile(admin_id, new_username, new_name, new_email):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE admins SET username = ?, name = ?, email = ? WHERE id = ?", (new_username, new_name, new_email, admin_id))
            conn.commit()
            return True, "Profil başarıyla güncellendi."
        except Exception as e:
            return False, "Bu kullanıcı adı veya e-posta zaten kullanımda olabilir."
        finally:
            conn.close()

    @staticmethod
    def change_admin_password(admin_id, old_pw, new_pw):
        if len(new_pw) < 7:
            return False, "Şifre en az 7 karakter olmalıdır."
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM admins WHERE id = ?", (admin_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Yönetici bulunamadı."
            
        if not bcrypt.checkpw(old_pw.encode('utf-8'), row[0].encode('utf-8')):
            conn.close()
            return False, "Mevcut şifre hatalı!"
            
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(new_pw.encode('utf-8'), salt).decode('utf-8')
        cursor.execute("UPDATE admins SET password_hash = ? WHERE id = ?", (hashed, admin_id))
        conn.commit()
        conn.close()
        return True, "Şifre başarıyla güncellendi."

    @staticmethod
    def register(name, email, phone, password):
        if len(password) < 7:
            return False, "Şifre en az 7 karakter olmalıdır."
            
        conn = get_connection()
        cursor = conn.cursor()
        try:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            # is_approved = 0
            cursor.execute("INSERT INTO members (name, email, phone, password_hash, is_approved) VALUES (?, ?, ?, ?, 0)", (name, email, phone, hashed))
            conn.commit()
            return True, "Kayıt başarılı! Yöneticinin onaylaması bekleniyor."
        except sqlite3.IntegrityError:
            return False, "Bu e-posta adresi sistemde zaten kayıtlı."
        except Exception as e:
            return False, "Bir hata oluştu."
        finally:
            conn.close()

    @staticmethod
    def login(email, password):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, password_hash, is_approved, must_change_password FROM members WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            is_approved = row[3]
            must_change = row[4]
            if not is_approved:
                return None, "Hesabınız henüz yönetici tarafından onaylanmamış."
                
            hashed = row[2].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), hashed):
                return {"id": row[0], "name": row[1], "email": email, "must_change_password": must_change}, "Başarılı"
        return None, "Hatalı e-posta veya şifre."

    @staticmethod
    def change_password(member_id, old_password, new_password):
        if len(new_password) < 7:
            return False, "Yeni şifre en az 7 karakter olmalıdır."
            
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM members WHERE id = ?", (member_id,))
        row = cursor.fetchone()
        
        if row:
            hashed = row[0].encode('utf-8')
            if bcrypt.checkpw(old_password.encode('utf-8'), hashed):
                new_salt = bcrypt.gensalt()
                new_hashed = bcrypt.hashpw(new_password.encode('utf-8'), new_salt).decode('utf-8')
                cursor.execute("UPDATE members SET password_hash = ?, must_change_password = 0 WHERE id = ?", (new_hashed, member_id))
                conn.commit()
                conn.close()
                return True, "Şifreniz başarıyla değiştirildi."
        conn.close()
        return False, "Mevcut şifreniz hatalı."

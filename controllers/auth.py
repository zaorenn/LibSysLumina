import bcrypt
from models.database import get_connection

class AuthController:
    @staticmethod
    def login_admin(username, password):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM admins WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            hashed = row[0].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), hashed):
                return True
        return False

    @staticmethod
    def login_member(email, password):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, password_hash FROM members WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            hashed = row[2].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), hashed):
                return {"id": row[0], "name": row[1], "email": email}
        return None

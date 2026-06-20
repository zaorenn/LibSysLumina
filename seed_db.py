import os
import sqlite3
import bcrypt
from models.database import init_db, get_connection

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
    conn.close()
    
    # init_db'yi çağırıp otomatik tohumlamanın çalışmasını sağlıyoruz
    init_db()
    print("Tüm kullanıcılar ve 100 adet kitap gerçek ISBN ve kapaklarıyla başarıyla veritabanına yüklendi!")

if __name__ == "__main__":
    seed()

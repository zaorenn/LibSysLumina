import sqlite3

def alter():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    try:
        c.execute('ALTER TABLE members ADD COLUMN must_change_password BOOLEAN DEFAULT 0')
    except sqlite3.OperationalError:
        pass # column might exist
        
    c.execute('''
    CREATE TABLE IF NOT EXISTS profile_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        member_name TEXT,
        new_name TEXT,
        new_email TEXT,
        status TEXT DEFAULT 'PENDING',
        request_date DATE DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()
    print("DB altered")

if __name__ == '__main__':
    alter()

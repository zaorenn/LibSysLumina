import sqlite3
try:
    c = sqlite3.connect('library.db')
    c.execute('ALTER TABLE members ADD COLUMN is_approved BOOLEAN DEFAULT 0;')
    # Mevcut adminleri (veya seed user) onaylamak isterseniz:
    c.execute('UPDATE members SET is_approved = 1')
    c.commit()
    print("Column added successfully")
except Exception as e:
    print(e)

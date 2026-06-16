from models.database import init_db
from views.ui import UserMainWindow

if __name__ == "__main__":
    init_db()  # Veritabanını ve varsayılan tabloları başlat
    app = UserMainWindow()
    app.mainloop()

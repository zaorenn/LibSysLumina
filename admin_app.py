from models.database import init_db
from views.admin_ui import AdminWindow

if __name__ == "__main__":
    init_db()  # Veritabanını ve varsayılan tabloları başlat
    app = AdminWindow()
    app.mainloop()

import traceback
from views.ui import UserMainWindow, CatalogCard
from models.database import get_connection

def test():
    try:
        app = UserMainWindow()
        # Mock book tuple: b_id, title, author, isbn, cat, year, desc, url, total, avail
        book = (1, "Test", "Test", "123", "Test", 2020, "Desc", "", 5, 5)
        # Create BookDetailModal directly to see error
        from views.ui import BookDetailModal
        def dummy_borrow(bid): pass
        modal = BookDetailModal(app, book, dummy_borrow)
        app.update()
        print("NO ERROR IN INIT")
    except Exception as e:
        print("ERROR CAUGHT:")
        traceback.print_exc()

if __name__ == "__main__":
    test()

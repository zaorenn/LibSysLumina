import pytest
import os
import models.database
from controllers.auth import AuthController
from controllers.library import BookController, MemberController, BorrowController

def setup_module(module):
    """Testler için geçici bir veritabanı ayarla."""
    models.database.DB_PATH = "test_library.db"
    if os.path.exists("test_library.db"): os.remove("test_library.db")
    models.database.init_db()

def teardown_module(module):
    """Test bittikten sonra geçici veritabanını sil."""
    if os.path.exists("test_library.db"): os.remove("test_library.db")

def test_admin_login():
    assert AuthController.login_admin("admin", "admin123")[0] == True
    assert AuthController.login_admin("admin", "wrong")[0] == False

def test_member_registration_and_login():
    assert MemberController.add_member("Ali Yılmaz", "ali@mail.com", "555", "pass123")[0] == True
    
    # Yeni üyenin girişi için önce onaylanması gerekiyor
    pending = MemberController.get_pending_members()
    assert len(pending) == 1
    m_id = pending[0][0]
    MemberController.approve_member(m_id)
    
    user, msg = AuthController.login("ali@mail.com", "pass123")
    assert user is not None
    assert user["name"] == "Ali Yılmaz"

def test_add_book():
    initial_count = len(BookController.get_all_books("", limit=200))
    # Benzersiz bir kitap ekliyoruz (ISBN BookController tarafından otomatik ezilir ve benzersiz oluşturulur)
    assert BookController.add_book("Test Kitap Adı", "Test Yazar Adı", "", "Roman", 2024, "", "", 3)[0] == True
    assert len(BookController.get_all_books("", limit=200)) == initial_count + 1

def test_borrow_and_return():
    books = BookController.get_all_books("", limit=10)
    assert len(books) > 0
    b_id = books[0][0]
    initial_avail = books[0][9]
    
    members = MemberController.get_all_members()
    assert len(members) > 0
    m_id = members[0][0]
    
    # Ödünç Ver
    assert BorrowController.borrow_book(b_id, m_id)[0] == True
    
    # Stok kontrolü
    books_after = BookController.get_all_books("", limit=10)
    assert books_after[0][9] == initial_avail - 1
    
    # İade Al
    br_id = BorrowController.get_all_borrows()[0][0]
    assert BorrowController.return_book(br_id)[0] == True
    
    books_final = BookController.get_all_books("", limit=10)
    assert books_final[0][9] == initial_avail

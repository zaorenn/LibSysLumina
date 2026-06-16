import customtkinter as ctk
from tkinter import ttk, messagebox
from controllers.auth import AuthController
from controllers.library import BookController, MemberController, BorrowController

class AdminLoginView(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        super().__init__(master)
        self.on_login_success = on_login_success
        self.pack(fill="both", expand=True)
        
        # Center Box
        self.center_frame = ctk.CTkFrame(self, width=400, height=500, corner_radius=15)
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.title_label = ctk.CTkLabel(self.center_frame, text="Lumina Yönetim", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.pack(pady=(50, 30))
        
        self.username_entry = ctk.CTkEntry(self.center_frame, placeholder_text="Yönetici Kullanıcı Adı", width=250, height=40)
        self.username_entry.pack(pady=(0, 20))
        
        self.password_entry = ctk.CTkEntry(self.center_frame, placeholder_text="Şifre", show="*", width=250, height=40)
        self.password_entry.pack(pady=(0, 30))
        
        self.login_btn = ctk.CTkButton(self.center_frame, text="Giriş Yap", width=250, height=40, command=self.handle_login)
        self.login_btn.pack()
        
        self.error_label = ctk.CTkLabel(self.center_frame, text="", text_color="#EF4444")
        self.error_label.pack(pady=(20, 0))

    def handle_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if AuthController.login_admin(username, password):
            self.error_label.configure(text="")
            self.on_login_success()
        else:
            self.error_label.configure(text="Hatalı kullanıcı adı veya şifre!")
            self.after(3000, lambda: self.error_label.configure(text=""))


class AdminDashboardView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        
        self.title = ctk.CTkLabel(self, text="Yönetici Paneli (Dashboard)", font=ctk.CTkFont(size=24, weight="bold"))
        self.title.pack(anchor="w", padx=30, pady=(30, 20))
        
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=30)
        
        self.total_books_card = self.create_card(self.cards_frame, "Toplam Kitap", "0", "#3B82F6")
        self.total_books_card.pack(side="left", expand=True, padx=(0, 10))
        
        self.active_borrows_card = self.create_card(self.cards_frame, "Aktif Ödünç", "0", "#10B981")
        self.active_borrows_card.pack(side="left", expand=True, padx=10)
        
        self.overdue_card = self.create_card(self.cards_frame, "Gecikmiş İade", "0", "#EF4444")
        self.overdue_card.pack(side="left", expand=True, padx=(10, 0))
        
        self.refresh_data()

    def create_card(self, parent, title, value, color):
        card = ctk.CTkFrame(parent, corner_radius=10, height=120)
        card.pack_propagate(False)
        title_lbl = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14))
        title_lbl.pack(pady=(20, 5))
        val_lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=32, weight="bold"), text_color=color)
        val_lbl.pack()
        card.val_lbl = val_lbl
        return card
        
    def refresh_data(self):
        total, active, overdue = BorrowController.get_dashboard_stats()
        self.total_books_card.val_lbl.configure(text=str(total))
        self.active_borrows_card.val_lbl.configure(text=str(active))
        self.overdue_card.val_lbl.configure(text=str(overdue))


class AdminBaseTableView(ctk.CTkFrame):
    def __init__(self, master, title, search_placeholder):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=30, pady=(30, 20))
        
        self.title_lbl = ctk.CTkLabel(self.header_frame, text=title, font=ctk.CTkFont(size=24, weight="bold"))
        self.title_lbl.pack(side="left")
        
        self.search_entry = ctk.CTkEntry(self.header_frame, placeholder_text=search_placeholder, width=250)
        self.search_entry.pack(side="right")
        self.search_entry.bind("<KeyRelease>", self.on_search)
        
        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.pack(fill="x", padx=30, pady=(0, 20))

        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=30, font=("Inter", 10), background="#2b2b2b", fieldbackground="#2b2b2b", foreground="white", borderwidth=0)
        style.configure("Treeview.Heading", font=("Inter", 11, "bold"), background="#1f538d", foreground="white", borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f538d')])

    def on_search(self, event):
        self.refresh_table(self.search_entry.get())
        
    def refresh_table(self, search_term=""):
        pass


class AdminBooksView(AdminBaseTableView):
    def __init__(self, master):
        super().__init__(master, "Kitap Yönetimi", "Kitap ara...")
        
        self.row1 = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.row1.pack(fill="x", padx=10, pady=10)
        self.title_entry = ctk.CTkEntry(self.row1, placeholder_text="Başlık")
        self.title_entry.pack(side="left", padx=5, expand=True, fill="x")
        self.author_entry = ctk.CTkEntry(self.row1, placeholder_text="Yazar")
        self.author_entry.pack(side="left", padx=5, expand=True, fill="x")
        self.isbn_entry = ctk.CTkEntry(self.row1, placeholder_text="ISBN")
        self.isbn_entry.pack(side="left", padx=5, expand=True, fill="x")
        
        self.row2 = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.row2.pack(fill="x", padx=10, pady=(0, 10))
        self.category_entry = ctk.CTkEntry(self.row2, placeholder_text="Kategori")
        self.category_entry.pack(side="left", padx=5, expand=True, fill="x")
        self.year_entry = ctk.CTkEntry(self.row2, placeholder_text="Yıl")
        self.year_entry.pack(side="left", padx=5, expand=True, fill="x")
        self.url_entry = ctk.CTkEntry(self.row2, placeholder_text="Kapak URL")
        self.url_entry.pack(side="left", padx=5, expand=True, fill="x")
        self.copies_entry = ctk.CTkEntry(self.row2, placeholder_text="Adet", width=70)
        self.copies_entry.pack(side="left", padx=5)
        
        self.add_btn = ctk.CTkButton(self.row2, text="Kitap Ekle", command=self.add_book, width=100)
        self.add_btn.pack(side="left", padx=5)

        self.tree = ttk.Treeview(self.table_frame, columns=("id", "title", "author", "isbn", "cat", "year", "total", "avail"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Başlık")
        self.tree.heading("author", text="Yazar")
        self.tree.heading("isbn", text="ISBN")
        self.tree.heading("cat", text="Kategori")
        self.tree.heading("year", text="Yıl")
        self.tree.heading("total", text="Toplam")
        self.tree.heading("avail", text="Mevcut")
        self.tree.column("id", width=40)
        self.tree.column("year", width=50)
        self.tree.column("total", width=60)
        self.tree.column("avail", width=60)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.refresh_table()

    def refresh_table(self, search_term=""):
        for item in self.tree.get_children(): self.tree.delete(item)
        for b in BookController.get_all_books(search_term): 
            self.tree.insert("", "end", values=(b[0], b[1], b[2], b[3], b[4], b[5], b[8], b[9]))

    def add_book(self):
        try:
            success, msg = BookController.add_book(
                title=self.title_entry.get(),
                author=self.author_entry.get(),
                isbn=self.isbn_entry.get(),
                category=self.category_entry.get(),
                published_year=int(self.year_entry.get()) if self.year_entry.get() else 0,
                description="",
                cover_image_url=self.url_entry.get(),
                total_copies=int(self.copies_entry.get())
            )
            if success:
                for entry in [self.title_entry, self.author_entry, self.isbn_entry, self.category_entry, self.year_entry, self.url_entry, self.copies_entry]:
                    entry.delete(0, 'end')
                self.refresh_table()
            else:
                messagebox.showerror("Hata", msg)
        except ValueError:
            messagebox.showerror("Hata", "Lütfen yıl ve adet alanlarına sayı girin.")

    def on_double_click(self, event):
        item = self.tree.selection()
        if item:
            if messagebox.askyesno("Sil", "Bu kitabı silmek istediğinize emin misiniz?"):
                BookController.delete_book(self.tree.item(item, "values")[0])
                self.refresh_table()


class AdminMembersView(AdminBaseTableView):
    def __init__(self, master):
        super().__init__(master, "Üye Yönetimi", "Üye ara...")
        self.name_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Ad Soyad")
        self.name_entry.pack(side="left", padx=10, pady=20, expand=True, fill="x")
        self.email_entry = ctk.CTkEntry(self.form_frame, placeholder_text="E-posta")
        self.email_entry.pack(side="left", padx=10, pady=20, expand=True, fill="x")
        self.phone_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Telefon")
        self.phone_entry.pack(side="left", padx=10, pady=20, expand=True, fill="x")
        self.pass_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Şifre (Geçici)", show="*")
        self.pass_entry.pack(side="left", padx=10, pady=20, expand=True, fill="x")
        
        self.add_btn = ctk.CTkButton(self.form_frame, text="Üye Ekle", command=self.add_member, width=100)
        self.add_btn.pack(side="left", padx=10, pady=20)

        self.tree = ttk.Treeview(self.table_frame, columns=("id", "name", "email", "phone", "date"), show="headings")
        for col, text in zip(self.tree["columns"], ["ID", "Ad Soyad", "E-posta", "Telefon", "Kayıt Tarihi"]):
            self.tree.heading(col, text=text)
        self.tree.column("id", width=50)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.refresh_table()

    def refresh_table(self, search_term=""):
        for item in self.tree.get_children(): self.tree.delete(item)
        for m in MemberController.get_all_members(search_term): self.tree.insert("", "end", values=m)

    def add_member(self):
        success, msg = MemberController.add_member(
            self.name_entry.get(), 
            self.email_entry.get(), 
            self.phone_entry.get(),
            self.pass_entry.get()
        )
        if success:
            for entry in [self.name_entry, self.email_entry, self.phone_entry, self.pass_entry]:
                entry.delete(0, 'end')
            self.refresh_table()
        else:
            messagebox.showerror("Hata", msg)

    def on_double_click(self, event):
        item = self.tree.selection()
        if item:
            if messagebox.askyesno("Sil", "Bu üyeyi silmek istediğinize emin misiniz?"):
                MemberController.delete_member(self.tree.item(item, "values")[0])
                self.refresh_table()


class AdminBorrowsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=30, pady=(30, 20))
        self.title = ctk.CTkLabel(self.header_frame, text="Ödünç & İade İşlemleri", font=ctk.CTkFont(size=24, weight="bold"))
        self.title.pack(side="left")
        
        self.form_frame = ctk.CTkFrame(self, height=80)
        self.form_frame.pack(fill="x", padx=30, pady=(0, 20))
        self.book_id_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Kitap ID")
        self.book_id_entry.pack(side="left", padx=10, pady=20, expand=True, fill="x")
        self.member_id_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Üye ID")
        self.member_id_entry.pack(side="left", padx=10, pady=20, expand=True, fill="x")
        self.borrow_btn = ctk.CTkButton(self.form_frame, text="Ödünç Ver", command=self.borrow_book, width=120)
        self.borrow_btn.pack(side="left", padx=10, pady=20)

        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=30, font=("Inter", 10), background="#2b2b2b", fieldbackground="#2b2b2b", foreground="white", borderwidth=0)
        style.configure("Treeview.Heading", font=("Inter", 11, "bold"), background="#1f538d", foreground="white", borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f538d')])
        
        self.tree = ttk.Treeview(self.table_frame, columns=("id", "book", "member", "b_date", "r_date", "act_date", "fee"), show="headings")
        for col, text in zip(self.tree["columns"], ["ID", "Kitap", "Üye", "Veriliş", "Son Tarih", "İade Edildi", "Ceza (TL)"]):
            self.tree.heading(col, text=text)
        self.tree.column("id", width=50)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.on_double_click)
        
        self.info_lbl = ctk.CTkLabel(self, text="* İade almak için tablodaki kaydın üzerine çift tıklayın.", text_color="gray", font=ctk.CTkFont(size=12))
        self.info_lbl.pack(pady=(0, 10))
        self.refresh_table()

    def refresh_table(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for b in BorrowController.get_all_borrows(): self.tree.insert("", "end", values=b)

    def borrow_book(self):
        try:
            success, msg = BorrowController.borrow_book(int(self.book_id_entry.get()), int(self.member_id_entry.get()))
            if success:
                self.book_id_entry.delete(0, 'end'); self.member_id_entry.delete(0, 'end')
                self.refresh_table()
            else:
                messagebox.showerror("Hata", msg)
        except ValueError: 
            pass

    def on_double_click(self, event):
        item = self.tree.selection()
        if item:
            actual_return = self.tree.item(item, "values")[5]
            if not actual_return or actual_return == 'None':
                BorrowController.return_book(self.tree.item(item, "values")[0])
                self.refresh_table()


class AdminWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Lumina - Yönetici Paneli")
        self.geometry("1100x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.current_frame = None
        self.show_login()

    def show_login(self):
        if self.current_frame: self.current_frame.destroy()
        self.current_frame = AdminLoginView(self, self.show_main_app)

    def show_main_app(self):
        if self.current_frame: self.current_frame.destroy()
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True)
        
        self.sidebar_frame = ctk.CTkFrame(self.main_container, width=220, corner_radius=0)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Lumina Admin", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.pack(pady=(30, 40))
        
        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Ana Panel", fg_color="transparent", anchor="w", command=lambda: self.switch_view(AdminDashboardView))
        self.btn_dashboard.pack(fill="x", padx=10, pady=5)
        self.btn_books = ctk.CTkButton(self.sidebar_frame, text="Kitap Yönetimi", fg_color="transparent", anchor="w", command=lambda: self.switch_view(AdminBooksView))
        self.btn_books.pack(fill="x", padx=10, pady=5)
        self.btn_members = ctk.CTkButton(self.sidebar_frame, text="Üye Yönetimi", fg_color="transparent", anchor="w", command=lambda: self.switch_view(AdminMembersView))
        self.btn_members.pack(fill="x", padx=10, pady=5)
        self.btn_borrows = ctk.CTkButton(self.sidebar_frame, text="Ödünç İşlemleri", fg_color="transparent", anchor="w", command=lambda: self.switch_view(AdminBorrowsView))
        self.btn_borrows.pack(fill="x", padx=10, pady=5)
        
        self.content_frame = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.content_frame.pack(side="left", fill="both", expand=True)
        
        self.current_view = None
        self.switch_view(AdminDashboardView)

    def switch_view(self, view_class):
        if self.current_view: self.current_view.destroy()
        self.current_view = view_class(self.content_frame)
        self.current_view.pack(fill="both", expand=True)

import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import requests
import io
import threading
from controllers.auth import AuthController
from controllers.library import BookController, MemberController, BorrowController

class ThemeSelectionView(ctk.CTkFrame):
    def __init__(self, master, on_complete):
        super().__init__(master)
        self.on_complete = on_complete
        self.pack(fill="both", expand=True)
        
        self.bg_frame = ctk.CTkFrame(self)
        self.bg_frame.pack(fill="both", expand=True)
        
        self.center_frame = ctk.CTkFrame(self.bg_frame, width=500, height=450, corner_radius=20)
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.title_label = ctk.CTkLabel(self.center_frame, text="Hoş Geldiniz", font=ctk.CTkFont(size=32, weight="bold"))
        self.title_label.pack(pady=(40, 20))
        
        self.sub_label = ctk.CTkLabel(self.center_frame, text="Lütfen uygulama temanızı seçin", font=ctk.CTkFont(size=16), text_color="gray")
        self.sub_label.pack(pady=(0, 30))
        
        # Tema Seçimi (Dark/Light)
        self.mode_var = ctk.StringVar(value="Dark")
        self.mode_segmented = ctk.CTkSegmentedButton(self.center_frame, values=["Dark", "Light"], variable=self.mode_var, command=self.change_mode, width=300, height=40)
        self.mode_segmented.pack(pady=(0, 20))
        
        # Vurgu Rengi Seçimi
        self.color_var = ctk.StringVar(value="blue")
        self.color_segmented = ctk.CTkSegmentedButton(self.center_frame, values=["blue", "dark-blue", "green"], variable=self.color_var, command=self.change_color, width=300, height=40)
        self.color_segmented.pack(pady=(0, 40))
        
        self.continue_btn = ctk.CTkButton(self.center_frame, text="Uygulamaya Devam Et", width=300, height=50, corner_radius=10, 
                                       font=ctk.CTkFont(size=16, weight="bold"), command=self.on_complete)
        self.continue_btn.pack()

    def change_mode(self, value):
        ctk.set_appearance_mode(value)
        
    def change_color(self, value):
        ctk.set_default_color_theme(value)
        # Uyarı: Renk teması değişimi genellikle anlık olmaz, pencerenin yeniden çizilmesini veya uygulamanın yeniden başlatılmasını gerektirebilir, 
        # ancak CustomTkinter bazı renkleri anında günceller.


class MemberLoginView(ctk.CTkFrame):
    def __init__(self, master, on_login_success, on_register_click, on_back):
        super().__init__(master)
        self.on_login_success = on_login_success
        self.on_register_click = on_register_click
        self.on_back = on_back
        self.pack(fill="both", expand=True)
        
        self.bg_frame = ctk.CTkFrame(self)
        self.bg_frame.pack(fill="both", expand=True)
        
        self.back_btn = ctk.CTkButton(self.bg_frame, text="← Geri Dön", fg_color="transparent", width=100, command=self.on_back)
        self.back_btn.place(x=20, y=20)
        
        self.center_frame = ctk.CTkFrame(self.bg_frame, width=450, height=550, corner_radius=20)
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.title_label = ctk.CTkLabel(self.center_frame, text="Üye Girişi", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.pack(pady=(50, 40))
        
        self.email_entry = ctk.CTkEntry(self.center_frame, placeholder_text="E-posta", width=300, height=45, corner_radius=10)
        self.email_entry.pack(pady=(0, 20))
        
        self.password_entry = ctk.CTkEntry(self.center_frame, placeholder_text="Şifre", show="*", width=300, height=45, corner_radius=10)
        self.password_entry.pack(pady=(0, 30))
        
        self.login_btn = ctk.CTkButton(self.center_frame, text="Giriş Yap", width=300, height=45, corner_radius=10, 
                                       font=ctk.CTkFont(size=15, weight="bold"), command=self.handle_login)
        self.login_btn.pack(pady=(0, 20))
        
        self.register_btn = ctk.CTkButton(self.center_frame, text="Hesabın yok mu? Kayıt Ol", width=300, height=45, corner_radius=10, 
                                          fg_color="transparent", border_width=2, command=self.on_register_click)
        self.register_btn.pack()
        
        self.error_label = ctk.CTkLabel(self.center_frame, text="", text_color="#EF4444")
        self.error_label.pack(pady=(20, 0))

    def handle_login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        user_data = AuthController.login_member(email, password)
        if user_data:
            self.error_label.configure(text="")
            self.on_login_success(user_data)
        else:
            self.error_label.configure(text="Hatalı e-posta veya şifre!")


class MemberRegisterView(ctk.CTkFrame):
    def __init__(self, master, on_register_success, on_login_click):
        super().__init__(master)
        self.on_register_success = on_register_success
        self.on_login_click = on_login_click
        self.pack(fill="both", expand=True)
        
        self.bg_frame = ctk.CTkFrame(self)
        self.bg_frame.pack(fill="both", expand=True)
        
        self.center_frame = ctk.CTkFrame(self.bg_frame, width=450, height=650, corner_radius=20)
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.title_label = ctk.CTkLabel(self.center_frame, text="Yeni Hesap Oluştur", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.pack(pady=(40, 30))
        
        self.name_entry = ctk.CTkEntry(self.center_frame, placeholder_text="Ad Soyad", width=300, height=45, corner_radius=10)
        self.name_entry.pack(pady=(0, 20))
        
        self.email_entry = ctk.CTkEntry(self.center_frame, placeholder_text="E-posta", width=300, height=45, corner_radius=10)
        self.email_entry.pack(pady=(0, 20))
        
        self.phone_entry = ctk.CTkEntry(self.center_frame, placeholder_text="Telefon", width=300, height=45, corner_radius=10)
        self.phone_entry.pack(pady=(0, 20))

        self.password_entry = ctk.CTkEntry(self.center_frame, placeholder_text="Şifre", show="*", width=300, height=45, corner_radius=10)
        self.password_entry.pack(pady=(0, 30))
        
        self.register_btn = ctk.CTkButton(self.center_frame, text="Kayıt Ol", width=300, height=45, corner_radius=10, 
                                       font=ctk.CTkFont(size=15, weight="bold"), command=self.handle_register)
        self.register_btn.pack(pady=(0, 20))
        
        self.login_btn = ctk.CTkButton(self.center_frame, text="Zaten hesabın var mı? Giriş Yap", width=300, height=45, corner_radius=10, 
                                          fg_color="transparent", border_width=2, command=self.on_login_click)
        self.login_btn.pack()

    def handle_register(self):
        success, msg = MemberController.add_member(
            self.name_entry.get(),
            self.email_entry.get(),
            self.phone_entry.get(),
            self.password_entry.get()
        )
        if success:
            messagebox.showinfo("Başarılı", "Kayıt işlemi başarılı! Lütfen giriş yapın.")
            self.on_login_click()
        else:
            messagebox.showerror("Hata", msg)


class CatalogView(ctk.CTkFrame):
    def __init__(self, master, get_current_user, require_login):
        super().__init__(master, fg_color="transparent")
        self.get_current_user = get_current_user
        self.require_login = require_login
        
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=80)
        self.header_frame.pack(fill="x", padx=40, pady=(40, 20))
        
        self.title_lbl = ctk.CTkLabel(self.header_frame, text="Kitap Kataloğu", font=ctk.CTkFont(size=32, weight="bold"))
        self.title_lbl.pack(side="left")
        
        self.search_entry = ctk.CTkEntry(self.header_frame, placeholder_text="Kitap ara...", width=300, height=40, corner_radius=20)
        self.search_entry.pack(side="right")
        self.search_entry.bind("<KeyRelease>", self.on_search)
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        # Grid variables
        self.columns = 4
        self.image_cache = {}
        
        self.load_books()

    def load_image_from_url(self, url, label):
        if not url or url == "None":
            return
            
        def fetch():
            if url in self.image_cache:
                img = self.image_cache[url]
            else:
                try:
                    response = requests.get(url, timeout=5)
                    image_data = Image.open(io.BytesIO(response.content))
                    img = ctk.CTkImage(light_image=image_data, dark_image=image_data, size=(130, 200))
                    self.image_cache[url] = img
                except:
                    return
            label.after(0, lambda: label.configure(image=img, text=""))
            
        threading.Thread(target=fetch, daemon=True).start()

    def on_search(self, event):
        self.load_books(self.search_entry.get())

    def load_books(self, search_term=""):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        books = BookController.get_all_books(search_term)
        
        row, col = 0, 0
        for b in books:
            book_id, title, author, isbn, category, year, desc, url, total, avail = b
            
            card = ctk.CTkFrame(self.scrollable_frame, width=220, height=380, corner_radius=15)
            card.pack_propagate(False)
            card.grid(row=row, column=col, padx=20, pady=20)
            
            img_lbl = ctk.CTkLabel(card, text="Yükleniyor...", width=130, height=200, corner_radius=10, fg_color="gray")
            img_lbl.pack(pady=(15, 10))
            self.load_image_from_url(url, img_lbl)
            
            title_lbl = ctk.CTkLabel(card, text=title[:22] + ("..." if len(title)>22 else ""), font=ctk.CTkFont(size=14, weight="bold"))
            title_lbl.pack()
            
            author_lbl = ctk.CTkLabel(card, text=author[:25], font=ctk.CTkFont(size=12), text_color="gray")
            author_lbl.pack()
            
            avail_color = "#10B981" if avail > 0 else "#EF4444"
            avail_text = f"Stok: {avail}/{total}"
            avail_lbl = ctk.CTkLabel(card, text=avail_text, font=ctk.CTkFont(size=12, weight="bold"), text_color=avail_color)
            avail_lbl.pack(pady=(5, 10))
            
            borrow_btn = ctk.CTkButton(card, text="Ödünç Al" if avail > 0 else "Stokta Yok", 
                                       state="normal" if avail > 0 else "disabled",
                                       command=lambda bid=book_id: self.borrow_book(bid))
            borrow_btn.pack(side="bottom", pady=(0, 15))
            
            col += 1
            if col >= self.columns:
                col = 0
                row += 1

    def borrow_book(self, book_id):
        user = self.get_current_user()
        if not user:
            # Login gerekli
            self.require_login()
            return

        success, msg = BorrowController.borrow_book(book_id, user["id"])
        if success:
            messagebox.showinfo("Başarılı", "Kitap başarıyla ödünç alındı. Profilinizden takip edebilirsiniz.")
            self.load_books(self.search_entry.get())
        else:
            messagebox.showerror("Hata", msg)


class ProfileView(ctk.CTkFrame):
    def __init__(self, master, current_user):
        super().__init__(master, fg_color="transparent")
        self.current_user = current_user
        
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=80)
        self.header_frame.pack(fill="x", padx=40, pady=(40, 20))
        
        self.title_lbl = ctk.CTkLabel(self.header_frame, text=f"Merhaba, {self.current_user['name']}", font=ctk.CTkFont(size=32, weight="bold"))
        self.title_lbl.pack(side="left")
        
        self.sub_lbl = ctk.CTkLabel(self, text="Ödünç Aldığınız Kitaplar", font=ctk.CTkFont(size=20, weight="bold"), text_color="gray")
        self.sub_lbl.pack(anchor="w", padx=40, pady=(0, 20))
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        self.load_borrows()

    def load_borrows(self):
        borrows = BorrowController.get_member_borrows(self.current_user["id"])
        
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        for br in borrows:
            br_id, title, author, url, b_date, r_date, act_date, fee = br
            
            card = ctk.CTkFrame(self.scrollable_frame, height=120, corner_radius=10)
            card.pack(fill="x", pady=10, padx=10)
            
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", padx=20, pady=20, fill="both", expand=True)
            
            ctk.CTkLabel(info_frame, text=title, font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=author, font=ctk.CTkFont(size=14), text_color="gray").pack(anchor="w")
            
            status_frame = ctk.CTkFrame(card, fg_color="transparent")
            status_frame.pack(side="right", padx=20, pady=20)
            
            if act_date and act_date != "None":
                status = f"İade Edildi ({act_date})"
                color = "#10B981"
            else:
                status = f"İade Bekleniyor (Son: {r_date})"
                color = "#F59E0B"
                
            ctk.CTkLabel(status_frame, text=status, font=ctk.CTkFont(size=14, weight="bold"), text_color=color).pack(anchor="e")
            
            if fee and fee > 0:
                ctk.CTkLabel(status_frame, text=f"Ceza: {fee} TL", font=ctk.CTkFont(size=14, weight="bold"), text_color="#EF4444").pack(anchor="e")


class UserMainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Lumina Kütüphane Sistemi")
        self.geometry("1280x800")
        
        # Varsayılan değerler
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.current_user = None
        self.current_frame = None
        
        # Tema seçimiyle başlat
        self.show_theme_selection()

    def show_theme_selection(self):
        if self.current_frame: self.current_frame.destroy()
        self.current_frame = ThemeSelectionView(self, self.show_main_app)

    def show_login(self):
        if hasattr(self, 'main_container') and self.main_container.winfo_exists():
            self.main_container.destroy()
        if self.current_frame: self.current_frame.destroy()
        self.current_frame = MemberLoginView(self, self.on_login_success, self.show_register, self.show_main_app)

    def show_register(self):
        if self.current_frame: self.current_frame.destroy()
        self.current_frame = MemberRegisterView(self, self.show_login, self.show_login)

    def on_login_success(self, user_data):
        self.current_user = user_data
        self.show_main_app()

    def show_main_app(self):
        if self.current_frame: self.current_frame.destroy()
        
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True)
        
        self.sidebar_frame = ctk.CTkFrame(self.main_container, width=250, corner_radius=0)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="LUMINA", font=ctk.CTkFont(size=32, weight="bold", slant="italic"))
        self.logo_label.pack(pady=(40, 50))
        
        # Menü Butonları
        self.btn_catalog = ctk.CTkButton(self.sidebar_frame, text="📚 Kitap Kataloğu", height=50, corner_radius=10, 
                                         fg_color="transparent", anchor="w", font=ctk.CTkFont(size=15),
                                         command=lambda: self.switch_view(CatalogView, self.get_current_user, self.show_login))
        self.btn_catalog.pack(fill="x", padx=20, pady=10)
        
        if self.current_user:
            self.btn_profile = ctk.CTkButton(self.sidebar_frame, text="👤 Profilim", height=50, corner_radius=10, 
                                             fg_color="transparent", anchor="w", font=ctk.CTkFont(size=15),
                                             command=lambda: self.switch_view(ProfileView, self.current_user))
            self.btn_profile.pack(fill="x", padx=20, pady=10)
            
            self.btn_auth = ctk.CTkButton(self.sidebar_frame, text="🚪 Çıkış Yap", height=50, corner_radius=10, 
                                            fg_color="transparent", text_color="#EF4444", anchor="w", font=ctk.CTkFont(size=15),
                                            command=self.logout)
            self.btn_auth.pack(fill="x", padx=20, pady=10)
        else:
            self.btn_auth = ctk.CTkButton(self.sidebar_frame, text="🔐 Giriş Yap / Kayıt Ol", height=50, corner_radius=10, 
                                            fg_color="transparent", anchor="w", font=ctk.CTkFont(size=15),
                                            command=self.show_login)
            self.btn_auth.pack(fill="x", padx=20, pady=10)
            
            self.guest_lbl = ctk.CTkLabel(self.sidebar_frame, text="(Misafir Girişi)", text_color="gray", font=ctk.CTkFont(size=12))
            self.guest_lbl.pack(pady=0)
            
        # Arayüz içi Tema Değiştirici
        self.theme_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.theme_frame.pack(side="bottom", fill="x", padx=20, pady=40)
        
        self.theme_lbl = ctk.CTkLabel(self.theme_frame, text="Tema Ayarı", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
        self.theme_lbl.pack(anchor="w", pady=(0, 5))
        
        self.mode_switch = ctk.CTkSegmentedButton(self.theme_frame, values=["Dark", "Light"], command=self.change_mode)
        self.mode_switch.set(ctk.get_appearance_mode())
        self.mode_switch.pack(fill="x")

    def change_mode(self, value):
        ctk.set_appearance_mode(value)

    def get_current_user(self):
        return self.current_user

    def switch_view(self, view_class, *args):
        if hasattr(self, 'content_frame') and self.content_frame.winfo_exists():
            pass
        else:
            self.content_frame = ctk.CTkFrame(self.main_container, corner_radius=0)
            self.content_frame.pack(side="left", fill="both", expand=True)

        if hasattr(self, 'current_view') and self.current_view:
            self.current_view.destroy()
            
        self.current_view = view_class(self.content_frame, *args)
        self.current_view.pack(fill="both", expand=True)

    def logout(self):
        self.current_user = None
        self.show_main_app()

import customtkinter as ctk
from tkinter import ttk, messagebox
from controllers.auth import AuthController
from controllers.library import BookController, BorrowController, RequestController, NotificationController
from PIL import Image
import urllib.request
import io
import threading
import requests

IMAGE_CACHE = {}
IMAGE_LOCK = threading.Lock()

# macOS Colors (Light, Dark)
APPLE_BG = ("#F2F2F7", "#1E1E1E")
APPLE_PANEL = ("#FFFFFF", "#2C2C2E")
APPLE_BLUE = ("#007AFF", "#0A84FF")
APPLE_GREEN = ("#34C759", "#30D158")
APPLE_RED = ("#FF3B30", "#FF453A")
APPLE_ORANGE = ("#FF9500", "#FF9F0A")
APPLE_TEXT = ("#000000", "#FFFFFF")
APPLE_TEXT_MUTED = ("#8E8E93", "#8E8E93")

def get_icon(name, size=20):
    try:
        l_img = Image.open(f"assets/icons/{name}_b.png")
        d_img = Image.open(f"assets/icons/{name}_w.png")
        return ctk.CTkImage(light_image=l_img, dark_image=d_img, size=(size, size))
    except:
        return None

def get_single_icon(name, size=20):
    try:
        return ctk.CTkImage(light_image=Image.open(f"assets/icons/{name}"), size=(size, size))
    except:
        return None

def apply_treeview_style():
    style = ttk.Style()
    style.theme_use("default")
    mode = ctk.get_appearance_mode()
    bg = "#FFFFFF" if mode == "Light" else "#2C2C2E"
    fg = "#000000" if mode == "Light" else "#FFFFFF"
    h_bg = "#E5E5EA" if mode == "Light" else "#3A3A3C"
    sel_bg = "#007AFF" if mode == "Light" else "#0A84FF"
    
    style.configure("Treeview", rowheight=35, font=("San Francisco", 11), background=bg, fieldbackground=bg, foreground=fg, borderwidth=0)
    style.configure("Treeview.Heading", font=("San Francisco", 12, "bold"), background=h_bg, foreground=fg, borderwidth=0)
    style.map('Treeview', background=[('selected', sel_bg)])

class AnimatedButton(ctk.CTkButton):
    def __init__(self, master, fg_color=APPLE_BLUE, hover_color="#005ecb", **kwargs):
        h = kwargs.pop("height", 32)
        f = kwargs.pop("font", ctk.CTkFont(family="San Francisco", size=13))
        super().__init__(master, fg_color=fg_color, hover_color=hover_color, corner_radius=6, height=h, font=f, **kwargs)

class GlassFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        cr = kwargs.pop("corner_radius", 12)
        super().__init__(master, fg_color=APPLE_PANEL, corner_radius=cr, border_width=1, border_color="#3A3A3C", **kwargs)

class CatalogCard(GlassFrame):
    def __init__(self, master, book, on_borrow):
        super().__init__(master)
        self.book = book
        self.pack_propagate(False)
        self.configure(width=260, height=360)
        
        b_id, title, author, isbn, cat, year, desc, url, total, avail = book
        
        self.cover_frame = ctk.CTkFrame(self, fg_color="transparent", height=180)
        self.cover_frame.pack(fill="x", padx=10, pady=(10, 5))
        self.cover_frame.pack_propagate(False)
        
        self.cover_lbl = ctk.CTkLabel(self.cover_frame, text="📖", font=ctk.CTkFont(size=50), text_color=APPLE_TEXT_MUTED)
        self.cover_lbl.pack(expand=True)
        
        if url and url.startswith("http"):
            self.load_image(url)
        
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        title_lbl = ctk.CTkLabel(self.info_frame, text=title[:25] + ("..." if len(title)>25 else ""), 
                                 font=ctk.CTkFont(family="San Francisco", size=15, weight="bold"), text_color=APPLE_TEXT)
        title_lbl.pack(anchor="w")
        
        author_lbl = ctk.CTkLabel(self.info_frame, text=f"👤 {author}", 
                                  font=ctk.CTkFont(size=12), text_color=APPLE_TEXT_MUTED)
        author_lbl.pack(anchor="w", pady=(2, 10))
        
        bot_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        bot_frame.pack(fill="x", side="bottom", pady=10)
        
        if avail > 0:
            status_text = f"✨ Stok: {avail}"
            color = APPLE_GREEN
            btn_state = "normal"
            btn_text = "Ödünç Al"
        else:
            status_text = "🚫 Tükendi"
            color = APPLE_RED
            btn_state = "disabled"
            btn_text = "Bekleniyor"
            
        ctk.CTkLabel(bot_frame, text=status_text, font=ctk.CTkFont(size=12, weight="bold"), text_color=color).pack(side="left")
        
        self.borrow_btn = AnimatedButton(bot_frame, text=btn_text, width=80, state=btn_state, command=lambda: on_borrow(b_id))
        self.borrow_btn.pack(side="right")
        
        self.detail_btn = AnimatedButton(bot_frame, text="Detaylar", width=70, fg_color=APPLE_PANEL, hover_color="#3A3A3C", text_color=APPLE_TEXT, border_width=1, border_color="#3A3A3C", command=lambda: BookDetailModal(self.winfo_toplevel(), book, on_borrow))
        self.detail_btn.pack(side="right", padx=(0, 5))

    def load_image(self, url):
        with IMAGE_LOCK:
            if url in IMAGE_CACHE:
                try:
                    ctk_img = ctk.CTkImage(IMAGE_CACHE[url], size=(120, 160))
                    self.cover_lbl.configure(image=ctk_img, text="")
                    return
                except:
                    pass

        def _fetch():
            try:
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=10, verify=False)
                if r.status_code == 200 and len(r.content) > 100:
                    img = Image.open(io.BytesIO(r.content))
                    with IMAGE_LOCK:
                        IMAGE_CACHE[url] = img
                    ctk_img = ctk.CTkImage(img, size=(120, 160))
                    self.cover_lbl.after(0, lambda: self.cover_lbl.configure(image=ctk_img, text=""))
            except Exception as e:
                pass
        threading.Thread(target=_fetch, daemon=True).start()

class BookDetailModal(ctk.CTkToplevel):
    def __init__(self, master, book, on_borrow):
        super().__init__(master)
        self.title("Kitap Detayları")
        self.geometry("600x700")
        self.configure(fg_color=APPLE_BG)
        self.grab_set()
        
        b_id, title, author, isbn, cat, year, desc, url, total, avail = book
        
        self.top = ctk.CTkFrame(self, fg_color="transparent")
        self.top.pack(fill="x", padx=20, pady=20)
        
        self.cover_lbl = ctk.CTkLabel(self.top, text="📖", font=ctk.CTkFont(size=100), text_color=APPLE_TEXT_MUTED)
        self.cover_lbl.pack(side="left", padx=(0, 20))
        if url and url.startswith("http"):
            self.load_image(url)
            
        self.info = ctk.CTkFrame(self.top, fg_color="transparent")
        self.info.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(self.info, text=title, font=ctk.CTkFont(family="San Francisco", size=24, weight="bold"), wraplength=350, justify="left").pack(anchor="w")
        ctk.CTkLabel(self.info, text=f"👤 Yazar: {author}", font=ctk.CTkFont(size=16), text_color=APPLE_TEXT_MUTED).pack(anchor="w", pady=(5,0))
        ctk.CTkLabel(self.info, text=f"🏷️ Kategori: {cat} | 📅 Yıl: {year}", font=ctk.CTkFont(size=14), text_color=APPLE_TEXT_MUTED).pack(anchor="w")
        ctk.CTkLabel(self.info, text=f"ISBN: {isbn}", font=ctk.CTkFont(size=14), text_color=APPLE_TEXT_MUTED).pack(anchor="w")
        
        if avail > 0:
            status = f"✨ Stok: {avail}"
            color = APPLE_GREEN
            btn_state = "normal"
        else:
            status = "🚫 Tükendi"
            color = APPLE_RED
            btn_state = "disabled"
        
        ctk.CTkLabel(self.info, text=status, font=ctk.CTkFont(size=16, weight="bold"), text_color=color).pack(anchor="w", pady=(15, 5))
        AnimatedButton(self.info, text="Ödünç Al", width=150, height=40, font=ctk.CTkFont(size=16, weight="bold"), state=btn_state, command=lambda: self.handle_borrow(on_borrow, b_id)).pack(anchor="w")
        
        self.desc_frame = GlassFrame(self, height=120)
        self.desc_frame.pack(fill="x", padx=20, pady=10)
        self.desc_frame.pack_propagate(False)
        ctk.CTkLabel(self.desc_frame, text="Kitap Özeti", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        ctk.CTkLabel(self.desc_frame, text=desc if desc else "Bu kitap için henüz bir özet bulunmuyor.", text_color=APPLE_TEXT_MUTED, wraplength=520, justify="left").pack(anchor="w", padx=15)
        
        self.borrowers_frame = GlassFrame(self)
        self.borrowers_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        ctk.CTkLabel(self.borrowers_frame, text="Şu An Ödünç Alanlar", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        borrowers = BorrowController.get_active_borrowers_by_book(b_id)
        if not borrowers:
            ctk.CTkLabel(self.borrowers_frame, text="Şu an bu kitabı ödünç alan kimse yok.", text_color=APPLE_TEXT_MUTED).pack(anchor="w", padx=15, pady=5)
        else:
            for b_name, b_date in borrowers:
                f = ctk.CTkFrame(self.borrowers_frame, fg_color="transparent")
                f.pack(fill="x", padx=15, pady=5)
                ctk.CTkLabel(f, text=f"👤 {b_name}", font=ctk.CTkFont(size=14)).pack(side="left")
                ctk.CTkLabel(f, text=f"⏳ Aldığı Tarih: {b_date}", font=ctk.CTkFont(size=12), text_color=APPLE_TEXT_MUTED).pack(side="right")

    def handle_borrow(self, on_borrow, b_id):
        self.destroy()
        on_borrow(b_id)

    def load_image(self, url):
        with IMAGE_LOCK:
            if url in IMAGE_CACHE:
                try:
                    ctk_img = ctk.CTkImage(IMAGE_CACHE[url], size=(160, 240))
                    self.cover_lbl.configure(image=ctk_img, text="")
                    return
                except:
                    pass

        def _fetch():
            try:
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=10, verify=False)
                if r.status_code == 200 and len(r.content) > 100:
                    img = Image.open(io.BytesIO(r.content))
                    with IMAGE_LOCK:
                        IMAGE_CACHE[url] = img
                    ctk_img = ctk.CTkImage(img, size=(160, 240))
                    self.cover_lbl.after(0, lambda: self.cover_lbl.configure(image=ctk_img, text=""))
            except Exception as e:
                pass
        threading.Thread(target=_fetch, daemon=True).start()

class AuthModal(ctk.CTkToplevel):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.title("Kütüphane Girişi")
        self.geometry("400x550")
        self.configure(fg_color=APPLE_BG)
        self.on_success = on_success
        self.grab_set() 
        self.current_frame = None
        self.show_login()

    def validate_phone(self, p):
        if p == "":
            return True
        return p.isdigit()

    def show_login(self):
        if self.current_frame: self.current_frame.destroy()
        self.current_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.current_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(self.current_frame, text=" Lumina", font=ctk.CTkFont(family="San Francisco", size=32, weight="bold")).pack(pady=(40, 10))
        ctk.CTkLabel(self.current_frame, text="Lütfen giriş yapın", text_color=APPLE_TEXT_MUTED).pack(pady=(0, 30))
        
        self.email_entry = ctk.CTkEntry(self.current_frame, placeholder_text="E-posta", width=260, height=36, corner_radius=6)
        self.email_entry.pack(pady=8)
        self.pass_entry = ctk.CTkEntry(self.current_frame, placeholder_text="Şifre", show="●", width=260, height=36, corner_radius=6)
        self.pass_entry.pack(pady=8)
        
        self.chk_login = ctk.CTkCheckBox(self.current_frame, text="Şifreyi Göster", command=lambda: self.toggle_pw(self.pass_entry, self.chk_login))
        self.chk_login.pack(pady=5)
        
        AnimatedButton(self.current_frame, text="Giriş Yap", width=260, command=self.do_login).pack(pady=20)
        self.err = ctk.CTkLabel(self.current_frame, text="", text_color=APPLE_RED)
        self.err.pack()
        ctk.CTkButton(self.current_frame, text="Hesabın yok mu? Kayıt Ol", fg_color="transparent", hover_color=APPLE_PANEL, text_color=APPLE_BLUE, command=self.show_register).pack(side="bottom", pady=20)

    def show_register(self):
        if self.current_frame: self.current_frame.destroy()
        self.current_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.current_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(self.current_frame, text="Yeni Hesap", font=ctk.CTkFont(family="San Francisco", size=28, weight="bold")).pack(pady=(30, 20))
        
        self.r_name = ctk.CTkEntry(self.current_frame, placeholder_text="Ad Soyad", width=260, height=36, corner_radius=6)
        self.r_name.pack(pady=5)
        self.r_email = ctk.CTkEntry(self.current_frame, placeholder_text="E-posta", width=260, height=36, corner_radius=6)
        self.r_email.pack(pady=5)
        
        vcmd = (self.register(self.validate_phone), "%P")
        self.r_phone = ctk.CTkEntry(self.current_frame, placeholder_text="Telefon", width=260, height=36, corner_radius=6, validate="key", validatecommand=vcmd)
        self.r_phone.pack(pady=5)
        self.r_pass = ctk.CTkEntry(self.current_frame, placeholder_text="Şifre", show="●", width=260, height=36, corner_radius=6)
        self.r_pass.pack(pady=5)
        
        self.chk_reg = ctk.CTkCheckBox(self.current_frame, text="Şifreyi Göster", command=lambda: self.toggle_pw(self.r_pass, self.chk_reg))
        self.chk_reg.pack(pady=5)
        
        AnimatedButton(self.current_frame, text="Kayıt Ol", width=260, command=self.do_register).pack(pady=20)
        self.err = ctk.CTkLabel(self.current_frame, text="", text_color=APPLE_RED)
        self.err.pack()
        ctk.CTkButton(self.current_frame, text="Geri Dön", fg_color="transparent", hover_color=APPLE_PANEL, text_color=APPLE_TEXT_MUTED, command=self.show_login).pack(side="bottom", pady=20)


    def toggle_pw(self, entry, chk):
        if chk.get() == 1: entry.configure(show="")
        else: entry.configure(show="●")

    def do_login(self):
        user, msg = AuthController.login(self.email_entry.get(), self.pass_entry.get())
        if user:
            self.on_success(user)
            self.destroy()
        else:
            self.err.configure(text=msg)
            
    def do_register(self):
        phone = self.r_phone.get().strip()
        if not phone.isdigit():
            self.err.configure(text="Hata: Telefon numarası sadece rakam içermelidir.")
            return
        succ, msg = AuthController.register(self.r_name.get(), self.r_email.get(), phone, self.r_pass.get())
        if succ:
            messagebox.showinfo("Başarılı", msg)
            self.show_login()
        else:
            self.err.configure(text=msg)


class CatalogView(ctk.CTkFrame):
    def __init__(self, master, main_app):
        super().__init__(master, fg_color="transparent")
        self.main_app = main_app
        self.offset = 0
        self.limit = 150
        self.query = ""
        self.books = []
        self.cards = []
        self.is_loading = False
        
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent", height=80)
        self.top_bar.pack(fill="x", padx=40, pady=(40, 10))
        
        self.title_lbl = ctk.CTkLabel(self.top_bar, text="Kütüphaneyi Keşfet", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_lbl.pack(side="left")
        
        self.search_entry = ctk.CTkEntry(self.top_bar, placeholder_text="Kitap veya Yazar Ara...", width=250, height=36, corner_radius=18, border_color="#3A3A3C")
        self.search_entry.pack(side="right")
        self.search_entry.bind("<KeyRelease>", self.on_search)
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=40)
        
        self.scroll.bind("<Configure>", self.on_resize)
        
        self.load_books()

    def on_search(self, e):
        self.query = self.search_entry.get()
        self.offset = 0
        for c in self.cards: c.destroy()
        self.cards.clear()
        self.books.clear()
        self.load_books()

    def load_books(self):
        if self.is_loading: return
        self.is_loading = True
        
        def _fetch():
            new_books = BookController.get_all_books(self.query, self.limit, self.offset)
            self.after(0, self._render_new_books, new_books)
        threading.Thread(target=_fetch, daemon=True).start()
        
    def _render_new_books(self, new_books):
        if not new_books: 
            self.is_loading = False
            return
        self.books.extend(new_books)
        self.offset += len(new_books)
        for b in new_books:
            card = CatalogCard(self.scroll, b, self.on_borrow)
            self.cards.append(card)
        self.rearrange_grid()
        self.is_loading = False
        
    def on_resize(self, event):
        self.rearrange_grid()
        
    def rearrange_grid(self):
        w = self.scroll.winfo_width()
        if w < 300: return
        cols = max(1, w // 280)
        for i, card in enumerate(self.cards):
            card.grid(row=i // cols, column=i % cols, padx=10, pady=15)

    def on_borrow(self, book_id):
        if not self.main_app.user:
            AuthModal(self.winfo_toplevel(), self.main_app.on_login_success)
            return
        if messagebox.askyesno("Onay", "Bu kitabı ödünç almak istiyor musunuz?"):
            success, msg = BorrowController.borrow_book(book_id, self.main_app.user["id"])
            if success:
                messagebox.showinfo("Başarılı", "Kitap profilinize eklendi.")
                self.load_books()
            else:
                messagebox.showerror("Hata", msg)


class ProfileView(ctk.CTkFrame):
    def __init__(self, master, main_app):
        super().__init__(master, fg_color="transparent")
        self.main_app = main_app
        ctk.CTkLabel(self, text="Hesap Bilgileri", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", padx=40, pady=(40, 20))
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=40)
        self.load_history()

    def load_history(self):
        for w in self.scroll.winfo_children(): w.destroy()
        if not self.main_app.user: return
        
        pw_frame = GlassFrame(self.scroll)
        pw_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(pw_frame, text="🔑 Şifre Değiştir", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))
        
        self.old_pw = ctk.CTkEntry(pw_frame, placeholder_text="Mevcut Şifre", show="●", width=300, height=36)
        self.old_pw.pack(anchor="w", padx=20, pady=5)
        self.new_pw1 = ctk.CTkEntry(pw_frame, placeholder_text="Yeni Şifre (En az 4 karakter)", show="●", width=300, height=36)
        self.new_pw1.pack(anchor="w", padx=20, pady=5)
        self.new_pw2 = ctk.CTkEntry(pw_frame, placeholder_text="Yeni Şifre (Tekrar)", show="●", width=300, height=36)
        self.new_pw2.pack(anchor="w", padx=20, pady=5)
        
        self.chk_pw = ctk.CTkCheckBox(pw_frame, text="Şifreleri Göster", command=self.toggle_pw)
        self.chk_pw.pack(anchor="w", padx=20, pady=5)
        
        AnimatedButton(pw_frame, text="Şifreyi Güncelle", width=300, command=self.change_pw).pack(anchor="w", padx=20, pady=15)
        
        req_frame = GlassFrame(self.scroll)
        req_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(req_frame, text="✏️ Bilgilerimi Güncelle", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))
        ctk.CTkLabel(req_frame, text="Güvenlik nedeniyle ad ve e-posta değişiklikleri yönetici onayına tabidir.", text_color=APPLE_TEXT_MUTED).pack(anchor="w", padx=20, pady=(0, 10))
        self.new_name = ctk.CTkEntry(req_frame, placeholder_text="Yeni Ad Soyad", width=300, height=36)
        self.new_name.pack(anchor="w", padx=20, pady=5)
        self.new_email = ctk.CTkEntry(req_frame, placeholder_text="Yeni E-posta", width=300, height=36)
        self.new_email.pack(anchor="w", padx=20, pady=5)
        AnimatedButton(req_frame, text="Değişiklik Talebi Gönder", width=300, command=self.req_profile).pack(anchor="w", padx=20, pady=15)
        
        ctk.CTkLabel(self.scroll, text="📚 Ödünç Geçmişi", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(10, 10))
        
        history = BorrowController.get_member_borrows(self.main_app.user["id"])
        if not history:
            ctk.CTkLabel(self.scroll, text="📭 Henüz hiç kitap ödünç almadınız.", font=ctk.CTkFont(size=16), text_color=APPLE_TEXT_MUTED).pack(pady=50)
            return
            
        for h in history:
            br_id, title, author, url, b_date, r_date, act_date, fee = h
            card = GlassFrame(self.scroll, height=120)
            card.pack(fill="x", pady=10)
            
            l_frame = ctk.CTkFrame(card, fg_color="transparent")
            l_frame.pack(side="left", padx=20, pady=20, fill="y")
            ctk.CTkLabel(l_frame, text=f"📖 {title}", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(l_frame, text=f"👤 {author}", font=ctk.CTkFont(size=13), text_color=APPLE_TEXT_MUTED).pack(anchor="w", pady=(5,0))
            
            r_frame = ctk.CTkFrame(card, fg_color="transparent")
            r_frame.pack(side="right", padx=20, pady=20)
            if act_date and act_date != "None":
                status = f"✅ İade Edildi ({act_date})"
                ctk.CTkLabel(r_frame, text=status, font=ctk.CTkFont(size=14, weight="bold"), text_color=APPLE_GREEN).pack(anchor="e")
            else:
                status = f"⏳ Bekleniyor (Son: {r_date})"
                ctk.CTkLabel(r_frame, text=status, font=ctk.CTkFont(size=14, weight="bold"), text_color=APPLE_ORANGE).pack(anchor="e")
                AnimatedButton(r_frame, text="İade Et", width=100, command=lambda bid=br_id: self.return_book(bid)).pack(anchor="e", pady=(5, 0))

    def return_book(self, bid):
        if messagebox.askyesno("İade", "Kitabı iade etmek istediğinize emin misiniz?"):
            success, msg = BorrowController.return_book(bid)
            if success: self.load_history()
            else: messagebox.showerror("Hata", msg)
            
    def toggle_pw(self):
        s = "" if self.chk_pw.get() == 1 else "●"
        self.old_pw.configure(show=s)
        self.new_pw1.configure(show=s)
        self.new_pw2.configure(show=s)
        
    def req_profile(self):
        nn = self.new_name.get()
        ne = self.new_email.get()
        if not nn or not ne:
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurun.")
            return
        from controllers.library import ProfileRequestController
        succ, msg = ProfileRequestController.add_request(self.main_app.user["id"], self.main_app.user["name"], nn, ne)
        if succ:
            messagebox.showinfo("Başarılı", msg)
            self.new_name.delete(0, "end")
            self.new_email.delete(0, "end")
        else:
            messagebox.showerror("Hata", msg)
            
    def change_pw(self):
        old = self.old_pw.get()
        n1 = self.new_pw1.get()
        n2 = self.new_pw2.get()
        if not old or not n1 or not n2:
            messagebox.showerror("Hata", "Tüm alanları doldurun.")
            return
        if n1 != n2:
            messagebox.showerror("Hata", "Yeni şifreler uyuşmuyor.")
            return
        succ, msg = AuthController.change_password(self.main_app.user["id"], old, n1)
        if succ:
            messagebox.showinfo("Başarılı", msg)
            self.old_pw.delete(0, "end")
            self.new_pw1.delete(0, "end")
            self.new_pw2.delete(0, "end")
        else:
            messagebox.showerror("Hata", msg)

class NotificationsView(ctk.CTkFrame):
    def __init__(self, master, main_app):
        super().__init__(master, fg_color="transparent")
        self.main_app = main_app
        ctk.CTkLabel(self, text="🔔 Bildirimler", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", padx=40, pady=(40, 20))
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=40)
        
        notifs = NotificationController.get_unread_notifications(self.main_app.user["id"])
        if not notifs:
            ctk.CTkLabel(self.scroll, text="Şu an okunmamış bir bildiriminiz yok.", text_color=APPLE_TEXT_MUTED).pack(pady=20)
        else:
            for n_id, msg, date in notifs:
                f = GlassFrame(self.scroll, height=80)
                f.pack(fill="x", pady=5)
                f.pack_propagate(False)
                ctk.CTkLabel(f, text=msg, font=ctk.CTkFont(size=14, weight="bold"), wraplength=700, justify="left").pack(anchor="w", padx=20, pady=(15, 0))
                ctk.CTkLabel(f, text=date, font=ctk.CTkFont(size=12), text_color=APPLE_TEXT_MUTED).pack(anchor="w", padx=20)
                NotificationController.mark_as_read(n_id)
        
        # Once viewed, update sidebar count to 0
        self.main_app.render_sidebar()

class UserRequestView(ctk.CTkFrame):
    def __init__(self, master, main_app):
        super().__init__(master, fg_color="transparent")
        self.main_app = main_app
        
        ctk.CTkLabel(self, text="🌟 Kitap İste", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", padx=40, pady=(40, 10))
        ctk.CTkLabel(self, text="Kütüphanede bulamadığınız kitapları internetten arayıp yöneticiden talep edebilirsiniz.", text_color=APPLE_TEXT_MUTED).pack(anchor="w", padx=40, pady=(0, 20))
        
        self.top = GlassFrame(self, height=80)
        self.top.pack(fill="x", padx=40, pady=(0, 20))
        self.top.pack_propagate(False)
        
        self.ent = ctk.CTkEntry(self.top, placeholder_text="🔍 Kitap Adı, Yazar (OpenLibrary)...", width=400, height=36, corner_radius=18)
        self.ent.pack(side="left", padx=20, pady=20)
        AnimatedButton(self.top, text="Ara", width=80, command=self.search).pack(side="left")
        self.status = ctk.CTkLabel(self.top, text="", text_color=APPLE_TEXT_MUTED)
        self.status.pack(side="left", padx=20)
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=40)
        
        # Default Recommendations
        self.show_recommendations()

    def show_recommendations(self):
        for w in self.scroll.winfo_children(): w.destroy()
        ctk.CTkLabel(self.scroll, text="💡 Popüler İstek Önerileri", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=10)
        recs = [
            ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", "9780590353427", "https://images-na.ssl-images-amazon.com/images/P/9780590353427.01._SCLZZZZZZZ_SX200_.jpg"),
            ("1984", "George Orwell", "9780451524935", "https://images-na.ssl-images-amazon.com/images/P/9780451524935.01._SCLZZZZZZZ_SX200_.jpg"),
            ("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", "https://images-na.ssl-images-amazon.com/images/P/9780743273565.01._SCLZZZZZZZ_SX200_.jpg")
        ]
        for title, author, isbn, cover in recs:
            self.build_result_card(title, author, isbn, cover)

    def search(self):
        q = self.ent.get()
        if not q: return
        self.status.configure(text="Aranıyor...")
        self.update()
        for w in self.scroll.winfo_children(): w.destroy()
        
        def _do_search():
            try:
                r = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={q}&maxResults=5", timeout=10)
                if r.status_code == 200:
                    items = r.json().get("items", [])
                    self.after(0, self._show_results, items)
                else:
                    self._do_gutenberg_search(q)
            except Exception as e:
                self._do_gutenberg_search(q)
                
        threading.Thread(target=_do_search, daemon=True).start()

    def _do_gutenberg_search(self, q):
        try:
            r = requests.get(f"https://gutendex.com/books/?search={q}", timeout=10)
            results = r.json().get("results", [])
            self.after(0, self._show_gutenberg_results, results)
        except Exception as e:
            self.after(0, lambda err=e: self.safe_update_status(f"❌ Hata: {str(err)[:25]}", APPLE_RED))

    def _show_gutenberg_results(self, results):
        self.safe_update_status(f"✅ {len(results)} sonuç (Gutenberg).")
        for book in results:
            t = book.get("title", "Bilinmiyor")
            authors = book.get("authors", [])
            a = ", ".join([auth.get("name", "Bilinmiyor") for auth in authors]) if authors else "Bilinmiyor"
            isbn = f"GUT{book.get('id', '000')}"
            cov = book.get("formats", {}).get("image/jpeg", "")
            self.build_result_card(t, a, isbn, cov)

    def safe_update_status(self, text, color=APPLE_TEXT_MUTED):
        try:
            if self.winfo_exists():
                self.status.configure(text=text, text_color=color)
        except:
            pass

    def _show_results(self, items):
        self.safe_update_status(f"✅ {len(items)} sonuç.")
        for item in items:
            volume_info = item.get("volumeInfo", {})
            t = volume_info.get("title", "Bilinmiyor")
            authors = volume_info.get("authors", ["Bilinmiyor"])
            a = ", ".join(authors) if isinstance(authors, list) else str(authors)
            
            isbn = ""
            identifiers = volume_info.get("industryIdentifiers", [])
            for idf in identifiers:
                if idf.get("type") in ("ISBN_13", "ISBN_10"):
                    isbn = idf.get("identifier")
                    break
            if not isbn and identifiers:
                isbn = identifiers[0].get("identifier", "000000")
            if not isbn:
                isbn = "000000"
                
            cov = volume_info.get("imageLinks", {}).get("thumbnail", "")
            if not cov and isbn and isbn != "000000":
                cov = f"https://images-na.ssl-images-amazon.com/images/P/{isbn}.01._SCLZZZZZZZ_SX200_.jpg"
            self.build_result_card(t, a, isbn, cov)

    def build_result_card(self, t, a, i, c_url):
        c = GlassFrame(self.scroll, height=100)
        c.pack(fill="x", pady=10)
        c.pack_propagate(False)
        
        f_left = ctk.CTkFrame(c, fg_color="transparent")
        f_left.pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(f_left, text=f"📖 {t[:50]}", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(f_left, text=f"👤 {a} | ISBN: {i}", text_color=APPLE_TEXT_MUTED).pack(anchor="w")
        
        AnimatedButton(c, text="Kütüphaneden İste", width=140, fg_color=APPLE_ORANGE, hover_color="#cc7a00", command=lambda: self.request_book(t, a, i, c_url)).pack(side="right", padx=20)

    def request_book(self, t, a, i, c_url):
        if messagebox.askyesno("İstek", f"{t} kitabını yöneticiden talep etmek istiyor musunuz?"):
            uid = self.main_app.user["id"]
            uname = self.main_app.user["name"]
            success, msg = RequestController.add_request(uid, uname, t, a, i, c_url)
            if success: messagebox.showinfo("Başarılı", "İsteğiniz yöneticiye iletildi!")
            else: messagebox.showerror("Hata", msg)


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, main_app):
        super().__init__(master, fg_color="transparent")
        self.main_app = main_app
        ctk.CTkLabel(self, text="Ayarlar", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", padx=40, pady=(40, 20))
        
        f = GlassFrame(self, height=200)
        f.pack(fill="x", padx=40, pady=20)
        f.pack_propagate(False)
        
        ctk.CTkLabel(f, text="Görünüm Modu", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))
        self.mode_var = ctk.StringVar(value=ctk.get_appearance_mode())
        
        ctk.CTkRadioButton(f, text="Karanlık Mod (Dark)", variable=self.mode_var, value="Dark", command=self.change_mode).pack(anchor="w", padx=20, pady=10)
        ctk.CTkRadioButton(f, text="Aydınlık Mod (Light)", variable=self.mode_var, value="Light", command=self.change_mode).pack(anchor="w", padx=20, pady=10)
        
    def change_mode(self):
        ctk.set_appearance_mode(self.mode_var.get())
        apply_treeview_style()

class UserMainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Lumina Kütüphane - macOS Style")
        self.geometry("1100x750")
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=APPLE_BG)
        
        self.user = None
        self.current_view = None
        
        self.sidebar = GlassFrame(self, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.configure(width=220)
        self.sidebar.pack_propagate(False)
        
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True)
        
        self.render_sidebar()
        self.show_catalog()

    def on_login_success(self, user):
        if user.get("must_change_password") == 1:
            ForcePasswordModal(self, user, self.finalize_login)
        else:
            self.finalize_login(user)
            
    def finalize_login(self, user):
        self.user = user
        self.render_sidebar()
        self.show_catalog()
        
    def logout(self):
        self.user = None
        self.render_sidebar()
        self.show_catalog()

    def render_sidebar(self):
        for w in self.sidebar.winfo_children(): w.destroy()
        
        ic_cat = get_icon("book")
        ic_req = get_icon("star")
        ic_prof = get_icon("user")
        ic_set = get_icon("settings")
        ic_out = get_single_icon("logout.png")
        
        if self.user:
            self.prof = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            self.prof.pack(fill="x", pady=(40, 20), padx=20)
            ctk.CTkLabel(self.prof, text="", image=get_icon("user", 36)).pack()
            ctk.CTkLabel(self.prof, text=self.user["name"], font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(5,0))
            ctk.CTkLabel(self.prof, text="Onaylı Üye", font=ctk.CTkFont(size=11), text_color=APPLE_GREEN).pack()
            
            notifs = NotificationController.get_unread_notifications(self.user["id"])
            n_count = len(notifs)
            ic_bell = get_icon("bell_active" if n_count>0 else "bell")
            
            ctk.CTkButton(self.sidebar, text=" Katalog", image=ic_cat, font=ctk.CTkFont(size=14), fg_color="transparent", text_color=APPLE_TEXT, hover_color=("#E5E5EA", "#3A3A3C"), anchor="w", command=self.show_catalog).pack(fill="x", padx=15, pady=5)
            ctk.CTkButton(self.sidebar, text=" Kitap İste", image=ic_req, font=ctk.CTkFont(size=14), fg_color="transparent", text_color=APPLE_TEXT, hover_color=("#E5E5EA", "#3A3A3C"), anchor="w", command=self.show_request).pack(fill="x", padx=15, pady=5)
            ctk.CTkButton(self.sidebar, text=f" Bildirimler ({n_count})", image=ic_bell, font=ctk.CTkFont(size=14), fg_color="transparent", text_color=APPLE_ORANGE if n_count>0 else APPLE_TEXT, hover_color=("#E5E5EA", "#3A3A3C"), anchor="w", command=self.show_notifications).pack(fill="x", padx=15, pady=5)
            ctk.CTkButton(self.sidebar, text=" Profilim", image=ic_prof, font=ctk.CTkFont(size=14), fg_color="transparent", text_color=APPLE_TEXT, hover_color=("#E5E5EA", "#3A3A3C"), anchor="w", command=self.show_profile).pack(fill="x", padx=15, pady=5)
            ctk.CTkButton(self.sidebar, text=" Ayarlar", image=ic_set, font=ctk.CTkFont(size=14), fg_color="transparent", text_color=APPLE_TEXT, hover_color=("#E5E5EA", "#3A3A3C"), anchor="w", command=self.show_settings).pack(fill="x", padx=15, pady=5)
            
            ctk.CTkButton(self.sidebar, text=" Çıkış", image=ic_out, font=ctk.CTkFont(size=14), fg_color="transparent", text_color=APPLE_RED, hover_color=("#E5E5EA", "#3A3A3C"), anchor="w", command=self.logout).pack(side="bottom", fill="x", padx=15, pady=30)
        else:
            self.prof = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            self.prof.pack(fill="x", pady=(40, 20), padx=20)
            ctk.CTkLabel(self.prof, text="", image=get_icon("user", 36)).pack()
            ctk.CTkLabel(self.prof, text="Ziyaretçi", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(5,0))
            
            ctk.CTkButton(self.sidebar, text=" Katalog", image=ic_cat, font=ctk.CTkFont(size=14), fg_color="transparent", text_color=APPLE_TEXT, hover_color=("#E5E5EA", "#3A3A3C"), anchor="w", command=self.show_catalog).pack(fill="x", padx=15, pady=5)
            ctk.CTkButton(self.sidebar, text=" Ayarlar", image=ic_set, font=ctk.CTkFont(size=14), fg_color="transparent", text_color=APPLE_TEXT, hover_color=("#E5E5EA", "#3A3A3C"), anchor="w", command=self.show_settings).pack(fill="x", padx=15, pady=5)
            ctk.CTkButton(self.sidebar, text=" Giriş Yap", image=ic_prof, font=ctk.CTkFont(size=14), fg_color="transparent", text_color=APPLE_BLUE, hover_color=("#E5E5EA", "#3A3A3C"), anchor="w", command=lambda: AuthModal(self, self.on_login_success)).pack(side="bottom", fill="x", padx=15, pady=30)

    def show_catalog(self):
        if self.current_view: self.current_view.destroy()
        self.current_view = CatalogView(self.content, self)
        self.current_view.pack(fill="both", expand=True)

    def show_profile(self):
        if self.current_view: self.current_view.destroy()
        self.current_view = ProfileView(self.content, self)
        self.current_view.pack(fill="both", expand=True)

    def show_request(self):
        if self.current_view: self.current_view.destroy()
        self.current_view = UserRequestView(self.content, self)
        self.current_view.pack(fill="both", expand=True)

    def show_notifications(self):
        if self.current_view: self.current_view.destroy()
        self.current_view = NotificationsView(self.content, self)
        self.current_view.pack(fill="both", expand=True)

    def show_settings(self):
        if self.current_view: self.current_view.destroy()
        self.current_view = SettingsView(self.content, self)
        self.current_view.pack(fill="both", expand=True)

class ForcePasswordModal(ctk.CTkToplevel):
    def __init__(self, master, user, on_complete):
        super().__init__(master)
        self.title("🛡️ Şifre Güvenliği")
        self.geometry("450x450")
        self.configure(fg_color=APPLE_BG)
        self.user = user
        self.on_complete = on_complete
        self.grab_set()
        
        # Disable close button (X) -> must change password
        self.protocol("WM_DELETE_WINDOW", self.disable_close)
        
        ctk.CTkLabel(self, text="Güvenlik Uyarısı", font=ctk.CTkFont(size=24, weight="bold"), text_color=APPLE_ORANGE).pack(pady=(30,10))
        ctk.CTkLabel(self, text="Yönetici tarafından oluşturulan bu hesapla\nilk defa giriş yaptınız. Lütfen güvenliğiniz için\nkendi şifrenizi belirleyin.", text_color=APPLE_TEXT_MUTED, justify="center").pack(pady=(0, 20))
        
        self.old_pw = ctk.CTkEntry(self, placeholder_text="Yöneticinin Verdiği Şifre (Mevcut)", show="●", width=300, height=36)
        self.old_pw.pack(pady=5)
        self.new_pw1 = ctk.CTkEntry(self, placeholder_text="Yeni Şifre (En az 4 karakter)", show="●", width=300, height=36)
        self.new_pw1.pack(pady=5)
        self.new_pw2 = ctk.CTkEntry(self, placeholder_text="Yeni Şifre Tekrar", show="●", width=300, height=36)
        self.new_pw2.pack(pady=5)
        
        self.chk = ctk.CTkCheckBox(self, text="Şifreleri Göster", command=self.toggle)
        self.chk.pack(pady=5)
        
        AnimatedButton(self, text="Şifreyi Belirle ve Giriş Yap", width=300, command=self.save).pack(pady=20)
        
    def disable_close(self):
        pass
        
    def toggle(self):
        s = "" if self.chk.get() == 1 else "●"
        self.old_pw.configure(show=s)
        self.new_pw1.configure(show=s)
        self.new_pw2.configure(show=s)
        
    def save(self):
        old = self.old_pw.get()
        n1 = self.new_pw1.get()
        n2 = self.new_pw2.get()
        
        if not old or not n1 or not n2:
            messagebox.showerror("Hata", "Tüm alanları doldurun.")
            return
        if n1 != n2:
            messagebox.showerror("Hata", "Yeni şifreler eşleşmiyor.")
            return
            
        succ, msg = AuthController.change_password(self.user["id"], old, n1)
        if succ:
            messagebox.showinfo("Başarılı", "Şifreniz başarıyla güncellendi! Hoş geldiniz.")
            self.user["must_change_password"] = 0
            self.destroy()
            self.on_complete(self.user)
        else:
            messagebox.showerror("Hata", msg)

import customtkinter as ctk
from tkinter import ttk, messagebox
import requests
from models.database import get_connection
from controllers.auth import AuthController
from controllers.library import BookController, MemberController, BorrowController, RequestController, NotificationController

import threading
from PIL import Image

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
    def __init__(self, master, fg_color=APPLE_BLUE, **kwargs):
        super().__init__(master, fg_color=fg_color, corner_radius=12, **kwargs)

class GlassFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        cr = kwargs.pop("corner_radius", 15)
        super().__init__(master, fg_color=APPLE_PANEL, corner_radius=cr, border_width=1, border_color="#3A3A3C", **kwargs)

class AdminLoginView(ctk.CTkFrame):
    def __init__(self, master, on_success):
        super().__init__(master, fg_color=APPLE_BG)
        self.on_success = on_success
        
        self.box = GlassFrame(self, width=450, height=550)
        self.box.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(self.box, text="⚙️ Yönetim", font=ctk.CTkFont(size=36, weight="bold")).pack(pady=(60, 40))
        
        self.user = ctk.CTkEntry(self.box, placeholder_text="Kullanıcı Adı", width=300, height=45, corner_radius=10)
        self.user.pack(pady=10)
        self.pwd = ctk.CTkEntry(self.box, placeholder_text="Şifre", show="●", width=300, height=45, corner_radius=10)
        self.pwd.pack(pady=10)
        
        self.btn = AnimatedButton(self.box, text="Giriş Yap", width=300, height=45, font=ctk.CTkFont(weight="bold"), command=self.login)
        self.btn.pack(pady=30)
        
        self.err = ctk.CTkLabel(self.box, text="", text_color=APPLE_RED)
        self.err.pack()

    def login(self):
        success, admin_info = AuthController.login_admin(self.user.get(), self.pwd.get())
        if success:
            self.on_success(admin_info)
        else:
            self.err.configure(text="Hatalı bilgiler!")

class AdminDashboard(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="📊 Genel Bakış", font=ctk.CTkFont(size=32, weight="bold")).pack(anchor="w", padx=40, pady=(40, 20))
        
        self.cards = ctk.CTkFrame(self, fg_color="transparent")
        self.cards.pack(fill="x", padx=40)
        
        self.lbl_tot = self.make_card("📚 Toplam Kitap", APPLE_BLUE)
        self.lbl_act = self.make_card("⏳ Aktif Ödünç", APPLE_ORANGE)
        self.lbl_ovr = self.make_card("🚫 Gecikmiş", APPLE_RED)
        
        self.refresh()
        
    def make_card(self, title, color):
        c = GlassFrame(self.cards, height=150)
        c.pack(side="left", expand=True, padx=10)
        c.pack_propagate(False)
        ctk.CTkLabel(c, text=title, font=ctk.CTkFont(size=18), text_color=APPLE_TEXT_MUTED).pack(pady=(30, 10))
        lbl = ctk.CTkLabel(c, text="0", font=ctk.CTkFont(size=40, weight="bold"), text_color=color)
        lbl.pack()
        return lbl
        
    def refresh(self):
        t, a, o = BorrowController.get_dashboard_stats()
        self.lbl_tot.configure(text=str(t))
        self.lbl_act.configure(text=str(a))
        self.lbl_ovr.configure(text=str(o))

class AdminBooksView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=40, pady=(40, 20))
        ctk.CTkLabel(top, text="📚 Kitap Envanteri", font=ctk.CTkFont(size=32, weight="bold")).pack(side="left")
        AnimatedButton(top, text="+ Manuel Kitap Ekle", command=self.manual_add).pack(side="right")
        
        # Table
        self.t_frame = GlassFrame(self)
        self.t_frame.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        
        apply_treeview_style()
        
        self.tree = ttk.Treeview(self.t_frame, columns=("id", "title", "author", "isbn", "cat", "year", "tot", "avl"), show="headings")
        heads = ["ID", "Başlık", "Yazar", "ISBN", "Kategori", "Yıl", "Toplam", "Mevcut"]
        for c, h in zip(self.tree["columns"], heads):
            self.tree.heading(c, text=h)
        self.tree.column("id", width=40)
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)
        self.tree.bind("<Double-1>", self.on_double)
        
        ctk.CTkLabel(self, text="* Düzenlemek için kitaba çift tıklayın", text_color=APPLE_TEXT_MUTED).pack(pady=10)
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for b in BookController.get_all_books(limit=1000):
            # Hide description in the TreeView but pass it
            self.tree.insert("", "end", values=(b[0], b[1], b[2], b[3], b[4], b[5], b[8], b[9], b[6]))

    def on_double(self, e):
        sel = self.tree.selection()
        if sel: EditBookModal(self, self.tree.item(sel, "values"), self.refresh)
        
    def manual_add(self):
        vals = ["", "", "", "", "Genel", "2024", "3", "0", ""]
        EditBookModal(self, vals, self.refresh, is_new=True)

class EditBookModal(ctk.CTkToplevel):
    def __init__(self, parent, vals, on_complete, is_new=False):
        super().__init__(parent)
        self.title("✏️ Yeni Kitap" if is_new else "✏️ Kitap Düzenle")
        self.geometry("450x700")
        self.configure(fg_color=APPLE_PANEL)
        self.on_complete = on_complete
        self.is_new = is_new
        self.bid = vals[0] if not is_new else None
        self.vals = vals
        
        ctk.CTkLabel(self, text="Yeni Kitap Ekle" if is_new else "Kitap Detayları", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)
        
        self.ents = {}
        for idx, pl in enumerate(["Başlık", "Yazar", "ISBN", "Kategori", "Yıl"]):
            e = ctk.CTkEntry(self, placeholder_text=pl, width=350, height=40)
            e.insert(0, vals[idx+1])
            e.pack(pady=10)
            self.ents[pl] = e
            
        self.tot = ctk.CTkEntry(self, placeholder_text="Mevcut Kopya Sayısı", width=350, height=40)
        self.tot.insert(0, vals[7] if not is_new else vals[6]) # vals[7] is available_copies
        self.tot.pack(pady=10)
        
        ctk.CTkLabel(self, text="Kitap Özeti (Description)").pack(anchor="w", padx=50)
        self.desc_txt = ctk.CTkTextbox(self, width=350, height=80)
        self.desc_txt.insert("0.0", str(vals[8]) if len(vals)>8 and str(vals[8]) != "None" else "")
        self.desc_txt.pack(pady=5)
        
        AnimatedButton(self, text="✨ İnternetten Özet Çek", width=350, height=35, fg_color=APPLE_ORANGE, hover_color="#cc7a00", command=self.auto_desc).pack(pady=5)
        AnimatedButton(self, text="Kaydet", width=350, height=45, command=self.save).pack(pady=15)
        
    def auto_desc(self):
        t = self.ents["Başlık"].get()
        if not t: return
        self.desc_txt.delete("0.0", "end")
        self.desc_txt.insert("0.0", "Aranıyor...")
        self.update()
        
        def _fetch():
            try:
                r = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={t}&maxResults=1", timeout=8)
                items = r.json().get("items", [])
                if items:
                    volume_info = items[0].get("volumeInfo", {})
                    desc = volume_info.get("description", "Bu kitap için özet bulunamadı.")
                    self.after(0, lambda d=desc: self.set_desc_text(d))
                else:
                    self.after(0, lambda: self.set_desc_text("Sonuç bulunamadı."))
            except Exception as e:
                self.after(0, lambda: self.set_desc_text(f"Hata: {str(e)[:30]}"))
                
        threading.Thread(target=_fetch, daemon=True).start()

    def set_desc_text(self, text):
        try:
            if self.winfo_exists():
                self.desc_txt.delete("0.0", "end")
                self.desc_txt.insert("0.0", text)
        except:
            pass

    def save(self):
        desc = self.desc_txt.get("0.0", "end").strip()
        if self.is_new:
            BookController.add_book(self.ents["Başlık"].get(), self.ents["Yazar"].get(), self.ents["ISBN"].get(), self.ents["Kategori"].get(), int(self.ents["Yıl"].get()), desc, "", int(self.tot.get()))
        else:
            # self.tot is available copies.
            # new_total = current_total + (new_avail - current_avail)
            new_avail = int(self.tot.get())
            curr_avail = int(self.vals[7])
            curr_total = int(self.vals[6])
            diff = new_avail - curr_avail
            new_total = curr_total + diff
            
            BookController.update_book(self.bid, self.ents["Başlık"].get(), self.ents["Yazar"].get(), self.ents["ISBN"].get(), self.ents["Kategori"].get(), int(self.ents["Yıl"].get()), desc, "", new_total)
        self.on_complete()
        self.destroy()

class AdminApprovalsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="✅ Bekleyen Onaylar", font=ctk.CTkFont(size=32, weight="bold")).pack(anchor="w", padx=40, pady=(40, 20))
        self.t_frame = GlassFrame(self)
        self.t_frame.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        
        apply_treeview_style()
        self.tree = ttk.Treeview(self.t_frame, columns=("id", "n", "e", "p", "d"), show="headings")
        for c, h in zip(self.tree["columns"], ["ID", "Ad Soyad", "E-posta", "Telefon", "Tarih"]): self.tree.heading(c, text=h)
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)
        self.tree.bind("<Double-1>", self.on_double)
        ctk.CTkLabel(self, text="* Üyeliği onaylamak için çift tıklayın.", text_color=APPLE_TEXT_MUTED).pack(pady=10)
        self.refresh()
        
    def refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for m in MemberController.get_pending_members(): self.tree.insert("", "end", values=m)
        
    def on_double(self, e):
        sel = self.tree.selection()
        if sel:
            if messagebox.askyesno("Onayla", "Bu hesabı aktifleştirmek istiyor musunuz?"):
                MemberController.approve_member(self.tree.item(sel, "values")[0])
                self.refresh()

class AdminMembersView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=40, pady=(40, 20))
        ctk.CTkLabel(top, text="👥 Üyeler (Onaylı)", font=ctk.CTkFont(size=32, weight="bold")).pack(side="left")
        AnimatedButton(top, text="+ Manuel Üye Ekle", command=self.manual_add).pack(side="right")
        
        self.t_frame = GlassFrame(self)
        self.t_frame.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        apply_treeview_style()
        self.tree = ttk.Treeview(self.t_frame, columns=("id", "n", "e", "p", "d"), show="headings")
        for c, h in zip(self.tree["columns"], ["ID", "Ad Soyad", "E-posta", "Telefon", "Tarih"]): self.tree.heading(c, text=h)
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)
        self.tree.bind("<Double-1>", self.on_double)
        self.refresh()
        
    def refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for m in MemberController.get_all_members(): self.tree.insert("", "end", values=m)
        
    def on_double(self, e):
        sel = self.tree.selection()
        if sel:
            EditMemberModal(self.winfo_toplevel(), self.tree.item(sel, "values"), self.refresh)

    def manual_add(self):
        AddMemberModal(self.winfo_toplevel(), self.refresh)

class EditMemberModal(ctk.CTkToplevel):
    def __init__(self, parent, vals, on_complete):
        super().__init__(parent)
        self.title("👤 Üye Düzenle")
        self.geometry("450x600")
        self.configure(fg_color=APPLE_PANEL)
        self.on_complete = on_complete
        self.mid = vals[0]
        self.vals = vals
        self.grab_set()
        
        ctk.CTkLabel(self, text="Üye Detayları & Düzenleme", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)
        
        vcmd = (self.register(self.validate_phone), "%P")
        self.ents = {}
        fields = [("Ad Soyad", vals[1]), ("E-posta", vals[2]), ("Telefon", vals[3]), ("Yeni Şifre (İsteğe Bağlı)", "")]
        for pl, val in fields:
            if pl == "Telefon":
                e = ctk.CTkEntry(self, placeholder_text=pl, width=350, height=40, validate="key", validatecommand=vcmd)
            else:
                e = ctk.CTkEntry(self, placeholder_text=pl, width=350, height=40)
                if "Şifre" in pl:
                    e.configure(show="●")
            e.insert(0, val)
            e.pack(pady=10)
            self.ents[pl] = e
            
        AnimatedButton(self, text="Değişiklikleri Kaydet", width=350, height=45, command=self.save).pack(pady=10)
        AnimatedButton(self, text="Üyeyi Sil", width=350, height=45, fg_color=APPLE_RED, command=self.delete_member).pack(pady=10)

    def validate_phone(self, p):
        if p == "":
            return True
        return p.isdigit()

    def save(self):
        name = self.ents["Ad Soyad"].get().strip()
        email = self.ents["E-posta"].get().strip()
        phone = self.ents["Telefon"].get().strip()
        pwd = self.ents["Yeni Şifre (İsteğe Bağlı)"].get()
        
        if not name or not email or not phone:
            messagebox.showerror("Hata", "Ad Soyad, E-posta ve Telefon alanları boş bırakılamaz.")
            return
            
        if not phone.isdigit():
            messagebox.showerror("Hata", "Telefon numarası sadece rakamlardan oluşmalıdır.")
            return
            
        succ, msg = MemberController.update_member_admin(self.mid, name, email, phone, pwd)
        if succ:
            messagebox.showinfo("Başarılı", msg)
            self.on_complete()
            self.destroy()
        else:
            messagebox.showerror("Hata", msg)
            
    def delete_member(self):
        if messagebox.askyesno("Sil", "Bu üyeyi sistemden silmek istediğinize emin misiniz? (Ödünç geçmişi 'Tüm Ödünç Geçmişi' sekmesinde tutulmaya devam edecektir)"):
            success, msg = MemberController.delete_member(self.mid)
            if success:
                self.on_complete()
                self.destroy()
            else:
                messagebox.showerror("Hata", msg)

class AddMemberModal(ctk.CTkToplevel):
    def __init__(self, parent, on_complete):
        super().__init__(parent)
        self.title("👤 Manuel Üye Ekle")
        self.geometry("450x500")
        self.configure(fg_color=APPLE_PANEL)
        self.on_complete = on_complete
        self.grab_set()
        
        ctk.CTkLabel(self, text="Yeni Üye Bilgileri", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)
        self.ents = {}
        vcmd = (self.register(self.validate_phone), "%P")
        for pl in ["Ad Soyad", "E-posta", "Telefon", "Şifre"]:
            if pl == "Telefon":
                e = ctk.CTkEntry(self, placeholder_text=pl, width=350, height=40, validate="key", validatecommand=vcmd)
            else:
                e = ctk.CTkEntry(self, placeholder_text=pl, width=350, height=40)
                if pl == "Şifre": e.configure(show="●")
            e.pack(pady=10)
            self.ents[pl] = e
            
        AnimatedButton(self, text="Ekle ve Aktifleştir", width=350, height=45, command=self.save).pack(pady=20)

    def validate_phone(self, p):
        if p == "":
            return True
        return p.isdigit()
        
    def save(self):
        phone = self.ents["Telefon"].get().strip()
        if not phone.isdigit():
            messagebox.showerror("Hata", "Telefon numarası sadece rakamlardan oluşmalıdır.")
            return
            
        succ, msg = AuthController.register(self.ents["Ad Soyad"].get(), self.ents["E-posta"].get(), phone, self.ents["Şifre"].get())
        if succ:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE members SET is_approved = 1, must_change_password = 1 WHERE email = ?", (self.ents["E-posta"].get(),))
            conn.commit()
            conn.close()
            self.on_complete()
            self.destroy()
        else:
            messagebox.showerror("Hata", msg)


class AdminBorrowsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="⏳ Tüm Ödünç Geçmişi", font=ctk.CTkFont(size=32, weight="bold")).pack(anchor="w", padx=40, pady=(40, 20))
        self.t_frame = GlassFrame(self)
        self.t_frame.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        
        apply_treeview_style()
        self.tree = ttk.Treeview(self.t_frame, columns=("id", "b", "m", "bd", "rd", "ad", "f"), show="headings")
        for c, h in zip(self.tree["columns"], ["ID", "Kitap", "Üye", "Veriliş Tarihi", "Son Teslim", "Durum", "Ceza"]): self.tree.heading(c, text=h)
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)
        self.tree.bind("<Double-1>", self.on_double)
        ctk.CTkLabel(self, text="* Manuel iade almak için kayda çift tıklayın (Örn: Üye silinmişse veya kitabı elden verdiyse).", text_color=APPLE_TEXT_MUTED).pack(pady=10)
        self.refresh()
        
    def refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for b in BorrowController.get_all_borrows(): 
            br_id, title, member, b_date, r_date, act_date, fee = b
            status = "✅ İade Edildi" if act_date and str(act_date) != "None" else "⏳ Kullanıcıda"
            self.tree.insert("", "end", values=(br_id, title, member, b_date, r_date, status, fee))
        
    def on_double(self, e):
        sel = self.tree.selection()
        if sel:
            act = self.tree.item(sel, "values")[5]
            if act == "⏳ Kullanıcıda":
                if messagebox.askyesno("İade", "Bu kitabı manuel olarak iade almak istiyor musunuz?"):
                    BorrowController.return_book(self.tree.item(sel, "values")[0])
                    self.refresh()

class AdminOpenLibraryView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="🌐 İnternetten Kitap Ekle", font=ctk.CTkFont(size=32, weight="bold")).pack(anchor="w", padx=40, pady=(40, 20))
        
        self.top = GlassFrame(self, height=100)
        self.top.pack(fill="x", padx=40, pady=(0, 20))
        self.top.pack_propagate(False)
        
        self.ent = ctk.CTkEntry(self.top, placeholder_text="🔍 Kitap Adı, ISBN veya Yazar (OpenLibrary)...", width=500, height=45)
        self.ent.pack(side="left", padx=20, pady=20)
        AnimatedButton(self.top, text="Bul", width=100, height=45, command=self.search).pack(side="left")
        self.status = ctk.CTkLabel(self.top, text="", text_color=APPLE_TEXT_MUTED)
        self.status.pack(side="left", padx=20)
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=40)

    def search(self):
        q = self.ent.get()
        if not q: return
        self.status.configure(text="Aranıyor...")
        self.update()
        for w in self.scroll.winfo_children(): w.destroy()
        
        def _do_search():
            try:
                r = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={q}&maxResults=10", timeout=10)
                if r.status_code == 200:
                    items = r.json().get("items", [])
                    if items:
                        self.after(0, self._show_results, items)
                    else:
                        self._do_gutenberg_search(q)
                else:
                    self._do_gutenberg_search(q)
            except Exception as e:
                print(f"DEBUG SEARCH ERROR: {e}")
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
        self.safe_update_status(f"✅ {len(results)} sonuç bulundu (Gutenberg).")
        for book in results:
            t = book.get("title", "Bilinmiyor")
            authors = book.get("authors", [])
            a = ", ".join([auth.get("name", "Bilinmiyor") for auth in authors]) if authors else "Bilinmiyor"
            isbn = f"GUT{book.get('id', '000')}"
            
            subjects = book.get("subjects", [])
            sub = subjects[0].split("--")[0].strip() if subjects else "Genel"
            y = 2024
            desc = f"{t} by {a}."
            cov_url = book.get("formats", {}).get("image/jpeg", "")
            
            c = GlassFrame(self.scroll, height=100)
            c.pack(fill="x", pady=10)
            c.pack_propagate(False)
            
            f_left = ctk.CTkFrame(c, fg_color="transparent")
            f_left.pack(side="left", padx=20, pady=10)
            ctk.CTkLabel(f_left, text=f"📖 {t[:60]}", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(f_left, text=f"👤 {a[:50]} | 🏷️ {sub[:30]} | 📅 {y} | ISBN: {isbn}", text_color=APPLE_TEXT_MUTED).pack(anchor="w")
            
            f_right = ctk.CTkFrame(c, fg_color="transparent")
            f_right.pack(side="right", padx=20, pady=10)
            ctk.CTkLabel(f_right, text="Adet:").pack(side="left", padx=5)
            qty = ctk.CTkEntry(f_right, width=50)
            qty.insert(0, "3")
            qty.pack(side="left", padx=10)
            AnimatedButton(f_right, text="Ekle", width=80, command=lambda title=t, auth=a, i=isbn, s=sub, yr=y, d=desc, img=cov_url, q_ent=qty: self.add_book(title, auth, i, s, yr, d, img, q_ent)).pack(side="left")

    def safe_update_status(self, text, color=APPLE_TEXT_MUTED):
        try:
            if self.winfo_exists():
                self.status.configure(text=text, text_color=color)
        except:
            pass

    def _show_results(self, items):
        self.safe_update_status(f"✅ {len(items)} sonuç bulundu.")
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
                isbn = identifiers[0].get("identifier", "000000000")
            if not isbn:
                isbn = "000000000"
                
            sub = volume_info.get("categories", ["Genel"])[0]
            y_str = volume_info.get("publishedDate", "2024")[:4]
            try:
                y = int(y_str)
            except:
                y = 2024
                
            desc = volume_info.get("description", "")
            cov_url = volume_info.get("imageLinks", {}).get("thumbnail", "")
            if not cov_url and isbn and isbn != "000000000":
                cov_url = f"https://images-na.ssl-images-amazon.com/images/P/{isbn}.01._SCLZZZZZZZ_SX200_.jpg"
            
            c = GlassFrame(self.scroll, height=100)
            c.pack(fill="x", pady=10)
            c.pack_propagate(False)
            
            f_left = ctk.CTkFrame(c, fg_color="transparent")
            f_left.pack(side="left", padx=20, pady=10)
            ctk.CTkLabel(f_left, text=f"📖 {t[:60]}", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(f_left, text=f"👤 {a[:50]} | 🏷️ {sub[:30]} | 📅 {y} | ISBN: {isbn}", text_color=APPLE_TEXT_MUTED).pack(anchor="w")
            
            f_right = ctk.CTkFrame(c, fg_color="transparent")
            f_right.pack(side="right", padx=20, pady=10)
            ctk.CTkLabel(f_right, text="Adet:").pack(side="left", padx=5)
            qty = ctk.CTkEntry(f_right, width=50)
            qty.insert(0, "3")
            qty.pack(side="left", padx=10)
            AnimatedButton(f_right, text="Ekle", width=80, command=lambda title=t, auth=a, i=isbn, s=sub, yr=y, d=desc, img=cov_url, q_ent=qty: self.add_book(title, auth, i, s, yr, d, img, q_ent)).pack(side="left")

    def add_book(self, t, a, i, s, y, d, img, q_ent):
        try:
            success, msg = BookController.add_book(t, a, i, s, y, d, img, int(q_ent.get()))
            if success: messagebox.showinfo("Başarılı", f"{t} başarıyla eklendi!")
            else: messagebox.showerror("Hata", msg)
        except ValueError: messagebox.showerror("Hata", "Adet hatalı.")

class AdminRequestsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="💡 Eklenmesi İstenenler", font=ctk.CTkFont(size=32, weight="bold")).pack(anchor="w", padx=40, pady=(40, 20))
        
        self.t_frame = GlassFrame(self)
        self.t_frame.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        
        apply_treeview_style()
        self.tree = ttk.Treeview(self.t_frame, columns=("id", "mid", "mem", "tit", "aut", "isbn", "date", "url"), show="headings")
        for c, h in zip(self.tree["columns"], ["ID", "Üye ID", "İsteyen Üye", "Kitap Başlığı", "Yazar", "ISBN", "Tarih", "URL"]): self.tree.heading(c, text=h)
        self.tree.column("url", width=0, stretch=False)
        self.tree.column("mid", width=0, stretch=False)
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)
        self.tree.bind("<Double-1>", self.on_double)
        
        ctk.CTkLabel(self, text="* Kütüphaneye eklemek veya reddetmek için isteğe çift tıklayın.", text_color=APPLE_TEXT_MUTED).pack(pady=10)
        self.refresh()
        
    def refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in RequestController.get_all_requests(): self.tree.insert("", "end", values=r)
        
    def on_double(self, e):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel, "values")
        req_id, member_id, member_name, title, author, isbn, date, url = vals
        
        msg = f"{member_name} adlı üye '{title}' kitabını istiyor.\nKütüphaneye eklensin mi?"
        if messagebox.askyesno("Kitap İsteği", msg):
            success, m = BookController.add_book(title, author, isbn, "Genel", 2024, "", url, 3)
            if success:
                messagebox.showinfo("Başarılı", "Kitap kütüphaneye eklendi!")
                RequestController.delete_request(req_id)
                NotificationController.add_notification(member_id, f"🎉 İstediğiniz '{title}' kitabı onaylandı ve kütüphaneye eklendi!")
                self.refresh()
            else:
                messagebox.showerror("Hata", m)
        else:
            if messagebox.askyesno("İsteği Sil", "Bu isteği reddedip listeden silmek ister misiniz?"):
                RequestController.delete_request(req_id)
                NotificationController.add_notification(member_id, f"❌ '{title}' kitabı isteğiniz yönetici tarafından reddedildi.")
                self.refresh()

class AdminProfileRequestsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="📝 Profil Değişiklik Talepleri", font=ctk.CTkFont(size=32, weight="bold")).pack(anchor="w", padx=40, pady=(40, 20))
        
        self.t_frame = GlassFrame(self)
        self.t_frame.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        
        apply_treeview_style()
        self.tree = ttk.Treeview(self.t_frame, columns=("id", "mid", "mem", "nn", "ne", "date"), show="headings")
        for c, h in zip(self.tree["columns"], ["ID", "Üye ID", "Mevcut Üye Adı", "Yeni İsim", "Yeni E-posta", "Tarih"]): self.tree.heading(c, text=h)
        self.tree.column("mid", width=0, stretch=False)
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)
        self.tree.bind("<Double-1>", self.on_double)
        
        ctk.CTkLabel(self, text="* Onaylamak veya reddetmek için talebe çift tıklayın.", text_color=APPLE_TEXT_MUTED).pack(pady=10)
        self.refresh()
        
    def refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        from controllers.library import ProfileRequestController
        for r in ProfileRequestController.get_pending_requests(): self.tree.insert("", "end", values=r)
        
    def on_double(self, e):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel, "values")
        req_id, member_id, member_name, new_name, new_email, date = vals
        
        msg = f"{member_name} adlı üye bilgilerini şunlarla değiştirmek istiyor:\n\nYeni İsim: {new_name}\nYeni E-posta: {new_email}\n\nOnaylıyor musunuz?"
        from controllers.library import ProfileRequestController, NotificationController
        if messagebox.askyesno("Profil Talebi", msg):
            ProfileRequestController.approve_request(req_id, member_id, new_name, new_email)
            NotificationController.add_notification(member_id, "🎉 Profil bilgileriniz başarıyla güncellendi.")
            self.refresh()
            messagebox.showinfo("Başarılı", "Kullanıcı bilgileri güncellendi.")
        else:
            if messagebox.askyesno("Talebi Reddet", "Bu talebi reddedip silmek ister misiniz?"):
                ProfileRequestController.reject_request(req_id)
                NotificationController.add_notification(member_id, "❌ Profil güncelleme talebiniz reddedildi.")
                self.refresh()

class AdminProfileView(ctk.CTkFrame):
    def __init__(self, master, admin_user, on_update):
        super().__init__(master, fg_color="transparent")
        self.admin_user = admin_user
        self.on_update = on_update
        
        ctk.CTkLabel(self, text="👤 Yönetici Profili", font=ctk.CTkFont(size=32, weight="bold")).pack(anchor="w", padx=40, pady=(40, 20))
        
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=40)
        
        f1 = GlassFrame(scroll)
        f1.pack(fill="x", pady=10)
        ctk.CTkLabel(f1, text="Genel Bilgiler", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))
        
        self.e_user = ctk.CTkEntry(f1, placeholder_text="Kullanıcı Adı", width=300, height=36)
        self.e_user.insert(0, admin_user.get("username", ""))
        self.e_user.pack(anchor="w", padx=20, pady=5)
        
        self.e_name = ctk.CTkEntry(f1, placeholder_text="Ad Soyad", width=300, height=36)
        self.e_name.insert(0, admin_user.get("name", ""))
        self.e_name.pack(anchor="w", padx=20, pady=5)
        
        self.e_email = ctk.CTkEntry(f1, placeholder_text="E-posta", width=300, height=36)
        self.e_email.insert(0, admin_user.get("email", ""))
        self.e_email.pack(anchor="w", padx=20, pady=5)
        
        AnimatedButton(f1, text="Bilgileri Kaydet", width=300, command=self.save_info).pack(anchor="w", padx=20, pady=15)
        
        f2 = GlassFrame(scroll)
        f2.pack(fill="x", pady=20)
        ctk.CTkLabel(f2, text="Şifre Değiştir", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))
        
        self.e_old_pw = ctk.CTkEntry(f2, placeholder_text="Mevcut Şifre", show="●", width=300, height=36)
        self.e_old_pw.pack(anchor="w", padx=20, pady=5)
        self.e_new_pw1 = ctk.CTkEntry(f2, placeholder_text="Yeni Şifre (En az 4 karakter)", show="●", width=300, height=36)
        self.e_new_pw1.pack(anchor="w", padx=20, pady=5)
        self.e_new_pw2 = ctk.CTkEntry(f2, placeholder_text="Yeni Şifre (Tekrar)", show="●", width=300, height=36)
        self.e_new_pw2.pack(anchor="w", padx=20, pady=5)
        
        self.chk = ctk.CTkCheckBox(f2, text="Şifreleri Göster", command=self.toggle)
        self.chk.pack(anchor="w", padx=20, pady=5)
        
        AnimatedButton(f2, text="Şifreyi Değiştir", width=300, command=self.save_pw).pack(anchor="w", padx=20, pady=15)
        
    def toggle(self):
        s = "" if self.chk.get() == 1 else "●"
        self.e_old_pw.configure(show=s)
        self.e_new_pw1.configure(show=s)
        self.e_new_pw2.configure(show=s)
        
    def save_info(self):
        u = self.e_user.get().strip()
        n = self.e_name.get().strip()
        e = self.e_email.get().strip()
        if not u or not n or not e:
            messagebox.showerror("Hata", "Tüm alanları doldurun.")
            return
        succ, msg = AuthController.update_admin_profile(self.admin_user["id"], u, n, e)
        if succ:
            self.on_update({"username": u, "name": n, "email": e})
            messagebox.showinfo("Başarılı", msg)
        else:
            messagebox.showerror("Hata", msg)
            
    def save_pw(self):
        o = self.e_old_pw.get()
        n1 = self.e_new_pw1.get()
        n2 = self.e_new_pw2.get()
        if not o or not n1 or not n2:
            messagebox.showerror("Hata", "Tüm alanları doldurun.")
            return
        if n1 != n2:
            messagebox.showerror("Hata", "Yeni şifreler eşleşmiyor.")
            return
        succ, msg = AuthController.change_admin_password(self.admin_user["id"], o, n1)
        if succ:
            messagebox.showinfo("Başarılı", msg)
            self.e_old_pw.delete(0, "end")
            self.e_new_pw1.delete(0, "end")
            self.e_new_pw2.delete(0, "end")
        else:
            messagebox.showerror("Hata", msg)

class AdminSettingsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="⚙️ Ayarlar", font=ctk.CTkFont(size=32, weight="bold")).pack(anchor="w", padx=40, pady=(40, 20))
        
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

class AdminWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Lumina - Admin Dashboard")
        self.geometry("1300x850")
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=APPLE_BG)
        self.cur = None
        self.admin_user = None
        self.show_login()
        
    def show_login(self):
        if self.cur: self.cur.destroy()
        self.cur = AdminLoginView(self, self.show_main)
        self.cur.pack(fill="both", expand=True)
        
    def update_admin_user(self, new_info):
        self.admin_user.update(new_info)
        
    def show_main(self, admin_user):
        self.admin_user = admin_user
        if self.cur: self.cur.destroy()
        m = ctk.CTkFrame(self, fg_color="transparent")
        m.pack(fill="both", expand=True)
        
        sb = GlassFrame(m, width=260, corner_radius=0)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        
        ctk.CTkLabel(sb, text=" Admin", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(50, 40))
        
        self.content = ctk.CTkFrame(m, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True)
        
        def nav(c):
            if self.cur: self.cur.destroy()
            if c == AdminProfileView:
                self.cur = c(self.content, self.admin_user, self.update_admin_user)
            else:
                self.cur = c(self.content)
            self.cur.pack(fill="both", expand=True)
            
        ic_cat = get_icon("book")
        ic_home = get_icon("home")
        ic_bell = get_icon("bell")
        ic_prof = get_icon("user")
        ic_set = get_icon("settings")
        ic_search = get_icon("search")
        ic_req = get_icon("star")
        
        menus = [
            ("Genel Bakış", AdminDashboard, ic_home), 
            ("Onay Bekleyenler", AdminApprovalsView, ic_bell), 
            ("Kitaplar", AdminBooksView, ic_cat), 
            ("İnternetten Ekle", AdminOpenLibraryView, ic_search), 
            ("İstenen Kitaplar", AdminRequestsView, ic_req), 
            ("Üyeler", AdminMembersView, ic_prof), 
            ("Profil İstekleri", AdminProfileRequestsView, ic_bell), 
            ("Tüm Geçmiş", AdminBorrowsView, ic_cat), 
            ("Profilim", AdminProfileView, ic_prof),
            ("Ayarlar", AdminSettingsView, ic_set)
        ]
        
        for text, cls, ic in menus:
            b = ctk.CTkButton(sb, text=f" {text}", image=ic, font=ctk.CTkFont(size=14), fg_color="transparent", text_color=APPLE_TEXT, hover_color=("#E5E5EA", "#3A3A3C"), anchor="w", command=lambda c=cls: nav(c))
            b.pack(fill="x", padx=15, pady=4)
            
        nav(AdminDashboard)

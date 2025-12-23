import os, shutil, json, sys, platform
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk
from PIL import Image, ImageTk

# macOS specific setup
if platform.system() == 'Darwin':
    # Enable high-resolution display support on macOS
    try:
        from Foundation import NSBundle
        bundle = NSBundle.mainBundle()
        info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
        info['NSHighResolutionCapable'] = True
    except ImportError:
        pass  # PyObjC not available, skip

# Hidden/system files to ignore (cross-platform)
HIDDEN_FILES = {'.DS_Store', 'Thumbs.db', '.gitkeep', 'desktop.ini'}

DATA_FILE = "data.json"
SETTINGS_FILE = "settings.json"

BG_COLOR = "#b2bec3"
PRIMARY_COLOR = "#2c3e50"
SECONDARY_COLOR = "#2980b9"  # Deeper blue
SUCCESS_COLOR = "#27ae60"    # Deeper green
DANGER_COLOR = "#c0392b"     # Deeper red
ACCENT_COLOR = "#f1c40f"
TEXT_COLOR = "#2c3e50"
TEXT_MUTED = "#5a6268"       # Darker muted text
TEXT_DARK = "#2c3e50"

ZORLUKLAR = {
    "1": "Çok Kolay",
    "2": "Kolay",
    "3": "Orta",
    "4": "Zor",
    "5": "Çok Zor"
}

# Set of difficulty folder names for matching (lowercase for case-insensitive comparison)
ZORLUK_ISIMLERI = {z.lower() for z in ZORLUKLAR.values()}

def is_zorluk_folder(name):
    """Check if a folder name is a difficulty folder (case-insensitive)"""
    return name.lower() in ZORLUK_ISIMLERI

def yukle_json(path, default):
    if not os.path.exists(path): return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return data if data is not None else default
        except: return default

def kaydet_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Soru Ayıklama Sistemi v2.0")
        self.root.geometry("1400x900")
        self.root.configure(bg=BG_COLOR)

        # Treeview Styling
        style = ttk.Style()
        style.theme_use('clam' if platform.system() != 'Darwin' else 'aqua')
        style.configure("Treeview", background="white", foreground=TEXT_DARK, 
                        fieldbackground="white", font=("Arial", 10))
        style.map("Treeview", background=[('selected', SECONDARY_COLOR)], 
                  foreground=[('selected', 'white')])

        self.settings = yukle_json(SETTINGS_FILE, {"input_dir": "Seçilmedi", "output_dir": "Seçilmedi"})
        self.data = yukle_json(DATA_FILE, {})

        self.settings = yukle_json(SETTINGS_FILE, {"input_dir": "", "output_dir": ""})
        self.data = {}
        self.yapiyi_guncelle()

        self.stack = [] 
        self.secili_alt = None
        self.ana_konu = None
        self.yol = "" 
        self.gorseller = []
        self.copluk_modu = False 

        self.menu()

    def create_btn(self, parent, txt, cmd, bg=None, fg=TEXT_DARK, width=None, height=None, font=("Helvetica", 11, "bold"), pady=None, padx=None):
        """Standardized button creator for the entire application"""
        btn = tk.Button(parent, text=txt, command=cmd, bg=bg or SECONDARY_COLOR, fg=fg, 
                        font=font, relief="flat", cursor="hand2")
        if width: btn.config(width=width)
        if height: btn.config(height=height)
        return btn

    def yapiyi_guncelle(self):
        out_dir = self.settings.get("output_dir", "")
        if not out_dir or not os.path.isdir(out_dir):
            self.data = yukle_json(DATA_FILE, {})
            return
        yeni_yapi = {}
        zorluk_isimleri = set(ZORLUKLAR.values())  # Set of difficulty folder names to exclude
        if os.path.exists(out_dir):
            ana_klasorler = [d for d in os.listdir(out_dir) if os.path.isdir(os.path.join(out_dir, d)) and d not in HIDDEN_FILES and not d.startswith('.')]
            for ana in ana_klasorler:
                ana_yol = os.path.join(out_dir, ana)
                alt_klasorler = [d for d in os.listdir(ana_yol) if os.path.isdir(os.path.join(ana_yol, d)) and d != "Copluk" and d not in HIDDEN_FILES and not d.startswith('.') and d not in zorluk_isimleri]
                yeni_yapi[ana] = alt_klasorler
        
        eski_data = yukle_json(DATA_FILE, {})
        for ana, altlar in eski_data.items():
            if ana in yeni_yapi:
                for alt in altlar:
                    if alt not in yeni_yapi[ana]: yeni_yapi[ana].append(alt)
            else: pass 
        
        self.data = yeni_yapi
        kaydet_json(DATA_FILE, self.data)

    def temizle(self):
        for w in self.root.winfo_children(): w.destroy()

    def geri(self, e=None):
        if self.stack:
            callback = self.stack.pop()
            if isinstance(callback, str):
                self.yol = callback
                self.liste_panel()
            elif callable(callback): callback()
        else: self.menu()

    def menu(self):
        self.yapiyi_guncelle()
        self.temizle()
        self.stack = [] 
        self.copluk_modu = False
        
        main_frame = tk.Frame(self.root, bg=BG_COLOR)
        main_frame.pack(expand=True)

        tk.Label(main_frame, text="SORU AYIKLAMA SİSTEMİ", font=("Helvetica", 28, "bold"), 
                 bg=BG_COLOR, fg=TEXT_DARK).pack(pady=(0, 40))
        
        btn_frame = tk.Frame(main_frame, bg=BG_COLOR)
        btn_frame.pack()

        self.create_btn(btn_frame, "▶ SORU İŞLEMEYE BAŞLA", self.basla_kontrol, SECONDARY_COLOR, width=35, height=2).pack(pady=10)
        self.create_btn(btn_frame, "📂 ÇIKTILARI İNCELE", lambda: self.klasor_gezin(self.settings["output_dir"]), "#95a5a6", fg=TEXT_DARK, width=35, height=2).pack(pady=10)
        self.create_btn(btn_frame, "🗑 ÇÖPLÜĞÜ İNCELE", self.copluk_ozel_menu, DANGER_COLOR, width=35, height=2).pack(pady=10)
        self.create_btn(btn_frame, "📊 İSTATİSTİKLER", self.istatistik_panel, SUCCESS_COLOR, width=35, height=2).pack(pady=10)
        self.create_btn(btn_frame, "⚙ AYARLAR", self.ayarlar_panel, "#7f8c8d", width=35, height=2).pack(pady=10)
        
        self.root.bind("<Escape>", lambda e: "break")

    def basla_kontrol(self):
        if not os.path.isdir(self.settings["input_dir"]) or not os.path.isdir(self.settings["output_dir"]):
            messagebox.showwarning("Eksik Ayar", "Lütfen ayarlar kısmından klasörleri tanımlayın."); return
        self.ana_konu_panel()

    def copluk_ozel_menu(self):
        self.temizle(); self.stack.append(self.menu); self.copluk_modu = True
        f = tk.Frame(self.root, bg=BG_COLOR); f.pack(expand=True)
        tk.Label(f, text="ÇÖPLÜK LİSTESİ", font=("Helvetica", 18, "bold"), bg=BG_COLOR, fg=TEXT_DARK).pack(pady=20)
        
        found = False
        for ana in sorted(self.data.keys()):
            path = os.path.join(self.settings["output_dir"], ana, "Copluk")
            if os.path.isdir(path):
                found = True
                self.create_btn(f, f"{ana.upper()} ÇÖPLÜĞÜ", lambda p=path: self.klasor_gezin(p), bg=DANGER_COLOR, width=40, height=2).pack(pady=5)
        
        if not found: tk.Label(f, text="Hiç çöp kaydı bulunamadı.", fg=TEXT_MUTED, bg=BG_COLOR).pack()
        self.create_btn(f, "ANA MENÜYE DÖN", self.menu, bg=PRIMARY_COLOR, width=20, height=1).pack(pady=30)
        self.root.bind("<Escape>", self.geri)

    def istatistik_panel(self):
        self.stack.append(self.menu); self.temizle()
        out_dir = self.settings["output_dir"]
        
        top_f = tk.Frame(self.root, bg=PRIMARY_COLOR, height=60)
        top_f.pack(fill="x")
        tk.Label(top_f, text="DETAYLI SORU İSTATİSTİKLERİ", font=("Helvetica", 16, "bold"), bg=PRIMARY_COLOR, fg="white").pack(pady=15)

        main_f = tk.Frame(self.root, bg=BG_COLOR); main_f.pack(fill="both", expand=True, padx=30, pady=20)
        canvas = tk.Canvas(main_f, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_f, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=BG_COLOR)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=1300)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")

        def dosya_say_zorluk(yol):
            """Count images directly in a folder (not recursive)"""
            if not os.path.isdir(yol): return 0
            count = 0
            for f in os.listdir(yol):
                if f.lower().endswith((".png", ".jpg", ".jpeg")) and os.path.isfile(os.path.join(yol, f)):
                    count += 1
            return count

        def zorluk_sayilari_hesapla(yol):
            """Recursively calculate difficulty counts from all subfolders"""
            sayilar = {z: 0 for z in ZORLUK_ISIMLERI}
            sayilar["copluk"] = 0
            
            if not os.path.isdir(yol): return sayilar
            
            for item in os.listdir(yol):
                if item.startswith('.') or item in HIDDEN_FILES: continue
                item_yol = os.path.join(yol, item)
                if not os.path.isdir(item_yol): continue
                
                if is_zorluk_folder(item):
                    # This is a difficulty folder, count images directly
                    sayilar[item.lower()] += dosya_say_zorluk(item_yol)
                elif item.lower() == "copluk":
                    # Count trash folder images
                    for root, dirs, files in os.walk(item_yol):
                        for f in files:
                            if f.lower().endswith((".png", ".jpg", ".jpeg")):
                                sayilar["copluk"] += 1
                else:
                    # Recurse into subfolders
                    alt_sayilar = zorluk_sayilari_hesapla(item_yol)
                    for z in sayilar:
                        sayilar[z] += alt_sayilar[z]
            
            return sayilar

        def klasor_agaci_olustur(parent_frame, yol, depth=0):
            """Recursively create folder tree with statistics"""
            if not os.path.isdir(yol): return
            
            subfolders = []
            for item in sorted(os.listdir(yol)):
                if item.startswith('.') or item in HIDDEN_FILES: continue
                item_yol = os.path.join(yol, item)
                if os.path.isdir(item_yol) and not is_zorluk_folder(item) and item.lower() != "copluk":
                    subfolders.append(item)
            
            for folder in subfolders:
                folder_yol = os.path.join(yol, folder)
                sayilar = zorluk_sayilari_hesapla(folder_yol)
                toplam = sum(sayilar[z] for z in ZORLUK_ISIMLERI)
                copluk = sayilar["copluk"]
                
                # Check if this folder has any non-difficulty subfolders
                has_child_folders = False
                for item in os.listdir(folder_yol):
                    if item.startswith('.') or item in HIDDEN_FILES: continue
                    item_yol = os.path.join(folder_yol, item)
                    if os.path.isdir(item_yol) and not is_zorluk_folder(item) and item.lower() != "copluk":
                        has_child_folders = True
                        break
                
                # Create card for this folder
                indent = depth * 20
                if depth == 0:
                    card_bg = "white"
                    font_size = 13
                    card = tk.Frame(parent_frame, bg=card_bg, pady=15, padx=15, bd=1, relief="flat")
                    card.pack(fill="x", pady=10, padx=(indent, 0))
                else:
                    card_bg = "#f8f9fa" if depth % 2 == 1 else "#fcfcfc"
                    font_size = 11 - min(depth, 2)
                    card = tk.Frame(parent_frame, bg=card_bg, pady=8, padx=10, bd=1, relief="groove")
                    card.pack(fill="x", pady=4, padx=(indent, 0))
                
                # Folder header with totals
                header_text = f"📁 {folder.upper()}" if depth == 0 else f"📂 {folder}"
                header_text += f" (Toplam: {toplam}"
                if copluk > 0:
                    header_text += f" | Çöplük: {copluk}"
                header_text += ")"
                
                tk.Label(card, text=header_text, font=("Helvetica", font_size, "bold"), 
                         bg=card_bg, fg=PRIMARY_COLOR if depth == 0 else TEXT_COLOR).pack(anchor="w", pady=(0, 5))
                
                # Difficulty counts
                zorluk_f = tk.Frame(card, bg="#edf2f7" if depth == 0 else card_bg, pady=3, padx=5)
                zorluk_f.pack(fill="x", pady=(0, 5))
                
                for z_ad in ZORLUKLAR.values():
                    sayi = sayilar[z_ad.lower()]
                    color = "#155724" if sayi > 0 else TEXT_MUTED  # Darker green for positive counts
                    tk.Label(zorluk_f, text=f"{z_ad}: {sayi}", font=("Arial", 9, "bold" if sayi > 0 else "normal"), 
                             fg=color, bg=zorluk_f.cget("bg"), padx=8).pack(side="left")
                
                # Only recursively add subfolders if this folder has child folders
                if has_child_folders:
                    klasor_agaci_olustur(card, folder_yol, depth + 1)

        # Start building the tree from output directory
        if os.path.isdir(out_dir):
            klasor_agaci_olustur(scrollable_frame, out_dir, 0)
        else:
            tk.Label(scrollable_frame, text="Çıktı klasörü bulunamadı!", font=("Helvetica", 14), 
                     fg=DANGER_COLOR, bg=BG_COLOR).pack(pady=50)

        self.create_btn(self.root, "GERİ DÖN", self.menu, bg=PRIMARY_COLOR, height=2).pack(side="bottom", fill="x")
        self.root.bind("<Escape>", self.geri)

    def ayarlar_panel(self):
        self.stack.append(self.menu); self.temizle()
        f = tk.Frame(self.root, bg=BG_COLOR); f.pack(expand=True)
        tk.Label(f, text="AYARLAR", font=("Helvetica", 18, "bold"), bg=BG_COLOR, fg=TEXT_DARK).pack(pady=20)
        
        def sec(key, lbl):
            p = filedialog.askdirectory()
            if p: 
                self.settings[key] = p
                kaydet_json(SETTINGS_FILE, self.settings)
                lbl.config(text=f"{p}")

        in_frame = tk.Frame(f, bg="white", padx=20, pady=15, bd=1, relief="solid")
        in_frame.pack(pady=10, fill="x")
        tk.Label(in_frame, text="Girdiler Klasörü (Ham Sorular):", font=("Arial", 10, "bold"), bg="white").pack(anchor="w")
        in_l = tk.Label(in_frame, text=self.settings.get('input_dir', "Seçilmedi"), fg=SECONDARY_COLOR, bg="white", wraplength=500)
        in_l.pack(pady=5)
        tk.Button(in_frame, text="Klasör Seç", command=lambda: sec("input_dir", in_l), fg=TEXT_DARK).pack()

        out_frame = tk.Frame(f, bg="white", padx=20, pady=15, bd=1, relief="solid")
        out_frame.pack(pady=10, fill="x")
        tk.Label(out_frame, text="Çıktılar Klasörü (Ayıklananlar):", font=("Arial", 10, "bold"), bg="white").pack(anchor="w")
        out_l = tk.Label(out_frame, text=self.settings.get('output_dir', "Seçilmedi"), fg=SUCCESS_COLOR, bg="white", wraplength=500)
        out_l.pack(pady=5)
        self.create_btn(out_frame, "Klasör Seç", lambda: sec("output_dir", out_l)).pack()

        self.create_btn(f, "ANA MENÜ", self.menu, bg=PRIMARY_COLOR, width=20, height=1).pack(pady=30)
        self.root.bind("<Escape>", self.geri)

    def ana_konu_panel(self, current_yol=None):
        if not current_yol:
            self.stack.append(self.menu)
            current_yol = self.settings["output_dir"]
        self.temizle()
        self.yol = current_yol
        
        f = tk.Frame(self.root, bg=BG_COLOR); f.pack(expand=True)
        tk.Label(f, text="KATEGORİ YÖNETİMİ", font=("Helvetica", 18, "bold"), bg=BG_COLOR, fg=TEXT_DARK).pack(pady=10)
        tk.Label(f, text=f"DİZİN: {os.path.basename(self.yol)}", font=("Arial", 10), bg=BG_COLOR, fg=TEXT_MUTED).pack()
        
        btn_f = tk.Frame(f, bg=BG_COLOR); btn_f.pack(pady=10)
        if self.yol != self.settings["output_dir"]:
            up_path = os.path.dirname(self.yol)
            self.create_btn(btn_f, "⬅ ÜST DİZİN", lambda p=up_path: self.ana_konu_panel(p), bg=ACCENT_COLOR, width=15).pack(side="left", padx=5)

        entry = tk.Entry(f, font=("Arial", 14), width=35, bg="white", fg=TEXT_DARK, insertbackground=TEXT_DARK)
        entry.pack(pady=5); entry.focus_set()
        
        def ekle(e=None):
            t = entry.get().strip()
            if t:
                new_p = os.path.join(self.yol, t)
                if not os.path.exists(new_p):
                    os.makedirs(new_p, exist_ok=True); self.yapiyi_guncelle(); self.ana_konu_panel(self.yol)
        
        entry.bind("<Return>", ekle)
        self.create_btn(f, "YENİ KLASÖR EKLE", ekle, SUCCESS_COLOR, width=20).pack(pady=5)
        
        liste = tk.Listbox(f, font=("Arial", 12), width=55, height=12, bg="white", fg=TEXT_DARK, 
                           highlightthickness=1, highlightbackground="#ccc"); liste.pack(pady=10)
        
        folders = []
        if os.path.exists(self.yol):
            folders = [d for d in os.listdir(self.yol) if os.path.isdir(os.path.join(self.yol, d)) 
                       and d not in HIDDEN_FILES and not d.startswith('.') and not is_zorluk_folder(d)]
            for k in sorted(folders): liste.insert(tk.END, k)
        
        def enter_folder():
            if not liste.curselection(): return
            sel = liste.get(liste.curselection())
            self.ana_konu_panel(os.path.join(self.yol, sel))

        self.create_btn(f, "İÇERİ GİR (ÇİFT TIKLA)", enter_folder, SECONDARY_COLOR, width=25).pack(pady=2)
        self.create_btn(f, "AYIKLAMAYA BAŞLA (BU KONU)", lambda: self.hizli_basla(), SUCCESS_COLOR, width=25).pack(pady=2)
        self.create_btn(f, "BU KLASÖRÜ SİL", lambda: self.silme(self.yol), DANGER_COLOR, width=25).pack(pady=2)
        
        tk.Label(f, text="İsim düzenlemek için bilgisayarınızın\ndosya yöneticisini kullanabilirsiniz.", font=("Arial", 8), bg=BG_COLOR, fg=TEXT_MUTED).pack(pady=5)
        
        liste.bind("<Double-Button-1>", lambda e: enter_folder())
        self.create_btn(f, "ANA MENÜ", self.menu, PRIMARY_COLOR, width=15).pack(pady=10)
        self.root.bind("<Escape>", self.geri); self.root.update_idletasks()

    def hizli_basla(self):
        # Determine ana_konu and sub-path from current folder (yol)
        rel = os.path.relpath(self.yol, self.settings["output_dir"])
        if rel == ".": 
            messagebox.showwarning("Uyarı", "Lütfen bir ana kategori seçin (Üst dizinde işlem yapılamaz).")
            return
        
        parts = rel.split(os.sep)
        self.ana_konu = parts[0]
        # Rest of the path becomes the starting subpath (relative to ana_konu)
        self.secili_alt = os.path.join(*parts[1:]) if len(parts) > 1 else ""
        self.soru_panel()

    def silme(self, yol):
        if not yol or yol == self.settings["output_dir"]: return
        if messagebox.askyesno("Onay", f"'{os.path.basename(yol)}' ve içindeki her şey silinsin mi?"):
            try:
                shutil.rmtree(yol); self.yapiyi_guncelle(); self.ana_konu_panel(os.path.dirname(yol))
            except Exception as e:
                messagebox.showerror("Hata", f"Silinemedi: {e}")

    def soru_panel(self):
        # Allow returning to the specific category folder we started from
        self.stack.append(lambda: self.ana_konu_panel(os.path.join(self.settings["output_dir"], self.ana_konu, os.path.dirname(self.secili_alt or "")))); self.temizle()
        input_dir = self.settings["input_dir"]
        self.gorseller = []
        for root, dirs, files in os.walk(input_dir):
            for f in files:
                if f.lower().endswith((".png", ".jpg", ".jpeg")) and f not in HIDDEN_FILES:
                    # Store relative path to handle move correctly
                    rel_path = os.path.relpath(os.path.join(root, f), input_dir)
                    self.gorseller.append(rel_path)
        
        if not self.gorseller:
            tk.Label(self.root, text="🎉 Klasörde görsel kalmadı!", font=("Helvetica", 22, "bold"), fg=SUCCESS_COLOR, bg=BG_COLOR).pack(expand=True)
            self.create_btn(self.root, "ANA MENÜYE DÖN", self.menu, bg=SECONDARY_COLOR, width=30, height=2).pack(pady=40)
            return

        top_panel = tk.Frame(self.root, bg=BG_COLOR, pady=10)
        top_panel.pack(fill="x")
        self.create_btn(top_panel, "🏠 ANA MENÜ", self.menu, bg=ACCENT_COLOR, width=12).pack(side="left", padx=20)
        tk.Label(top_panel, text=f"Soru İşleniyor: {self.ana_konu}", font=("Arial", 10, "bold"), bg=BG_COLOR, fg=TEXT_DARK).pack(side="left")

        ana_f = tk.Frame(self.root, bg=BG_COLOR); ana_f.pack(fill="both", expand=True)
        sol = tk.Frame(ana_f, bg=BG_COLOR); sol.pack(side="left", expand=True, fill="both")
        sag = tk.Frame(ana_f, width=380, bg="white", padx=20); sag.pack(side="right", fill="y")
        
        self.img_label = tk.Label(sol, bg=BG_COLOR); self.img_label.pack(pady=20, expand=True)
        
        tk.Label(sag, text="ALT KONU SEÇİMİ (AĞAÇ)", font=("Helvetica", 11, "bold"), bg="white").pack(pady=15)
        
        tree_f = tk.Frame(sag, bg="white")
        tree_f.pack(fill="both", expand=True)
        
        self.tree = ttk.Treeview(tree_f, show="tree", selectmode="browse")
        self.tree.pack(side="left", fill="both", expand=True)
        
        ysb = ttk.Scrollbar(tree_f, orient="vertical", command=self.tree.yview)
        ysb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=ysb.set)
        
        # Populate Tree recursively
        self.tree_map = {}
        ana_yol = os.path.abspath(os.path.join(self.settings["output_dir"], self.ana_konu))
        os.makedirs(ana_yol, exist_ok=True)
        self.populate_tree("", ana_yol)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Show current selection if coming from hizli_basla
        lbl_txt = "Lütfen bir alt konu seçin"
        lbl_fg = DANGER_COLOR
        if self.secili_alt:
            lbl_txt = f"HEDEF: {os.path.basename(self.secili_alt)}"
            lbl_fg = SUCCESS_COLOR
            # Try to find and select the node in the tree
            for node, full_p in self.tree_map.items():
                # Compare absolute paths for reliability
                if os.path.abspath(full_p) == os.path.abspath(os.path.join(ana_yol, self.secili_alt)):
                    self.tree.selection_set(node)
                    self.tree.see(node)
                    break

        self.secili_lbl = tk.Label(sag, text=lbl_txt, fg=lbl_fg, bg="white", font=("Arial", 10, "bold")); self.secili_lbl.pack(pady=10)

        for k, v in ZORLUKLAR.items():
            self.create_btn(sag, f"[{k}] {v}", lambda z=v: self.kaydet(z), bg="#ecf0f1", width=35).pack(pady=2)
        
        self.create_btn(sag, "ÇÖP (X)", lambda: self.kaydet("Copluk"), bg="#fab1a0", fg="#d63031", width=35, height=2).pack(pady=30)
        self.root.bind("<Key>", self.tuslar); self.goster(); self.root.bind("<Escape>", self.geri)

    def populate_tree(self, parent_node, path):
        zorluk_isimleri = {z.lower().strip() for z in ZORLUKLAR.values()}
        try:
            with os.scandir(path) as it:
                # Filter and sort folders
                entries = []
                for entry in it:
                    if entry.name.startswith('.') or entry.name in HIDDEN_FILES: continue
                    if entry.name.lower() == "copluk": continue
                    if entry.name.lower() in zorluk_isimleri: continue
                    if entry.is_dir():
                        entries.append(entry)
                
                entries.sort(key=lambda e: e.name.lower())
                
                for entry in entries:
                    full_p = os.path.abspath(entry.path)
                    base_ana = os.path.abspath(os.path.join(self.settings["output_dir"], self.ana_konu))
                    rel_p = os.path.relpath(full_p, base_ana)
                    
                    # Create node and store ABSOLUTE path in map
                    node = self.tree.insert(parent_node, "end", text=f"📁 {entry.name}", open=True)
                    self.tree_map[node] = full_p 
                    
                    # Recurse
                    self.populate_tree(node, full_p)
        except Exception as e:
            print(f"Tree error at {path}: {e}")

    def on_tree_select(self, event):
        sel = self.tree.selection()
        if sel:
            full_path = self.tree_map.get(sel[0])
            if full_path:
                base_ana = os.path.abspath(os.path.join(self.settings["output_dir"], self.ana_konu))
                self.secili_alt = os.path.relpath(full_path, base_ana)
                display_name = os.path.basename(full_path)
                self.secili_lbl.config(text=f"HEDEF: {display_name}", fg=SUCCESS_COLOR)
                self.root.update_idletasks()

    def goster(self):
        if self.gorseller:
            # Short delay to ensure UI geometry is calculated accurately
            self.root.after(50, self._goster_actual)

    def _goster_actual(self):
        if not self.gorseller: return
        try:
            p = os.path.join(self.settings["input_dir"], self.gorseller[0])
            img = Image.open(p)
            
            # Dynamic scaling based on the available space
            self.root.update_idletasks()
            avail_w = max(self.root.winfo_width() - 420, 800)
            avail_h = max(self.root.winfo_height() - 100, 600)
            
            w, h = img.size
            ratio = min(avail_w/w, avail_h/h)
            
            new_w, new_h = int(w*ratio), int(h*ratio)
            if new_w > 0 and new_h > 0:
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                self.tkimg = ImageTk.PhotoImage(img)
                self.img_label.config(image=self.tkimg)
        except Exception as e:
            print(f"Goster error: {e}")

    def tuslar(self, e):
        c = e.char.lower()
        if c in ZORLUKLAR: self.kaydet(ZORLUKLAR[c])
        elif c == 'x': self.kaydet("Copluk")

    def kaydet(self, zorluk):
        if not self.gorseller: return
        if zorluk != "Copluk" and not self.secili_alt:
            messagebox.showwarning("Uyarı", "Önce bir Alt Konu seçin!"); return
        
        rel_path = self.gorseller[0]
        src = os.path.join(self.settings["input_dir"], rel_path)
        file_name = os.path.basename(rel_path)
        
        if zorluk == "Copluk":
            dst = os.path.join(self.settings["output_dir"], self.ana_konu, "Copluk")
        else:
            dst = os.path.join(self.settings["output_dir"], self.ana_konu, self.secili_alt, zorluk)
            
        try:
            os.makedirs(dst, exist_ok=True)
            shutil.move(src, os.path.join(dst, file_name))
            # Keep self.secili_alt persistent
            self.soru_panel()
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydedilemedi: {e}")

    def klasor_gezin(self, h):
        if not h:
            messagebox.showwarning("Uyarı", "Lütfen önce Ayarlar'dan çıktı klasörünü seçin.")
            return
        if not os.path.isdir(h):
            messagebox.showwarning("Uyarı", f"Klasör bulunamadı: {h}")
            return
        self.yol = h
        # Only add Menu to stack if navigating from a different section
        if not self.stack or (callable(self.stack[-1]) and self.stack[-1] != self.menu):
            self.stack.append(self.menu)
        self.liste_panel()

    def liste_panel(self, recursive=False):
        self.temizle()
        top = tk.Frame(self.root, bg=PRIMARY_COLOR, pady=10)
        top.pack(fill="x")
        self.create_btn(top, "🏠 ANA MENÜ", self.menu, bg=ACCENT_COLOR, width=12).pack(side="left", padx=10)
        self.create_btn(top, "⬅ GERİ GİT", self.geri, bg="#95a5a6", width=12).pack(side="left")
        
        # Recursive Toggle
        rec_text = "🔄 TÜMÜNÜ GÖSTER (AÇIK)" if recursive else "📂 KLASÖR GÖRÜNÜMÜ"
        self.create_btn(top, rec_text, lambda: self.liste_panel(not recursive), bg=SECONDARY_COLOR, width=20).pack(side="left", padx=10)
        
        tk.Label(top, text=f"KONUM: {self.yol}", fg="white", bg=PRIMARY_COLOR, font=("Courier", 9)).pack(side="left", padx=20)

        orta = tk.Frame(self.root, bg=BG_COLOR); orta.pack(fill="both", expand=True)
        liste_f = tk.Frame(orta, bg="white", padx=10, pady=10); liste_f.pack(side="left", fill="y")
        self.preview = tk.Label(orta, bg=BG_COLOR, text="Önizleme"); self.preview.pack(side="right", expand=True)

        liste = tk.Listbox(liste_f, font=("Arial", 11), width=45, height=30, bg="white", fg=TEXT_DARK,
                           highlightthickness=1, highlightbackground="#ccc"); liste.pack()
        
        self.yol_map = {} # To store full paths for recursive view
        
        if recursive:
            for root, dirs, files in os.walk(self.yol):
                for f in sorted(files):
                    if f.lower().endswith((".png", ".jpg", ".jpeg")) and f not in HIDDEN_FILES:
                        full_p = os.path.join(root, f)
                        display_n = os.path.relpath(full_p, self.yol)
                        liste.insert(tk.END, display_n)
                        self.yol_map[display_n] = full_p
        elif os.path.exists(self.yol):
            for i in sorted(os.listdir(self.yol)):
                if i not in HIDDEN_FILES and not i.startswith('.'):
                    liste.insert(tk.END, i)
                    self.yol_map[i] = os.path.join(self.yol, i)

        def on_select(e):
            if not liste.curselection(): return
            p = self.yol_map.get(liste.get(liste.curselection()))
            if p and os.path.isfile(p) and p.lower().endswith((".png", ".jpg", ".jpeg")):
                img = Image.open(p); img.thumbnail((750, 750)); self.tkp = ImageTk.PhotoImage(img)
                self.preview.config(image=self.tkp, text="")

        self.create_btn(liste_f, "Seçiliyi Girdilere Geri Yükle", lambda: self.geri_yukle(liste, recursive), bg="#ffeaa7", width=35, height=2).pack(pady=10)
        liste.bind("<<ListboxSelect>>", on_select); liste.bind("<Double-Button-1>", lambda e: self.ac(liste, recursive))
        self.root.bind("<Escape>", self.geri); self.root.update_idletasks()

    def geri_yukle(self, liste, recursive):
        if not liste.curselection(): return
        sec = liste.get(liste.curselection())
        p = self.yol_map.get(sec)
        
        if p and os.path.isfile(p):
            file_name = os.path.basename(p)
            shutil.move(p, os.path.join(self.settings["input_dir"], file_name))
            
            # Clean up empty folders except base ones
            curr = os.path.dirname(p)
            while curr != self.settings["output_dir"] and len(curr) > len(self.settings["output_dir"]):
                if os.path.isdir(curr) and not os.listdir(curr):
                    os.rmdir(curr); curr = os.path.dirname(curr)
                else: break
            self.liste_panel(recursive)

    def ac(self, liste, recursive):
        if not liste.curselection(): return
        sec = liste.get(liste.curselection())
        yeni = self.yol_map.get(sec)
        if yeni and os.path.isdir(yeni):
            # Save parent path as string for robust back-navigation
            self.stack.append(self.yol)
            self.yol = yeni
            self.liste_panel(recursive)

if __name__ == "__main__":
    root = tk.Tk(); App(root); root.mainloop()
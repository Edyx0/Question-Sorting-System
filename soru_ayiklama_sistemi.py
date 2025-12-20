import os, shutil, json
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk
from PIL import Image, ImageTk

DATA_FILE = "data.json"
SETTINGS_FILE = "settings.json"

BG_COLOR = "#f4f7f6"
PRIMARY_COLOR = "#2c3e50"
SECONDARY_COLOR = "#3498db"
SUCCESS_COLOR = "#2ecc71"
DANGER_COLOR = "#e74c3c"
ACCENT_COLOR = "#f1c40f"

ZORLUKLAR = {
    "1": "Çok Kolay",
    "2": "Kolay",
    "3": "Orta",
    "4": "Zor",
    "5": "Çok Zor"
}

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

        self.settings = yukle_json(SETTINGS_FILE, {"input_dir": "Seçilmedi", "output_dir": "Seçilmedi"})
        self.data = yukle_json(DATA_FILE, {})

        self.settings = yukle_json(SETTINGS_FILE, {"input_dir": "", "output_dir": ""})
        self.data = {}
        self.yapiyi_guncelle()

        self.stack = [] 
        self.secili_alt = None
        self.alt_butonlar_listesi = {}
        self.ana_konu = None
        self.yol = "" 
        self.gorseller = []
        self.copluk_modu = False 

        self.menu()

    def yapiyi_guncelle(self):
        out_dir = self.settings.get("output_dir", "")
        if not out_dir or not os.path.isdir(out_dir):
            self.data = yukle_json(DATA_FILE, {})
            return
        yeni_yapi = {}
        if os.path.exists(out_dir):
            ana_klasorler = [d for d in os.listdir(out_dir) if os.path.isdir(os.path.join(out_dir, d))]
            for ana in ana_klasorler:
                ana_yol = os.path.join(out_dir, ana)
                alt_klasorler = [d for d in os.listdir(ana_yol) if os.path.isdir(os.path.join(ana_yol, d)) and d != "Copluk"]
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
                 bg=BG_COLOR, fg=PRIMARY_COLOR).pack(pady=(0, 40))
        
        btn_frame = tk.Frame(main_frame, bg=BG_COLOR)
        btn_frame.pack()

        def create_btn(txt, cmd, color):
            return tk.Button(btn_frame, text=txt, command=cmd, width=35, height=2, 
                             bg=color, fg="white", font=("Helvetica", 11, "bold"),
                             relief="flat", cursor="hand2")

        create_btn("▶ SORU İŞLEMEYE BAŞLA", self.basla_kontrol, SECONDARY_COLOR).pack(pady=10)
        create_btn("📂 ÇIKTILARI İNCELE", lambda: self.klasor_gezin(self.settings["output_dir"]), "#34495e").pack(pady=10)
        create_btn("🗑 ÇÖPLÜĞÜ İNCELE", self.copluk_ozel_menu, DANGER_COLOR).pack(pady=10)
        create_btn("📊 İSTATİSTİKLER", self.istatistik_panel, SUCCESS_COLOR).pack(pady=10)
        create_btn("⚙ AYARLAR", self.ayarlar_panel, "#7f8c8d").pack(pady=10)
        
        self.root.bind("<Escape>", lambda e: "break")

    def basla_kontrol(self):
        if not os.path.isdir(self.settings["input_dir"]) or not os.path.isdir(self.settings["output_dir"]):
            messagebox.showwarning("Eksik Ayar", "Lütfen ayarlar kısmından klasörleri tanımlayın."); return
        self.ana_konu_panel()

    def copluk_ozel_menu(self):
        self.temizle(); self.stack.append(self.menu); self.copluk_modu = True
        f = tk.Frame(self.root, bg=BG_COLOR); f.pack(expand=True)
        tk.Label(f, text="ÇÖPLÜK LİSTESİ", font=("Helvetica", 18, "bold"), bg=BG_COLOR).pack(pady=20)
        
        found = False
        for ana in sorted(self.data.keys()):
            path = os.path.join(self.settings["output_dir"], ana, "Copluk")
            if os.path.isdir(path):
                found = True
                tk.Button(f, text=f"{ana.upper()} ÇÖPLÜĞÜ", width=40, height=2, bg=DANGER_COLOR, fg="white",
                          command=lambda p=path: self.klasor_gezin(p)).pack(pady=5)
        
        if not found: tk.Label(f, text="Hiç çöp kaydı bulunamadı.", fg="gray", bg=BG_COLOR).pack()
        tk.Button(f, text="ANA MENÜYE DÖN", command=self.menu, bg=PRIMARY_COLOR, fg="white", width=20).pack(pady=30)
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

        def dosya_say(yol):
            if not os.path.isdir(yol): return 0
            count = 0
            for root, dirs, files in os.walk(yol):
                for f in files:
                    if f.lower().endswith((".png", ".jpg", ".jpeg")): count += 1
            return count

        for ana in sorted(self.data.keys()):
            ana_yol = os.path.join(out_dir, ana)
            card = tk.Frame(scrollable_frame, bg="white", pady=15, padx=15, bd=1, relief="flat")
            card.pack(fill="x", pady=10)
            
            copluk_sayisi = dosya_say(os.path.join(ana_yol, "Copluk"))
            ana_toplam = dosya_say(ana_yol) - copluk_sayisi
            
            tk.Label(card, text=f"ANA KONU: {ana.upper()} (Soru Sayısı: {ana_toplam} | Çöplük: {copluk_sayisi})", 
                     font=("Helvetica", 13, "bold"), bg="white", fg=PRIMARY_COLOR).pack(anchor="w", pady=(0, 5))

            ana_zorluk_ozet = tk.Frame(card, bg="#edf2f7", pady=5, padx=10)
            ana_zorluk_ozet.pack(fill="x", pady=(0, 10))
            tk.Label(ana_zorluk_ozet, text="Grup Genel Zorluk Toplamları:", font=("Arial", 9, "bold"), bg="#edf2f7").pack(side="left", padx=(0,10))
            
            for z_ad in ZORLUKLAR.values():
                ana_z_sayi = 0
                for alt in self.data[ana]:
                    ana_z_sayi += dosya_say(os.path.join(ana_yol, alt, z_ad))
                tk.Label(ana_zorluk_ozet, text=f"{z_ad}: {ana_z_sayi}", font=("Arial", 9), 
                         fg=SUCCESS_COLOR if ana_z_sayi > 0 else "#718096", bg="#edf2f7", padx=10).pack(side="left")

            for alt in sorted(self.data[ana]):
                alt_yol = os.path.join(ana_yol, alt)
                alt_toplam = dosya_say(alt_yol)
                
                alt_card = tk.Frame(card, bg="#fcfcfc", pady=8, padx=10, bd=1, relief="groove")
                alt_card.pack(fill="x", pady=4)
                
                tk.Label(alt_card, text=f"ALT KONU: {alt} (Toplam: {alt_toplam})", font=("Arial", 10, "bold"), bg="#fcfcfc", anchor="w").pack(fill="x")
                
                zorluk_f = tk.Frame(alt_card, bg="#fcfcfc")
                zorluk_f.pack(fill="x", pady=(5, 0))
                
                for z_ad in ZORLUKLAR.values():
                    sayi = dosya_say(os.path.join(alt_yol, z_ad))
                    color = SECONDARY_COLOR if sayi > 0 else "#bdc3c7"
                    tk.Label(zorluk_f, text=f"{z_ad}: {sayi}", font=("Arial", 9), fg=color, bg="#fcfcfc", padx=15).pack(side="left")

        tk.Button(self.root, text="GERİ DÖN", command=self.menu, bg=PRIMARY_COLOR, fg="white", pady=10).pack(side="bottom", fill="x")
        self.root.bind("<Escape>", self.geri)

    def ayarlar_panel(self):
        self.stack.append(self.menu); self.temizle()
        f = tk.Frame(self.root, bg=BG_COLOR); f.pack(expand=True)
        tk.Label(f, text="AYARLAR", font=("Helvetica", 18, "bold"), bg=BG_COLOR).pack(pady=20)
        
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
        tk.Button(in_frame, text="Klasör Seç", command=lambda: sec("input_dir", in_l)).pack()

        out_frame = tk.Frame(f, bg="white", padx=20, pady=15, bd=1, relief="solid")
        out_frame.pack(pady=10, fill="x")
        tk.Label(out_frame, text="Çıktılar Klasörü (Ayıklananlar):", font=("Arial", 10, "bold"), bg="white").pack(anchor="w")
        out_l = tk.Label(out_frame, text=self.settings.get('output_dir', "Seçilmedi"), fg=SUCCESS_COLOR, bg="white", wraplength=500)
        out_l.pack(pady=5)
        tk.Button(out_frame, text="Klasör Seç", command=lambda: sec("output_dir", out_l)).pack()

        tk.Button(f, text="ANA MENÜ", command=self.menu, bg=PRIMARY_COLOR, fg="white", width=20, pady=10).pack(pady=30)
        self.root.bind("<Escape>", self.geri)

    def ana_konu_panel(self):
        self.stack.append(self.menu); self.temizle()
        f = tk.Frame(self.root, bg=BG_COLOR); f.pack(expand=True)
        tk.Label(f, text="ANA KATEGORİLER", font=("Helvetica", 18, "bold"), bg=BG_COLOR).pack(pady=20)
        entry = tk.Entry(f, font=("Arial", 14), width=35); entry.pack()
        def ekle(e=None):
            t = entry.get().strip()
            if t and t not in self.data:
                self.data[t] = []; kaydet_json(DATA_FILE, self.data); self.ana_konu_panel()
        entry.bind("<Return>", ekle)
        tk.Button(f, text="KATEGORİ EKLE", bg=SUCCESS_COLOR, fg="white", command=ekle).pack(pady=10)
        liste = tk.Listbox(f, font=("Arial", 12), width=50, height=12); liste.pack(pady=10)
        for k in sorted(self.data.keys()): liste.insert(tk.END, k)
        tk.Button(f, text="İSMİ DÜZENLE", bg=SECONDARY_COLOR, fg="white", command=lambda: self.isim_degistir(liste, "ana")).pack(pady=2)
        tk.Button(f, text="SİL", bg=DANGER_COLOR, fg="white", command=lambda: self.silme(liste, "ana")).pack(pady=2)
        liste.bind("<Double-Button-1>", lambda e: self.alt_konu_panel(liste.get(liste.curselection())))
        tk.Button(f, text="GERİ", command=self.menu).pack(pady=10); self.root.bind("<Escape>", self.geri)

    def alt_konu_panel(self, ana):
        self.stack.append(self.ana_konu_panel); self.temizle(); self.ana_konu = ana
        f = tk.Frame(self.root, bg=BG_COLOR); f.pack(expand=True)
        tk.Label(f, text=f"ALT KONULAR: {ana}", font=("Helvetica", 18, "bold"), bg=BG_COLOR).pack(pady=20)
        entry = tk.Entry(f, font=("Arial", 14), width=35); entry.pack()
        def ekle(e=None):
            t = entry.get().strip()
            if t and t not in self.data[ana]:
                self.data[ana].append(t); kaydet_json(DATA_FILE, self.data); self.alt_konu_panel(ana)
        entry.bind("<Return>", ekle)
        tk.Button(f, text="ALT KONU EKLE", bg=SUCCESS_COLOR, fg="white", command=ekle).pack(pady=10)
        liste = tk.Listbox(f, font=("Arial", 12), width=50, height=12); liste.pack(pady=10)
        for k in sorted(self.data[ana]): liste.insert(tk.END, k)
        tk.Button(f, text="İSMİ DÜZENLE", bg=SECONDARY_COLOR, fg="white", command=lambda: self.isim_degistir(liste, "alt")).pack(pady=2)
        tk.Button(f, text="SİL", bg=DANGER_COLOR, fg="white", command=lambda: self.silme(liste, "alt")).pack(pady=2)
        tk.Button(f, text="AYIKLAMAYA BAŞLA >>>", bg=SUCCESS_COLOR, fg="white", font=("Arial", 12, "bold"), command=self.soru_panel, pady=10).pack(pady=20)
        tk.Button(f, text="GERİ", command=self.geri).pack(); self.root.bind("<Escape>", self.geri)

    def isim_degistir(self, liste, tip):
        if not liste.curselection(): return
        eski = liste.get(liste.curselection())
        yeni = simpledialog.askstring("Düzenle", f"Yeni {tip} ismi:", initialvalue=eski)
        if yeni and yeni != eski:
            if tip == "ana":
                ey, yy = os.path.join(self.settings["output_dir"], eski), os.path.join(self.settings["output_dir"], yeni)
                if os.path.isdir(ey): os.rename(ey, yy)
                self.data[yeni] = self.data.pop(eski); self.ana_konu_panel()
            else:
                ey, yy = os.path.join(self.settings["output_dir"], self.ana_konu, eski), os.path.join(self.settings["output_dir"], self.ana_konu, yeni)
                if os.path.isdir(ey): os.rename(ey, yy)
                idx = self.data[self.ana_konu].index(eski); self.data[self.ana_konu][idx] = yeni; self.alt_konu_panel(self.ana_konu)
            kaydet_json(DATA_FILE, self.data)

    def silme(self, liste, tip):
        if not liste.curselection(): return
        sec = liste.get(liste.curselection())
        if messagebox.askyesno("Onay", f"'{sec}' silinsin mi?"):
            if tip == "ana": self.data.pop(sec); self.ana_konu_panel()
            else: self.data[self.ana_konu].remove(sec); self.alt_konu_panel(self.ana_konu)
            kaydet_json(DATA_FILE, self.data)

    def soru_panel(self):
        self.stack.append(lambda: self.alt_konu_panel(self.ana_konu)); self.temizle()
        self.gorseller = [f for f in os.listdir(self.settings["input_dir"]) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        
        if not self.gorseller:
            tk.Label(self.root, text="🎉 Klasörde görsel kalmadı!", font=("Helvetica", 22, "bold"), fg=SUCCESS_COLOR, bg=BG_COLOR).pack(expand=True)
            tk.Button(self.root, text="ANA MENÜYE DÖN", bg=SECONDARY_COLOR, fg="white", command=self.menu, width=30, pady=10).pack(pady=40)
            return

        top_panel = tk.Frame(self.root, bg=BG_COLOR, pady=10)
        top_panel.pack(fill="x")
        tk.Button(top_panel, text="🏠 ANA MENÜ", command=self.menu, bg=ACCENT_COLOR, font=("Arial", 9, "bold")).pack(side="left", padx=20)
        tk.Label(top_panel, text=f"Soru İşleniyor: {self.ana_konu}", font=("Arial", 10, "bold"), bg=BG_COLOR).pack(side="left")

        ana_f = tk.Frame(self.root, bg=BG_COLOR); ana_f.pack(fill="both", expand=True)
        sol = tk.Frame(ana_f, bg=BG_COLOR); sol.pack(side="left", expand=True, fill="both")
        sag = tk.Frame(ana_f, width=380, bg="white", padx=20); sag.pack(side="right", fill="y")
        
        self.img_label = tk.Label(sol, bg=BG_COLOR); self.img_label.pack(pady=20, expand=True)
        
        tk.Label(sag, text="ALT KONU SEÇİMİ", font=("Helvetica", 11, "bold"), bg="white").pack(pady=15)
        self.alt_butonlar_listesi = {}
        for alt in self.data[self.ana_konu]:
            btn = tk.Button(sag, text=alt, width=35, bg=BG_COLOR, command=lambda a=alt: self.alt_sec(a))
            btn.pack(pady=2); self.alt_butonlar_listesi[alt] = btn

        self.secili_lbl = tk.Label(sag, text="Lütfen bir alt konu seçin", fg=DANGER_COLOR, bg="white", font=("Arial", 10, "bold")); self.secili_lbl.pack(pady=10)

        for k, v in ZORLUKLAR.items():
            tk.Button(sag, text=f"[{k}] {v}", width=35, bg="#ecf0f1", command=lambda z=v: self.kaydet(z)).pack(pady=2)
        
        tk.Button(sag, text="ÇÖP (X)", bg="#fab1a0", fg="#d63031", width=35, pady=10, command=lambda: self.kaydet("Copluk")).pack(pady=30)
        self.root.bind("<Key>", self.tuslar); self.goster(); self.root.bind("<Escape>", self.geri)

    def alt_sec(self, alt):
        for b in self.alt_butonlar_listesi.values(): b.config(bg=BG_COLOR, fg="black")
        self.secili_alt = alt; self.alt_butonlar_listesi[alt].config(bg=SUCCESS_COLOR, fg="white")
        self.secili_lbl.config(text=f"SEÇİLDİ: {alt}", fg=SUCCESS_COLOR)

    def goster(self):
        if self.gorseller:
            p = os.path.join(self.settings["input_dir"], self.gorseller[0])
            img = Image.open(p)
            w, h = img.size; ratio = min(950/w, 750/h)
            img = img.resize((int(w*ratio), int(h*ratio)), Image.Resampling.LANCZOS)
            self.tkimg = ImageTk.PhotoImage(img); self.img_label.config(image=self.tkimg)

    def tuslar(self, e):
        c = e.char.lower()
        if c in ZORLUKLAR: self.kaydet(ZORLUKLAR[c])
        elif c == 'x': self.kaydet("Copluk")

    def kaydet(self, zorluk):
        if not self.gorseller: return
        if zorluk != "Copluk" and not self.secili_alt:
            messagebox.showwarning("Uyarı", "Önce bir Alt Konu seçin!"); return
        
        src = os.path.join(self.settings["input_dir"], self.gorseller[0])
        if zorluk == "Copluk":
            dst = os.path.join(self.settings["output_dir"], self.ana_konu, "Copluk")
        else:
            dst = os.path.join(self.settings["output_dir"], self.ana_konu, self.secili_alt, zorluk)
            
        os.makedirs(dst, exist_ok=True); shutil.move(src, os.path.join(dst, self.gorseller[0]))
        self.secili_alt = None; self.soru_panel()

    def klasor_gezin(self, h):
        if h and os.path.isdir(h): self.yol = h; self.liste_panel()

    def liste_panel(self):
        self.temizle()
        top = tk.Frame(self.root, bg=PRIMARY_COLOR, pady=10)
        top.pack(fill="x")
        tk.Button(top, text="🏠 ANA MENÜ", command=self.menu, bg=ACCENT_COLOR, font=("Arial", 9, "bold")).pack(side="left", padx=10)
        tk.Button(top, text="⬅ GERİ GİT", command=self.geri, bg="#95a5a6", fg="white").pack(side="left")
        tk.Label(top, text=f"KONUM: {self.yol}", fg="white", bg=PRIMARY_COLOR, font=("Courier", 9)).pack(side="left", padx=20)

        orta = tk.Frame(self.root, bg=BG_COLOR); orta.pack(fill="both", expand=True)
        liste_f = tk.Frame(orta, bg="white", padx=10, pady=10); liste_f.pack(side="left", fill="y")
        self.preview = tk.Label(orta, bg=BG_COLOR, text="Önizleme"); self.preview.pack(side="right", expand=True)

        liste = tk.Listbox(liste_f, font=("Arial", 11), width=45, height=30); liste.pack()
        if os.path.exists(self.yol):
            for i in sorted(os.listdir(self.yol)): liste.insert(tk.END, i)

        def on_select(e):
            if not liste.curselection(): return
            p = os.path.join(self.yol, liste.get(liste.curselection()))
            if os.path.isfile(p) and p.lower().endswith((".png", ".jpg", ".jpeg")):
                img = Image.open(p); img.thumbnail((750, 750)); self.tkp = ImageTk.PhotoImage(img)
                self.preview.config(image=self.tkp, text="")

        tk.Button(liste_f, text="Seçiliyi Girdilere Geri Yükle", bg="#ffeaa7", command=lambda: self.geri_yukle(liste), width=35, pady=10).pack(pady=10)
        liste.bind("<<ListboxSelect>>", on_select); liste.bind("<Double-Button-1>", lambda e: self.ac(liste))
        self.root.bind("<Escape>", self.geri)

    def geri_yukle(self, liste):
        if not liste.curselection(): return
        sec = liste.get(liste.curselection()); p = os.path.join(self.yol, sec)
        if os.path.isfile(p):
            shutil.move(p, os.path.join(self.settings["input_dir"], sec))
            curr = self.yol
            while curr != self.settings["output_dir"]:
                if os.path.isdir(curr) and not os.listdir(curr):
                    os.rmdir(curr); curr = os.path.dirname(curr); self.yol = curr
                else: break
            self.liste_panel()

    def ac(self, liste):
        if not liste.curselection(): return
        yeni = os.path.join(self.yol, liste.get(liste.curselection()))
        if os.path.isdir(yeni): self.stack.append(self.yol); self.yol = yeni; self.liste_panel()

if __name__ == "__main__":
    root = tk.Tk(); App(root); root.mainloop()
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import psutil
import json
from src.scanner_manager import ScannerManager

# --- CONFIGURATION DYNAMIQUE DES COULEURS ---
# On utilise des tuples (Mode Clair, Mode Sombre) pour une compatibilité parfaite
COLOR_BG = ("#f2f2f2", "#0a0a0a")           # Fond principal
COLOR_SIDEBAR = ("#ebebeb", "#141414")     # Barre latérale
COLOR_CARD = ("#ffffff", "#1a1a1a")        # Conteneurs/Cartes
COLOR_ACCENT = ("#1a73e8", "#00d4ff")      # Bleu (Action primaire)
COLOR_TEXT = ("#212529", "#e0e0e0")        # Texte principal
COLOR_SUCCESS = ("#28a745", "#00ff9d")     # Vert (Succès)
COLOR_WARNING = ("#e6a23c", "#ffcc00")     # Jaune (Attention)
COLOR_DANGER = ("#dc3545", "#ff3e3e")      # Rouge (Danger)

LOGO_PATH = "img/logo.png"

class TafustUI(ctk.CTk):
    def __init__(self, root_dummy, manager: ScannerManager):
        super().__init__()
        
        # Forcer le mode sombre par défaut au démarrage
        ctk.set_appearance_mode("Dark")
        
        self.manager = manager
        
        # Configuration de la fenêtre principale
        self.title("🧿 Tafust - Advanced Security Monitor")
        self.geometry("1100x750")
        
        # Grid layout (1x2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_area()
        
        # Style initial du Treeview
        self.update_treeview_style()
        
        # Mise à jour périodique
        self.update_system_info()

    def setup_sidebar(self):
        """Configure la barre latérale avec couleurs dynamiques."""
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        # --- Logo ---
        try:
            if os.path.exists(LOGO_PATH):
                logo_image = Image.open(LOGO_PATH)
                # CTkImage gère automatiquement l'apparence si on passe deux images, 
                # ici on utilise la même car le fond de la sidebar s'adapte.
                self.logo_img = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(120, 120))
                self.logo_label = ctk.CTkLabel(self.sidebar_frame, image=self.logo_img, text="")
                self.logo_label.pack(pady=(30, 10))
            else:
                self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="🧿", font=ctk.CTkFont(size=50))
                self.logo_label.pack(pady=(30, 10))
        except: pass

        ctk.CTkLabel(self.sidebar_frame, text="TAFUST", text_color=COLOR_TEXT,
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 20))

        # --- Infos Système ---
        self.info_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.info_frame.pack(fill="x", padx=20, pady=10)

        self.os_label = ctk.CTkLabel(self.info_frame, text=f"OS: {self.manager.os_type}", text_color=COLOR_TEXT, font=ctk.CTkFont(size=12))
        self.os_label.pack(anchor="w")

        self.cpu_label = ctk.CTkLabel(self.info_frame, text="CPU: 0%", text_color=COLOR_TEXT, font=ctk.CTkFont(size=12))
        self.cpu_label.pack(anchor="w")

        self.ram_label = ctk.CTkLabel(self.info_frame, text="RAM: 0%", text_color=COLOR_TEXT, font=ctk.CTkFont(size=12))
        self.ram_label.pack(anchor="w")

        # --- Actions Supplémentaires ---
        self.export_button = ctk.CTkButton(
            self.sidebar_frame, 
            text="EXPORTER RÉSULTATS", 
            command=self.export_results,
            fg_color="transparent",
            border_width=2,
            border_color=COLOR_ACCENT,
            text_color=COLOR_TEXT,
            hover_color=COLOR_ACCENT,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.export_button.pack(padx=20, pady=20, fill="x")

        # --- Footer : Theme Toggle ---
        self.theme_button = ctk.CTkButton(
            self.sidebar_frame, 
            text="SWITCH TO LIGHT", # Initialisé pour le mode Dark par défaut
            command=self.toggle_theme_event,
            fg_color=COLOR_CARD,
            text_color=COLOR_TEXT,
            hover_color=COLOR_ACCENT,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.theme_button.pack(side="bottom", padx=20, pady=20, fill="x")

    def setup_main_area(self):
        """Zone principale avec conteneurs adaptatifs."""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_BG)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Content Padding Frame
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=30, pady=30)
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # --- Header ---
        self.header_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        self.scan_button = ctk.CTkButton(
            self.header_frame, 
            text="LANCER L'ANALYSE", 
            command=self.start_scan,
            fg_color=COLOR_ACCENT,
            text_color="white", # Toujours blanc sur l'accent
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45
        )
        self.scan_button.pack(side="left")

        self.status_label = ctk.CTkLabel(self.header_frame, text="Statut : Prêt", text_color=COLOR_TEXT, font=ctk.CTkFont(size=13, slant="italic"))
        self.status_label.pack(side="right")

        # --- Results Table ---
        self.table_container = ctk.CTkFrame(self.content_frame, fg_color=COLOR_CARD, corner_radius=10)
        self.table_container.grid(row=1, column=0, sticky="nsew")

        self.tree = ttk.Treeview(self.table_container, columns=("proto", "port", "service", "addr", "proc", "score", "status"), show="headings")
        
        cols = {"proto": "PROTO", "port": "PORT", "service": "SERVICE", "addr": "ADRESSE", "proc": "PROCESSUS", "score": "SCORE", "status": "STATUT"}
        for col, head in cols.items():
            self.tree.heading(col, text=head)
            self.tree.column(col, width=100, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        
        self.scrollbar = ttk.Scrollbar(self.table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self.on_double_click)

    def update_treeview_style(self):
        """Met à jour dynamiquement le style du Treeview selon le mode (Clair/Sombre)."""
        is_dark = ctk.get_appearance_mode() == "Dark"
        
        bg_color = COLOR_CARD[1] if is_dark else COLOR_CARD[0]
        text_color = COLOR_TEXT[1] if is_dark else COLOR_TEXT[0]
        head_bg = "#2b2b2b" if is_dark else "#e0e0e0"
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background=bg_color,
                        foreground=text_color,
                        rowheight=35,
                        fieldbackground=bg_color,
                        bordercolor=bg_color,
                        borderwidth=0,
                        font=("Consolas", 10))
        
        style.map("Treeview", background=[('selected', COLOR_ACCENT[1] if is_dark else COLOR_ACCENT[0])])
        style.configure("Treeview.Heading",
                        background=head_bg,
                        foreground=text_color,
                        relief="flat",
                        font=("Consolas", 10, "bold"))

    def export_results(self):
        """Exporte les résultats de l'analyse vers un fichier."""
        if not self.manager.last_results:
            messagebox.showwarning("Export", "Aucun résultat à exporter. Lancez d'abord un scan.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichier texte", "*.txt"), ("Fichier JSON", "*.json")],
            title="Exporter les résultats"
        )

        if not file_path:
            return

        try:
            if file_path.endswith(".json"):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.manager.last_results, f, indent=4, ensure_ascii=False)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"RAPPORT DE SÉCURITÉ TAFUST - {os.path.basename(file_path)}\n")
                    f.write("="*60 + "\n")
                    for r in self.manager.last_results:
                        f.write(f"[{r['status']}] {r['proc']} | Port: {r['port']} | Score: {r['score']}/100\n")
                        f.write(f"   Détails : {', '.join(r['reasons'])}\n\n")
            
            messagebox.showinfo("Export", f"Résultats exportés avec succès vers :\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export", f"Erreur lors de l'export : {e}")

    def update_system_info(self):
        self.cpu_label.configure(text=f"CPU: {psutil.cpu_percent()}%")
        self.ram_label.configure(text=f"RAM: {psutil.virtual_memory().percent}%")
        self.after(2000, self.update_system_info)

    def start_scan(self):
        self.scan_button.configure(state="disabled", text="ANALYSE EN COURS...")
        self.status_label.configure(text="Statut : Scan en cours...", text_color=COLOR_ACCENT)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.manager.start_async_scan(self.on_scan_complete, self.on_scan_error)

    def on_scan_complete(self, data):
        self.after(0, lambda: self._populate_results(data))

    def _populate_results(self, data):
        for e in data:
            self.tree.insert("", tk.END, values=(
                e["proto"], e["port"], e["service"],
                e["ip"], e["proc"], f"{e['score']}/100", e["status"]
            ))
        self.scan_button.configure(state="normal", text="LANCER L'ANALYSE")
        self.status_label.configure(text="Statut : Terminé", text_color=COLOR_SUCCESS)

    def on_scan_error(self, message):
        self.after(0, lambda: messagebox.showerror("Erreur Scan", message))
        self.scan_button.configure(state="normal", text="LANCER L'ANALYSE")
        self.status_label.configure(text="Statut : Erreur", text_color=COLOR_DANGER)

    def on_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id: return
        values = self.tree.item(item_id, "values")
        entry = self.manager.get_result_by_port_and_proc(values[1], values[4])
        if entry:
            details = f"ANALYSE DE RISQUE : {values[4]} (Port {values[1]})\n" + "="*40 + "\n"
            details += "\n".join([f"[*] {r}" for r in entry.get("reasons", [])])
            messagebox.showinfo("Détails du risque", details)

    def toggle_theme_event(self):
        """Bascule intelligemment entre Light et Dark mode."""
        current_mode = ctk.get_appearance_mode()
        
        if current_mode == "Dark":
            ctk.set_appearance_mode("Light")
            self.theme_button.configure(text="SWITCH TO DARK")
        else:
            ctk.set_appearance_mode("Dark")
            self.theme_button.configure(text="SWITCH TO LIGHT")
            
        # Mise à jour immédiate du style du Treeview pour la lisibilité
        self.after(100, self.update_treeview_style)

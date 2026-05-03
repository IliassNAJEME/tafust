import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import psutil
import json
from src.scanner_manager import ScannerManager

# --- CONFIGURATION DYNAMIQUE DES COULEURS ---
COLOR_BG = ("#f2f2f2", "#0a0a0a")
COLOR_SIDEBAR = ("#ebebeb", "#141414")
COLOR_CARD = ("#ffffff", "#1a1a1a")
COLOR_ACCENT = ("#1a73e8", "#00d4ff")
COLOR_TEXT = ("#212529", "#e0e0e0")

LOGO_PATH = "img/logo.png"

class TafustUI(ctk.CTk):
    def __init__(self, root_dummy, manager: ScannerManager):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        self.manager = manager
        self.title("🧿 Tafust - Advanced Security Monitor")
        self.geometry("1100x750")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_area()
        self.update_system_info()

    def setup_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        try:
            if os.path.exists(LOGO_PATH):
                logo_image = Image.open(LOGO_PATH)
                self.logo_img = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(120, 120))
                self.logo_label = ctk.CTkLabel(self.sidebar_frame, image=self.logo_img, text="")
                self.logo_label.pack(pady=(30, 10))
            else:
                self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="🧿", font=ctk.CTkFont(size=50))
                self.logo_label.pack(pady=(30, 10))
        except: pass

        ctk.CTkLabel(self.sidebar_frame, text="TAFUST", text_color=COLOR_TEXT,
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 20))

        self.info_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.info_frame.pack(fill="x", padx=20, pady=10)

        self.os_label = ctk.CTkLabel(self.info_frame, text=f"OS: {self.manager.os_type}", text_color=COLOR_TEXT, font=ctk.CTkFont(size=12))
        self.os_label.pack(anchor="w")
        self.cpu_label = ctk.CTkLabel(self.info_frame, text="CPU: 0%", text_color=COLOR_TEXT, font=ctk.CTkFont(size=12))
        self.cpu_label.pack(anchor="w")
        self.ram_label = ctk.CTkLabel(self.info_frame, text="RAM: 0%", text_color=COLOR_TEXT, font=ctk.CTkFont(size=12))
        self.ram_label.pack(anchor="w")

        self.export_button = ctk.CTkButton(
            self.sidebar_frame, text="EXPORTER RÉSULTATS", command=self.export_results,
            fg_color="transparent", border_width=2, border_color=COLOR_ACCENT,
            text_color=COLOR_TEXT, hover_color=COLOR_ACCENT, font=ctk.CTkFont(size=12, weight="bold")
        )
        self.export_button.pack(padx=20, pady=20, fill="x")

        self.theme_button = ctk.CTkButton(
            self.sidebar_frame, text="SWITCH TO LIGHT", command=self.toggle_theme_event,
            fg_color=COLOR_CARD, text_color=COLOR_TEXT, hover_color=COLOR_ACCENT,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.theme_button.pack(side="bottom", padx=20, pady=20, fill="x")

    def render_result_card(self, parent, status, service, port, score, reasons):
        """Rendu du rapport d'analyse selon les directives utilisateur."""
        status = str(status).strip().upper()
        
        # Configuration des styles
        config = {
            "SAFE": {"fg": "#1e3d24", "border": "#2ecc71", "icon": "🟢", "label": "SAFE"},
            "SUSPICIOUS": {"fg": "#3d361e", "border": "#f1c40f", "icon": "🟡", "label": "SUSPICIOUS"},
            "DANGER": {"fg": "#3d1e1e", "border": "#e74c3c", "icon": "🔴", "label": "DANGER"},
            "UNKNOWN": {"fg": "#2b2b2b", "border": "#95a5a6", "icon": "⚪", "label": "UNKNOWN"}
        }
        
        style = config.get(status, config["UNKNOWN"])
        text_color = "#e0e0e0"

        # Frame principale de l'entrée
        card = ctk.CTkFrame(parent, fg_color=style["fg"], border_color=style["border"], border_width=2, corner_radius=8)
        card.pack(fill="x", padx=15, pady=10)

        # Ligne de titre : [ICÔNE + COULEUR] NOM_PROCESSUS | Port: XXXX | Score: XX
        title_frame = ctk.CTkFrame(card, fg_color="transparent")
        title_frame.pack(fill="x", padx=15, pady=(12, 5))

        title_text = f"{style['icon']} {service.upper()} | Port: {port} | Score: {score}"
        service_label = ctk.CTkLabel(title_frame, text=title_text, font=ctk.CTkFont(size=14, weight="bold"), text_color=text_color)
        service_label.pack(side="left")

        # Statut : message d'explication
        reasons_text = " • ".join(reasons) if isinstance(reasons, list) else str(reasons)
        status_line = ctk.CTkLabel(card, text=f"Statut : {reasons_text}", font=ctk.CTkFont(size=11), 
                                   text_color="#aaaaaa", wraplength=700, justify="left")
        status_line.pack(anchor="w", padx=35, pady=(0, 12))

        # Séparateur visuel (optionnel car le border+pady fait déjà office de séparateur, 
        # mais on peut ajouter une ligne si besoin)
        return card

    def setup_main_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_BG)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=30, pady=30)

        self.scan_button = ctk.CTkButton(
            self.header_frame, text="LANCER L'ANALYSE", command=self.start_scan,
            fg_color=COLOR_ACCENT, text_color="white", font=ctk.CTkFont(size=14, weight="bold"), height=45
        )
        self.scan_button.pack(side="left")

        self.status_label = ctk.CTkLabel(self.header_frame, text="Statut : Prêt", text_color=COLOR_TEXT, font=ctk.CTkFont(size=13, slant="italic"))
        self.status_label.pack(side="right")

        self.filter_local_var = tk.BooleanVar(value=False)
        self.filter_local_checkbox = ctk.CTkCheckBox(
            self.header_frame, text="Exclure local", variable=self.filter_local_var,
            command=self.toggle_local_filter, font=ctk.CTkFont(size=12)
        )
        self.filter_local_checkbox.pack(side="right", padx=20)

        self.results_container = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent", label_text="RAPPORTS D'ANALYSE")
        self.results_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def start_scan(self):
        self.scan_button.configure(state="disabled", text="ANALYSE EN COURS...")
        self.status_label.configure(text="Statut : Scan en cours...", text_color=COLOR_ACCENT)
        for child in self.results_container.winfo_children():
            child.destroy()
        self.manager.start_async_scan(self.on_scan_complete, self.on_scan_error)

    def on_scan_complete(self, data):
        self.after(0, lambda: self._populate_results(data))

    def _populate_results(self, data):
        for child in self.results_container.winfo_children():
            child.destroy()
            
        if not data:
            ctk.CTkLabel(self.results_container, text="Aucun service détecté.").pack(pady=20)
            return

        # Groupement et Tri par niveau de risque
        priority = {"DANGER": 0, "SUSPICIOUS": 1, "SAFE": 2, "UNKNOWN": 3}
        sorted_data = sorted(data, key=lambda x: priority.get(x.get('status', 'UNKNOWN'), 4))

        stats = {"DANGER": 0, "SUSPICIOUS": 0, "SAFE": 0, "UNKNOWN": 0}
        for e in sorted_data:
            status = e.get('status', 'UNKNOWN')
            stats[status] = stats.get(status, 0) + 1

        # Résumé en haut
        self.render_summary(stats)

        for e in sorted_data:
            self.render_result_card(
                parent=self.results_container,
                status=e.get('status', 'UNKNOWN'),
                service=e['proc'],
                port=e['port'],
                score=e['score'],
                reasons=e['reasons']
            )
        
        self.scan_button.configure(state="normal", text="LANCER L'ANALYSE")
        self.status_label.configure(text="Statut : Terminé", text_color="#28a745")

    def render_summary(self, stats):
        summary_frame = ctk.CTkFrame(self.results_container, fg_color="#141414", border_width=1, border_color=COLOR_ACCENT)
        summary_frame.pack(fill="x", padx=15, pady=20)
        
        ctk.CTkLabel(summary_frame, text="📊 RÉSUMÉ DE L'ANALYSE", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
        
        stats_line = ctk.CTkFrame(summary_frame, fg_color="transparent")
        stats_line.pack(pady=10)

        colors = {"DANGER": "#e74c3c", "SUSPICIOUS": "#f1c40f", "SAFE": "#2ecc71", "UNKNOWN": "#95a5a6"}
        icons = {"DANGER": "🔴", "SUSPICIOUS": "🟡", "SAFE": "🟢", "UNKNOWN": "⚪"}

        for cat in ["DANGER", "SUSPICIOUS", "SAFE", "UNKNOWN"]:
            count = stats.get(cat, 0)
            lbl = ctk.CTkLabel(stats_line, text=f"{icons[cat]} {cat}: {count}  ", 
                               text_color=colors[cat], font=ctk.CTkFont(size=12, weight="bold"))
            lbl.pack(side="left", padx=10)

    def on_scan_error(self, message):
        self.after(0, lambda: messagebox.showerror("Erreur Scan", message))
        self.scan_button.configure(state="normal", text="LANCER L'ANALYSE")
        self.status_label.configure(text="Statut : Erreur", text_color="#dc3545")

    def update_system_info(self):
        try:
            self.cpu_label.configure(text=f"CPU: {psutil.cpu_percent()}%")
            self.ram_label.configure(text=f"RAM: {psutil.virtual_memory().percent}%")
        except: pass
        self.after(2000, self.update_system_info)

    def export_results(self):
        if not self.manager.last_results:
            messagebox.showwarning("Export", "Aucun résultat à exporter.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".json")
        if file_path:
            with open(file_path, "w") as f:
                json.dump(self.manager.last_results, f, indent=4)
            messagebox.showinfo("Export", "Résultats exportés avec succès.")

    def toggle_local_filter(self):
        self.manager.exclude_local = self.filter_local_var.get()

    def toggle_theme_event(self):
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("Light")
            self.theme_button.configure(text="SWITCH TO DARK")
        else:
            ctk.set_appearance_mode("Dark")
            self.theme_button.configure(text="SWITCH TO LIGHT")

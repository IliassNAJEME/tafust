import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import psutil
from PIL import Image

from src.app_paths import get_resource_path
from src.scanner_manager import ScannerManager


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# ── Palette premium cybersécurité ──────────────────────────────────────────────
APP_BG        = "#0f172a"
CARD_BG       = "#1e293b"
CARD_BG_SOFT  = "#334155"
CARD_BORDER   = "#475569"
SIDEBAR_BG    = "#0f172a"
SIDEBAR_SEL   = "#1e293b"
TEXT_MAIN     = "#f8fafc"
TEXT_MUTED    = "#94a3b8"
TEXT_DIM      = "#64748b"
SIGNAL        = "#10b981"
SIGNAL_SOFT   = "#064e3b"
SIGNAL_DIM    = "#059669"
DANGER        = "#ef4444"
DANGER_SOFT   = "#7f1d1d"
DANGER_DIM    = "#dc2626"
WARNING       = "#f59e0b"
WARNING_SOFT  = "#78350f"
SAFE          = "#10b981"
SAFE_SOFT     = "#064e3b"
INFO          = "#3b82f6"
EMBER         = "#f97316"
GRID_LINE     = "#1e293b"
GRID_BOLD     = "#334155"

LOGO_PATH = get_resource_path("img", "logo.png")
ICON_PATH = get_resource_path("img", "logo.png")

RISK_COLORS = {
    "CRITIQUE":    DANGER,
    "ELEVE":       EMBER,
    "ÉLEVÉ":       EMBER,
    "MODERE":      WARNING,
    "MODÉRÉ":      WARNING,
    "FAIBLE":      SAFE,
    "TRES FAIBLE": SIGNAL,
    "TRÈS FAIBLE": SIGNAL,
}

RISK_BG = {
    "CRITIQUE":    DANGER_SOFT,
    "ELEVE":       "#2a1808",
    "ÉLEVÉ":       "#2a1808",
    "MODERE":      WARNING_SOFT,
    "MODÉRÉ":      WARNING_SOFT,
    "FAIBLE":      SAFE_SOFT,
    "TRES FAIBLE": SIGNAL_SOFT,
    "TRÈS FAIBLE": SIGNAL_SOFT,
}

RISK_DESC = {
    "CRITIQUE":    "Menace active — intervention immédiate requise",
    "ÉLEVÉ":       "Risque significatif — vérification urgente recommandée",
    "MODÉRÉ":      "Service connu mais nécessite une surveillance active",
    "FAIBLE":      "Risque mineur — service reconnu, surveiller occasionnellement",
    "TRÈS FAIBLE": "Processus système légitime et de confiance",
}

RISK_ICONS = {
    "CRITIQUE":    "🔴",
    "ÉLEVÉ":       "🟠",
    "MODÉRÉ":      "🟡",
    "FAIBLE":      "🟢",
    "TRÈS FAIBLE": "✅",
}


def normalize_risk(level: str) -> str:
    return (
        (level or "")
        .replace("É", "E").replace("È", "E").replace("Ê", "E")
        .replace("é", "e").replace("è", "e").replace("ê", "e")
        .replace("À", "A").replace("à", "a")
        .upper()
    )


def make_card(parent, fg=CARD_BG, border=CARD_BORDER, radius=16):
    return ctk.CTkFrame(parent, fg_color=fg, border_color=border, border_width=1, corner_radius=radius)


def get_risk_color(level: str) -> str:
    return RISK_COLORS.get(level, RISK_COLORS.get(normalize_risk(level), INFO))


def get_risk_bg(level: str) -> str:
    return RISK_BG.get(level, RISK_BG.get(normalize_risk(level), CARD_BG_SOFT))


# ── Analyse narrative par catégorie ───────────────────────────────────────────
def build_analysis_text(item: dict) -> str:
    """Génère un paragraphe d'analyse en langage clair pour chaque entrée."""
    risk = item.get("risk_level", "FAIBLE")
    proc = item.get("label") or item.get("proc", "Inconnu")
    port = (
        ", ".join(str(p) for p in item["ports_list"])
        if item.get("ports_list")
        else str(item.get("port", "?"))
    )
    ip = item.get("ip", "?")
    proto = item.get("proto", "TCP")
    justification = item.get("justification", "")
    reputation_verdict = item.get("reputation_verdict", "unknown")

    if risk == "CRITIQUE":
        return (
            f"MENACE ACTIVE DETECTEE\n\n"
            f"Le processus '{proc}' a ete signale comme MALVEILLANT par les bases de donnees de "
            f"reputation cloud. Ce type de detection indique une forte probabilite de comportement "
            f"malveillant : logiciel espion, trojan, C2 (Command & Control) ou exfiltration de donnees.\n\n"
            f"Ce service doit etre ARRETE et ISOLE immediatement. Le systeme doit faire l'objet d'une "
            f"analyse forensic complete avant d'etre remis en service.\n\n"
            f"Details techniques : port {port}/{proto} sur {ip}."
        )

    if risk == "ÉLEVÉ":
        if reputation_verdict == "suspicious":
            return (
                f"SIGNAL DE SUSPICION DETECTE\n\n"
                f"Le processus '{proc}' a recu un signal de suspicion de la part des moteurs d'analyse "
                f"cloud. Sans preuve locale de confiance (signature numerique valide, publisher reconnu), "
                f"ce comportement ne peut pas etre exclu comme potentiellement malveillant.\n\n"
                f"Il ecoute sur le port {port}/{proto} depuis l'adresse {ip}, ce qui le rend accessible "
                f"sur le reseau. Verificez manuellement l'origine de ce processus, son chemin "
                f"d'installation, et son comportement reseau.\n\n"
                f"{justification}"
            )
        return (
            f"EXPOSITION RESEAU RISQUEE\n\n"
            f"Le service '{proc}' ecoute sur le port {port}/{proto}, un port classe comme sensible. "
            f"{justification}\n\n"
            f"Ce type d'exposition reseau (IP: {ip}) represente un vecteur d'attaque courant : "
            f"brute-force, exploitation de vulnerabilites connues, mouvement lateral. Aucune preuve "
            f"de confiance suffisante n'a ete trouvee pour ce processus."
        )

    if risk == "MODÉRÉ":
        return (
            f"SERVICE A SURVEILLER\n\n"
            f"'{proc}' est un service connu qui ecoute sur le port {port}/{proto} ({ip}). "
            f"{justification}\n\n"
            f"Bien qu'il s'agisse generalement d'un service legitime, sa presence active sur le reseau "
            f"merite une attention particuliere. Verifiez que son utilisation est intentionnelle et que "
            f"son exposition est necessaire dans votre contexte d'utilisation actuel."
        )

    if risk == "FAIBLE":
        return (
            f"RISQUE RESIDUEL FAIBLE\n\n"
            f"'{proc}' est un processus reconnu avec un risque residuel faible. {justification}\n\n"
            f"Il ecoute sur le port {port}/{proto} depuis {ip}. Son exposition est consideree comme "
            f"controlee, mais une surveillance periodique reste conseillee pour s'assurer que son "
            f"comportement ne change pas au fil du temps."
        )

    # TRÈS FAIBLE / LÉGITIME
    return (
        f"PROCESSUS LEGITIME\n\n"
        f"'{proc}' est un processus systeme ou une application de confiance. "
        f"{justification or 'Ses signatures numeriques et/ou son publisher ont ete verifies.'}\n\n"
        f"Il ecoute sur le port {port}/{proto} depuis {ip}. Aucune action requise — ce service "
        f"est classe comme legitime et de confiance."
    )


class StatBadge(ctk.CTkFrame):
    def __init__(self, parent, title: str, value: str, accent: str = TEXT_MUTED):
        super().__init__(
            parent,
            fg_color=CARD_BG_SOFT,
            border_color=CARD_BORDER,
            border_width=1,
            corner_radius=14,
        )
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self, text=title,
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 0))
        self.value_label = ctk.CTkLabel(
            self, text=value,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=accent,
        )
        self.value_label.grid(row=1, column=0, sticky="w", padx=14, pady=(2, 10))

    def set_value(self, value: str, accent: str | None = None):
        self.value_label.configure(text=value)
        if accent is not None:
            self.value_label.configure(text_color=accent)


class TafustUI(ctk.CTk):
    def __init__(self, _root_dummy, manager: ScannerManager):
        super().__init__()
        self.manager = manager
        self._last_report_text = ""
        self._logo = None
        self._window_icon = None
        self._loading_frame = None
        self._empty_state_frame = None
        self._summary_frame = None
        self._verdict_frame = None
        self._tab_bar_frame = None
        self._results_body = None
        self._active_tab = "dashboard"
        self._current_report = None
        self._loading_step_labels = {}
        self._tab_buttons = {}

        self.title("Tafust — Network Security Audit")
        self.geometry("1400x860")
        self.minsize(1100, 720)
        self.configure(fg_color=APP_BG)

        try:
            if os.path.exists(ICON_PATH):
                self._window_icon = tk.PhotoImage(file=ICON_PATH)
                self.iconphoto(True, self._window_icon)
        except Exception:
            pass

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_shell()
        self._render_empty_state()
        self._tick_system_info()

    # ── Shell layout ──────────────────────────────────────────────────────────
    def _build_shell(self):
        shell = ctk.CTkFrame(self, fg_color=APP_BG)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.grid_rowconfigure(2, weight=1)
        shell.grid_columnconfigure(0, weight=1)

        # Grid background canvas
        self._background = tk.Canvas(shell, bg=APP_BG, highlightthickness=0, bd=0)
        self._background.grid(row=0, column=0, sticky="nsew")
        self._background.bind("<Configure>", self._draw_grid_background)

        # Header
        self._header_card = make_card(shell, radius=20)
        self._header_card.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 12))
        self._header_card.grid_columnconfigure(0, weight=1)
        self._header_card.grid_columnconfigure(1, weight=0)
        self._build_header(self._header_card)

        # Scan panel
        self._scan_card = make_card(shell, radius=20)
        self._scan_card.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))
        self._scan_card.grid_columnconfigure(0, weight=1)
        self._build_scan_panel(self._scan_card)

        # Results area
        self._results_card = make_card(shell, radius=20)
        self._results_card.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 18))
        self._results_card.grid_columnconfigure(0, weight=1)
        self._results_card.grid_rowconfigure(3, weight=1)
        self._results_card.grid_propagate(False)

        self._summary_frame = ctk.CTkFrame(self._results_card, fg_color="transparent")
        self._summary_frame.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 0))
        self._summary_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._verdict_frame = ctk.CTkFrame(self._results_card, fg_color="transparent")
        self._verdict_frame.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 0))
        self._verdict_frame.grid_columnconfigure(0, weight=1)

        self._tab_bar_frame = ctk.CTkFrame(self._results_card, fg_color="transparent")
        self._tab_bar_frame.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 0))
        self._tab_bar_frame.grid_columnconfigure(0, weight=1)

        self._results_body = ctk.CTkScrollableFrame(
            self._results_card,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=CARD_BORDER,
            scrollbar_button_hover_color=SIGNAL,
        )
        self._results_body.grid(row=3, column=0, sticky="nsew", padx=18, pady=12)
        self._results_body.grid_columnconfigure(0, weight=1)

    def _draw_grid_background(self, event):
        canvas = event.widget
        canvas.delete("grid")
        w, h = max(event.width, 1), max(event.height, 1)
        step = 32
        for x in range(0, w, step):
            c = GRID_BOLD if x % (step * 5) == 0 else GRID_LINE
            canvas.create_line(x, 0, x, h, fill=c, tags="grid")
        for y in range(0, h, step):
            c = GRID_BOLD if y % (step * 5) == 0 else GRID_LINE
            canvas.create_line(0, y, w, y, fill=c, tags="grid")
        # Subtle top glow
        canvas.create_rectangle(0, 0, w, 3, fill="#003020", outline="", tags="grid")

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self, parent):
        left = ctk.CTkFrame(parent, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=20, pady=18)

        # Logo orb
        logo_wrap = ctk.CTkFrame(
            left, fg_color="#091a28", border_color="#004d3a",
            border_width=2, corner_radius=22, width=80, height=80,
        )
        logo_wrap.pack(side="left", padx=(0, 20))
        logo_wrap.pack_propagate(False)

        try:
            if os.path.exists(LOGO_PATH):
                img = Image.open(LOGO_PATH)
                self._logo = ctk.CTkImage(light_image=img, dark_image=img, size=(58, 58))
                ctk.CTkLabel(logo_wrap, image=self._logo, text="").place(relx=0.5, rely=0.5, anchor="center")
        except Exception:
            ctk.CTkLabel(
                logo_wrap, text="T",
                font=ctk.CTkFont(size=32, weight="bold"),
                text_color=SIGNAL,
            ).place(relx=0.5, rely=0.5, anchor="center")

        text_block = ctk.CTkFrame(left, fg_color="transparent")
        text_block.pack(side="left", anchor="center")

        meta = ctk.CTkFrame(text_block, fg_color="transparent")
        meta.pack(anchor="w")
        ctk.CTkLabel(meta, text="TAFUST",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=SIGNAL).pack(side="left")
        ctk.CTkLabel(meta, text=" v0.1",
                     font=ctk.CTkFont(size=11),
                     text_color=TEXT_MUTED,
                     fg_color=CARD_BG_SOFT, corner_radius=8, padx=8, pady=2,
                     ).pack(side="left", padx=(10, 0))

        ctk.CTkLabel(text_block,
                     text="Network Security Audit",
                     font=ctk.CTkFont(size=38, weight="bold"),
                     text_color=TEXT_MAIN,
                     ).pack(anchor="w", pady=(8, 0))
        ctk.CTkLabel(text_block,
                     text="Ports · Processus · Classification des risques réseau",
                     font=ctk.CTkFont(size=16),
                     text_color=TEXT_MUTED,
                     ).pack(anchor="w", pady=(6, 0))

        self._header_badges = ctk.CTkFrame(parent, fg_color="transparent")
        self._header_badges.grid(row=0, column=1, sticky="e", padx=20, pady=18)
        self._api_badge = StatBadge(self._header_badges, "Moteur", "local actif", SIGNAL)
        self._api_badge.pack(anchor="e", pady=(0, 8))
        self._os_badge = StatBadge(self._header_badges, "Système", self.manager.os_type, TEXT_MAIN)
        self._os_badge.pack(anchor="e", pady=(0, 8))
        vt_color = SIGNAL if bool(os.getenv("VIRUSTOTAL_API_KEY")) else WARNING
        vt_value = "VirusTotal actif" if bool(os.getenv("VIRUSTOTAL_API_KEY")) else "VirusTotal inactif"
        self._vt_badge = StatBadge(self._header_badges, "Réputation", vt_value, vt_color)
        self._vt_badge.pack(anchor="e")

    # ── Scan panel ────────────────────────────────────────────────────────────
    def _build_scan_panel(self, parent):
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 6))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top, text="Lancer un scan",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(top, text="Inspecte les ports en écoute et classifie les processus par niveau de risque",
                     font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(anchor="w", pady=(4, 0))

        control_row = ctk.CTkFrame(parent, fg_color="transparent")
        control_row.grid(row=1, column=0, sticky="ew", padx=22, pady=(8, 14))
        control_row.grid_columnconfigure(0, weight=1)

        self._excl_local = tk.BooleanVar(value=False)
        self._exclude_toggle = ctk.CTkSwitch(
            control_row,
            text="Exclure les listeners loopback",
            variable=self._excl_local,
            command=self._on_toggle_local,
            progress_color=SIGNAL, button_color=CARD_BORDER,
            button_hover_color=TEXT_MAIN,
            fg_color=APP_BG, border_color=CARD_BORDER,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_MUTED, switch_width=42, switch_height=24,
        )
        self._exclude_toggle.grid(row=0, column=0, sticky="w", padx=(0, 20))

        self._scan_btn = ctk.CTkButton(
            control_row, text="⚡ Lancer l'audit",
            command=self._start_scan,
            fg_color=SIGNAL, hover_color=SIGNAL_DIM,
            text_color="#ffffff",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=44, width=200, corner_radius=12,
        )
        self._scan_btn.grid(row=0, column=1, sticky="e")

        action_row = ctk.CTkFrame(parent, fg_color="transparent")
        action_row.grid(row=2, column=0, sticky="ew", padx=22, pady=(0, 14))

        self._status_lbl = ctk.CTkLabel(
            action_row, text="Prêt pour un audit local",
            font=ctk.CTkFont(size=13), text_color=TEXT_MUTED)
        self._status_lbl.pack(side="left")

        for text, cmd in [("Exporter JSON", self._export_results), ("Copier rapport", self._copy_report)]:
            ctk.CTkButton(
                action_row, text=text, command=cmd,
                fg_color="transparent", border_width=1,
                border_color=CARD_BORDER, hover_color=CARD_BG_SOFT,
                text_color=TEXT_MAIN, width=120, height=34, corner_radius=12,
                font=ctk.CTkFont(size=12),
            ).pack(side="right", padx=(8, 0))

    # ── Results management ────────────────────────────────────────────────────
    def _clear_results(self):
        for w in self._summary_frame.winfo_children():
            w.destroy()
        for w in self._verdict_frame.winfo_children():
            w.destroy()
        for w in self._tab_bar_frame.winfo_children():
            w.destroy()
        for w in self._results_body.winfo_children():
            w.destroy()
        self._loading_frame = None
        self._empty_state_frame = None
        self._loading_step_labels = {}

    def _render_empty_state(self):
        self._clear_results()
        self._empty_state_frame = ctk.CTkFrame(self._results_body, fg_color="transparent")
        self._empty_state_frame.grid(row=0, column=0, sticky="nsew", pady=40)
        self._empty_state_frame.grid_columnconfigure(0, weight=1)

        orb = ctk.CTkFrame(self._empty_state_frame,
                            fg_color="#091828", border_color="#004d3a",
                            border_width=1, corner_radius=40, width=80, height=80)
        orb.grid(row=0, column=0, pady=(40, 14))
        orb.grid_propagate(False)
        ctk.CTkLabel(orb, text="🛡", font=ctk.CTkFont(size=30), text_color=SIGNAL
                     ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self._empty_state_frame, text="Aucun rapport disponible",
                     font=ctk.CTkFont(size=26, weight="bold"), text_color=TEXT_MAIN,
                     ).grid(row=1, column=0, pady=(0, 10))
        ctk.CTkLabel(self._empty_state_frame,
                     text="Lance un audit depuis le panneau ci-dessus pour afficher les résultats.",
                     font=ctk.CTkFont(size=15), text_color=TEXT_MUTED,
                     ).grid(row=2, column=0, pady=(0, 40))

    def _render_loading_state(self):
        self._clear_results()
        self._loading_frame = ctk.CTkFrame(self._results_body, fg_color="transparent")
        self._loading_frame.grid(row=0, column=0, sticky="nsew", pady=24)
        self._loading_frame.grid_columnconfigure(0, weight=1)

        ring = ctk.CTkFrame(self._loading_frame,
                             fg_color="#091828", border_color="#004d3a",
                             border_width=2, corner_radius=44, width=88, height=88)
        ring.grid(row=0, column=0, pady=(24, 14))
        ring.grid_propagate(False)
        ctk.CTkLabel(ring, text="SCAN",
                     font=ctk.CTkFont(size=15, weight="bold"), text_color=SIGNAL,
                     ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self._loading_frame, text="Audit en cours...",
                     font=ctk.CTkFont(size=22, weight="bold"), text_color=SIGNAL,
                     ).grid(row=1, column=0, pady=(0, 6))
        ctk.CTkLabel(self._loading_frame,
                     text="Inspection des ports, des processus et de la réputation locale.",
                     font=ctk.CTkFont(size=14), text_color=TEXT_MUTED,
                     ).grid(row=2, column=0, pady=(0, 20))

        steps = [
            ("collect",    "Collecte des connexions réseau"),
            ("resolve",    "Résolution des processus"),
            ("filter",     "Filtrage des listeners"),
            ("reputation", "Enrichissement de réputation"),
            ("analyze",    "Analyse des risques"),
        ]
        for i, (step_key, step) in enumerate(steps):
            row = make_card(self._loading_frame, fg=CARD_BG_SOFT, radius=12)
            row.grid(row=3 + i, column=0, sticky="ew", padx=180, pady=5)
            ctk.CTkLabel(row, text=step, font=ctk.CTkFont(size=13),
                         text_color=TEXT_MAIN).pack(side="left", padx=16, pady=10)
            status = ctk.CTkLabel(row, text="en attente",
                                  font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DIM)
            status.pack(side="right", padx=16)
            self._loading_step_labels[step_key] = status

    # ── Scan callbacks ────────────────────────────────────────────────────────
    def _start_scan(self):
        self._scan_btn.configure(state="disabled", text="Analyse en cours...")
        self._status_lbl.configure(text="Scan réseau en cours...", text_color=SIGNAL)
        self._last_report_text = ""
        self.manager.exclude_local = self._excl_local.get()
        self.manager.progress_callback = self._on_scan_progress
        self._render_loading_state()
        self.manager.start_async_scan(self._on_scan_ok, self._on_scan_err)

    def _on_scan_progress(self, step: str, detail: str):
        def update():
            if detail:
                self._status_lbl.configure(text=detail, text_color=SIGNAL)
            for key, label in self._loading_step_labels.items():
                if key == step:
                    label.configure(text="en cours ▶", text_color=SIGNAL)
                elif label.cget("text") in ("en cours ▶",):
                    label.configure(text="terminé ✓", text_color=SAFE)
            if step == "done":
                for label in self._loading_step_labels.values():
                    if label.cget("text") == "en cours ▶":
                        label.configure(text="terminé ✓", text_color=SAFE)
        self.after(0, update)

    def _on_scan_ok(self, report: dict):
        self.manager.progress_callback = None
        self.after(0, lambda: self._render_report(report))

    def _on_scan_err(self, msg: str):
        def show_error():
            self.manager.progress_callback = None
            messagebox.showerror("Erreur de scan", msg)
            self._scan_btn.configure(state="normal", text="⚡  Lancer l'audit")
            self._status_lbl.configure(text="Erreur pendant le scan", text_color=DANGER)
            self._render_empty_state()
        self.after(0, show_error)

    # ── Summary cards ─────────────────────────────────────────────────────────
    def _render_summary_cards(self, summary: dict, meta: dict):
        nb_a = summary.get("nb_alertes", 0)
        nb_s = summary.get("nb_surveiller", 0)
        nb_l = summary.get("nb_legitimes", 0)
        total = summary.get("total", 0)

        # Security score
        score = max(0, min(100, 100 - nb_a * 25 - nb_s * 8)) if total > 0 else 100
        score_color = SIGNAL if score >= 80 else (WARNING if score >= 50 else DANGER)
        score_label = "Sécurisé" if score >= 80 else ("Attention" if score >= 50 else "Critique")

        cards = [
            ("Score",          f"{score}/100  {score_label}", score_color),
            ("Alertes",        str(nb_a),   DANGER if nb_a > 0 else TEXT_MUTED),
            ("À Surveiller",   str(nb_s),   WARNING if nb_s > 0 else TEXT_MUTED),
            ("Légitimes",      str(nb_l),   SIGNAL),
        ]

        self._summary_frame.grid_columnconfigure(list(range(len(cards))), weight=1)
        for idx, (title, value, accent) in enumerate(cards):
            card = make_card(self._summary_frame, fg=CARD_BG_SOFT, radius=16)
            card.grid(row=0, column=idx, sticky="ew",
                      padx=(0 if idx == 0 else 10, 0), pady=(0, 10))
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11),
                         text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(14, 4))
            ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=19, weight="bold"),
                         text_color=accent).pack(anchor="w", padx=16, pady=(0, 14))

    # ── Tab bar ───────────────────────────────────────────────────────────────
    def _build_tab_bar(self, parent, report: dict):
        for w in self._tab_bar_frame.winfo_children():
            w.destroy()
            
        tabs = [
            ("dashboard",  "Dashboard",       len(report.get("alertes", [])) + len(report.get("surveiller", []))),
            ("alertes",    "🔴 Alertes",       len(report.get("alertes", []))),
            ("surveiller", "🟡 Surveillance",  len(report.get("surveiller", []))),
            ("legitimes",  "✅ Légitimes",     len(report.get("legitimes", []))),
            ("hardenings", "🛡 Durcissement",  len(report.get("hardenings", []))),
            ("raw",        "{} Données brutes", 0),
        ]
        self._tab_buttons = {}
        bar = ctk.CTkFrame(self._tab_bar_frame, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 12))

        nav = ctk.CTkFrame(bar, fg_color="transparent")
        nav.pack(side="left", fill="x", expand=True)

        for tab_id, label, count in tabs:
            text = f"{label}  ({count})" if count > 0 else label
            btn = ctk.CTkButton(
                nav, text=text,
                command=lambda v=tab_id: self._set_active_tab(v),
                fg_color="transparent", hover_color=CARD_BG_SOFT,
                text_color=TEXT_MUTED, border_width=0,
                corner_radius=14, height=34, width=124,
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            btn.pack(side="left", padx=(0, 6))
            self._tab_buttons[tab_id] = btn

        self._sync_tab_styles()

    def _sync_tab_styles(self):
        for tab_id, btn in self._tab_buttons.items():
            active = tab_id == self._active_tab
            btn.configure(
                fg_color=CARD_BG_SOFT if active else "transparent",
                text_color=SIGNAL if active else TEXT_MUTED,
                border_width=1 if active else 0,
                border_color=SIGNAL if active else CARD_BORDER,
            )

    def _set_active_tab(self, tab_id: str):
        self._active_tab = tab_id
        self._sync_tab_styles()
        if self._current_report:
            self._render_tab_content(self._current_report)

    # ── Risk chip ─────────────────────────────────────────────────────────────
    def _risk_chip(self, parent, level: str):
        color = get_risk_color(level)
        bg    = get_risk_bg(level)
        chip  = ctk.CTkFrame(parent, fg_color=bg, border_color=color, border_width=1, corner_radius=999)
        icon  = RISK_ICONS.get(level, "·")
        ctk.CTkLabel(chip, text=f"{icon}  {level or 'INCONNU'}",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=color).pack(padx=12, pady=6)
        return chip

    # ── Analysis panel per item ───────────────────────────────────────────────
    def _render_analysis_panel(self, parent, item: dict):
        """
        Renders a detailed analysis section beneath each result card,
        showing risk explanation, remediation commands, and metadata.
        """
        risk_level = item.get("risk_level", "FAIBLE")
        risk_color = get_risk_color(risk_level)

        panel = make_card(parent, fg=APP_BG, border=CARD_BORDER, radius=12)
        panel.pack(fill="x", padx=16, pady=(0, 14))

        # ── Analyse tab ──────────────────────────────────────────────────────
        # Section title
        title_row = ctk.CTkFrame(panel, fg_color="transparent")
        title_row.pack(fill="x", padx=16, pady=(14, 6))
        ctk.CTkLabel(title_row, text="🔍  ANALYSE DÉTAILLÉE",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=risk_color).pack(side="left")

        # Risk description
        risk_desc = RISK_DESC.get(risk_level, "Service à examiner.")
        ctk.CTkLabel(panel, text=risk_desc,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=risk_color,
                     wraplength=960, justify="left",
                     ).pack(anchor="w", padx=16, pady=(0, 4))

        # Full analysis text
        analysis_text = build_analysis_text(item)
        ctk.CTkLabel(panel, text=analysis_text,
                     font=ctk.CTkFont(size=12),
                     text_color=TEXT_MUTED,
                     wraplength=960, justify="left",
                     ).pack(anchor="w", padx=16, pady=(0, 10))

        # ── Exposure ─────────────────────────────────────────────────────────
        if item.get("exposure"):
            sep = ctk.CTkFrame(panel, fg_color=CARD_BORDER, height=1, corner_radius=0)
            sep.pack(fill="x", padx=16, pady=(0, 8))
            ctk.CTkLabel(panel, text="🌐  EXPOSITION RÉSEAU",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 4))
            ctk.CTkLabel(panel, text=item["exposure"],
                         font=ctk.CTkFont(size=12),
                         text_color=TEXT_MUTED,
                         wraplength=960, justify="left",
                         ).pack(anchor="w", padx=16, pady=(0, 10))

        # ── Hardening note ───────────────────────────────────────────────────
        if item.get("hardening_note"):
            sep = ctk.CTkFrame(panel, fg_color=CARD_BORDER, height=1, corner_radius=0)
            sep.pack(fill="x", padx=16, pady=(0, 8))
            note_frame = ctk.CTkFrame(panel, fg_color=WARNING_SOFT,
                                      border_color=WARNING, border_width=1, corner_radius=12)
            note_frame.pack(fill="x", padx=16, pady=(0, 10))
            ctk.CTkLabel(note_frame, text="⚠  Note de Hardening",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=WARNING).pack(anchor="w", padx=14, pady=(10, 4))
            ctk.CTkLabel(note_frame, text=item["hardening_note"],
                         font=ctk.CTkFont(size=12),
                         text_color=TEXT_MAIN,
                         wraplength=940, justify="left",
                         ).pack(anchor="w", padx=14, pady=(0, 10))

        # ── PowerShell commands ───────────────────────────────────────────────
        ps_cmds = item.get("powershell", [])
        if ps_cmds:
            sep = ctk.CTkFrame(panel, fg_color=CARD_BORDER, height=1, corner_radius=0)
            sep.pack(fill="x", padx=16, pady=(0, 8))
            ctk.CTkLabel(panel, text="⚡  COMMANDES POWERSHELL",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=INFO).pack(anchor="w", padx=16, pady=(0, 6))

            ps_box = ctk.CTkTextbox(
                panel, fg_color=CARD_BG,
                border_color=CARD_BORDER, border_width=1, corner_radius=10,
                text_color=INFO, font=ctk.CTkFont(family="Consolas", size=12),
                wrap="none", height=max(70, len(ps_cmds) * 22 + 20),
                activate_scrollbars=False,
            )
            ps_box.pack(fill="x", padx=16, pady=(0, 10))
            for cmd in ps_cmds:
                prefix = "#  " if cmd.startswith("#") else "PS> "
                color_tag = "comment" if cmd.startswith("#") else "cmd"
                ps_box.insert("end", f"{prefix}{cmd}\n")
            ps_box.configure(state="disabled")

            # Copy button
            def copy_ps(cmds=ps_cmds):
                self.clipboard_clear()
                self.clipboard_append("\n".join(cmds))
                self._status_lbl.configure(text="Commandes PowerShell copiées !", text_color=SIGNAL)
                self.after(2500, lambda: self._status_lbl.configure(
                    text="Audit terminé", text_color=TEXT_MUTED))

            ctk.CTkButton(
                panel, text="📋  Copier les commandes", command=copy_ps,
                fg_color="transparent", border_width=1, border_color=INFO,
                hover_color="#0a1f33", text_color=INFO,
                width=200, height=30, corner_radius=10,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(anchor="w", padx=16, pady=(0, 10))

        # ── Bash commands ─────────────────────────────────────────────────────
        bash_cmds = item.get("bash", [])
        if bash_cmds:
            sep = ctk.CTkFrame(panel, fg_color=CARD_BORDER, height=1, corner_radius=0)
            sep.pack(fill="x", padx=16, pady=(0, 8))
            ctk.CTkLabel(panel, text="🐧  COMMANDES BASH / LINUX",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=SAFE).pack(anchor="w", padx=16, pady=(0, 6))
            for cmd in bash_cmds:
                ctk.CTkLabel(panel, text=f"$  {cmd}",
                             font=ctk.CTkFont(family="Consolas", size=12),
                             text_color=SAFE,
                             ).pack(anchor="w", padx=16, pady=(2, 0))
            ctk.CTkLabel(panel, text="", height=8).pack()

        # ── Metadata ──────────────────────────────────────────────────────────
        sep = ctk.CTkFrame(panel, fg_color=CARD_BORDER, height=1, corner_radius=0)
        sep.pack(fill="x", padx=16, pady=(4, 8))
        ctk.CTkLabel(panel, text="📊  MÉTADONNÉES TECHNIQUES",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=TEXT_DIM).pack(anchor="w", padx=16, pady=(0, 6))

        meta_items = []
        if item.get("pid"):         meta_items.append(("PID",           str(item["pid"])))
        if item.get("path"):        meta_items.append(("Chemin",        item["path"]))
        if item.get("publisher"):   meta_items.append(("Publisher",     item["publisher"]))
        if item.get("company_name"):meta_items.append(("Éditeur",       item["company_name"]))
        if item.get("signature_status"):
            meta_items.append(("Signature", item["signature_status"]))
        if item.get("sha256"):
            meta_items.append(("SHA-256", item["sha256"][:28] + "..."))
        if item.get("reputation_verdict") and item["reputation_verdict"] != "unknown":
            meta_items.append(("Réputation", item["reputation_verdict"].upper()))
        if item.get("reputation_source"):
            meta_items.append(("Source", item["reputation_source"]))
        if item.get("reputation_summary"):
            meta_items.append(("Résumé", item["reputation_summary"]))

        meta_grid = ctk.CTkFrame(panel, fg_color="transparent")
        meta_grid.pack(fill="x", padx=16, pady=(0, 14))
        for key, val in meta_items:
            row = ctk.CTkFrame(meta_grid, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{key}:", width=90,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=TEXT_DIM, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val,
                         font=ctk.CTkFont(family="Consolas", size=11),
                         text_color=TEXT_MUTED,
                         wraplength=820, justify="left").pack(side="left")

    # ── Result section ────────────────────────────────────────────────────────
    def _render_result_section(self, parent, title: str, subtitle: str,
                                items: list, grouped: bool = False):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", pady=(0, 20))

        # Section header
        ctk.CTkLabel(section, text=title,
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(section, text=subtitle,
                     font=ctk.CTkFont(size=12),
                     text_color=TEXT_MUTED).pack(anchor="w", pady=(4, 10))

        if not items:
            empty = make_card(section, fg=CARD_BG_SOFT, radius=16)
            empty.pack(fill="x")
            ctk.CTkLabel(empty, text="Aucun élément dans cette section.",
                         font=ctk.CTkFont(size=14), text_color=TEXT_MUTED,
                         ).pack(anchor="w", padx=16, pady=14)
            return

        for item in items:
            risk_label = item.get("risk_level", "INCONNU")
            risk_color = get_risk_color(risk_label)
            risk_bg    = get_risk_bg(risk_label)

            # ── Main entry card ───────────────────────────────────────────────
            card = ctk.CTkFrame(section, fg_color=CARD_BG_SOFT,
                                border_color=CARD_BORDER, border_width=1, corner_radius=18)
            card.pack(fill="x", pady=(0, 6))
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=18, pady=(16, 0))

            left = ctk.CTkFrame(top_row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)

            proc = item.get("proc", "?")
            if grouped:
                ports = ", ".join(str(p) for p in item.get("ports_list", [])) or str(item.get("port", "?"))
                ips   = ", ".join(item.get("ips_list", [])) or item.get("ip", "?")
                title_txt  = f"{item.get('label') or proc}"
                detail_txt = f"Ports: {ports}  ·  IPs: {ips}  ·  {item.get('count', 1)} instance(s)"
            else:
                title_txt  = f"{item.get('label') or proc}"
                detail_txt = f"Port {item.get('port', '?')}/{item.get('proto', 'TCP')}  ·  {item.get('ip', '?')}"
                if item.get("exposure"):
                    detail_txt += f"  ·  {item['exposure'][:60]}"

            ctk.CTkLabel(left, text=title_txt,
                         font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_MAIN,
                         ).pack(anchor="w")
            ctk.CTkLabel(left, text=detail_txt,
                         font=ctk.CTkFont(family="Consolas", size=12), text_color=TEXT_MUTED,
                         ).pack(anchor="w", pady=(4, 0))

            if item.get("company_name"):
                ctk.CTkLabel(left, text=f"  {item['company_name']}",
                             font=ctk.CTkFont(size=12), text_color=TEXT_DIM,
                             ).pack(anchor="w", pady=(2, 0))

            self._risk_chip(top_row, risk_label).pack(side="right", anchor="n", padx=(14, 0))

            # ── Analysis panel (always visible) ───────────────────────────────
            self._render_analysis_panel(card, item)

    # ── Hardenings ────────────────────────────────────────────────────────────
    def _render_hardenings(self, parent, hardenings: list):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(section, text="🛡  Recommandations de durcissement",
                     font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_MAIN,
                     ).pack(anchor="w")
        ctk.CTkLabel(section,
                     text="Commandes PowerShell et Bash pour réduire la surface d'attaque.",
                     font=ctk.CTkFont(size=12), text_color=TEXT_MUTED,
                     ).pack(anchor="w", pady=(4, 10))

        if not hardenings:
            empty = make_card(section, fg=CARD_BG_SOFT, radius=16)
            empty.pack(fill="x")
            ctk.CTkLabel(empty,
                         text="Aucune recommandation de durcissement disponible pour ce scan.",
                         font=ctk.CTkFont(size=14), text_color=TEXT_MUTED,
                         ).pack(anchor="w", padx=16, pady=14)
            return

        for item in hardenings:
            card = make_card(section, fg=CARD_BG_SOFT, radius=16)
            card.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(card, text=item.get("label", item.get("proc", "?")),
                         font=ctk.CTkFont(size=15, weight="bold"), text_color=SIGNAL,
                         ).pack(anchor="w", padx=16, pady=(14, 4))
            ctk.CTkLabel(card, text=item.get("justification", ""),
                         font=ctk.CTkFont(size=12), text_color=TEXT_MUTED,
                         wraplength=920, justify="left",
                         ).pack(anchor="w", padx=16, pady=(0, 8))

            ps_cmds = item.get("powershell", [])
            if ps_cmds:
                ps_box = ctk.CTkTextbox(
                    card, fg_color=CARD_BG, border_color=CARD_BORDER,
                    border_width=1, corner_radius=10,
                    text_color=INFO, font=ctk.CTkFont(family="Consolas", size=11),
                    wrap="none", height=max(60, len(ps_cmds) * 22 + 16),
                    activate_scrollbars=False,
                )
                ps_box.pack(fill="x", padx=16, pady=(0, 8))
                for cmd in ps_cmds:
                    prefix = "#  " if cmd.startswith("#") else "PS> "
                    ps_box.insert("end", f"{prefix}{cmd}\n")
                ps_box.configure(state="disabled")

            for cmd in item.get("bash", []):
                ctk.CTkLabel(card, text=f"$  {cmd}",
                             font=ctk.CTkFont(family="Consolas", size=11),
                             text_color=SAFE).pack(anchor="w", padx=16, pady=(2, 0))
            ctk.CTkLabel(card, text="", height=6).pack()

    def _render_raw_data(self, parent, payload: dict):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="both", expand=True, pady=(0, 12))
        ctk.CTkLabel(section, text="{}  Données brutes",
                     font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_MAIN,
                     ).pack(anchor="w")
        ctk.CTkLabel(section, text="Résultats JSON complets retournés par l'application.",
                     font=ctk.CTkFont(size=12), text_color=TEXT_MUTED,
                     ).pack(anchor="w", pady=(4, 10))
        tb = ctk.CTkTextbox(
            section, fg_color=CARD_BG, border_color=CARD_BORDER,
            border_width=1, corner_radius=12,
            text_color=SIGNAL, font=ctk.CTkFont(family="Consolas", size=12),
            wrap="none", height=360,
        )
        tb.pack(fill="both", expand=True)
        tb.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False))
        tb.configure(state="disabled")

    # ── Tab content ───────────────────────────────────────────────────────────
    def _render_tab_content(self, report: dict):
        for w in self._results_body.winfo_children():
            w.destroy()

        content = ctk.CTkFrame(self._results_body, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)

        if self._active_tab == "dashboard":
            self._render_result_section(
                content, "🔴  Alertes",
                "Processus suspects ou exposés sur le réseau sans preuve de confiance.",
                report.get("alertes") or [],
            )
            self._render_result_section(
                content, "🟡  À Surveiller",
                "Services watchlist et outils d'accès distant.",
                report.get("surveiller") or [],
            )
            self._render_result_section(
                content, "✅  Services légitimes",
                "Processus connus, groupés par application.",
                report.get("legitimes") or [], grouped=True,
            )
            self._render_hardenings(content, report.get("hardenings") or [])

        elif self._active_tab == "alertes":
            self._render_result_section(
                content, "🔴  Alertes",
                "Processus suspects ou exposés sur le réseau sans preuve de confiance.",
                report.get("alertes") or [],
            )

        elif self._active_tab == "surveiller":
            self._render_result_section(
                content, "🟡  À Surveiller",
                "Services watchlist et outils d'accès distant.",
                report.get("surveiller") or [],
            )

        elif self._active_tab == "legitimes":
            self._render_result_section(
                content, "✅  Services légitimes",
                "Processus classés comme sûrs, groupés par application.",
                report.get("legitimes") or [], grouped=True,
            )

        elif self._active_tab == "hardenings":
            self._render_hardenings(content, report.get("hardenings") or [])

        elif self._active_tab == "raw":
            self._render_raw_data(content, {
                "report": report,
                "raw_results": self.manager.last_results,
            })

    # ── Report rendering ──────────────────────────────────────────────────────
    def _render_report(self, report: dict):
        self._clear_results()
        self._current_report = report

        meta    = report.get("meta", {})
        summary = report.get("summary", {})
        self._last_report_text = self._build_report_text(report)

        self._render_summary_cards(summary, meta)

        nb_a = summary.get("nb_alertes", 0)
        verdict_color = SIGNAL if nb_a == 0 else DANGER

        for w in self._verdict_frame.winfo_children():
            w.destroy()

        # Verdict card
        v_card = make_card(self._verdict_frame, fg=CARD_BG_SOFT, radius=16)
        v_card.pack(fill="x", pady=(12, 12))

        v_top = ctk.CTkFrame(v_card, fg_color="transparent")
        v_top.pack(fill="x", padx=16, pady=(16, 0))
        icon = "✅" if nb_a == 0 else "🔴"
        ctk.CTkLabel(v_top, text=f"{icon}  {summary.get('verdict', 'Verdict indisponible')}",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=verdict_color).pack(side="left")

        score = max(0, min(100, 100 - nb_a * 25 - summary.get("nb_surveiller", 0) * 8))
        score_color = SIGNAL if score >= 80 else (WARNING if score >= 50 else DANGER)
        ctk.CTkLabel(v_top,
                     text=f"Score: {score}/100",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=score_color,
                     fg_color=get_risk_bg("TRÈS FAIBLE") if score >= 80 else (WARNING_SOFT if score >= 50 else DANGER_SOFT),
                     corner_radius=8, padx=10, pady=4,
                     ).pack(side="right")

        ctk.CTkLabel(v_card, text=summary.get("verdict_detail", ""),
                     font=ctk.CTkFont(size=12), text_color=TEXT_MUTED,
                     wraplength=960, justify="left",
                     ).pack(anchor="w", padx=16, pady=(8, 0))
        ctk.CTkLabel(v_card,
                     text=f"Date : {meta.get('date', '-')}  ·  {meta.get('total_unique', summary.get('total', 0))} processus analysés",
                     font=ctk.CTkFont(size=11), text_color=TEXT_DIM,
                     ).pack(anchor="w", padx=16, pady=(4, 16))

        self._build_tab_bar(self._results_body, report)
        self._render_tab_content(report)

        self._scan_btn.configure(state="normal", text="⚡ Lancer l'audit")
        self._status_lbl.configure(text="Audit terminé", text_color=SIGNAL)

    # ── System info ticker ────────────────────────────────────────────────────
    def _tick_system_info(self):
        try:
            cpu = f"{psutil.cpu_percent()}%"
            ram = f"{psutil.virtual_memory().percent}%"
            self._api_badge.set_value(f"local actif  ·  CPU {cpu}  RAM {ram}", SIGNAL)
        except Exception:
            pass
        self.after(2500, self._tick_system_info)

    # ── Export / Copy ─────────────────────────────────────────────────────────
    def _export_results(self):
        if not self.manager.last_results:
            messagebox.showwarning("Export", "Aucun résultat à exporter.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.manager.last_results, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Export", "Résultats exportés avec succès.")

    def _copy_report(self):
        if not self._last_report_text:
            messagebox.showwarning("Copie", "Aucun rapport à copier. Lance d'abord un audit.")
            return
        self.clipboard_clear()
        self.clipboard_append(self._last_report_text)
        messagebox.showinfo("Copie", "Le rapport complet a été copié dans le presse-papier.")

    def _build_report_text(self, report: dict) -> str:
        meta    = report.get("meta", {})
        summary = report.get("summary", {})
        lines = [
            "TAFUST - RAPPORT D'AUDIT",
            f"Date: {meta.get('date', '')}",
            f"Verdict: {summary.get('verdict', '')}",
            f"Résumé: {summary.get('verdict_detail', '')}",
            f"Totaux — alertes: {summary.get('nb_alertes', 0)}, "
            f"à surveiller: {summary.get('nb_surveiller', 0)}, "
            f"légitimes: {summary.get('nb_legitimes', 0)}",
            "",
        ]
        lines.extend(self._format_report_entries("ALERTES",      report.get("alertes",    [])))
        lines.extend(self._format_report_entries("À SURVEILLER", report.get("surveiller", [])))
        lines.extend(self._format_report_entries("LÉGITIMES",    report.get("legitimes",  []), grouped=True))
        lines.append("RECOMMANDATIONS")
        hardenings = report.get("hardenings", [])
        if not hardenings:
            lines.append("- Aucune recommandation")
        else:
            for item in hardenings:
                lines.append(f"- {item.get('label', item.get('proc', '?'))}: {item.get('justification', '')}")
                for cmd in item.get("powershell", []):
                    lines.append(f"  PS> {cmd}")
                for cmd in item.get("bash", []):
                    lines.append(f"  SH> {cmd}")
        return "\n".join(lines)

    def _format_report_entries(self, title: str, entries: list, grouped: bool = False) -> list[str]:
        lines = [title]
        if not entries:
            lines += ["- Aucun", ""]
            return lines
        for item in entries:
            if grouped:
                target   = ", ".join(str(p) for p in item.get("ports_list", [])) or str(item.get("port", "?"))
                exposure = ", ".join(item.get("ips_list", [])) or item.get("ip", "?")
            else:
                target   = f"{item.get('port', '?')}/{item.get('proto', 'TCP')}"
                exposure = item.get("ip", "?")
            lines.append(f"- {item.get('proc', '?')} | {item.get('risk_level', '')} | {target} | {exposure}")
            if item.get("justification"):
                lines.append(f"  Justification: {item.get('justification')}")
            if item.get("publisher"):
                lines.append(f"  Publisher: {item.get('publisher')}")
            if item.get("company_name"):
                lines.append(f"  Éditeur: {item.get('company_name')}")
            if item.get("path"):
                lines.append(f"  Chemin: {item.get('path')}")
            if item.get("reputation_source") == "virustotal" and item.get("reputation_summary"):
                lines.append(f"  Réputation: {item.get('reputation_summary')}")
        lines.append("")
        return lines

    def _on_toggle_local(self):
        self.manager.exclude_local = self._excl_local.get()

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

APP_BG = "#08111f"
CARD_BG = "#0d1b2d"
CARD_BG_SOFT = "#10233b"
CARD_BORDER = "#17365a"
TEXT_MAIN = "#d9e3f3"
TEXT_MUTED = "#8ca2bf"
SIGNAL = "#12f0a3"
SIGNAL_SOFT = "#12372f"
DANGER = "#ff5f6d"
WARNING = "#f7b955"
INFO = "#7ea6d8"
GRID = "#0f2138"
GRID_SOFT = "#0b1729"

LOGO_PATH = get_resource_path("img", "logo.png")
ICON_PATH = get_resource_path("img", "logo.png")

RISK_COLORS = {
    "CRITIQUE": DANGER,
    "ELEVEE": "#ff8a65",
    "ELEVE": "#ff8a65",
    "MODEREE": WARNING,
    "MODERE": WARNING,
    "FAIBLE": "#7fd6a3",
    "TRES FAIBLE": SIGNAL,
}


def normalize_risk(level: str) -> str:
    return (
        (level or "")
        .replace("É", "E")
        .replace("È", "E")
        .replace("Ê", "E")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("À", "A")
        .replace("à", "a")
        .upper()
    )


def make_card(parent, fg=CARD_BG, border=CARD_BORDER, radius=20):
    return ctk.CTkFrame(parent, fg_color=fg, border_color=border, border_width=1, corner_radius=radius)


def section_title(parent, title: str, subtitle: str | None = None):
    ctk.CTkLabel(
        parent,
        text=title,
        font=ctk.CTkFont(size=20, weight="bold"),
        text_color=TEXT_MAIN,
    ).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(
            parent,
            text=subtitle,
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(4, 0))


class StatBadge(ctk.CTkFrame):
    def __init__(self, parent, title: str, value: str, accent: str = TEXT_MUTED):
        super().__init__(
            parent,
            fg_color=CARD_BG_SOFT,
            border_color=CARD_BORDER,
            border_width=1,
            corner_radius=12,
        )
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))
        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=accent,
        )
        self.value_label.grid(row=1, column=0, sticky="w", padx=12, pady=(2, 8))

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
        self._active_tab = "dashboard"
        self._current_report = None
        self._loading_step_labels = {}
        self._tab_buttons = {}
        self._active_scroll_canvas = None

        self.title("Tafust - Network Security Audit")
        self.geometry("1320x800")
        self.minsize(1080, 700)
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

    def _build_shell(self):
        shell = ctk.CTkFrame(self, fg_color=APP_BG)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.grid_rowconfigure(2, weight=1)
        shell.grid_columnconfigure(0, weight=1)

        self._background = tk.Canvas(shell, bg=APP_BG, highlightthickness=0, bd=0)
        self._background.grid(row=0, column=0, sticky="nsew")
        self._background.bind("<Configure>", self._draw_grid_background)

        self._header_card = make_card(shell)
        self._header_card.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 12))
        self._header_card.grid_columnconfigure(0, weight=1)
        self._header_card.grid_columnconfigure(1, weight=0)
        self._build_header(self._header_card)

        self._scan_card = make_card(shell)
        self._scan_card.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
        self._scan_card.grid_columnconfigure(0, weight=1)
        self._build_scan_panel(self._scan_card)

        self._results_card = make_card(shell)
        self._results_card.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 16))
        self._results_card.grid_columnconfigure(0, weight=1)
        self._results_card.grid_rowconfigure(1, weight=1)
        self._results_card.grid_propagate(False)

        self._summary_frame = ctk.CTkFrame(self._results_card, fg_color="transparent")
        self._summary_frame.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 0))
        self._summary_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._results_body = ctk.CTkScrollableFrame(
            self._results_card,
            fg_color="transparent",
            corner_radius=0,
        )
        self._results_body.grid(row=1, column=0, sticky="nsew", padx=18, pady=12)
        self._results_body.grid_columnconfigure(0, weight=1)
        self._enable_mousewheel_scroll(self._results_body)

    def _enable_mousewheel_scroll(self, scrollable_frame):
        canvas = getattr(scrollable_frame, "_parent_canvas", None)
        if canvas is None:
            return

        def on_enter(_event):
            self._active_scroll_canvas = canvas

        def on_leave(_event):
            if self._active_scroll_canvas is canvas:
                self._active_scroll_canvas = None

        def on_mousewheel(event):
            if self._active_scroll_canvas is not canvas:
                return
            delta = int(-event.delta / 120) if event.delta else 0
            if delta:
                canvas.yview_scroll(delta, "units")

        scrollable_frame.bind("<Enter>", on_enter)
        scrollable_frame.bind("<Leave>", on_leave)
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        self.bind_all("<MouseWheel>", on_mousewheel, add="+")

    def _draw_grid_background(self, event):
        canvas = event.widget
        canvas.delete("grid")
        width = max(event.width, 1)
        height = max(event.height, 1)
        for x in range(0, width, 36):
            color = GRID if x % 180 else GRID_SOFT
            canvas.create_line(x, 0, x, height, fill=color, tags="grid")
        for y in range(0, height, 36):
            color = GRID if y % 180 else GRID_SOFT
            canvas.create_line(0, y, width, y, fill=color, tags="grid")
        canvas.create_rectangle(0, 0, width * 0.7, 56, fill="#0a3b36", outline="", tags="grid")

    def _build_header(self, parent):
        left = ctk.CTkFrame(parent, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=20, pady=20)

        logo_wrap = ctk.CTkFrame(
            left,
            fg_color="#0d2433",
            border_color="#0d6b5f",
            border_width=1,
            corner_radius=18,
            width=74,
            height=74,
        )
        logo_wrap.pack(side="left", padx=(0, 16))
        logo_wrap.pack_propagate(False)

        try:
            if os.path.exists(LOGO_PATH):
                img = Image.open(LOGO_PATH)
                self._logo = ctk.CTkImage(light_image=img, dark_image=img, size=(54, 54))
                ctk.CTkLabel(logo_wrap, image=self._logo, text="").place(relx=0.5, rely=0.5, anchor="center")
        except Exception:
            ctk.CTkLabel(
                logo_wrap,
                text="T",
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color=SIGNAL,
            ).place(relx=0.5, rely=0.5, anchor="center")

        text_block = ctk.CTkFrame(left, fg_color="transparent")
        text_block.pack(side="left", anchor="center")

        meta = ctk.CTkFrame(text_block, fg_color="transparent")
        meta.pack(anchor="w")
        ctk.CTkLabel(
            meta,
            text="TAFUST",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=SIGNAL,
        ).pack(side="left")
        ctk.CTkLabel(
            meta,
            text="v0.1",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
            fg_color=CARD_BG_SOFT,
            corner_radius=8,
            padx=8,
            pady=2,
        ).pack(side="left", padx=(12, 0))

        ctk.CTkLabel(
            text_block,
            text="Network Security Audit",
            font=ctk.CTkFont(size=40, weight="bold"),
            text_color=TEXT_MAIN,
        ).pack(anchor="w", pady=(10, 0))
        ctk.CTkLabel(
            text_block,
            text="Ports - Processus - Classification des risques",
            font=ctk.CTkFont(size=20),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(8, 0))

        self._header_badges = ctk.CTkFrame(parent, fg_color="transparent")
        self._header_badges.grid(row=0, column=1, sticky="e", padx=20, pady=20)
        self._api_badge = StatBadge(self._header_badges, "Moteur", "local actif", SIGNAL)
        self._api_badge.pack(anchor="e", pady=(0, 10))
        self._os_badge = StatBadge(self._header_badges, "Systeme", self.manager.os_type, TEXT_MAIN)
        self._os_badge.pack(anchor="e", pady=(0, 10))
        vt_color = SIGNAL if bool(os.getenv("VIRUSTOTAL_API_KEY")) else WARNING
        vt_value = "VirusTotal actif" if bool(os.getenv("VIRUSTOTAL_API_KEY")) else "VirusTotal inactif"
        self._vt_badge = StatBadge(self._header_badges, "Reputation", vt_value, vt_color)
        self._vt_badge.pack(anchor="e")

    def _build_scan_panel(self, parent):
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 8))
        top.grid_columnconfigure(0, weight=1)
        section_title(
            top,
            "Lancer un scan",
            "Inspecte les ports en ecoute et classe les processus par niveau de risque",
        )

        control_row = ctk.CTkFrame(parent, fg_color="transparent")
        control_row.grid(row=1, column=0, sticky="ew", padx=20, pady=(6, 14))
        control_row.grid_columnconfigure(1, weight=1)

        self._excl_local = tk.BooleanVar(value=False)
        self._exclude_toggle = ctk.CTkSwitch(
            control_row,
            text="Exclure les listeners loopback",
            variable=self._excl_local,
            command=self._on_toggle_local,
            progress_color=SIGNAL,
            button_color="#9bb0c8",
            button_hover_color="#c0d2e7",
            fg_color="#0a1220",
            border_color=CARD_BORDER,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_MUTED,
            switch_width=40,
            switch_height=22,
        )
        self._exclude_toggle.grid(row=0, column=0, sticky="w", padx=(0, 18))

        self._scan_btn = ctk.CTkButton(
            control_row,
            text="Lancer l'audit",
            command=self._start_scan,
            fg_color=SIGNAL,
            hover_color="#0fd48f",
            text_color="#02150f",
            font=ctk.CTkFont(size=26, weight="bold"),
            height=48,
            corner_radius=16,
        )
        self._scan_btn.grid(row=0, column=1, sticky="ew")

        action_row = ctk.CTkFrame(parent, fg_color="transparent")
        action_row.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))
        self._status_lbl = ctk.CTkLabel(
            action_row,
            text="Pret pour un audit local",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
        )
        self._status_lbl.pack(side="left")

        self._copy_btn = ctk.CTkButton(
            action_row,
            text="Copier rapport",
            command=self._copy_report,
            fg_color="transparent",
            border_width=1,
            border_color=CARD_BORDER,
            hover_color=CARD_BG_SOFT,
            text_color=TEXT_MAIN,
            width=118,
            height=34,
            corner_radius=12,
        )
        self._copy_btn.pack(side="right", padx=(10, 0))

        self._export_btn = ctk.CTkButton(
            action_row,
            text="Exporter JSON",
            command=self._export_results,
            fg_color="transparent",
            border_width=1,
            border_color=CARD_BORDER,
            hover_color=CARD_BG_SOFT,
            text_color=TEXT_MAIN,
            width=118,
            height=34,
            corner_radius=12,
        )
        self._export_btn.pack(side="right")

    def _clear_results(self):
        for widget in self._summary_frame.winfo_children():
            widget.destroy()
        for widget in self._results_body.winfo_children():
            widget.destroy()
        self._loading_frame = None
        self._empty_state_frame = None
        self._loading_step_labels = {}

    def _render_empty_state(self):
        self._clear_results()
        self._empty_state_frame = ctk.CTkFrame(self._results_body, fg_color="transparent")
        self._empty_state_frame.grid(row=0, column=0, sticky="nsew", pady=40)
        self._empty_state_frame.grid_columnconfigure(0, weight=1)

        shield = ctk.CTkFrame(
            self._empty_state_frame,
            fg_color="#15263f",
            border_color=CARD_BORDER,
            border_width=1,
            corner_radius=22,
            width=64,
            height=64,
        )
        shield.grid(row=0, column=0, pady=(34, 14))
        shield.grid_propagate(False)
        ctk.CTkLabel(
            shield,
            text="[]",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=INFO,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self._empty_state_frame,
            text="Aucun rapport disponible",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=TEXT_MAIN,
        ).grid(row=1, column=0, pady=(0, 10))
        ctk.CTkLabel(
            self._empty_state_frame,
            text="Lance un audit depuis le panneau ci-dessus pour afficher les resultats.",
            font=ctk.CTkFont(size=17),
            text_color=TEXT_MUTED,
        ).grid(row=2, column=0, pady=(0, 34))

    def _render_loading_state(self):
        self._clear_results()
        self._loading_frame = ctk.CTkFrame(self._results_body, fg_color="transparent")
        self._loading_frame.grid(row=0, column=0, sticky="nsew", pady=24)
        self._loading_frame.grid_columnconfigure(0, weight=1)

        ring = ctk.CTkFrame(
            self._loading_frame,
            fg_color="#0f2337",
            border_color="#1d466d",
            border_width=1,
            corner_radius=35,
            width=88,
            height=88,
        )
        ring.grid(row=0, column=0, pady=(20, 12))
        ring.grid_propagate(False)
        ctk.CTkLabel(
            ring,
            text="SCAN",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=SIGNAL,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self._loading_frame,
            text="Scan en cours...",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=SIGNAL,
        ).grid(row=1, column=0, pady=(0, 6))
        ctk.CTkLabel(
            self._loading_frame,
            text="Inspection des ports, des processus et de la reputation locale.",
            font=ctk.CTkFont(size=14),
            text_color=TEXT_MUTED,
        ).grid(row=2, column=0, pady=(0, 18))

        steps = [
            ("collect", "Collecte des connexions reseau"),
            ("resolve", "Resolution des processus"),
            ("filter", "Filtrage des listeners"),
            ("reputation", "Enrichissement de reputation"),
            ("analyze", "Analyse des risques"),
        ]
        for index, (step_key, step) in enumerate(steps):
            row = ctk.CTkFrame(
                self._loading_frame,
                fg_color=CARD_BG_SOFT,
                border_color=CARD_BORDER,
                border_width=1,
                corner_radius=12,
            )
            row.grid(row=3 + index, column=0, sticky="ew", padx=160, pady=5)
            ctk.CTkLabel(
                row,
                text=step,
                font=ctk.CTkFont(size=13),
                text_color=TEXT_MAIN,
            ).pack(side="left", padx=14, pady=10)
            status = ctk.CTkLabel(
                row,
                text="en attente",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=TEXT_MUTED,
            )
            status.pack(side="right", padx=14)
            self._loading_step_labels[step_key] = status

    def _start_scan(self):
        self._scan_btn.configure(state="disabled", text="Analyse en cours...")
        self._status_lbl.configure(text="Scan reseau en cours...", text_color=SIGNAL)
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
                    label.configure(text="en cours", text_color=SIGNAL)
                elif label.cget("text") == "en cours":
                    label.configure(text="termine", text_color=INFO)
            if step == "done":
                for label in self._loading_step_labels.values():
                    if label.cget("text") == "en cours":
                        label.configure(text="termine", text_color=INFO)

        self.after(0, update)

    def _on_scan_ok(self, report: dict):
        self.manager.progress_callback = None
        self.after(0, lambda: self._render_report(report))

    def _on_scan_err(self, msg: str):
        def show_error():
            self.manager.progress_callback = None
            messagebox.showerror("Erreur de scan", msg)
            self._scan_btn.configure(state="normal", text="Lancer l'audit")
            self._status_lbl.configure(text="Erreur pendant le scan", text_color=DANGER)
            self._render_empty_state()

        self.after(0, show_error)

    def _render_summary_cards(self, summary: dict, meta: dict):
        cards = [
            ("Verdict", summary.get("verdict", "-"), SIGNAL if summary.get("nb_alertes", 0) == 0 else DANGER),
            ("Entrees totales", str(summary.get("total", 0)), TEXT_MAIN),
            ("Alertes", str(summary.get("nb_alertes", 0)), DANGER),
            ("Legitimes", str(summary.get("nb_legitimes", 0)), SIGNAL),
        ]
        if meta.get("total_raw") is not None:
            cards[1] = ("Entrees totales", f"{summary.get('total', 0)} / {meta.get('total_raw', 0)}", TEXT_MAIN)

        for idx, (title, value, accent) in enumerate(cards):
            card = make_card(self._summary_frame, fg=CARD_BG_SOFT, radius=16)
            card.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 10, 0), pady=(0, 8))
            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=12),
                text_color=TEXT_MUTED,
            ).pack(anchor="w", padx=16, pady=(14, 4))
            ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color=accent,
            ).pack(anchor="w", padx=16, pady=(0, 14))

    def _build_tab_bar(self, parent, report: dict):
        tabs = [
            ("dashboard", "Dashboard", len((report.get("alertes") or [])) + len((report.get("surveiller") or []))),
            ("alertes", "Alertes", len(report.get("alertes") or [])),
            ("surveiller", "Surveillance", len(report.get("surveiller") or [])),
            ("legitimes", "Legitimes", len(report.get("legitimes") or [])),
            ("hardenings", "Durcissement", len(report.get("hardenings") or [])),
            ("raw", "Donnees brutes", 0),
        ]
        self._tab_buttons = {}
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        bar.grid_columnconfigure(0, weight=1)

        nav = ctk.CTkFrame(bar, fg_color="transparent")
        nav.pack(side="left", fill="x", expand=True)
        for tab_id, label, count in tabs:
            text = f"{label}  {count}" if count > 0 else label
            btn = ctk.CTkButton(
                nav,
                text=text,
                command=lambda value=tab_id: self._set_active_tab(value),
                fg_color="transparent",
                hover_color=CARD_BG_SOFT,
                text_color=TEXT_MUTED,
                border_width=0,
                corner_radius=12,
                height=32,
                width=112,
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            btn.pack(side="left", padx=(0, 8))
            self._tab_buttons[tab_id] = btn

        export_btn = ctk.CTkButton(
            bar,
            text="Export JSON",
            command=self._export_results,
            fg_color=CARD_BG_SOFT,
            hover_color="#183251",
            text_color=TEXT_MAIN,
            border_width=1,
            border_color=CARD_BORDER,
            corner_radius=12,
            height=32,
            width=112,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        export_btn.pack(side="right")
        self._sync_tab_styles()

    def _sync_tab_styles(self):
        for tab_id, btn in self._tab_buttons.items():
            active = tab_id == self._active_tab
            btn.configure(
                fg_color=CARD_BG_SOFT if active else "transparent",
                text_color=TEXT_MAIN if active else TEXT_MUTED,
                border_width=1 if active else 0,
                border_color=SIGNAL if active else CARD_BORDER,
            )

    def _set_active_tab(self, tab_id: str):
        self._active_tab = tab_id
        self._sync_tab_styles()
        if self._current_report:
            self._render_tab_content(self._current_report)

    def _risk_chip(self, parent, level: str):
        normalized = normalize_risk(level)
        color = RISK_COLORS.get(normalized, INFO)
        chip = ctk.CTkFrame(parent, fg_color="#11253d", border_color=color, border_width=1, corner_radius=999)
        ctk.CTkLabel(
            chip,
            text=level or "INCONNU",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=color,
        ).pack(padx=8, pady=4)
        return chip

    def _render_result_section(self, parent, title: str, subtitle: str, items: list, grouped: bool = False):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", pady=(0, 22))
        section_title(section, title, subtitle)

        if not items:
            empty = make_card(section, fg=CARD_BG_SOFT, radius=16)
            empty.pack(fill="x", pady=(12, 0))
            ctk.CTkLabel(
                empty,
                text="Aucun element dans cette section.",
                font=ctk.CTkFont(size=14),
                text_color=TEXT_MUTED,
            ).pack(anchor="w", padx=16, pady=14)
            return

        for item in items:
            risk_label = item.get("risk_level", "INCONNU")
            risk_color = RISK_COLORS.get(normalize_risk(risk_label), INFO)
            card = make_card(section, fg=CARD_BG_SOFT, radius=16)
            card.pack(fill="x", pady=(12, 0))
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(14, 6))

            left = ctk.CTkFrame(top, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)

            proc = item.get("proc", "?")
            if grouped:
                ports = ", ".join(str(p) for p in item.get("ports_list", [])) or str(item.get("port", "?"))
                ips = ", ".join(item.get("ips_list", [])) or item.get("ip", "?")
                title_line = f"{proc}  |  Ports: {ports}"
                detail_line = f"IPs: {ips}  |  {item.get('count', 1)} instance(s)"
            else:
                title_line = f"{proc}  |  Port {item.get('port', '?')}/{item.get('proto', 'TCP')}"
                detail_line = item.get("ip", "?")
                if item.get("exposure"):
                    detail_line = f"{detail_line}  |  {item.get('exposure')}"

            ctk.CTkLabel(
                left,
                text=title_line,
                font=ctk.CTkFont(size=17, weight="bold"),
                text_color=TEXT_MAIN,
            ).pack(anchor="w")
            ctk.CTkLabel(
                left,
                text=detail_line,
                font=ctk.CTkFont(size=13),
                text_color=TEXT_MUTED,
            ).pack(anchor="w", pady=(4, 0))

            self._risk_chip(top, risk_label).pack(side="right", anchor="n", padx=(12, 0))

            details = []
            if item.get("label") and item.get("label") != proc:
                details.append(item.get("label"))
            if item.get("justification"):
                details.append(item.get("justification"))
            if item.get("publisher"):
                details.append(f"Publisher: {item.get('publisher')}")
            if item.get("company_name"):
                details.append(f"Company: {item.get('company_name')}")
            if item.get("signature_status"):
                details.append(f"Signature: {item.get('signature_status')}")
            if item.get("path"):
                details.append(f"Path: {item.get('path')}")
            if item.get("reputation_source") == "virustotal" and item.get("reputation_summary"):
                details.append(f"Reputation: {item.get('reputation_summary')}")

            if details:
                body = ctk.CTkFrame(card, fg_color="transparent")
                body.pack(fill="x", padx=16, pady=(0, 14))
                for detail in details:
                    ctk.CTkLabel(
                        body,
                        text=detail,
                        font=ctk.CTkFont(size=12),
                        text_color=risk_color if detail == item.get("label") else TEXT_MUTED,
                        wraplength=900,
                        justify="left",
                    ).pack(anchor="w", pady=(4, 0))

    def _render_raw_data(self, parent, payload: dict):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="both", expand=True, pady=(0, 12))
        section_title(
            section,
            "Donnees brutes",
            "Resultats JSON complets retournes par l'application.",
        )
        textbox = ctk.CTkTextbox(
            section,
            fg_color=CARD_BG_SOFT,
            border_color=CARD_BORDER,
            border_width=1,
            corner_radius=16,
            text_color=SIGNAL,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="none",
            height=340,
        )
        textbox.pack(fill="both", expand=True, pady=(12, 0))
        textbox.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False))
        textbox.configure(state="disabled")

    def _render_hardenings(self, parent, hardenings: list):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", pady=(0, 12))
        section_title(
            section,
            "Recommandations de durcissement",
            "Commandes PowerShell et Bash pour reduire la surface d'attaque.",
        )

        if not hardenings:
            empty = make_card(section, fg=CARD_BG_SOFT, radius=16)
            empty.pack(fill="x", pady=(12, 0))
            ctk.CTkLabel(
                empty,
                text="Aucune recommandation de durcissement disponible pour ce scan.",
                font=ctk.CTkFont(size=14),
                text_color=TEXT_MUTED,
            ).pack(anchor="w", padx=16, pady=14)
            return

        for item in hardenings:
            card = make_card(section, fg=CARD_BG_SOFT, radius=16)
            card.pack(fill="x", pady=(12, 0))
            ctk.CTkLabel(
                card,
                text=item.get("label", item.get("proc", "?")),
                font=ctk.CTkFont(size=17, weight="bold"),
                text_color=SIGNAL,
            ).pack(anchor="w", padx=16, pady=(14, 4))
            ctk.CTkLabel(
                card,
                text=item.get("justification", ""),
                font=ctk.CTkFont(size=13),
                text_color=TEXT_MUTED,
                wraplength=900,
                justify="left",
            ).pack(anchor="w", padx=16, pady=(0, 8))

            for cmd in item.get("powershell", []):
                ctk.CTkLabel(
                    card,
                    text=f"PS> {cmd}",
                    font=ctk.CTkFont(family="Consolas", size=11),
                    text_color=INFO,
                ).pack(anchor="w", padx=16, pady=(2, 0))
            for cmd in item.get("bash", []):
                ctk.CTkLabel(
                    card,
                    text=f"SH> {cmd}",
                    font=ctk.CTkFont(family="Consolas", size=11),
                    text_color=SIGNAL,
                ).pack(anchor="w", padx=16, pady=(2, 0))
            ctk.CTkLabel(card, text="", height=6).pack()

    def _render_tab_content(self, report: dict):
        for widget in self._results_body.winfo_children():
            widget.destroy()

        content = ctk.CTkFrame(self._results_body, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)

        if self._active_tab == "dashboard":
            self._render_result_section(
                content,
                "File de priorite",
                "Alertes et services a examiner en premier.",
                (report.get("alertes") or []) + (report.get("surveiller") or []),
            )
            self._render_result_section(
                content,
                "Alertes",
                "Processus suspects ou exposes sur le reseau sans preuve de confiance.",
                report.get("alertes") or [],
            )
            self._render_result_section(
                content,
                "A surveiller",
                "Services watchlist et outils d'acces distant.",
                report.get("surveiller") or [],
            )
            self._render_result_section(
                content,
                "Services legitimes",
                "Processus connus, groupes par application.",
                report.get("legitimes") or [],
                grouped=True,
            )
            self._render_hardenings(content, report.get("hardenings") or [])
            return

        if self._active_tab == "alertes":
            self._render_result_section(
                content,
                "Alertes",
                "Processus suspects ou exposes sur le reseau sans preuve de confiance.",
                report.get("alertes") or [],
            )
            return

        if self._active_tab == "surveiller":
            self._render_result_section(
                content,
                "A surveiller",
                "Services watchlist et outils d'acces distant.",
                report.get("surveiller") or [],
            )
            return

        if self._active_tab == "legitimes":
            self._render_result_section(
                content,
                "Services legitimes",
                "Processus classes comme surs, groupes par application.",
                report.get("legitimes") or [],
                grouped=True,
            )
            return

        if self._active_tab == "hardenings":
            self._render_hardenings(content, report.get("hardenings") or [])
            return

        if self._active_tab == "raw":
            payload = {
                "report": report,
                "raw_results": self.manager.last_results,
            }
            self._render_raw_data(content, payload)

    def _render_report(self, report: dict):
        self._clear_results()
        self._current_report = report

        meta = report.get("meta", {})
        summary = report.get("summary", {})
        self._last_report_text = self._build_report_text(report)

        self._render_summary_cards(summary, meta)

        verdict_card = make_card(self._results_body, fg="#0f2337", radius=18)
        verdict_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        verdict_color = SIGNAL if summary.get("nb_alertes", 0) == 0 else DANGER
        ctk.CTkLabel(
            verdict_card,
            text=summary.get("verdict", "Verdict indisponible"),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=verdict_color,
        ).pack(anchor="w", padx=18, pady=(16, 6))
        ctk.CTkLabel(
            verdict_card,
            text=summary.get("verdict_detail", ""),
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
            wraplength=920,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 8))
        ctk.CTkLabel(
            verdict_card,
            text=f"Date du rapport: {meta.get('date', '-')}",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=18, pady=(0, 16))
        self._build_tab_bar(self._results_body, report)
        self._render_tab_content(report)

        self._scan_btn.configure(state="normal", text="Lancer l'audit")
        self._status_lbl.configure(text="Audit termine", text_color=SIGNAL)

    def _tick_system_info(self):
        try:
            cpu = f"{psutil.cpu_percent()}%"
            ram = f"{psutil.virtual_memory().percent}%"
            self._api_badge.set_value(f"local actif  |  CPU {cpu}  RAM {ram}", SIGNAL)
        except Exception:
            pass
        self.after(2500, self._tick_system_info)

    def _export_results(self):
        if not self.manager.last_results:
            messagebox.showwarning("Export", "Aucun resultat a exporter.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(self.manager.last_results, handle, indent=4, ensure_ascii=False)
            messagebox.showinfo("Export", "Resultats exportes avec succes.")

    def _copy_report(self):
        if not self._last_report_text:
            messagebox.showwarning("Copie", "Aucun rapport a copier. Lance d'abord un audit.")
            return
        self.clipboard_clear()
        self.clipboard_append(self._last_report_text)
        messagebox.showinfo("Copie", "Le rapport complet a ete copie dans le presse-papier.")

    def _build_report_text(self, report: dict) -> str:
        meta = report.get("meta", {})
        summary = report.get("summary", {})
        lines = [
            "TAFUST - RAPPORT D'AUDIT",
            f"Date: {meta.get('date', '')}",
            f"Verdict: {summary.get('verdict', '')}",
            f"Resume: {summary.get('verdict_detail', '')}",
            f"Totaux - alertes: {summary.get('nb_alertes', 0)}, a surveiller: {summary.get('nb_surveiller', 0)}, legitimes: {summary.get('nb_legitimes', 0)}",
            "",
        ]
        lines.extend(self._format_report_entries("ALERTES", report.get("alertes", [])))
        lines.extend(self._format_report_entries("A SURVEILLER", report.get("surveiller", [])))
        lines.extend(self._format_report_entries("LEGITIMES", report.get("legitimes", []), grouped=True))
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
            lines.append("- Aucun")
            lines.append("")
            return lines

        for item in entries:
            if grouped:
                target = ", ".join(str(p) for p in item.get("ports_list", [])) or str(item.get("port", "?"))
                exposure = ", ".join(item.get("ips_list", [])) or item.get("ip", "?")
            else:
                target = f"{item.get('port', '?')}/{item.get('proto', 'TCP')}"
                exposure = item.get("ip", "?")

            lines.append(f"- {item.get('proc', '?')} | {item.get('risk_level', '')} | {target} | {exposure}")
            if item.get("label") and item.get("label") != item.get("proc"):
                lines.append(f"  Label: {item.get('label')}")
            if item.get("justification"):
                lines.append(f"  Justification: {item.get('justification')}")
            if item.get("publisher"):
                lines.append(f"  Publisher: {item.get('publisher')}")
            if item.get("company_name"):
                lines.append(f"  Company: {item.get('company_name')}")
            if item.get("signature_status"):
                lines.append(f"  Signature: {item.get('signature_status')}")
            if item.get("path"):
                lines.append(f"  Path: {item.get('path')}")
            if item.get("reputation_source") == "virustotal" and item.get("reputation_summary"):
                lines.append(f"  Reputation: {item.get('reputation_summary')}")
        lines.append("")
        return lines

    def _on_toggle_local(self):
        self.manager.exclude_local = self._excl_local.get()

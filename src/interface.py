"""
interface.py — Interface Tafust — Rapport d'Audit 4 sections
  1. Résumé Exécutif
  2. Matrice des Risques
  3. Analyse Technique Détaillée
  4. Recommandations de Hardening
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from PIL import Image
import os
import json
import psutil
from src.scanner_manager import ScannerManager

# ── Palette ───────────────────────────────────────────────────────────────────
COLOR_BG      = ("#f0f2f5", "#0d0d0d")
COLOR_SIDEBAR = ("#e8eaed", "#111111")
COLOR_CARD    = ("#ffffff",  "#181818")
COLOR_ACCENT  = ("#1a73e8", "#00d4ff")
COLOR_TEXT    = ("#212529", "#e0e0e0")
COLOR_MUTED   = ("#6c757d", "#888888")

C_ALERTE     = "#c0392b"
C_SURVEILLER = "#c87f0a"
C_LEGITIME   = "#1e7e34"
C_HARDENING  = "#6f42c1"

LOGO_PATH = "img/logo.png"

RISK_COLORS = {
    "CRITIQUE":    "#8b0000",
    "ÉLEVÉ":       "#c0392b",
    "MODÉRÉ":      "#c87f0a",
    "FAIBLE":      "#b8860b",
    "TRÈS FAIBLE": "#1e7e34",
}

# ── Helpers visuels ───────────────────────────────────────────────────────────

def _sep(parent, color="#2a2a2a", pady=(8, 8)):
    f = ctk.CTkFrame(parent, fg_color=color, height=1, corner_radius=0)
    f.pack(fill="x", padx=15, pady=pady)


def _section_title(parent, icon, title, count, color):
    """En-tête de section avec compteur bulle."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", padx=15, pady=(22, 6))

    ctk.CTkLabel(frame, text=f"{icon}  {title}",
                 font=ctk.CTkFont(size=15, weight="bold"),
                 text_color=color).pack(side="left")

    bubble = ctk.CTkFrame(frame, fg_color=color, corner_radius=12, width=36, height=24)
    bubble.pack(side="left", padx=10)
    bubble.pack_propagate(False)
    ctk.CTkLabel(bubble, text=str(count),
                 font=ctk.CTkFont(size=11, weight="bold"),
                 text_color="white").place(relx=0.5, rely=0.5, anchor="center")


def _copy_button(parent, text_to_copy: str, label="📋 Copier"):
    """Petit bouton de copie dans le presse-papier."""
    def _copy():
        parent.clipboard_clear()
        parent.clipboard_append(text_to_copy)

    ctk.CTkButton(parent, text=label, command=_copy,
                  fg_color="transparent", border_width=1, border_color="#444",
                  text_color=COLOR_TEXT, hover_color=COLOR_ACCENT,
                  width=110, height=24,
                  font=ctk.CTkFont(size=10)).pack(side="right", padx=4, pady=4)


# ── Section 1 : Résumé Exécutif ───────────────────────────────────────────────

def render_executive_summary(parent, summary: dict, meta: dict):
    nb_a = summary.get("nb_alertes", 0)
    nb_s = summary.get("nb_surveiller", 0)
    nb_l = summary.get("nb_legitimes", 0)
    verdict = summary.get("verdict", "")
    detail  = summary.get("verdict_detail", "")
    date    = meta.get("date", "")

    is_ok     = nb_a == 0
    border    = C_LEGITIME if is_ok else C_ALERTE
    bg        = "#0d1f0d" if is_ok else "#1f0d0d"

    frame = ctk.CTkFrame(parent, fg_color=bg, border_color=border,
                         border_width=2, corner_radius=12)
    frame.pack(fill="x", padx=15, pady=(10, 4))

    # Titre + date
    top = ctk.CTkFrame(frame, fg_color="transparent")
    top.pack(fill="x", padx=20, pady=(14, 4))
    ctk.CTkLabel(top, text=f"{'✅' if is_ok else '⚠️'}  {verdict}",
                 font=ctk.CTkFont(size=17, weight="bold"),
                 text_color=border).pack(side="left")
    ctk.CTkLabel(top, text=f"Audit du {date}",
                 font=ctk.CTkFont(size=11),
                 text_color=COLOR_MUTED).pack(side="right")

    # Détail
    ctk.CTkLabel(frame, text=detail,
                 font=ctk.CTkFont(size=12), text_color=COLOR_TEXT,
                 wraplength=720, justify="left").pack(anchor="w", padx=20, pady=(2, 6))

    # Compteurs badges
    badges = ctk.CTkFrame(frame, fg_color="transparent")
    badges.pack(anchor="w", padx=20, pady=(0, 12))
    for label, val, col in [
        (f"🔴  {nb_a} Alerte(s)",       nb_a, C_ALERTE),
        (f"🟡  {nb_s} À Surveiller",     nb_s, C_SURVEILLER),
        (f"🟢  {nb_l} Légitimes écartés", nb_l, C_LEGITIME),
    ]:
        ctk.CTkLabel(badges, text=label,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=col).pack(side="left", padx=14)


# ── Section 2 : Matrice des Risques ──────────────────────────────────────────

def render_risk_matrix(parent, alertes, surveiller, legitimes_grouped):
    """Tableau consolidé de tous les services."""
    _section_title(parent, "📊", "Matrice des Risques",
                   len(alertes) + len(surveiller) + len(legitimes_grouped), COLOR_ACCENT[1])

    table = ctk.CTkFrame(parent, fg_color=COLOR_CARD,
                         border_color="#2a2a2a", border_width=1, corner_radius=8)
    table.pack(fill="x", padx=20, pady=4)

    # En-tête
    header = ctk.CTkFrame(table, fg_color="#1a1a2e", corner_radius=6)
    header.pack(fill="x", padx=8, pady=(8, 2))
    for col, w in [("Processus", 220), ("Port(s)", 100), ("Risque", 110), ("Justification", 0)]:
        ctk.CTkLabel(header, text=col,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#aaaacc", width=w, anchor="w").pack(side="left", padx=8, pady=6)

    # Lignes — ordre : ALERTE, À SURVEILLER, LÉGITIMES
    all_rows = (
        [(e, C_ALERTE)     for e in alertes]     +
        [(e, C_SURVEILLER) for e in surveiller]   +
        [(e, C_LEGITIME)   for e in legitimes_grouped]
    )

    for i, (e, col) in enumerate(all_rows):
        bg = "#141414" if i % 2 == 0 else "#111111"
        row = ctk.CTkFrame(table, fg_color=bg, corner_radius=0)
        row.pack(fill="x", padx=8, pady=1)

        proc  = e.get("proc", "?")
        ports = e.get("ports_list", [e.get("port", "?")])
        ports_str = ", ".join(str(p) for p in ports[:4])
        if len(ports) > 4:
            ports_str += f" +{len(ports)-4}"

        risk_icon  = e.get("risk_icon", "🟢")
        risk_level = e.get("risk_level", "TRÈS FAIBLE")
        justif     = e.get("justification", "")[:80] + ("…" if len(e.get("justification", "")) > 80 else "")

        for text, w in [
            (proc,      220),
            (ports_str, 100),
            (f"{risk_icon} {risk_level}", 110),
            (justif,    0),
        ]:
            ctk.CTkLabel(row, text=text,
                         font=ctk.CTkFont(size=11),
                         text_color=RISK_COLORS.get(risk_level, COLOR_TEXT[1]) if "Risque" not in text else RISK_COLORS.get(risk_level, "#aaa"),
                         width=w, anchor="w").pack(side="left", padx=8, pady=5)


# ── Section 3 : Analyse Technique Détaillée ──────────────────────────────────

def _detail_card(parent, e: dict, border_color: str, grouped=False):
    """Carte d'analyse détaillée pour une entrée."""
    card = ctk.CTkFrame(parent, fg_color=COLOR_CARD,
                        border_color=border_color, border_width=1, corner_radius=8)
    card.pack(fill="x", padx=20, pady=5)

    inner = ctk.CTkFrame(card, fg_color="transparent")
    inner.pack(fill="x", padx=14, pady=10)

    left = ctk.CTkFrame(inner, fg_color="transparent")
    left.pack(side="left", fill="x", expand=True)

    proc  = e.get("proc", "?")
    label = e.get("label", proc)
    risk  = e.get("risk_level", "TRÈS FAIBLE")
    icon  = e.get("risk_icon", "🟢")

    if grouped:
        ports_str = ", ".join(str(p) for p in e.get("ports_list", [e.get("port", "?")]))
        ips_str   = ", ".join(e.get("ips_list", [e.get("ip", "?")]))
        top = f"{proc}  ·  Ports : {ports_str}"
        sub = f"IPs : {ips_str}  ·  {e.get('count', 1)} instance(s)"
    else:
        top = f"{proc}  ·  Port {e.get('port','?')}/{e.get('proto','TCP')}  ·  {e.get('ip','?')}"
        sub = e.get("exposure", "")

    ctk.CTkLabel(left, text=top,
                 font=ctk.CTkFont(size=12, weight="bold"),
                 text_color=COLOR_TEXT, anchor="w").pack(anchor="w")

    if label and label != proc:
        ctk.CTkLabel(left, text=label,
                     font=ctk.CTkFont(size=11),
                     text_color=border_color, anchor="w").pack(anchor="w")

    if sub:
        ctk.CTkLabel(left, text=sub,
                     font=ctk.CTkFont(size=10), text_color=COLOR_MUTED,
                     anchor="w").pack(anchor="w", pady=(1, 0))

    justif = e.get("justification", "")
    if justif:
        ctk.CTkLabel(left, text=justif,
                     font=ctk.CTkFont(size=10), text_color="#bbbbbb",
                     wraplength=560, justify="left", anchor="w").pack(anchor="w", pady=(3, 0))

    # Droite : badge risque
    right = ctk.CTkFrame(inner, fg_color="transparent")
    right.pack(side="right", anchor="n")
    ctk.CTkLabel(right, text=f"{icon} {risk}",
                 font=ctk.CTkFont(size=10, weight="bold"),
                 text_color=RISK_COLORS.get(risk, "#aaa")).pack(anchor="e")


def render_detailed_analysis(parent, alertes, surveiller, legitimes_grouped):
    total = len(alertes) + len(surveiller) + len(legitimes_grouped)
    _section_title(parent, "🔬", "Analyse Technique Détaillée", total, "#aaaacc")

    # Alertes
    if alertes:
        ctk.CTkLabel(parent, text="  🔴  Services inconnus / exposés",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C_ALERTE).pack(anchor="w", padx=22, pady=(6, 2))
        for e in alertes:
            _detail_card(parent, e, C_ALERTE)

    # À surveiller
    if surveiller:
        ctk.CTkLabel(parent, text="  🟡  Services à vérifier",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C_SURVEILLER).pack(anchor="w", padx=22, pady=(10, 2))
        for e in surveiller:
            _detail_card(parent, e, C_SURVEILLER)

    # Légitimes groupés
    if legitimes_grouped:
        ctk.CTkLabel(parent, text="  🟢  Processus système / légitimes (groupés)",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C_LEGITIME).pack(anchor="w", padx=22, pady=(10, 2))
        for e in legitimes_grouped:
            _detail_card(parent, e, "#2d5a2d", grouped=True)


# ── Section 4 : Recommandations de Hardening ─────────────────────────────────

def render_hardenings(parent, hardenings: list):
    _section_title(parent, "🔧", "Recommandations de Hardening", len(hardenings), C_HARDENING)

    if not hardenings:
        ctk.CTkLabel(parent,
                     text="  Aucune action de hardening requise. Système optimalement configuré.",
                     font=ctk.CTkFont(size=12), text_color=C_LEGITIME).pack(anchor="w", padx=24, pady=8)
        return

    for h in hardenings:
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD,
                            border_color=C_HARDENING, border_width=1, corner_radius=8)
        card.pack(fill="x", padx=20, pady=5)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)

        # Titre
        title_row = ctk.CTkFrame(inner, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row,
                     text=f"{h.get('risk_icon','')}  {h.get('label', h['proc'])}",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C_HARDENING).pack(side="left")

        # Justification pédagogique
        justif = h.get("justification", "")
        if justif:
            ctk.CTkLabel(inner, text=justif,
                         font=ctk.CTkFont(size=10), text_color="#bbbbbb",
                         wraplength=580, justify="left").pack(anchor="w", pady=(4, 4))

        # Commandes PowerShell
        ps_cmds = h.get("powershell", [])
        if ps_cmds:
            ps_text = "\n".join(ps_cmds)
            ps_frame = ctk.CTkFrame(inner, fg_color="#0d0d1a", corner_radius=6)
            ps_frame.pack(fill="x", pady=(4, 2))

            top_ps = ctk.CTkFrame(ps_frame, fg_color="transparent")
            top_ps.pack(fill="x", padx=10, pady=(6, 0))
            ctk.CTkLabel(top_ps, text="PowerShell",
                         font=ctk.CTkFont(size=9, weight="bold"),
                         text_color="#5588ff").pack(side="left")
            _copy_button(top_ps, ps_text, "📋 Copier PS")

            ctk.CTkLabel(ps_frame, text=ps_text,
                         font=ctk.CTkFont(family="Courier", size=10),
                         text_color="#88aaff", justify="left",
                         anchor="w").pack(anchor="w", padx=12, pady=(2, 8))

        # Commandes Bash (si disponibles)
        bash_cmds = h.get("bash", [])
        if bash_cmds:
            bash_text = "\n".join(bash_cmds)
            bash_frame = ctk.CTkFrame(inner, fg_color="#0d1a0d", corner_radius=6)
            bash_frame.pack(fill="x", pady=(2, 4))

            top_bash = ctk.CTkFrame(bash_frame, fg_color="transparent")
            top_bash.pack(fill="x", padx=10, pady=(6, 0))
            ctk.CTkLabel(top_bash, text="Bash / Linux",
                         font=ctk.CTkFont(size=9, weight="bold"),
                         text_color="#55cc88").pack(side="left")
            _copy_button(top_bash, bash_text, "📋 Copier Bash")

            ctk.CTkLabel(bash_frame, text=bash_text,
                         font=ctk.CTkFont(family="Courier", size=10),
                         text_color="#88ffaa", justify="left",
                         anchor="w").pack(anchor="w", padx=12, pady=(2, 8))


# ══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPALE
# ══════════════════════════════════════════════════════════════════════════════

class TafustUI(ctk.CTk):
    def __init__(self, _root_dummy, manager: ScannerManager):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        self.manager = manager
        self.title("🧿 Tafust — Security Audit Monitor")
        self.geometry("1180x820")
        self.minsize(920, 640)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()
        self._tick_system_info()

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=COLOR_SIDEBAR)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_rowconfigure(7, weight=1)

        try:
            if os.path.exists(LOGO_PATH):
                img = Image.open(LOGO_PATH)
                self._logo = ctk.CTkImage(light_image=img, dark_image=img, size=(110, 110))
                ctk.CTkLabel(sb, image=self._logo, text="").pack(pady=(26, 6))
            else:
                ctk.CTkLabel(sb, text="🧿", font=ctk.CTkFont(size=46)).pack(pady=(26, 6))
        except Exception:
            pass

        ctk.CTkLabel(sb, text="TAFUST",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COLOR_TEXT).pack()
        ctk.CTkLabel(sb, text="Security Audit Monitor",
                     font=ctk.CTkFont(size=10),
                     text_color=COLOR_MUTED).pack(pady=(0, 16))

        _sep(sb, color="#252525", pady=(0, 12))

        info = ctk.CTkFrame(sb, fg_color="transparent")
        info.pack(fill="x", padx=18, pady=4)
        ctk.CTkLabel(info, text=f"OS : {self.manager.os_type}",
                     font=ctk.CTkFont(size=11), text_color=COLOR_MUTED).pack(anchor="w")
        self._cpu_lbl = ctk.CTkLabel(info, text="CPU : —",
                                     font=ctk.CTkFont(size=11), text_color=COLOR_MUTED)
        self._cpu_lbl.pack(anchor="w")
        self._ram_lbl = ctk.CTkLabel(info, text="RAM : —",
                                     font=ctk.CTkFont(size=11), text_color=COLOR_MUTED)
        self._ram_lbl.pack(anchor="w")

        self._excl_local = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(sb, text="Exclure trafic local",
                        variable=self._excl_local,
                        command=self._on_toggle_local,
                        font=ctk.CTkFont(size=11)).pack(padx=18, pady=14, anchor="w")

        ctk.CTkButton(sb, text="⬇  Exporter JSON",
                      command=self._export_results,
                      fg_color="transparent", border_width=2, border_color=COLOR_ACCENT,
                      text_color=COLOR_TEXT, hover_color=COLOR_ACCENT,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      height=36).pack(padx=18, pady=6, fill="x")

        self._theme_btn = ctk.CTkButton(
            sb, text="☀  Mode Clair", command=self._toggle_theme,
            fg_color=COLOR_CARD, text_color=COLOR_TEXT, hover_color=COLOR_ACCENT,
            font=ctk.CTkFont(size=11, weight="bold"), height=34)
        self._theme_btn.pack(side="bottom", padx=18, pady=18, fill="x")

    # ── Zone principale ───────────────────────────────────────────────────────

    def _build_main_area(self):
        main = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_BG)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(main, fg_color="transparent")
        hdr.pack(fill="x", padx=28, pady=20)

        self._scan_btn = ctk.CTkButton(
            hdr, text="▶  Lancer l'Audit",
            command=self._start_scan,
            fg_color=COLOR_ACCENT, text_color="white",
            font=ctk.CTkFont(size=14, weight="bold"), height=44)
        self._scan_btn.pack(side="left")

        self._status_lbl = ctk.CTkLabel(
            hdr, text="Prêt", font=ctk.CTkFont(size=12, slant="italic"),
            text_color=COLOR_MUTED)
        self._status_lbl.pack(side="right")

        self._results_area = ctk.CTkScrollableFrame(
            main, fg_color="transparent", label_text="RAPPORT D'AUDIT")
        self._results_area.pack(fill="both", expand=True, padx=22, pady=(0, 22))

    # ── Scan ──────────────────────────────────────────────────────────────────

    def _start_scan(self):
        self._scan_btn.configure(state="disabled", text="⏳  Analyse en cours…")
        self._status_lbl.configure(text="Scan réseau…", text_color=COLOR_ACCENT)
        for w in self._results_area.winfo_children():
            w.destroy()
        self.manager.exclude_local = self._excl_local.get()
        self.manager.start_async_scan(self._on_scan_ok, self._on_scan_err)

    def _on_scan_ok(self, report: dict):
        self.after(0, lambda: self._render_report(report))

    def _render_report(self, report: dict):
        for w in self._results_area.winfo_children():
            w.destroy()

        meta       = report.get("meta", {})
        summary    = report.get("summary", {})
        alertes    = report.get("alertes", [])
        surveiller = report.get("surveiller", [])
        legitimes  = report.get("legitimes", [])
        hardenings = report.get("hardenings", [])

        # ── 1. Résumé Exécutif
        render_executive_summary(self._results_area, summary, meta)
        _sep(self._results_area, pady=(12, 4))

        # ── 2. Matrice des Risques
        render_risk_matrix(self._results_area, alertes, surveiller, legitimes)
        _sep(self._results_area, pady=(12, 4))

        # ── 3. Analyse Technique Détaillée
        render_detailed_analysis(self._results_area, alertes, surveiller, legitimes)
        _sep(self._results_area, pady=(12, 4))

        # ── 4. Recommandations de Hardening
        render_hardenings(self._results_area, hardenings)

        self._scan_btn.configure(state="normal", text="▶  Lancer l'Audit")
        self._status_lbl.configure(text="Audit terminé", text_color=C_LEGITIME)

    def _on_scan_err(self, msg: str):
        self.after(0, lambda: messagebox.showerror("Erreur de scan", msg))
        self._scan_btn.configure(state="normal", text="▶  Lancer l'Audit")
        self._status_lbl.configure(text="Erreur", text_color=C_ALERTE)

    # ── Utilitaires ───────────────────────────────────────────────────────────

    def _tick_system_info(self):
        try:
            self._cpu_lbl.configure(text=f"CPU : {psutil.cpu_percent()}%")
            self._ram_lbl.configure(text=f"RAM : {psutil.virtual_memory().percent}%")
        except Exception:
            pass
        self.after(2000, self._tick_system_info)

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

    def _on_toggle_local(self):
        self.manager.exclude_local = self._excl_local.get()

    def _toggle_theme(self):
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("Light")
            self._theme_btn.configure(text="🌙  Mode Sombre")
        else:
            ctk.set_appearance_mode("Dark")
            self._theme_btn.configure(text="☀  Mode Clair")

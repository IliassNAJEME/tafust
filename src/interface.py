import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import psutil
from PIL import Image

from src.scanner_manager import ScannerManager


COLOR_BG = ("#f0f2f5", "#0d0d0d")
COLOR_SIDEBAR = ("#e8eaed", "#111111")
COLOR_CARD = ("#ffffff", "#181818")
COLOR_ACCENT = ("#1a73e8", "#00d4ff")
COLOR_TEXT = ("#212529", "#e0e0e0")
COLOR_MUTED = ("#6c757d", "#888888")

C_ALERT = "#c0392b"
C_WATCH = "#c87f0a"
C_OK = "#1e7e34"
C_HARDENING = "#6f42c1"

LOGO_PATH = "img/logo.png"

RISK_COLORS = {
    "CRITIQUE": "#8b0000",
    "ÉLEVÉ": "#c0392b",
    "MODÉRÉ": "#c87f0a",
    "FAIBLE": "#b8860b",
    "TRÈS FAIBLE": "#1e7e34",
}


def _sep(parent, color="#2a2a2a", pady=(8, 8)):
    frame = ctk.CTkFrame(parent, fg_color=color, height=1, corner_radius=0)
    frame.pack(fill="x", padx=15, pady=pady)


def _section_title(parent, icon, title, count, color):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", padx=15, pady=(22, 6))

    ctk.CTkLabel(
        frame,
        text=f"{icon}  {title}",
        font=ctk.CTkFont(size=15, weight="bold"),
        text_color=color,
    ).pack(side="left")

    bubble = ctk.CTkFrame(frame, fg_color=color, corner_radius=12, width=36, height=24)
    bubble.pack(side="left", padx=10)
    bubble.pack_propagate(False)
    ctk.CTkLabel(
        bubble,
        text=str(count),
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color="white",
    ).place(relx=0.5, rely=0.5, anchor="center")


def render_executive_summary(parent, summary: dict, meta: dict):
    nb_alerts = summary.get("nb_alertes", 0)
    nb_watch = summary.get("nb_surveiller", 0)
    nb_ok = summary.get("nb_legitimes", 0)
    verdict = summary.get("verdict", "")
    detail = summary.get("verdict_detail", "")
    date = meta.get("date", "")

    is_ok = nb_alerts == 0
    border = C_OK if is_ok else C_ALERT
    bg = "#0d1f0d" if is_ok else "#1f0d0d"

    frame = ctk.CTkFrame(parent, fg_color=bg, border_color=border, border_width=2, corner_radius=12)
    frame.pack(fill="x", padx=15, pady=(10, 4))

    top = ctk.CTkFrame(frame, fg_color="transparent")
    top.pack(fill="x", padx=20, pady=(14, 4))
    ctk.CTkLabel(
        top,
        text=f"{'OK' if is_ok else 'ALERTE'}  {verdict}",
        font=ctk.CTkFont(size=17, weight="bold"),
        text_color=border,
    ).pack(side="left")
    ctk.CTkLabel(
        top,
        text=f"Audit du {date}",
        font=ctk.CTkFont(size=11),
        text_color=COLOR_MUTED,
    ).pack(side="right")

    ctk.CTkLabel(
        frame,
        text=detail,
        font=ctk.CTkFont(size=12),
        text_color=COLOR_TEXT,
        wraplength=720,
        justify="left",
    ).pack(anchor="w", padx=20, pady=(2, 6))

    badges = ctk.CTkFrame(frame, fg_color="transparent")
    badges.pack(anchor="w", padx=20, pady=(0, 12))
    for label, color in [
        (f"{nb_alerts} Alerte(s)", C_ALERT),
        (f"{nb_watch} A surveiller", C_WATCH),
        (f"{nb_ok} Legitimes", C_OK),
    ]:
        ctk.CTkLabel(
            badges,
            text=label,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=color,
        ).pack(side="left", padx=14)


def _detail_card(parent, entry: dict, border_color: str, grouped=False):
    card = ctk.CTkFrame(parent, fg_color=COLOR_CARD, border_color=border_color, border_width=1, corner_radius=8)
    card.pack(fill="x", padx=20, pady=5)

    inner = ctk.CTkFrame(card, fg_color="transparent")
    inner.pack(fill="x", padx=14, pady=10)

    left = ctk.CTkFrame(inner, fg_color="transparent")
    left.pack(side="left", fill="x", expand=True)

    proc = entry.get("proc", "?")
    risk = entry.get("risk_level", "TRÈS FAIBLE")
    icon = entry.get("risk_icon", "•")

    if grouped:
        ports = ", ".join(str(p) for p in entry.get("ports_list", [entry.get("port", "?")]))
        ips = ", ".join(entry.get("ips_list", [entry.get("ip", "?")]))
        top = f"{proc}  |  Ports: {ports}"
        sub = f"IPs: {ips}  |  {entry.get('count', 1)} instance(s)"
    else:
        top = f"{proc}  |  Port {entry.get('port', '?')}/{entry.get('proto', 'TCP')}  |  {entry.get('ip', '?')}"
        sub = entry.get("exposure", "")

    ctk.CTkLabel(
        left,
        text=top,
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=COLOR_TEXT,
        anchor="w",
    ).pack(anchor="w")

    if entry.get("label") and entry.get("label") != proc:
        ctk.CTkLabel(
            left,
            text=entry.get("label"),
            font=ctk.CTkFont(size=11),
            text_color=border_color,
            anchor="w",
        ).pack(anchor="w")

    if sub:
        ctk.CTkLabel(
            left,
            text=sub,
            font=ctk.CTkFont(size=10),
            text_color=COLOR_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(1, 0))

    for text in [
        entry.get("justification", ""),
        f"Publisher: {entry.get('publisher')}" if entry.get("publisher") else "",
        f"Company: {entry.get('company_name')}" if entry.get("company_name") else "",
        f"Signature: {entry.get('signature_status')}" if entry.get("signature_status") else "",
        f"Path: {entry.get('path')}" if entry.get("path") else "",
        f"Reputation: {entry.get('reputation_summary')}" if entry.get("reputation_source") == "virustotal" and entry.get("reputation_summary") else "",
    ]:
        if text:
            ctk.CTkLabel(
                left,
                text=text,
                font=ctk.CTkFont(size=10),
                text_color="#bbbbbb",
                wraplength=560,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=(3, 0))

    right = ctk.CTkFrame(inner, fg_color="transparent")
    right.pack(side="right", anchor="n")
    ctk.CTkLabel(
        right,
        text=f"{icon} {risk}",
        font=ctk.CTkFont(size=10, weight="bold"),
        text_color=RISK_COLORS.get(risk, "#aaa"),
    ).pack(anchor="e")


def render_risk_matrix(parent, alertes, surveiller, legitimes_grouped):
    total = len(alertes) + len(surveiller) + len(legitimes_grouped)
    _section_title(parent, "R", "Matrice des Risques", total, COLOR_ACCENT[1])

    for title, items, color, grouped in [
        ("Alertes", alertes, C_ALERT, False),
        ("A surveiller", surveiller, C_WATCH, False),
        ("Legitimes", legitimes_grouped, C_OK, True),
    ]:
        if not items:
            continue
        ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=color,
        ).pack(anchor="w", padx=22, pady=(8, 2))
        for entry in items:
            _detail_card(parent, entry, color if not grouped else "#2d5a2d", grouped=grouped)


def render_detailed_analysis(parent, alertes, surveiller, legitimes_grouped):
    total = len(alertes) + len(surveiller) + len(legitimes_grouped)
    _section_title(parent, "A", "Analyse Technique Detaillee", total, "#aaaacc")
    render_risk_matrix(parent, alertes, surveiller, legitimes_grouped)


def render_hardenings(parent, hardenings: list):
    _section_title(parent, "H", "Recommandations de Hardening", len(hardenings), C_HARDENING)
    if not hardenings:
        ctk.CTkLabel(
            parent,
            text="Aucune action de hardening requise.",
            font=ctk.CTkFont(size=12),
            text_color=C_OK,
        ).pack(anchor="w", padx=24, pady=8)
        return

    for item in hardenings:
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD, border_color=C_HARDENING, border_width=1, corner_radius=8)
        card.pack(fill="x", padx=20, pady=5)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(
            inner,
            text=item.get("label", item.get("proc", "?")),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=C_HARDENING,
        ).pack(anchor="w")
        ctk.CTkLabel(
            inner,
            text=item.get("justification", ""),
            font=ctk.CTkFont(size=10),
            text_color="#bbbbbb",
            wraplength=580,
            justify="left",
        ).pack(anchor="w", pady=(4, 4))
        for cmd in item.get("powershell", []):
            ctk.CTkLabel(
                inner,
                text=cmd,
                font=ctk.CTkFont(family="Courier", size=10),
                text_color="#88aaff",
                justify="left",
            ).pack(anchor="w")
        for cmd in item.get("bash", []):
            ctk.CTkLabel(
                inner,
                text=cmd,
                font=ctk.CTkFont(family="Courier", size=10),
                text_color="#88ffaa",
                justify="left",
            ).pack(anchor="w")


class TafustUI(ctk.CTk):
    def __init__(self, _root_dummy, manager: ScannerManager):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        self.manager = manager
        self._last_report_text = ""
        self.title("Tafust - Security Audit Monitor")
        self.geometry("1180x820")
        self.minsize(920, 640)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()
        self._tick_system_info()

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=COLOR_SIDEBAR)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_rowconfigure(7, weight=1)

        try:
            if os.path.exists(LOGO_PATH):
                img = Image.open(LOGO_PATH)
                self._logo = ctk.CTkImage(light_image=img, dark_image=img, size=(110, 110))
                ctk.CTkLabel(sb, image=self._logo, text="").pack(pady=(26, 6))
        except Exception:
            pass

        ctk.CTkLabel(sb, text="TAFUST", font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_TEXT).pack()
        ctk.CTkLabel(sb, text="Security Audit Monitor", font=ctk.CTkFont(size=10), text_color=COLOR_MUTED).pack(pady=(0, 16))

        _sep(sb, color="#252525", pady=(0, 12))

        info = ctk.CTkFrame(sb, fg_color="transparent")
        info.pack(fill="x", padx=18, pady=4)
        ctk.CTkLabel(info, text=f"OS : {self.manager.os_type}", font=ctk.CTkFont(size=11), text_color=COLOR_MUTED).pack(anchor="w")
        self._cpu_lbl = ctk.CTkLabel(info, text="CPU : -", font=ctk.CTkFont(size=11), text_color=COLOR_MUTED)
        self._cpu_lbl.pack(anchor="w")
        self._ram_lbl = ctk.CTkLabel(info, text="RAM : -", font=ctk.CTkFont(size=11), text_color=COLOR_MUTED)
        self._ram_lbl.pack(anchor="w")

        self._excl_local = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            sb,
            text="Exclure trafic local",
            variable=self._excl_local,
            command=self._on_toggle_local,
            font=ctk.CTkFont(size=11),
        ).pack(padx=18, pady=14, anchor="w")

        for text, command in [
            ("Exporter JSON", self._export_results),
            ("Copier rapport", self._copy_report),
        ]:
            ctk.CTkButton(
                sb,
                text=text,
                command=command,
                fg_color="transparent",
                border_width=2,
                border_color=COLOR_ACCENT,
                text_color=COLOR_TEXT,
                hover_color=COLOR_ACCENT,
                font=ctk.CTkFont(size=12, weight="bold"),
                height=36,
            ).pack(padx=18, pady=6, fill="x")

        self._theme_btn = ctk.CTkButton(
            sb,
            text="Mode Clair",
            command=self._toggle_theme,
            fg_color=COLOR_CARD,
            text_color=COLOR_TEXT,
            hover_color=COLOR_ACCENT,
            font=ctk.CTkFont(size=11, weight="bold"),
            height=34,
        )
        self._theme_btn.pack(side="bottom", padx=18, pady=18, fill="x")

    def _build_main_area(self):
        main = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_BG)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=20)

        self._scan_btn = ctk.CTkButton(
            header,
            text="Lancer l'Audit",
            command=self._start_scan,
            fg_color=COLOR_ACCENT,
            text_color="white",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
        )
        self._scan_btn.pack(side="left")

        self._status_lbl = ctk.CTkLabel(
            header,
            text="Pret",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color=COLOR_MUTED,
        )
        self._status_lbl.pack(side="right")

        self._results_area = ctk.CTkScrollableFrame(main, fg_color="transparent", label_text="RAPPORT D'AUDIT")
        self._results_area.pack(fill="both", expand=True, padx=22, pady=(0, 22))

    def _start_scan(self):
        self._scan_btn.configure(state="disabled", text="Analyse en cours...")
        self._status_lbl.configure(text="Scan reseau...", text_color=COLOR_ACCENT)
        self._last_report_text = ""
        for widget in self._results_area.winfo_children():
            widget.destroy()
        self.manager.exclude_local = self._excl_local.get()
        self.manager.start_async_scan(self._on_scan_ok, self._on_scan_err)

    def _on_scan_ok(self, report: dict):
        self.after(0, lambda: self._render_report(report))

    def _render_report(self, report: dict):
        for widget in self._results_area.winfo_children():
            widget.destroy()

        meta = report.get("meta", {})
        summary = report.get("summary", {})
        alertes = report.get("alertes", [])
        surveiller = report.get("surveiller", [])
        legitimes = report.get("legitimes", [])
        hardenings = report.get("hardenings", [])
        self._last_report_text = self._build_report_text(report)

        render_executive_summary(self._results_area, summary, meta)
        _sep(self._results_area, pady=(12, 4))
        render_risk_matrix(self._results_area, alertes, surveiller, legitimes)
        _sep(self._results_area, pady=(12, 4))
        render_detailed_analysis(self._results_area, alertes, surveiller, legitimes)
        _sep(self._results_area, pady=(12, 4))
        render_hardenings(self._results_area, hardenings)

        self._scan_btn.configure(state="normal", text="Lancer l'Audit")
        self._status_lbl.configure(text="Audit termine", text_color=C_OK)

    def _on_scan_err(self, msg: str):
        self.after(0, lambda: messagebox.showerror("Erreur de scan", msg))
        self._scan_btn.configure(state="normal", text="Lancer l'Audit")
        self._status_lbl.configure(text="Erreur", text_color=C_ALERT)

    def _tick_system_info(self):
        try:
            self._cpu_lbl.configure(text=f"CPU : {psutil.cpu_percent()}%")
            self._ram_lbl.configure(text=f"RAM : {psutil.virtual_memory().percent}%")
        except Exception:
            pass
        self.after(2000, self._tick_system_info)

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

    def _format_report_entries(self, title: str, entries: list, grouped=False) -> list[str]:
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

    def _toggle_theme(self):
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("Light")
            self._theme_btn.configure(text="Mode Sombre")
        else:
            ctk.set_appearance_mode("Dark")
            self._theme_btn.configure(text="Mode Clair")

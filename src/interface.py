import tkinter as tk
from tkinter import ttk, messagebox
import os
from PIL import Image, ImageTk

# Import critique demandé pour la cohérence de la structure
from src.scanner_manager import ScannerManager

LOGO_PATH = "img/logo.png"

class TafustUI:
    def __init__(self, root, manager: ScannerManager):
        self.root = root
        self.manager = manager
        self.root.title("🧿 Tafust - Cross Platform Security Monitor")
        self.root.geometry("800x900")
        self.root.configure(bg="#f8f9fa")

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        
        self.setup_ui()

    def setup_ui(self):
        """Construction de l'interface graphique."""
        self.header_frame = tk.Frame(self.root, bg="#f8f9fa")
        self.header_frame.pack(pady=15)

        try:
            if os.path.exists(LOGO_PATH):
                img = Image.open(LOGO_PATH).resize((100, 100), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                tk.Label(self.header_frame, image=self.logo_img, bg="#f8f9fa").pack()
            else:
                tk.Label(self.header_frame, text="🧿", font=("Arial", 50), bg="#f8f9fa", fg="#1a73e8").pack()
        except: pass

        tk.Label(self.header_frame, text="TAFUST", font=("Helvetica", 24, "bold"), bg="#f8f9fa", fg="#212529").pack()
        
        os_type = self.manager.os_type
        os_color = "#28a745" if os_type == "Linux" else "#0078d4"
        tk.Label(
            self.header_frame, 
            text=f"Detected System: {os_type}", 
            font=("Helvetica", 10, "italic"), 
            bg="#f8f9fa", 
            fg=os_color
        ).pack()

        self.dashboard_frame = tk.Frame(self.root, bg="white", relief="groove", borderwidth=1)
        self.dashboard_frame.pack(padx=20, pady=10, fill="x")

        self.summary_labels = {}
        for i, (label, color) in enumerate([("SAFE ✅", "#28a745"), ("WARNING ⚠️", "#ffc107"), ("SUSPICIOUS 🚨", "#dc3545")]):
            lbl = tk.Label(self.dashboard_frame, text=f"{label}: 0", font=("Helvetica", 11, "bold"), bg="white", fg=color, padx=20, pady=10)
            lbl.grid(row=0, column=i, sticky="nsew")
            self.summary_labels[label.split()[0]] = lbl
        self.dashboard_frame.columnconfigure((0, 1, 2), weight=1)

        self.scan_btn = tk.Button(
            self.root, text="SCAN SYSTEM PORTS", command=self.start_scan,
            font=("Helvetica", 12, "bold"), bg="#1a73e8", fg="white",
            padx=40, pady=12, relief="flat", cursor="hand2"
        )
        self.scan_btn.pack(pady=10)

        self.table_frame = tk.Frame(self.root, bg="#f8f9fa")
        self.table_frame.pack(padx=20, pady=10, fill="both", expand=True)

        columns = ("proto", "port", "service", "addr", "proc", "score", "status")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", selectmode="browse")
        
        col_names = {
            "proto": "Protocole", "port": "Port", "service": "Service",
            "addr": "Adresse", "proc": "Processus", "score": "Score", "status": "Status"
        }
        for col in columns:
            self.tree.heading(col, text=col_names[col])
            self.tree.column(col, width=100, anchor="center")

        self.scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.tree.tag_configure("safe", background="#d4edda", foreground="#155724")
        self.tree.tag_configure("warning", background="#fff3cd", foreground="#856404")
        self.tree.tag_configure("suspicious", background="#f8d7da", foreground="#721c24")
        self.tree.bind("<Double-1>", self.on_double_click)

    def start_scan(self):
        self.scan_btn.config(text="Analyzing...", state="disabled", bg="#6c757d")
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.manager.start_async_scan(self.on_scan_complete, self.on_scan_error)

    def on_scan_complete(self, data):
        self.root.after(0, lambda: self.update_ui(data))

    def on_scan_error(self, message):
        self.root.after(0, lambda: self.finish_scan(f"❌ Error: {message}"))

    def update_ui(self, data):
        counts = {"SAFE": 0, "WARNING": 0, "SUSPICIOUS": 0}
        icons = {"SAFE": "✅", "WARNING": "⚠️", "SUSPICIOUS": "🚨"}
        for e in data:
            status = e["status"]
            counts[status] += 1
            tag = status.lower()
            self.tree.insert("", tk.END, values=(
                e["proto"], e["port"], e["service"],
                e["ip"], e["proc"], f"{e['score']}/100", status
            ), tags=(tag,))
        for key, count in counts.items():
            self.summary_labels[key].config(text=f"{key} {icons[key]}: {count}")
        self.finish_scan()

    def on_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id: return
        values = self.tree.item(item_id, "values")
        proc_name, port = values[4], values[1]
        entry = self.manager.get_result_by_port_and_proc(port, proc_name)
        if entry:
            details = f"🔍 Details pour {proc_name} (Port {port})\n" + "-"*40 + "\n"
            details += "\n".join([f"• {r}" for r in entry.get("reasons", [])])
            messagebox.showinfo("🧿 Tafust - Risk Analysis", details)

    def finish_scan(self, error=None):
        if error: messagebox.showerror("Error", error)
        self.scan_btn.config(text="SCAN SYSTEM PORTS", state="normal", bg="#1a73e8")

#!/usr/bin/env python3
"""
🧿 Tafust - Cross Platform Security Monitor
A professional cybersecurity tool for intelligent system port risk analysis.
Supports both Linux and Windows.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import re
import os
import threading
import platform
import psutil
from datetime import datetime
from PIL import Image, ImageTk

# --- CONFIGURATION & KNOWLEDGE BASE ---
DATA_DIR = "tafust_data"
LOGO_PATH = "img/logo.png"

# Standard Service Mappings
COMMON_SERVICES = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 135: "RPC", 139: "NetBIOS", 1883: "MQTT", 443: "HTTPS", 
    445: "SMB", 3306: "MySQL", 5353: "mDNS", 7680: "Windows Update",
    27017: "MongoDB"
}

# Tiered Process Classification (Normalized: lowercase, no .exe)
CORE_SYSTEM = [
    "system", "svchost", "lsass", "services", "wininit", "spoolsv", 
    "explorer", "system idle process", "smss", "csrss", "winlogon"
]

# 1. Configuration de la Whitelist
WHITELIST_FILE = "whitelist.txt"

def load_whitelist():
    """
    Charge la liste des processus de confiance depuis un fichier externe.
    """
    whitelist = set()
    try:
        if os.path.exists(WHITELIST_FILE):
            with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    proc = line.strip().lower()
                    if proc:
                        # On retire l'extension .exe pour une comparaison plus souple
                        if proc.endswith(".exe"): proc = proc[:-4]
                        whitelist.add(proc)
            print(f"Whitelist chargée : {len(whitelist)} processus identifiés.")
        else:
            print(f"Avertissement : '{WHITELIST_FILE}' absent. Utilisation d'une liste vide.")
    except Exception as e:
        print(f"Erreur lors du chargement de la whitelist : {e}")
    
    return whitelist

# Initialisation globale (sera rafraîchie au démarrage de l'app)
CURRENT_WHITELIST = set()

DEV_TOOLS = [
    "python", "node", "mongod", "mosquitto", "docker", "java", "code", "git"
]

# Process to Port Expectations (Reduces risk if matched)
EXPECTED_PORTS = {
    "mosquitto": [1883, 8883],
    "mongod": [27017],
    "mysql": [3306],
    "nginx": [80, 443],
    "apache": [80, 443],
    "sshd": [22]
}

def get_risk_score(process_name, port, address):
    """
    Calcule le score de risque en fonction du processus et de l'exposition réseau.
    """
    score = 0
    reasoning = []
    
    # Normalisation du nom du processus
    proc_norm = process_name.lower()
    if proc_norm.endswith(".exe"): proc_norm = proc_norm[:-4]

    # A. Analyse de confiance (via CURRENT_WHITELIST)
    if proc_norm in CURRENT_WHITELIST:
        score += 0
        reasoning.append(f"✅ TRUSTED: '{process_name}' est dans la whitelist.")
    else:
        score += 50
        reasoning.append(f"❓ UNKNOWN: '{process_name}' n'est pas reconnu.")

    # B. Analyse de l'exposition (IPv4 & IPv6 robustesse)
    addr_clean = address.strip("[]").lower()
    
    # Définition des scopes
    is_local = addr_clean in ["127.0.0.1", "::1", "localhost", "0:0:0:0:0:0:0:1"]
    is_exposed = addr_clean in ["0.0.0.0", "::", "any", "all"]

    if is_local:
        score -= 20
        reasoning.append("🔒 LOCAL ONLY: Service isolé en loopback.")
    elif is_exposed:
        score += 30
        reasoning.append("🌐 NETWORK EXPOSED: Service accessible via interface publique.")
    else:
        score += 15 # IP spécifique
        reasoning.append(f"📡 IP BIND: Service lié à une interface spécifique ({address}).")

    # C. Ajustement final (Min/Max)
    return max(0, min(100, score)), reasoning

class TafustApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧿 Tafust - Cross Platform Security Monitor")
        self.root.geometry("800x900")
        self.root.configure(bg="#f8f9fa")

        os.makedirs(DATA_DIR, exist_ok=True)
        self.os_type = platform.system()
        
        # Chargement de la Whitelist au démarrage
        global CURRENT_WHITELIST
        CURRENT_WHITELIST = load_whitelist()
        
        # Style & Thème
        self.style = ttk.Style()
        self.style.theme_use('clam') # Thème moderne
        self.style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        
        self.setup_ui()

    def setup_ui(self):
        """Builds the graphical user interface."""
        # --- Header ---
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
        
        # OS Indicator
        os_color = "#28a745" if self.os_type == "Linux" else "#0078d4" # Linux Green, Windows Blue
        self.os_label = tk.Label(
            self.header_frame, 
            text=f"Detected System: {self.os_type}", 
            font=("Helvetica", 10, "italic"), 
            bg="#f8f9fa", 
            fg=os_color
        )
        self.os_label.pack()

        # --- Dashboard ---
        self.dashboard_frame = tk.Frame(self.root, bg="white", relief="groove", borderwidth=1)
        self.dashboard_frame.pack(padx=20, pady=10, fill="x")

        self.summary_labels = {}
        for i, (label, color) in enumerate([("SAFE ✅", "#28a745"), ("WARNING ⚠️", "#ffc107"), ("SUSPICIOUS 🚨", "#dc3545")]):
            lbl = tk.Label(self.dashboard_frame, text=f"{label}: 0", font=("Helvetica", 11, "bold"), bg="white", fg=color, padx=20, pady=10)
            lbl.grid(row=0, column=i, sticky="nsew")
            self.summary_labels[label.split()[0]] = lbl
        self.dashboard_frame.columnconfigure((0, 1, 2), weight=1)

        # --- Scan Button ---
        self.scan_btn = tk.Button(
            self.root, text="SCAN SYSTEM PORTS", command=self.start_scan,
            font=("Helvetica", 12, "bold"), bg="#1a73e8", fg="white",
            padx=40, pady=12, relief="flat", cursor="hand2"
        )
        self.scan_btn.pack(pady=10)

        # --- Results Table (Treeview) ---
        self.table_frame = tk.Frame(self.root, bg="#f8f9fa")
        self.table_frame.pack(padx=20, pady=10, fill="both", expand=True)

        columns = ("proto", "port", "service", "addr", "proc", "score", "status")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", selectmode="browse")
        
        # Define Headings & Sorting
        col_names = {
            "proto": "Protocole", "port": "Port", "service": "Service",
            "addr": "Adresse", "proc": "Processus", "score": "Score", "status": "Status"
        }
        for col in columns:
            self.tree.heading(col, text=col_names[col], command=lambda c=col: self.sort_column(c, False))
            self.tree.column(col, width=100, anchor="center")

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Color Tags
        self.tree.tag_configure("safe", background="#d4edda", foreground="#155724")
        self.tree.tag_configure("warning", background="#fff3cd", foreground="#856404")
        self.tree.tag_configure("suspicious", background="#f8d7da", foreground="#721c24")

        # Double Click Event
        self.tree.bind("<Double-1>", self.on_double_click)
        
        self.scan_results = [] # Store full data for details

    def start_scan(self):
        self.scan_btn.config(text="Analyzing...", state="disabled", bg="#6c757d")
        for item in self.tree.get_children():
            self.tree.delete(item)
        threading.Thread(target=self.run_analysis, daemon=True).start()

    def run_analysis(self):
        try:
            if self.os_type == "Windows":
                raw_data = self.get_windows_ports()
                parsed_data = self.parse_windows_output(raw_data)
            else:
                raw_data = self.get_linux_ports()
                parsed_data = self.parse_linux_output(raw_data)
                
            analyzed_data = self.analyze_risk(parsed_data)
            self.root.after(0, lambda: self.update_ui(analyzed_data))
        except Exception as e:
            error_msg = str(e)
            self.log_error(f"Analysis failed: {error_msg}")
            self.root.after(0, lambda: self.finish_scan(f"❌ Critical Error: {error_msg}"))

    def log_error(self, message):
        """Logs error message to a file."""
        log_path = os.path.join(DATA_DIR, "tafust.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] ERROR: {message}\n")
        except:
            print(f"Failed to write to log: {message}")

    def log_debug(self, message):
        """Logs debug message to a file and console."""
        log_path = os.path.join(DATA_DIR, "debug.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] DEBUG: {message}\n")
        except: pass
        print(f"DEBUG: {message}")

    def get_linux_ports(self):
        """Returns raw output from ss command."""
        try:
            return subprocess.run(
                ['ss', '-tulnp'], 
                capture_output=True, 
                encoding="utf-8", 
                errors="ignore", 
                check=True
            ).stdout
        except Exception as e:
            self.log_error(f"Linux port scan failed: {str(e)}")
            return ""

    def get_windows_ports(self):
        """Returns raw output from netstat command."""
        try:
            return subprocess.run(
                ['netstat', '-ano'], 
                capture_output=True, 
                encoding="utf-8", 
                errors="ignore", 
                check=True
            ).stdout
        except Exception as e:
            self.log_error(f"Windows port scan failed: {str(e)}")
            return ""

    def parse_linux_output(self, output):
        parsed = []
        lines = output.strip().split('\n')
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 5: continue
            proto, local = parts[0].upper(), parts[4]
            if ':' not in local: continue
            ip, port = local.rsplit(':', 1)
            
            proc = "Unknown"
            proc_match = re.search(r'users:\(\("([^"]+)"', line)
            if proc_match: proc = proc_match.group(1)
            
            parsed.append({"proto": proto, "ip": ip, "port": int(port), "proc": proc})
        return parsed

    def parse_windows_output(self, output):
        parsed = []
        lines = output.strip().split('\n')
        for line in lines:
            if "LISTENING" not in line: continue
            parts = line.split()
            if len(parts) < 5: continue
            
            proto = parts[0].upper()
            local = parts[1]
            pid = parts[4]
            
            if ':' not in local: continue
            ip, port = local.rsplit(':', 1)
            
            # Use psutil to get process name from PID
            try:
                proc = psutil.Process(int(pid)).name()
            except:
                proc = f"PID {pid}"
                
            parsed.append({"proto": proto, "ip": ip, "port": int(port), "proc": proc})
        return parsed

    def calculate_risk_score(self, entry):
        """
        Calculates risk score using the logic provided by the user.
        """
        proc_name = entry["proc"]
        port = entry["port"]
        addr = entry["ip"]
        
        # Call the user's risk score function
        final_score, reasoning = get_risk_score(proc_name, port, addr)
        
        # Determine Status for UI (EDR-style)
        if final_score < 35:
            status = "SAFE"
        elif final_score < 75:
            status = "WARNING"
        else:
            status = "SUSPICIOUS"

        self.log_debug(f"EDR Analysis: {proc_name} | Final Score: {final_score} | Decision: {status}")
        
        return int(final_score), status, reasoning

    def analyze_risk(self, data):
        for entry in data:
            score, status, reasons = self.calculate_risk_score(entry)
            entry.update({
                "score": score, "status": status, "reasons": reasons,
                "service": COMMON_SERVICES.get(entry["port"], "Unknown")
            })
        return data

    def update_ui(self, data):
        self.scan_results = data
        counts = {"SAFE": 0, "WARNING": 0, "SUSPICIOUS": 0}
        icons = {"SAFE": "✅", "WARNING": "⚠️", "SUSPICIOUS": "🚨"}
        
        for e in data:
            status = e["status"]
            counts[status] += 1
            
            # Tag for coloring
            tag = status.lower()
            
            self.tree.insert("", tk.END, values=(
                e["proto"], e["port"], e["service"],
                e["ip"], e["proc"], f"{e['score']}/100", status
            ), tags=(tag,))

        for key, count in counts.items():
            self.summary_labels[key].config(text=f"{key} {icons[key]}: {count}")
        
        self.finish_scan()

    def on_double_click(self, event):
        """Shows detailed reasoning for the selected process."""
        item_id = self.tree.identify_row(event.y)
        if not item_id: return
        
        values = self.tree.item(item_id, "values")
        proc_name = values[4]
        port = values[1]
        
        # Find original data entry
        entry = next((e for e in self.scan_results if str(e["port"]) == str(port) and e["proc"] == proc_name), None)
        
        if entry:
            details = f"🔍 Details pour {proc_name} (Port {port})\n"
            details += "-"*40 + "\n"
            details += "\n".join([f"• {r}" for r in entry["reasons"]])
            messagebox.showinfo("🧿 Tafust - Risk Analysis", details)

    def sort_column(self, col, reverse):
        """Sorts the Treeview column."""
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        
        # Try numeric sort if possible
        try:
            l.sort(key=lambda t: int(t[0].split('/')[0]) if '/' in t[0] else int(t[0]), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def finish_scan(self, error=None):
        if error: messagebox.showerror("Error", error)
        self.scan_btn.config(text="SCAN SYSTEM PORTS", state="normal", bg="#1a73e8")

if __name__ == "__main__":
    root = tk.Tk()
    app = TafustApp(root)
    root.mainloop()

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

# --- CONFIGURATION ---
DATA_DIR = "tafust_data"
LOGO_PATH = "img/logo.png"

# Port Knowledge Base
COMMON_SERVICES = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 443: "HTTPS", 3306: "MySQL", 5353: "mDNS"
}

# Known/Safe Process Patterns (Cross-platform)
KNOWN_PROCESSES = [
    "sshd", "nginx", "apache", "mysql", "brave", "python", 
    "language_server", "systemd", "avahi-daemon", "antigravity",
    "lsass", "svchost", "explorer", "services", "system idle process"
]

class TafustApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧿 Tafust - Cross Platform Security Monitor")
        self.root.geometry("800x900")
        self.root.configure(bg="#f8f9fa")

        os.makedirs(DATA_DIR, exist_ok=True)
        self.os_type = platform.system()
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

        # --- Results ---
        self.results_area = scrolledtext.ScrolledText(
            self.root, font=("Consolas", 10), bg="white", fg="#212529", padx=10, pady=10
        )
        self.results_area.pack(padx=20, pady=10, fill="both", expand=True)
        self.results_area.insert(tk.END, f"Cross-platform analyzer ready for {self.os_type}...\n")

    def start_scan(self):
        self.scan_btn.config(text="Analyzing...", state="disabled", bg="#6c757d")
        self.results_area.delete(1.0, tk.END)
        self.results_area.insert(tk.END, f"🔍 Initializing Smart Risk Engine on {self.os_type}...\n")
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
            self.root.after(0, lambda: self.finish_scan(f"❌ Critical Error: {str(e)}"))

    def get_linux_ports(self):
        """Returns raw output from ss command."""
        return subprocess.run(['ss', '-tulnp'], capture_output=True, text=True, check=True).stdout

    def get_windows_ports(self):
        """Returns raw output from netstat command."""
        return subprocess.run(['netstat', '-ano'], capture_output=True, text=True, check=True).stdout

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
        score = 50
        reasons = []

        # Interface Factor
        if entry["ip"] in ["127.0.0.1", "::1", "0:0:0:0:0:0:0:1"]:
            score -= 15
            reasons.append("Localhost interface reduces external exposure.")
        else:
            score += 20
            reasons.append("External interface allows remote connections.")

        # Process Factor
        is_known = any(p in entry["proc"].lower() for p in KNOWN_PROCESSES)
        if is_known:
            score -= 30
            reasons.append(f"Known/Common process: {entry['proc']}")
        else:
            score += 25
            reasons.append(f"Unrecognized process: {entry['proc']}")

        # Port Factor
        if entry["port"] in COMMON_SERVICES:
            score -= 10
            reasons.append(f"Standard service port: {entry['port']} ({COMMON_SERVICES[entry['port']]})")
        elif entry["port"] > 1024:
            score += 15
            reasons.append(f"Unusual high port: {entry['port']}")

        score = max(0, min(100, score))
        status = "SAFE" if score <= 30 else "WARNING" if score <= 70 else "SUSPICIOUS"
        return score, status, reasons

    def analyze_risk(self, data):
        for entry in data:
            score, status, reasons = self.calculate_risk_score(entry)
            entry.update({
                "score": score, "status": status, "reasons": reasons,
                "service": COMMON_SERVICES.get(entry["port"], "Unknown")
            })
        return data

    def update_ui(self, data):
        self.results_area.delete(1.0, tk.END)
        self.results_area.insert(tk.END, f"✅ Scan Complete on {self.os_type}! Found {len(data)} services.\n\n")
        
        counts = {"SAFE": 0, "WARNING": 0, "SUSPICIOUS": 0}
        icons = {"SAFE": "✅", "WARNING": "⚠️", "SUSPICIOUS": "🚨"}
        
        for e in data:
            counts[e["status"]] += 1
            icon = icons[e["status"]]
            self.results_area.insert(tk.END, f"[{e['proto']}] Port: {e['port']} → {e['service']}\n")
            self.results_area.insert(tk.END, f"   📍 Address: {e['ip']} | ⚙️ Process: {e['proc']}\n")
            self.results_area.insert(tk.END, f"   📊 Risk Score: {e['score']}/100 | Status: {e['status']} {icon}\n")
            self.results_area.insert(tk.END, "   📝 Reasoning:\n")
            for r in e["reasons"]:
                self.results_area.insert(tk.END, f"      - {r}\n")
            self.results_area.insert(tk.END, "-"*60 + "\n")

        for key, count in counts.items():
            self.summary_labels[key].config(text=f"{key} {icons[key]}: {count}")
        
        self.finish_scan()

    def finish_scan(self, error=None):
        if error: self.results_area.insert(tk.END, error)
        self.scan_btn.config(text="SCAN SYSTEM PORTS", state="normal", bg="#1a73e8")

if __name__ == "__main__":
    root = tk.Tk()
    app = TafustApp(root)
    root.mainloop()

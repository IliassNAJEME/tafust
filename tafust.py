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

TRUSTED_APPS = [
    "brave", "chrome", "firefox", "msedge", "antigravity", "armourycrate",
    "asus", "nvidia", "steam", "discord", "spotify"
]

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
        Advanced Context-Aware Risk Engine (EDR-style).
        Analyzes Process Trust, Network Exposure, and Port Reputation.
        """
        reasons = []
        
        # --- PHASE 1: Normalization & Classification ---
        proc_raw = entry["proc"]
        proc_norm = proc_raw.lower()
        if proc_norm.endswith(".exe"): proc_norm = proc_norm[:-4]
        
        # Determine Trust Level
        if proc_norm in CORE_SYSTEM:
            trust_level = "CORE"
            base_score = 0
            reasons.append(f"✅ CORE SYSTEM: '{proc_raw}' is a verified Windows system component.")
        elif any(app in proc_norm for app in TRUSTED_APPS):
            trust_level = "TRUSTED"
            base_score = 10
            reasons.append(f"✅ TRUSTED APP: '{proc_raw}' is a recognized legitimate application.")
        elif any(tool in proc_norm for tool in DEV_TOOLS):
            trust_level = "DEV"
            base_score = 20
            reasons.append(f"🛠️ DEV TOOL: '{proc_raw}' is a known developer utility.")
        else:
            trust_level = "UNKNOWN"
            base_score = 60
            reasons.append(f"❓ UNKNOWN: '{proc_raw}' is not in the local trust database.")

        # --- PHASE 2: Exposure Analysis ---
        is_localhost = entry["ip"] in ["127.0.0.1", "::1", "0:0:0:0:0:0:0:1"]
        if is_localhost:
            exposure_multiplier = 0.5
            reasons.append("🔒 LOCAL ONLY: Service is isolated to localhost (significant risk reduction).")
        else:
            exposure_multiplier = 1.2
            reasons.append("🌐 NETWORK EXPOSED: Service is listening on a network interface.")

        # --- PHASE 3: Port Reputation & Mapping ---
        port = entry["port"]
        is_common = port in COMMON_SERVICES
        is_expected = port in EXPECTED_PORTS.get(proc_norm, [])
        is_dynamic = 49152 <= port <= 65535

        port_score = 0
        if is_expected:
            port_score -= 20
            reasons.append(f"🎯 EXPECTED PORT: Port {port} is standard for {proc_raw}.")
        elif is_common:
            port_score -= 10
            reasons.append(f"📋 COMMON PORT: Port {port} matches a known service ({COMMON_SERVICES[port]}).")
        elif is_dynamic:
            port_score += 5
            reasons.append(f"🔄 DYNAMIC RANGE: Port {port} is in the standard ephemeral range.")
        else:
            port_score += 25
            reasons.append(f"⚠️ UNUSUAL PORT: Port {port} is non-standard for this system.")

        # --- PHASE 4: Decision Logic (Final Scoring) ---
        # Calculation: (Base + Port) * Exposure
        final_score = (base_score + port_score) * exposure_multiplier
        
        # Apply Guardrails
        if trust_level == "CORE":
            final_score = min(final_score, 15) # Never above SAFE
        elif trust_level == "DEV" and is_localhost:
            final_score = min(final_score, 25) # Always SAFE if local dev
        elif trust_level == "TRUSTED" and is_common:
            final_score = min(final_score, 30) # Likely SAFE

        # Final Status Determination
        final_score = max(0, min(100, final_score))
        
        # EDR-style Decision Criteria
        if final_score < 35:
            status = "SAFE"
        elif final_score < 75:
            status = "WARNING"
        else:
            # SUSPICIOUS only if: Unknown process AND Network Exposed AND Unusual Port
            if trust_level == "UNKNOWN" and not is_localhost and not is_common:
                status = "SUSPICIOUS"
            else:
                status = "WARNING" # Downgrade if any safety factor exists

        self.log_debug(f"EDR Analysis: {proc_raw} | Trust: {trust_level} | Final Score: {final_score:.1f} | Decision: {status}")
        
        return int(final_score), status, reasons

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

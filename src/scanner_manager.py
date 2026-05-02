import subprocess
import json
import os
import platform
import psutil
import threading
import re
from datetime import datetime

# Configuration
DATA_DIR = "tafust_data"
WHITELIST_FILE = "whitelist.txt"
GO_ENGINE_PATH = os.path.join("engine", "scanner.exe")

class ScannerManager:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.os_type = platform.system()
        self.whitelist = self.load_whitelist()
        self.last_results = []

    def load_whitelist(self):
        whitelist = set()
        try:
            if os.path.exists(WHITELIST_FILE):
                with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        proc = line.strip().lower()
                        if proc:
                            if proc.endswith(".exe"): proc = proc[:-4]
                            whitelist.add(proc)
        except Exception:
            pass
        return whitelist

    def get_risk_score(self, process_name, port, address):
        score = 0
        reasoning = []
        proc_norm = process_name.lower()
        if proc_norm.endswith(".exe"): proc_norm = proc_norm[:-4]

        if proc_norm in self.whitelist:
            score += 0
            reasoning.append(f"✅ TRUSTED: '{process_name}' est dans la whitelist.")
        else:
            score += 50
            reasoning.append(f"❓ UNKNOWN: '{process_name}' n'est pas reconnu.")

        addr_clean = address.strip("[]").lower()
        is_local = addr_clean in ["127.0.0.1", "::1", "localhost"]
        
        if is_local:
            score -= 20
            reasoning.append("🔒 LOCAL ONLY: Service isolé.")
        else:
            score += 30
            reasoning.append("🌐 NETWORK EXPOSED: Service accessible via interface publique.")

        return max(0, min(100, score)), reasoning

    def run_go_scan(self):
        """Exécute l'exécutable Go et récupère le JSON."""
        if not os.path.exists(GO_ENGINE_PATH):
            return []
        
        try:
            result = subprocess.run([GO_ENGINE_PATH], capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except Exception:
            return []

    def start_async_scan(self, callback_success, callback_error):
        threading.Thread(target=self._scan_thread, args=(callback_success, callback_error), daemon=True).start()

    def _scan_thread(self, callback_success, callback_error):
        try:
            # 1. Fallback Python
            if self.os_type == "Windows":
                raw_data = self.get_windows_ports()
                parsed_data = self.parse_windows_output(raw_data)
            else:
                raw_data = self.get_linux_ports()
                parsed_data = self.parse_linux_output(raw_data)

            # 2. Go Backend data (Optional merge)
            go_data = self.run_go_scan()
            
            # 3. Analyze
            analyzed_data = self.analyze_risk(parsed_data)
            self.last_results = analyzed_data
            callback_success(analyzed_data)
        except Exception as e:
            callback_error(str(e))

    def analyze_risk(self, data):
        for entry in data:
            score, reasoning = self.get_risk_score(entry["proc"], entry["port"], entry["ip"])
            status = "SAFE" if score < 35 else "WARNING" if score < 75 else "SUSPICIOUS"
            entry.update({
                "score": score, 
                "status": status, 
                "reasons": reasoning,
                "service": "Service" # Placeholder
            })
        return data

    def get_result_by_port_and_proc(self, port, proc_name):
        return next((e for e in self.last_results if str(e["port"]) == str(port) and e["proc"] == proc_name), None)

    def get_windows_ports(self):
        return subprocess.run(['netstat', '-ano'], capture_output=True, text=True, errors="ignore").stdout

    def get_linux_ports(self):
        return subprocess.run(['ss', '-tulnp'], capture_output=True, text=True, errors="ignore").stdout

    def parse_windows_output(self, output):
        parsed = []
        for line in output.strip().split('\n'):
            if "LISTENING" not in line: continue
            parts = line.split()
            if len(parts) < 5: continue
            ip, port = parts[1].rsplit(':', 1)
            pid = parts[4]
            try: proc = psutil.Process(int(pid)).name()
            except: proc = f"PID {pid}"
            parsed.append({"proto": parts[0].upper(), "ip": ip, "port": int(port), "proc": proc})
        return parsed

    def parse_linux_output(self, output):
        parsed = []
        for line in output.strip().split('\n')[1:]:
            parts = line.split()
            if len(parts) < 5 or ':' not in parts[4]: continue
            ip, port = parts[4].rsplit(':', 1)
            proc = "Unknown"
            match = re.search(r'users:\(\("([^"]+)"', line)
            if match: proc = match.group(1)
            parsed.append({"proto": parts[0].upper(), "ip": ip, "port": int(port), "proc": proc})
        return parsed

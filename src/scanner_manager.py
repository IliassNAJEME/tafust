import subprocess
import json
import os
import sys
import platform
import psutil
import threading
import re
from datetime import datetime
from src import security_analyst

# Force UTF-8 stdout pour éviter les UnicodeEncodeError sur Windows (cp1252)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Configuration
DATA_DIR = "tafust_data"
# Résolution robuste du chemin de configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WHITELIST_FILE = os.path.join(BASE_DIR, "config", "whitelist.json")
GO_ENGINE_PATH = os.path.join(BASE_DIR, "engine", "scanner.exe")

# Listes de confiance pour réduire les faux positifs
KNOWN_BROWSERS = ["brave", "chrome", "firefox", "msedge", "safari", "opera"]

class ScannerManager:
    def __init__(self, exclude_local=False):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.os_type = platform.system()
        self.exclude_local = exclude_local
        self.whitelist = self.load_whitelist()
        self.last_results = []

    def load_whitelist(self):
        whitelist = set()
        print(f"[DEBUG] Recherche de la whitelist : {WHITELIST_FILE}")
        try:
            if os.path.exists(WHITELIST_FILE):
                with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    services = data.get("authorized_services", [])
                    for s in services:
                        whitelist.add(s.strip().lower())
                print(f"[OK] Whitelist chargee : {len(whitelist)} services autorises.")
            else:
                print(f"[WARN] Fichier whitelist non trouve : {WHITELIST_FILE}")
        except Exception as e:
            print(f"[ERR] Erreur lors du chargement de la whitelist : {e}")
        return whitelist

    def get_risk_score(self, process_name, port, address):
        score = 0
        reasoning = []
        proc_norm = process_name.lower()
        if proc_norm.endswith(".exe"): proc_norm = proc_norm[:-4]

        # 1. Vérification Whitelist (Services critiques autorisés)
        is_whitelisted = False
        for whitelisted_service in self.whitelist:
            if whitelisted_service == proc_norm or whitelisted_service in proc_norm:
                is_whitelisted = True
                break
        
        if is_whitelisted:
            return 0, [f"✅ [SAFE] Whitelisted: '{process_name}' est un service autorisé."]

        # 2. Détection de Navigateurs Connus (Réduction de faux positifs)
        is_browser = any(browser in proc_norm for browser in KNOWN_BROWSERS)
        if is_browser:
            if port == 5353:
                return 10, [f"ℹ️ [KNOWN BROWSER] '{process_name}' utilise mDNS (Port 5353). Activité réseau normale."]
            return 12, [f"ℹ️ [KNOWN BROWSER] '{process_name}' est un navigateur identifié."]

        # 3. Cas particulier : mDNS (Port 5353) hors navigateur
        if port == 5353:
            return 20, ["📡 [NETWORK] Port 5353 (mDNS) détecté. Souvent utilisé pour la découverte de services."]

        # 4. Scoring par défaut pour processus inconnu
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
            # 1. Collecte des ports (fallback Python)
            if self.os_type == "Windows":
                raw_data = self.get_windows_ports()
                parsed_data = self.parse_windows_output(raw_data)
            else:
                raw_data = self.get_linux_ports()
                parsed_data = self.parse_linux_output(raw_data)

            # 2. (Optionnel) Données du moteur Go
            self.run_go_scan()

            # 3. Filtrage local si activé
            if self.exclude_local:
                parsed_data = [
                    e for e in parsed_data
                    if not security_analyst._is_local_address(e.get("ip", ""))
                ]

            # 4. Analyse intelligente via security_analyst
            report = security_analyst.analyze(parsed_data)
            self.last_results = parsed_data   # Conservé pour l'export JSON brut
            self.last_report   = report        # Rapport structuré pour l'UI
            callback_success(report)
        except Exception as e:
            callback_error(str(e))

    def analyze_risk(self, data):
        """Conservé pour compatibilité — désormais délégué à security_analyst."""
        return security_analyst.analyze(data)

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

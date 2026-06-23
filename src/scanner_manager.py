import json
import os
import platform
import re
import subprocess
import sys
import threading

import psutil

from src import security_analyst
from src.reputation import ReputationService


if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


DATA_DIR = "tafust_data"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WHITELIST_FILE = os.path.join(BASE_DIR, "config", "whitelist.json")
GO_ENGINE_PATH = os.path.join(BASE_DIR, "engine", "scanner.exe")


class ScannerManager:
    def __init__(self, exclude_local: bool = False):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.os_type = platform.system()
        self.exclude_local = exclude_local
        self.whitelist = self.load_whitelist()
        self.last_results = []
        self.last_report = {}
        self.reputation = ReputationService()

    def load_whitelist(self) -> set[str]:
        whitelist = set()
        try:
            if os.path.exists(WHITELIST_FILE):
                with open(WHITELIST_FILE, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                for service in data.get("authorized_services", []):
                    whitelist.add(service.strip().lower())
        except Exception as exc:
            print(f"[ERR] Failed to load whitelist: {exc}")
        return whitelist

    def run_go_scan(self) -> list[dict]:
        if not os.path.exists(GO_ENGINE_PATH):
            return []
        try:
            result = subprocess.run([GO_ENGINE_PATH], capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except Exception:
            return []

    def start_async_scan(self, callback_success, callback_error) -> None:
        threading.Thread(
            target=self._scan_thread,
            args=(callback_success, callback_error),
            daemon=True,
        ).start()

    def run_scan(self) -> dict:
        parsed_data = self._collect_scan_data()
        report = security_analyst.analyze(parsed_data)
        self.last_results = parsed_data
        self.last_report = report
        return report

    def _scan_thread(self, callback_success, callback_error) -> None:
        try:
            callback_success(self.run_scan())
        except Exception as exc:
            callback_error(str(exc))

    def _collect_scan_data(self) -> list[dict]:
        if self.os_type == "Windows":
            parsed_data = self.parse_windows_output(self.get_windows_ports())
        else:
            parsed_data = self.parse_linux_output(self.get_linux_ports())

        self.run_go_scan()

        if self.exclude_local:
            parsed_data = [
                entry
                for entry in parsed_data
                if not security_analyst.is_local_address(entry.get("ip", ""))
            ]

        return [self.reputation.enrich_entry(entry) for entry in parsed_data]

    def analyze_risk(self, data: list[dict]) -> dict:
        return security_analyst.analyze(data)

    def get_result_by_port_and_proc(self, port, proc_name):
        return next(
            (entry for entry in self.last_results if str(entry["port"]) == str(port) and entry["proc"] == proc_name),
            None,
        )

    def get_windows_ports(self) -> str:
        return subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            errors="ignore",
        ).stdout

    def get_linux_ports(self) -> str:
        return subprocess.run(
            ["ss", "-tulnp"],
            capture_output=True,
            text=True,
            errors="ignore",
        ).stdout

    def parse_windows_output(self, output: str) -> list[dict]:
        parsed = []
        for line in output.strip().splitlines():
            if "LISTENING" not in line:
                continue
            parts = line.split()
            if len(parts) < 5:
                continue

            ip, port = parts[1].rsplit(":", 1)
            pid_text = parts[4]
            pid = int(pid_text)
            proc = f"PID {pid}"
            path = ""

            try:
                process = psutil.Process(pid)
                proc = process.name()
                try:
                    path = process.exe()
                except Exception:
                    path = ""
            except Exception:
                pass

            parsed.append(
                {
                    "proto": parts[0].upper(),
                    "ip": ip,
                    "port": int(port),
                    "proc": proc,
                    "pid": pid,
                    "path": path,
                }
            )
        return parsed

    def parse_linux_output(self, output: str) -> list[dict]:
        parsed = []
        for line in output.strip().splitlines()[1:]:
            parts = line.split()
            if len(parts) < 5 or ":" not in parts[4]:
                continue

            ip, port = parts[4].rsplit(":", 1)
            proc = "Unknown"
            match = re.search(r'users:\(\("([^"]+)"', line)
            if match:
                proc = match.group(1)

            parsed.append(
                {
                    "proto": parts[0].upper(),
                    "ip": ip,
                    "port": int(port),
                    "proc": proc,
                    "pid": None,
                    "path": "",
                }
            )
        return parsed

import json
import os
import psutil
from tkinter import filedialog, messagebox
import tkinter as tk

class WebviewAPI:
    def __init__(self, manager):
        self._manager = manager
        self._window = None
        
        # Attach the progress callback so the manager can report back
        self._manager.progress_callback = self.on_progress

    def set_window(self, window):
        """Called immediately after creating the webview window to store its reference."""
        self._window = window

    def on_progress(self, step, detail):
        """Called by ScannerManager during the scan process."""
        if self._window:
            # We must call evaluate_js to execute JS in the frontend
            # The JS should define a global window.updateProgress(step, detail)
            self._window.evaluate_js(f"window.updateProgress('{step}', '{detail}')")

    def start_scan(self, exclude_local):
        """Called by JS to start the scan."""
        self._manager.exclude_local = exclude_local
        # The manager runs in a thread automatically with start_async_scan
        self._manager.start_async_scan(self.on_scan_success, self.on_scan_error)
        return {"status": "started"}

    def on_scan_success(self, report):
        """Called when start_async_scan completes successfully."""
        self._manager.last_report = report
        if self._window:
            # Pass the report object as a JSON string to a JS function
            # json.dumps escapes quotes, making it safe for JS evaluation
            import base64
            # A safer way to pass large JSON objects is base64
            json_str = json.dumps(report)
            b64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
            self._window.evaluate_js(f"window.onScanComplete(JSON.parse(atob('{b64_str}')))")

    def on_scan_error(self, error_msg):
        """Called when start_async_scan fails."""
        if self._window:
            import json
            safe_error = json.dumps(error_msg)
            self._window.evaluate_js(f"window.onScanError({safe_error})")

    def get_system_info(self):
        """Called by JS to get real-time CPU/RAM usage and OS info."""
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            os_type = self._manager.os_type
            vt_active = bool(os.getenv("VIRUSTOTAL_API_KEY"))
            return {
                "cpu": cpu,
                "ram": ram,
                "os": os_type,
                "vt_active": vt_active
            }
        except Exception as e:
            return {"error": str(e)}

    def export_json(self):
        """Called by JS to save the report to a file."""
        if not self._manager.last_report:
            return {"error": "Aucun rapport à exporter."}
            
        # We need a hidden root for filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        filepath = filedialog.asksaveasfilename(
            parent=root,
            defaultextension=".json",
            filetypes=[("Fichiers JSON", "*.json")],
            title="Exporter le rapport d'audit"
        )
        
        root.destroy()
        
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(self._manager.last_report, f, indent=4, ensure_ascii=False)
                return {"success": True, "path": filepath}
            except Exception as e:
                return {"error": str(e)}
        return {"success": False, "cancelled": True}

    def copy_to_clipboard(self, text):
        """Called by JS to copy text to clipboard."""
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update() # necessary to process events
        root.destroy()
        return {"success": True}

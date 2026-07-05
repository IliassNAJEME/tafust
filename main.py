import os
import webview

from src.app_paths import get_runtime_dir
from src.scanner_manager import ScannerManager
from src.webview_api import WebviewAPI

try:
    from dotenv import find_dotenv, load_dotenv
except Exception:
    find_dotenv = None
    load_dotenv = None

def main():
    if load_dotenv is not None:
        dotenv_path = find_dotenv(usecwd=True) if find_dotenv is not None else ""
        if not dotenv_path:
            runtime_env = os.path.join(get_runtime_dir(), ".env")
            dotenv_path = runtime_env if os.path.exists(runtime_env) else ""
        load_dotenv(dotenv_path or None)

    # 1. Initialisation de la logique (Backend)
    manager = ScannerManager()

    # 2. JS Bridge API
    api = WebviewAPI(manager)

    # 3. Chemins de l'UI HTML
    from src.app_paths import get_resource_path
    html_path = get_resource_path("webview_ui", "index.html")

    # 4. Lancement de pywebview
    print("🧿 Tafust : Interface PyWebview (HTML/JS) chargée.")
    window = webview.create_window(
        'Tafust - Network Security Audit',
        html_path,
        js_api=api,
        width=1300,
        height=850,
        background_color='#0a0e14'
    )
    
    api.set_window(window)
    webview.start(debug=True)

if __name__ == "__main__":
    main()

import os

import customtkinter as ctk
from src.interface import TafustUI
from src.app_paths import get_runtime_dir
from src.scanner_manager import ScannerManager

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

    # 2. Initialisation de l'Interface Moderne (CustomTkinter)
    # TafustUI hérite maintenant de ctk.CTk, elle est sa propre fenêtre racine.
    app = TafustUI(None, manager)

    # 3. Lancement
    print("🧿 Tafust : Interface Moderne chargée.")
    app.mainloop()

if __name__ == "__main__":
    main()

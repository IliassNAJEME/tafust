import customtkinter as ctk
from src.interface import TafustUI
from src.scanner_manager import ScannerManager

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

def main():
    if load_dotenv is not None:
        load_dotenv()

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

import tkinter as tk
from src.interface import TafustUI
from src.scanner_manager import ScannerManager

def main():
    # 1. Initialisation de la logique
    manager = ScannerManager()

    # 2. Initialisation de l'UI
    root = tk.Tk()
    app = TafustUI(root, manager)

    # 3. Lancement
    print("🧿 Tafust : Application démarrée (Architecture Modulaire)")
    root.mainloop()

if __name__ == "__main__":
    main()

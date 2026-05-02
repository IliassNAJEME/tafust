import os

def setup_project():
    print("--- Reconstruction de la structure Tafust ---")

    # Dossiers a creer
    folders = ["src", "engine"]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"[OK] Dossier cree : /{folder}")

    # Creation du fichier __init__.py pour faire de /src un module Python
    init_file = os.path.join("src", "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            pass
        print("[OK] Fichier src/__init__.py cree")

    print("\n--- Structure prete. Les fichiers de code vont etre generes. ---")

if __name__ == "__main__":
    setup_project()

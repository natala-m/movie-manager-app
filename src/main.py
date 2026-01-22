import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication

# KOnfiguracja ścieżek
# Dodajemy folder 'src' do ścieżek, żeby Python widział moduły
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir / 'src'))

# Ładowanie zmiennych środowiskowych (.env)
load_dotenv(current_dir / '.env')

# Import modułów
try:
    from core.database import DataBase
    from core.file_scanner import FileScanner
    from core.tmdb_api import TMDBClient
    from ui.main_window import MovieLibrary
except ImportError as e:
    print(f"BŁĄD KRYTYCZNY: Nie znaleziono modułów.\nSzczegóły: {e}")
    print("Upewnij się, że struktura folderów to: src/core oraz src/ui")
    sys.exit(1)

def load_stylesheet(app):
    """Inteligentne ładowanie stylu QSS"""
    # 1. Pobiera ścieżkę do folderu, w którym fizycznie leży main.py
    script_dir = Path(__file__).resolve().parent
    
    # 2. Definiuje potencjalne lokalizacje (zależnie od tego, czy main.py jest w / czy w /src)
    possible_paths = [
        script_dir / "ui" / "style.qss",          # jeśli main.py jest w src/
        script_dir / "src" / "ui" / "style.qss",  # jeśli main.py jest w folderze głównym
        Path.cwd() / "src" / "ui" / "style.qss"   # ostateczność: ścieżka z terminala
    ]

    for qss_path in possible_paths:
        if qss_path.exists():
            try:
                with open(qss_path, "r", encoding="utf-8") as f:
                    app.setStyleSheet(f.read())
                    print(f"Styl załadowany z: {qss_path}")
                    return
            except Exception as e:
                print(f" Błąd odczytu pliku stylu: {e}")
                return

    print(f"Nie znaleziono pliku style.qss. Sprawdzono lokalizacje: {[str(p) for p in possible_paths]}")

def main():
    # 1. Inicjalizacja aplikacji Qt
    app = QApplication(sys.argv)
    
    # 2. Załadowanie stylów
    load_stylesheet(app)

    # 3. Inicjalizacja komponentów
    try:
        db = DataBase() 
        scanner = FileScanner() # Skaner plików
        tmdb = TMDBClient()     # Klient API (Filmy + Seriale)
        
        print("Backend zainicjalizowany pomyślnie.")
    except Exception as e:
        print(f"Błąd inicjalizacji backendu: {e}")
        sys.exit(1)

    # 4. Uruchomienie głównego okna
    window = MovieLibrary(db, scanner, tmdb)
    window.show()

    # 5. Pętla główna aplikacji
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    
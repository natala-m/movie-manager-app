import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import pprint  # Do czytelnego wyświetlania struktur danych

# --- KONFIGURACJA ŚRODOWISKA ---
# Ustalanie ścieżki do katalogu głównego projektu, aby Python widział folder 'src'
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
src_path = project_root / 'src'

# Dodanie src do ścieżek systemowych
sys.path.append(str(src_path))

# Jawne ładowanie pliku .env
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

# --- IMPORT MODUŁU API ---
try:
    from core.tmdb_api import TMDBClient
except ImportError as e:
    print(f"[CRITICAL] Nie udalo sie zaimportowac modulu core.tmdb_api.")
    print(f"Szukano w: {src_path}")
    print(f"Blad: {e}")
    sys.exit(1)

# --- PARAMETRY TESTU ---
TEST_QUERY = "Pluribus"  # Tutaj wpisz tytul do testu
IS_TV_SHOW = True
def run_integration_test():
    print(f"[INFO] Rozpoczynam test integracyjny API TMDB.")
    print(f"[INFO] Sciezka projektu: {project_root}")
    
    # 1. Weryfikacja klucza API
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        print("[ERROR] Brak zmiennej TMDB_API_KEY w pliku .env.")
        return

    print(f"[INFO] Klucz API zaladowany: {api_key[:5]}...")

    # 2. Inicjalizacja klienta
    try:
        client = TMDBClient()
    except Exception as e:
        print(f"[ERROR] Blad podczas inicjalizacji klasy TMDBClient: {e}")
        return

    # 3. Wykonanie zapytania
    print(f"[INFO] Wysylanie zapytania dla: '{TEST_QUERY}' (Tryb TV: {IS_TV_SHOW})...")
    
    try:
        if IS_TV_SHOW:
            data = client.search_tv_show(TEST_QUERY) # Nowa metoda
        else:
            data = client.search_movies(TEST_QUERY)  # Stara metoda
            
    except Exception as e:
        print(f"[ERROR] Wyjatek: {e}")
        return
    # 4. Analiza wynikow
    if data is None:
        print("[FAIL] Metoda zwrocila None. Mozliwe przyczyny:")
        print(" - Blad autoryzacji (401)")
        print(" - Brak wynikow dla podanego tytulu")
        print(" - Blad polaczenia sieciowego")
    else:
        print("\n" + "="*40)
        print("WYNIK TESTU (DANE OTRZYMANE Z API)")
        print("="*40)
        
        # Weryfikacja kluczowych pol
        title = data.get('title')
        director = data.get('director')
        year = data.get('release_year')
        poster = data.get('poster_url')
        tmdb_id = data.get('tmdb_id')

        # Wyswietlanie surowych danych wymaganych przez UI
        print(f"ID Filmu (TMDB): {tmdb_id}")
        print(f"Tytul:           {title}")
        print(f"Rezyser:         {director}")
        print(f"Rok produkcji:   {year}")
        print(f"URL Plakatu:     {poster}")
        
        print("-" * 40)
        
        # Walidacja logiczna (Assertion logic)
        missing = []
        if not title: missing.append("title")
        if not poster: missing.append("poster_url")
        
        if missing:
            print(f"[WARNING] Otrzymano dane, ale brakuje kluczowych wartosci: {missing}")
        elif poster and not poster.startswith("http"):
             print(f"[WARNING] URL plakatu wyglada na niepoprawny: {poster}")
        else:
            print("[SUCCESS] Test zakonczony pomyslnie. Dane sa poprawne i gotowe do wyswietlenia w UI.")

if __name__ == "__main__":
    run_integration_test()
import pytest
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Konfiguracja ścieżek (żeby widzieć folder src)
current_path = Path(__file__).resolve().parent
project_root = current_path.parent
sys.path.append(str(project_root / 'src'))

# Ładowanie zmiennych środowiskowych
load_dotenv(project_root / '.env')

# Import Twojej klasy bazy danych
try:
    from core.database import DataBase
except ImportError:
    print("Nie znaleziono pliku src/core/database.py")
    sys.exit(1)

# --- KONFIGURACJA TESTÓW (FIXTURES) ---

@pytest.fixture
def db():
    """
    To jest 'setup' testu. Uruchamia się przed każdą funkcją testową.
    Tworzy połączenie i podmienia kolekcję na testową.
    """
    database = DataBase()
    
    # WAŻNE: Podmieniamy kolekcję na testową, żeby nie usunąć Twoich prawdziwych filmów!
    # Zakładam, że w db_manager masz self.db jako obiekt bazy
    database.collection = database.db["test_movies_collection"]
    
    # Wyczyść starą bazę testową przed startem
    database.collection.drop()
    
    yield database  # Tutaj dzieje się test
    
    # Sprzątanie po teście (opcjonalne, można zostawić do podglądu w Compass)
    database.collection.drop()

# --- WŁAŚCIWE TESTY ---

def test_connection(db):
    """Sprawdza czy w ogóle połączyliśmy się z Mongo"""
    # Pingowanie serwera
    try:
        db.client.admin.command('ping')
        assert True
    except Exception as e:
        pytest.fail(f"Nie można połączyć się z MongoDB: {e}")

def test_add_movie(db):
    """Sprawdza czy można dodać nowy film"""
    path = "/home/user/Filmy/TestowyFilm.mkv"
    title = "Testowy Film"
    
    # 1. Dodajemy film
    movie_id = db.add_movie(path, title)
    
    # Sprawdzamy czy ID zostało zwrócone (czyli czy zapis się udał)
    assert movie_id is not None
    
    # 2. Sprawdzamy czy film faktycznie jest w bazie
    saved_movie = db.collection.find_one({"_id": movie_id})
    assert saved_movie['file_path'] == path
    assert saved_movie['title_scanned'] == title

def test_no_duplicates(db):
    """Sprawdza czy system blokuje dodawanie tego samego pliku dwa razy"""
    path = "/home/user/Filmy/TenSam.mp4"
    
    # Pierwsze dodanie
    id1 = db.add_movie(path, "Tytuł 1")
    assert id1 is not None
    
    # Drugie dodanie tego samego pliku
    id2 = db.add_movie(path, "Tytuł Inny")
    
    # Powinno zwrócić None (lub ID pierwszego filmu), zależnie od Twojej logiki w db_manager.
    # Zakładając standardową logikę 'nie dodawaj duplikatów':
    
    # Sprawdźmy ile jest dokumentów - powinien być tylko 1
    count = db.collection.count_documents({})
    assert count == 1

def test_update_movie_details(db):
    """Sprawdza czy dane z API (TMDB) poprawnie aktualizują rekord w bazie"""
    # 1. Najpierw dodajemy 'pusty' film ze skanera
    path = "/home/user/Avatar.mp4"
    movie_id = db.add_movie(path, "Avatar")
    
    # 2. Symulujemy dane, które przyszłyby z API
    tmdb_data = {
        "title": "Avatar: Istota Wody",
        "director": "James Cameron",
        "release_year": "2022",
        "poster_url": "http://obrazek.jpg",
        "overview": "Opis filmu..."
    }
    
    # 3. Aktualizujemy rekord
    db.update_movie_details(movie_id, tmdb_data, tmdb_id=99999)
    
    # 4. Pobieramy film z powrotem i sprawdzamy zmiany
    updated_movie = db.collection.find_one({"_id": movie_id})
    
    details = updated_movie.get('movie_details', {})
    assert details['director'] == "James Cameron"
    assert details['release_year'] == "2022"
    assert updated_movie['tmdb_id'] == 99999

def test_get_all_movies(db):
    """Sprawdza czy pobieranie listy działa"""
    db.add_movie("/a.mp4", "A")
    db.add_movie("/b.mp4", "B")
    
    movies = db.get_all_movies()
    assert len(movies) == 2
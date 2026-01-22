import os
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId

class DataBase:
    def __init__(self):
        # Pobieramy URI lub domyślny localhost
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.client = MongoClient(uri)
        self.db = self.client["movie_library"]
        self.collection = self.db["movies"]

    def add_movie(self, file_path, title_scanned):
        """
        Dodaje film i zwraca jego ID.
        Jeśli film już istnieje, zwraca ID istniejącego.
        """
        existing = self.collection.find_one({"file_path": file_path})
        if existing:
            # Zwracamy istniejące ID (to jest obiekt ObjectId)
            return existing["_id"]
        
        movie_doc = {
            "file_path": file_path,
            "title_scanned": title_scanned,
            "movie_details": {}, # Puste na start
            "tmdb_id": None
        }
        result = self.collection.insert_one(movie_doc)
        return result.inserted_id

    def update_movie_details(self, movie_id, details, tmdb_id):
        """
        Aktualizuje rekord o dane z API.
        Obsługuje zarówno ID jako string jak i ObjectId.
        """
        try:
            # Upewniamy się, że ID to ObjectId
            if isinstance(movie_id, str):
                oid = ObjectId(movie_id)
            else:
                oid = movie_id

            # Wykonaj aktualizację
            result = self.collection.update_one(
                {"_id": oid},
                {"$set": {
                    "movie_details": details,
                    "tmdb_id": tmdb_id
                }}
            )
            
            # DIAGNOSTYKA W TERMINALU
            if result.modified_count > 0:
                print(f"Zaktualizowano rekord {oid}")
            elif result.matched_count > 0:
                print(f"Rekord znaleziony, ale dane te same (brak zmian).")
            else:
                print(f"Nie znaleziono ID {oid} do aktualizacji!")

        except InvalidId:
            print(f"Nieprawidłowy format ID: {movie_id}")
        except Exception as e:
            print(f" BŁĄD KRYTYCZNY: {e}")

    def get_all_movies(self):
        """Pobiera wszystkie filmy"""
        try:
            # Sortujemy alfabetycznie po tytule skanera
            return list(self.collection.find().sort("title_scanned", 1))
        except Exception as e:
            print(f"Błąd pobierania listy: {e}")
            return []
    
    # Metoda pomocnicza do czyszczenia bazy (przyda się zaraz)
    def clear_database(self):
        self.collection.drop()
        print("Baza danych wyczyszczona.")
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class TMDBClient:
    def __init__(self):
        self.api_key = os.getenv("TMDB_API_KEY")
        self.BASE_URL = "https://api.themoviedb.org/3"
        self.IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
        self.BACKDROP_BASE_URL = "https://image.tmdb.org/t/p/w1280"

    def _format_result(self, item, media_type=None):
        if not item: return None
        
        m_type = media_type or item.get('media_type')

        if m_type == 'tv':
            title = item.get('name')
            date = item.get('first_air_date', '')
            final_type = 'tv'
        else:
            title = item.get('title')
            date = item.get('release_date', '')
            final_type = 'movie'

        found_year = date[:4] if date else '----'
        genres = [g['name'] for g in item.get('genres', [])]
        
        return {
            "tmdb_id": item.get('id'),
            "title": title,
            "release_year": found_year,
            "poster_url": f"{self.IMAGE_BASE_URL}{item.get('poster_path')}" if item.get('poster_path') else None,
            "backdrop_url": f"{self.BACKDROP_BASE_URL}{item.get('backdrop_path')}" if item.get('backdrop_path') else None,
            "vote_average": item.get('vote_average', 0),
            "genres": genres,
            "overview": item.get('overview', 'Brak opisu'),
            "type": final_type
        }

    # multipoint search, szuka i filmy i seriale
    def search_smart(self, query, year=None, force_tv=False):
        if not self.api_key: return None
        
        # Jeśli plik wygląda na serial, szukaj w serialach
        if force_tv:
            return self._search_specific(query, year, 'tv')
        
        try:
            url = f"{self.BASE_URL}/search/multi"
            params = {
                "api_key": self.api_key, "query": query, 
                "language": "en-EN", "include_adult": "false"
            }
            res = requests.get(url, params=params)
            results = res.json().get('results', [])
            
            valid = [r for r in results if r['media_type'] in ['movie', 'tv']]
            if not valid: return None
            
            best = valid[0]
            if year:
                for match in valid:
                    d = match.get('release_date') or match.get('first_air_date')
                    if d and d.startswith(str(year)):
                        best = match
                        break
            
            return self._get_details_by_id(best['id'], best['media_type'])

        except Exception as e:
            print(f"Błąd Multi: {e}")
            return None

    def _search_specific(self, query, year, endpoint):
        try:
            url = f"{self.BASE_URL}/search/{endpoint}"
            params = {"api_key": self.api_key, "query": query, "language": "pl-PL"}
            if year:
                if endpoint == 'movie': params["primary_release_year"] = year
                else: params["first_air_date_year"] = year

            res = requests.get(url, params=params)
            results = res.json().get('results', [])
            if not results: return None
            
            return self._get_details_by_id(results[0]['id'], endpoint)
        except Exception as e:
            print(f"Błąd Specific {endpoint}: {e}")
            return None

    # === SMART GET BY ID (POPRAWIONE) ===
    def get_smart_by_id(self, tmdb_input, prefer_tv=False):
        """
        tmdb_input: może być '123' albo 'tv:123'
        prefer_tv: True jeśli plik wygląda na serial
        """
        if not self.api_key: return None
        
        # Obsługa wymuszenia przez prefiks "tv:"
        tmdb_str = str(tmdb_input).strip().lower()
        if tmdb_str.startswith('tv:'):
            clean_id = tmdb_str.replace('tv:', '')
            return self._get_details_by_id(clean_id, 'tv')
        
        if tmdb_str.startswith('movie:'):
            clean_id = tmdb_str.replace('movie:', '')
            return self._get_details_by_id(clean_id, 'movie')

        # Logika priorytetów (gdy podano samo ID)
        if prefer_tv:
            # 1. Serial, 2. Film
            res = self._get_details_by_id(tmdb_input, 'tv')
            if res: return res
            return self._get_details_by_id(tmdb_input, 'movie')
        else:
            # 1. Film, 2. Serial
            res = self._get_details_by_id(tmdb_input, 'movie')
            if res: return res
            return self._get_details_by_id(tmdb_input, 'tv')

    def _get_details_by_id(self, tmdb_id, endpoint):
        try:
            url = f"{self.BASE_URL}/{endpoint}/{tmdb_id}"
            params = {"api_key": self.api_key, "language": "en-EN"}
            res = requests.get(url, params=params)
            if res.status_code == 200:
                return self._format_result(res.json(), endpoint) 
            return None
        except:
            return None
import os
import re

class FileScanner:
    VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv')

    def scan_folder(self, folder_path):
        found_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(self.VIDEO_EXTENSIONS):
                    full_path = os.path.join(root, file)
                    
                    # Pobieramy też kod odcinka (np. "S01E01")
                    clean_title, year, is_tv, episode_code = self._analyze_filename(file)
                    
                    found_files.append({
                        'filepath': full_path,
                        'title_guess': clean_title,
                        'year_guess': year,
                        'is_tv_guess': is_tv,
                        'episode_code': episode_code # <--- ZAPAMIĘTUJEMY ODCINEK
                    })
        return found_files

    def _analyze_filename(self, filename):
        name = os.path.splitext(filename)[0]
        name = name.replace('.', ' ').replace('_', ' ').replace('-', ' ')
        
        is_tv = False
        episode_code = ""

        # Szukamy S01E01, 1x01 itp.
        serial_match = re.search(r'\b(s\d+e\d+|s\d+|\d+x\d+)\b', name, re.IGNORECASE)
        
        if serial_match:
            is_tv = True
            episode_code = serial_match.group(0).upper() # Wyciągamy np. "S01E01"
            name = name[:serial_match.start()] # Ucinamy tytuł przed numerem

        year_match = re.findall(r'\b(19\d{2}|20\d{2})\b', name)
        year = year_match[-1] if year_match else None
        
        if year:
            year_pos = name.find(year)
            if year_pos != -1:
                name = name[:year_pos]

        junk = [
            '1080p', '720p', '4k', 'bluray', 'web-dl', 'webrip', 'x264', 'hevc', 
            'aac', 'dts', 'hdr', 'amzn', 'netflix', 'galaxy', 'rarbg', 'leaked', 
            'dubbed', 'pl', 'season', 'episode'
        ]
        
        for j in junk:
            name = re.sub(f'(?i)\\b{j}\\b', '', name)
            
        name = re.sub(r'[\[\]\(\)\{\}]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name, year, is_tv, episode_code
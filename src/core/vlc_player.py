import subprocess
import shutil
import os

class VLCPlayer:
    def __init__(self):
        # Sprawdzamy, czy w systemie jest komenda 'vlc'
        self.vlc_executable = shutil.which("vlc")
        self.process = None

    def play(self, file_path):
        if not self.vlc_executable:
            print(" Nie znaleziono VLC w systemie. Zainstaluj je (sudo apt install vlc).")
            return

        if not os.path.exists(file_path):
            print(f"Plik nie istnieje: {file_path}")
            return
        
        # 1. Jeśli coś już gra, zabij poprzedni proces (żeby nie otwierać 10 okien)
        self.stop()

        try:
            # 2. Uruchom VLC jako osobny proces
            # --fullscreen: startuje od razu na pełnym ekranie
            # --play-and-exit: zamyka VLC po końcu filmu (opcjonalne, możesz usunąć)
            cmd = [self.vlc_executable, "--fullscreen", "--quiet", file_path]
            
            # Popen uruchamia program i pozwala Pythonowi działać dalej
            self.process = subprocess.Popen(cmd)
            print(f"Uruchomiono systemowe VLC: {file_path}")
            
        except Exception as e:
            print(f"Błąd uruchamiania VLC: {e}")

    def stop(self):
        """Zabija zewnętrzny proces VLC"""
        if self.process:
            try:
                self.process.terminate()  # Próba łagodnego zamknięcia
                self.process = None
            except:
                pass
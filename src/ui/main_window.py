import re
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFileDialog, QApplication, QFrame,
                             QMenu, QInputDialog)
from PyQt6.QtCore import Qt
from ui.movie_tile import MovieTile
from core.vlc_player import VLCPlayer

class MovieLibrary(QMainWindow):
    def __init__(self, db, scanner, tmdb):
        super().__init__()
        self.db = db
        self.scanner = scanner
        self.tmdb = tmdb
        self.vlc = VLCPlayer()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Biblioteka filmów")
        self.resize(1200, 800)
        
        central = QWidget()
        central.setObjectName("main_bg")
        self.setCentralWidget(central)
        
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        # Lewy Panel
        left_panel = QFrame()
        left_panel.setObjectName("sidebar")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 40, 20, 20)
        
        self.table = QTableWidget(0, 3) 
        self.table.setHorizontalHeaderLabels(["TYTUŁ", "ROK", "PATH"])
        self.table.setColumnHidden(2, True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 90)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self.on_select)
        
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)
        
        left_layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        self.btn_scan = QPushButton("Scan")
        self.btn_scan.clicked.connect(self.scan)
        self.btn_play = QPushButton("Play")
        self.btn_play.setObjectName("play_btn")
        self.btn_play.clicked.connect(self.play)
        
        btn_layout.addWidget(self.btn_scan)
        btn_layout.addWidget(self.btn_play)
        left_layout.addLayout(btn_layout)

        self.tile = MovieTile()
        layout.addWidget(left_panel, 35) 
        layout.addWidget(self.tile, 65)
        
        self.refresh()

    def scan(self):
        folder = QFileDialog.getExistingDirectory(self, "Wybierz folder")
        if not folder: return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            # 1. Pobierz aktualną listę plików z dysku
            found_files = self.scanner.scan_folder(folder)
            
            # --- MODUŁ SPRZĄTAJĄCY (NOWOŚĆ) ---
            # Tworzymy zbiór ścieżek, które fizycznie istnieją
            found_paths = {f['filepath'] for f in found_files}
            
            # Pobieramy wszystko z bazy
            all_db_movies = self.db.get_all_movies()
            
            for movie in all_db_movies:
                db_path = movie['file_path']
                
                # Sprawdzamy tylko pliki, które powinny być w skanowanym folderze
                if db_path.startswith(folder):
                    # Jeśli plik jest w bazie, ale nie ma go na liście znalezionych -> USUŃ
                    if db_path not in found_paths:
                        self.db.collection.delete_one({'_id': movie['_id']})
                        print(f"Usunieto nieistniejacy plik: {db_path}")

            # 2. Standardowe dodawanie/aktualizacja
            for f in found_files:
                mid = self.db.add_movie(f['filepath'], f['title_guess'])
                if mid:
                    # Aktualizacja kodu odcinka
                    if f.get('episode_code'):
                        self.db.collection.update_one(
                            {'_id': mid}, 
                            {'$set': {'episode_code': f['episode_code']}}
                        )
                    
                    print(f"Szukam: '{f['title_guess']}' (Serial? {f.get('is_tv_guess')})")
                    
                    data = self.tmdb.search_smart(
                        f['title_guess'], 
                        f.get('year_guess'), 
                        f.get('is_tv_guess')
                    )
                    
                    if data:
                        print(f"   Znaleziono: {data['title']} [{data['type'].upper()}]")
                        self.db.update_movie_details(mid, data, data['tmdb_id'])
        finally:
            QApplication.restoreOverrideCursor()
            self.refresh()

    def refresh(self):
        self.table.setRowCount(0)
        movies = self.db.get_all_movies()
        for m in movies:
            row = self.table.rowCount()
            self.table.insertRow(row)
            details = m.get('movie_details', {})
            
            title = details.get('title') or m.get('title_scanned')
            year = details.get('release_year', '')
            
            # Doklejanie kodu odcinka (S01E01)
            ep_code = m.get('episode_code', '')
            display_title = str(title)
            if ep_code:
                display_title += f"   {ep_code}"

            self.table.setItem(row, 0, QTableWidgetItem(display_title))
            
            item_year = QTableWidgetItem(str(year))
            item_year.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, item_year)
            self.table.setItem(row, 2, QTableWidgetItem(m['file_path']))

    def on_select(self):
        sel = self.table.selectedItems()
        if not sel: return
        path = self.table.item(sel[0].row(), 2).text()
        doc = self.db.collection.find_one({"file_path": path})
        if doc: self.tile.update_info(doc)

    def play(self):
        sel = self.table.selectedItems()
        if sel:
            path = self.table.item(sel[0].row(), 2).text()
            self.vlc.play(path)

    def open_context_menu(self, position):
        menu = QMenu()
        fix_action = menu.addAction("Napraw (Podaj ID)")
        action = menu.exec(self.table.viewport().mapToGlobal(position))
        if action == fix_action: self.fix_match()

    def fix_match(self):
        sel = self.table.selectedItems()
        if not sel: return
        row = sel[0].row()
        file_path = self.table.item(row, 2).text()
        
        tmdb_id, ok = QInputDialog.getText(self, "Napraw", 
            "Podaj ID")
        
        if ok and tmdb_id:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                looks_like_tv = False
                if re.search(r'\b(s\d+|e\d+|season|episode)\b', file_path, re.IGNORECASE):
                    looks_like_tv = True

                print(f"Naprawiam ID: {tmdb_id}")
                data = self.tmdb.get_smart_by_id(tmdb_id.strip(), prefer_tv=looks_like_tv)
                
                if data:
                    doc = self.db.collection.find_one({"file_path": file_path})
                    self.db.update_movie_details(doc['_id'], data, data['tmdb_id'])
                    print(f"Naprawiono na: {data['title']} ({data['type']})")
                else:
                    print("Nie znaleziono ID")
            finally:
                QApplication.restoreOverrideCursor()
                self.refresh()
                self.on_select()

    def closeEvent(self, event):
        self.vlc.stop()
        event.accept()
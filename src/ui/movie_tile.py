from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush, QLinearGradient
from PyQt6.QtCore import Qt, QUrl, QRect
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

class MovieTile(QWidget):
    def __init__(self):
        super().__init__()
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self._on_image_loaded)
        
        self.backdrop_pixmap = None 
        self.init_ui()

    def init_ui(self):
        # Główny układ - marginesy dają "oddech"
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignBottom) # Treść przyklejona do dołu

        # === KONTENER NA TREŚĆ ===
        # Dzięki temu tekst będzie nad tłem
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(25)
        content_layout.setContentsMargins(0,0,0,0)

        # 1. PLAKAT (Mały, elegancki po lewej)
        self.poster_label = QLabel()
        self.poster_label.setFixedSize(160, 240)
        self.poster_label.setStyleSheet("""
            border: 1px solid rgba(255,255,255,0.3); 
            border-radius: 6px; 
            background-color: #000;
        """)
        self.poster_label.setScaledContents(True)

        # 2. DANE (Tytuł, Ocena, Opis)
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setSpacing(8)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        # Tytuł
        self.title_label = QLabel("Wybierz film")
        self.title_label.setStyleSheet("font-size: 38px; font-weight: 800; color: white;")
        self.title_label.setWordWrap(True)

        # Meta (Rok | Gatunki)
        self.meta_label = QLabel("")
        self.meta_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #ccc; text-transform: uppercase;")
        
        # Ocena (Gwiazdka)
        self.rating_label = QLabel("")
        self.rating_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f5c518;") # IMDb yellow

        # Opis
        self.overview_text = QLabel("Opis filmu pojawi się tutaj...")
        self.overview_text.setWordWrap(True)
        self.overview_text.setStyleSheet("font-size: 15px; color: #ddd; line-height: 1.4;")
        self.overview_text.setMaximumHeight(100) # Ograniczamy wysokość opisu

        # Składanie tekstów
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.rating_label)
        text_layout.addWidget(self.meta_label)
        text_layout.addWidget(self.overview_text)

        # Składanie całości (Plakat + Teksty)
        content_layout.addWidget(self.poster_label)
        content_layout.addWidget(text_container)

        self.layout.addWidget(content_widget)

    def paintEvent(self, event):
        """Rysowanie tła (Backdrop) z przyciemnieniem"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Czarne tło bazowe
        painter.fillRect(self.rect(), QColor("#050505"))

        # 2. Rysuj obraz tła (jeśli jest)
        if self.backdrop_pixmap and not self.backdrop_pixmap.isNull():
            scaled = self.backdrop_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            
            # Wyśrodkowanie cropa
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        # 3. PROFESJONALNY GRADIENT (Vignette)
        # Przyciemniamy dół (tam gdzie tekst) i górę
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(0, 0, 0, 100))   # Góra - lekko ciemna
        gradient.setColorAt(0.4, QColor(0, 0, 0, 50))    # Środek - jasny (widać obraz)
        gradient.setColorAt(0.8, QColor(0, 0, 0, 220))   # Dół - ciemny (pod tekst)
        gradient.setColorAt(1.0, QColor(0, 0, 0, 255))   # Sam dół - czarny
        
        painter.fillRect(self.rect(), QBrush(gradient))

    def update_info(self, movie_doc):
        details = movie_doc.get('movie_details', {})
        
        # Dane
        title = details.get('title') or movie_doc.get('title_scanned')
        year = details.get('release_year', '')
        overview = details.get('overview', '')
        vote = details.get('vote_average', 0)
        genres = details.get('genres', [])

        # Aktualizacja tekstów
        self.title_label.setText(str(title))
        
        # Meta: Rok | Gatunki
        genres_str = "  •  ".join(genres[:3]) # Max 3 gatunki
        self.meta_label.setText(f"{year}   |   {genres_str}")
        
        # Ocena
        if vote > 0:
            self.rating_label.setText(f"★  {vote:.1f} / 10")
        else:
            self.rating_label.setText("")

        # Opis (utnij jeśli za długi)
        if len(overview) > 300:
            overview = overview[:300] + "..."
        self.overview_text.setText(overview)

        # Pobieranie obrazków
        poster_url = details.get('poster_url')
        backdrop_url = details.get('backdrop_url')

        # Reset
        self.poster_label.clear()
        self.backdrop_pixmap = None
        self.update() # Odśwież tło

        if poster_url:
            req = QNetworkRequest(QUrl(poster_url))
            req.setAttribute(QNetworkRequest.Attribute.User, "poster")
            self.network_manager.get(req)
        
        if backdrop_url:
            req = QNetworkRequest(QUrl(backdrop_url))
            req.setAttribute(QNetworkRequest.Attribute.User, "backdrop")
            self.network_manager.get(req)

    def _on_image_loaded(self, reply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            
            req_type = reply.request().attribute(QNetworkRequest.Attribute.User)

            if req_type == "poster":
                self.poster_label.setPixmap(pixmap.scaled(
                    self.poster_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                ))
            elif req_type == "backdrop":
                self.backdrop_pixmap = pixmap
                self.update() # Wywołuje paintEvent
        
        reply.deleteLater()
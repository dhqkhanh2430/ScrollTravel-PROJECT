# map_widget.py
import os
import folium
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl


class MapWidget(QWidget):
    """
    Simple wrapper that generates a Folium map to 'map.html' and loads it into QWebEngineView.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.web = QWebEngineView()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web)
        self.setLayout(layout)

        self.map_file = os.path.join(os.path.dirname(__file__), "map.html")

    def load_coordinates(self, lat, lon, zoom=14, popup_text=None):
        """Generate a Folium map and display a marker at (lat, lon)."""
        fmap = folium.Map(location=[lat, lon], zoom_start=zoom)
        folium.Marker([lat, lon], popup=popup_text or f"{lat}, {lon}").add_to(fmap)
        fmap.save(self.map_file)
        self.web.load(QUrl.fromLocalFile(self.map_file))

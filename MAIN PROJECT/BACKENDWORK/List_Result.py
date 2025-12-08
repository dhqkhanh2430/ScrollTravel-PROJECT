import os
import random
from PyQt5.QtGui import QPixmap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def random_qpixmap(folder):
    folder_path = os.path.join(BASE_DIR, folder)

    files = os.listdir(folder_path)
    images = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg"))]

    filename = random.choice(images)
    full_path = os.path.join(folder_path, filename)

    return QPixmap(full_path)

class Location_Components:
    def __init__(self, name, addr, category, lat, lon, label=None):
        self.name = name
        self.addr = addr
        self.lat = lat
        self.lon = lon
        self.label = label

        if "accomodation.hotel" in category:
            self.category = "Accomodation.Hotel"
        elif "accomodation.motel" in category:
            self.category = "Accomodation.Motel"

        elif "catering.bar" in category:
            self.category = "Catering.Bar"
        elif "catering.bar" in category:
            self.category = "Catering.Bar"
        elif "catering.cafe" in category:
            self.category = "Catering.Cafe"
        elif "catering.restaurant" in category:
            self.category = "Catering.Restaurant"

        elif "commercial.market" in category:
            self.category = "Commercial.Market"
        elif "commercial.supermarket" in category:
            self.category = "Commercial.Supermarket"

        elif "entertainment.aquarium" in category:
            self.category = "Entertainment.Aquarium"
        elif "entertainment.cinema" in category:
            self.category = "Entertainment.Cinema"
        elif "entertainment.theater" in category:
            self.category = "Entertainment.Theater"
        elif "entertainment.theme_park" in category:
            self.category = "Entertainment.Theme_Park"
        elif "entertainment.water_park" in category:
            self.category = "Entertainment.Water_Park"
        elif "entertainment.zoo" in category:
            self.category = "Entertainment.Zoo"

        else:
            self.category = "Unknown"

        if self.label:
            image_folder = f"images/{self.category}"
            pix = random_qpixmap(image_folder)
            if pix:
                self.label.setPixmap(pix)
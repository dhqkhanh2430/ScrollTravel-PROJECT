import os
import random
from PyQt5.QtGui import QPixmap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
ASSETS_IMAGES_DIR = os.path.join(PROJECT_ROOT, "ASSETS", "images")

#this method pulls a random photo in the folder which name is the category of the object 
#the main folder "images" is in ASSETS
def random_qpixmap(folder_name):
    folder_path = os.path.join(ASSETS_IMAGES_DIR, folder_name)

    if not os.path.isdir(folder_path):
        return QPixmap()

    images = [
        f for f in os.listdir(folder_path)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    if not images:
        return QPixmap()

    filename = random.choice(images)
    full_path = os.path.join(folder_path, filename)

    return QPixmap(full_path)

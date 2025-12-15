import requests

# BY ODIN'S BEARD YOU SHALL NOT TOUCH THIS KEY TOKEN
TOKEN = "08e15bbec77050" #<--- Sacred Artifact, priority: Absolute
ip = ""

url = f"https://ipinfo.io/{ip}?token={TOKEN}"
data = requests.get(url).json()

loc = data.get("loc")
lat, lon = loc.split(",")

print(lat, lon)
class Location_Components:
    def __init__(self, name, addr, category, lat, lon, place_id=None):
        self.name = name
        self.addr = addr
        self.lat = lat
        self.lon = lon
        self.place_id = place_id  # Thêm place_id để lấy ảnh

        if "accommodation.hotel" in category:
            self.category = "Accommodation.Hotel"
        elif "accommodation.motel" in category:
            self.category = "Accommodation.Motel"

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

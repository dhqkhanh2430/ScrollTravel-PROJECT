from geopy import Nominatim

# Hàm này để check input luôn trước khi nhét vào API để đỡ tốn credit và rút ngắn thời gian trả về nếu nhập sai
# Trong trường hợp này thì chỉ call API nếu input đúng là thành phố / làng / thị trấn
# Dự tính nếu nhập vùng (quốc gia) thì bắt phải nhập thành phố cụ thể hơn
def classify_location(query):
    # Phải khởi tạo với user_agent (module nó bắt)
    geolocator = Nominatim(user_agent="location_type_classifier")
    # Trả về đia chỉ cụ thể
    location = geolocator.geocode(query, addressdetails=True)
    if not location:
        return None, None, None  # No result found
    
    raw = location.raw
    address = raw.get('address', {})
    cls = raw.get('class', '')

    # Nếu ko có "class" hay "boundary" trong biến cls thì là nơi cụ thể
    if cls not in ("place", "boundary"):
        loc_type = "Specific Place"
    else:
        # Nếu trong address có "city", "town", bla bla
        if any(field in address for field in ("city", "town", "village", "hamlet")):
            loc_type = "City/Town"
        else:
            # Còn không thì trả về vùng như đất nước (các bang cũng tính là vùng)
            loc_type = "Region"

    # Trả về địa chỉ, loại, tọa độ
    return location.address, loc_type, (location.latitude, location.longitude)


def cityCheck(query):
    loc_query = query.strip()
    name, loc_type, coords = classify_location(loc_query)
    if name:
        if loc_type == "City/Town":
            lat, lon = coords
            return lat, lon
    else:
        return 0, 0
    
#lat, lon = cityCheck("Ha Noi")
#print(lat, lon)
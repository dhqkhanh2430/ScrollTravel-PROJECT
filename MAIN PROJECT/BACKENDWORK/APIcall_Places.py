import requests
import List_Result

# ABSOLUTELY DO NOT LEAK THIS KEY
# ABSOLUTELY DO NOT LEAK THIS KEY
# ABSOLUTELY DO NOT LEAK THIS KEY
API_KEY2 = "66edf8ecc8744a7baec8aedbfeca506f"

# Hàm tạo địa chỉ theo format: số nhà tên đường, phường, quận
def format_address(properties):
    address_parts = []
    street_part = ""
    if properties.get("housenumber"):
        street_part = properties.get("housenumber")
    
    if properties.get("street"):
        if street_part:
            street_part += " " + properties.get("street")
        else:
            street_part = properties.get("street")
    
    if street_part:
        address_parts.append(street_part)
    
    # Lấy phường/xã (suburb)
    if properties.get("suburb"):
        address_parts.append(properties.get("suburb"))
    
    # Lấy quận/huyện (district)
    if properties.get("district"):
        address_parts.append(properties.get("district"))
    
    # Nếu có ít nhất 1 thông tin thì trả về
    if address_parts:
        return ", ".join(address_parts)
    
    # Fallback: Thử dùng address_line1 hoặc address_line2
    if properties.get("address_line1"):
        return properties.get("address_line1")
    
    if properties.get("address_line2"):
        return properties.get("address_line2")
    
    # Cuối cùng mới dùng formatted
    return properties.get("formatted", "Không có địa chỉ")

# Hàm lấy input là tọa độ nơi khởi tạo tìm kiếm (Lấy từ Input_Classify nếu là thành phố), bán kính tìm kiếm (m), và loại hình giải trí
# Hàm trả một cái list tên, địa chỉ, tọa độ của các địa điểm trả về từ API call
# Thứ tự địa điểm đã được sort sẵn theo khoảng cách (gần tới xa) tới tọa độ khởi tạo tìm kiếm
def getPlaces(lat, lon, radius, categories):
    url = (
    f"https://api.geoapify.com/v2/places?"
    f"categories={categories}&"
    f"filter=circle:{lon},{lat},{radius}&"      #Cái API gọi bằng kinh độ rồi vĩ đồ
    f"bias=proximity:{lon},{lat}&"              #Trong gg map hiển thị vĩ độ rồi kinh độ =)))
    f"limit=5&apiKey={API_KEY2}"
)

    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        if data and 'features' in data and len(data['features']) > 0:
            processed_data = [
                List_Result.Location_Components(
                    f["properties"].get("name"),
                    format_address(f["properties"]),  # Dùng hàm format địa chỉ tùy chỉnh
                    f["properties"].get("categories", []),
                    f.get("geometry", {}).get("coordinates", [None, None])[1],
                    f.get("geometry", {}).get("coordinates", [None, None])[0],
                    f["properties"].get("place_id")  # Lưu place_id để lấy ảnh
                )
                for f in data.get("features", [])
            ]
            return processed_data
        else:
            return []

    except requests.exceptions.RequestException as e:
        return f"API call failed: {e}"
    except KeyError:

        return "Resp struct Error"

import requests
import List_Result

API_KEY2 = "66edf8ecc8744a7baec8aedbfeca506f"

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
                    f["properties"].get("address_line2"),
                    f["properties"].get("categories", []),
                    f.get("geometry", {}).get("coordinates", [None, None])[1],
                    f.get("geometry", {}).get("coordinates", [None, None])[0]
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
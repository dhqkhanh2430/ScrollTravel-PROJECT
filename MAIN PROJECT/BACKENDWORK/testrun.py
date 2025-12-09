import Input_Classify as ic
import APIcall_Places as ap
import Categories_Input as ci
import List_Result as lr

#This is a test file to show how the sequence of methods when running the search function

newcate = ci.Cate
newcate["Accommodation"]["Hotel"] = True
categories = ci.SetCategories(newcate)

ra = "15000"

city = "Ho Chi Minh City"

lat, lon = ic.cityCheck(city)

result = ap.getPlaces(lat, lon, ra, categories)


print(result)

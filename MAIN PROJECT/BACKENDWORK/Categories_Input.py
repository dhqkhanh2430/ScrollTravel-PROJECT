Cate = {
    "Commercial" : {
        "Supermarket" : False,
        "Market" : False
    },
    "Accommodation" : {
        "Hotel" : False,
        "Motel" : False,
    },
    "Entertainment" : {
        "Culture" : False,
        "Cinema" : False,
        "Aquarium" : False,
        "Theme_Park" : False,
        "Water_Park" : False,
        "Zoo" : False
    },
    "Catering" : {
        "Restaurant" : False,
        "Cafe" : False,
        "Bar" : False
    }
}

def SetCategories(cate_dict):
    result = []
    for main_cat, subcats in cate_dict.items():
        for subcat, value in subcats.items():
            if value:  # Only include if True
                result.append(f"{main_cat.lower()}.{subcat.lower()}")
    return ",".join(result)


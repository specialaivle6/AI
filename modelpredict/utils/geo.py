from geopy.distance import geodesic

region_coords = {
    "Region_Seoul": (37.5665, 126.9780),
    "Region_Gyeonggi": (37.4138, 127.5183),
    "Region_Daegu": (35.8714, 128.6014),
    "Region_Daejeon": (36.3504, 127.3845),
    "Region_Gangwon": (37.8228, 128.1555),
    "Region_Gwangju": (35.1595, 126.8526),
    "Region_Gyeongbuk": (36.4919, 128.8889),
    "Region_Gyeongnam": (35.4606, 128.2132),
    "Region_Incheon": (37.4563, 126.7052),
    "Region_Jeonbuk": (35.7175, 127.1530),
    "Region_Ulsan": (35.5384, 129.3114),
}

def find_nearest_region(lat: float, lon: float) -> str:
    input_coord = (lat, lon)
    return min(region_coords, key=lambda region: geodesic(input_coord, region_coords[region]).km)

# utils/region_utils.py
from functools import lru_cache
from typing import Dict, Tuple
from geopy.distance import geodesic
import csv
from utils.data_paths import find_data_file

__all__ = ["find_nearest_region", "get_region_coords"]

# CSV 없을 때 기본 좌표
_FALLBACK: Dict[str, Tuple[float, float]] = {
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

@lru_cache(maxsize=1)
def _region_coords() -> Dict[str, Tuple[float, float]]:
    """data/regions.csv가 있으면 로드, 없으면 폴백"""
    p = find_data_file("regions.csv")
    if not p:
        return _FALLBACK
    table: Dict[str, Tuple[float, float]] = {}
    with open(p, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                table[row["region"]] = (float(row["lat"]), float(row["lon"]))
            except Exception:
                continue
    return table or _FALLBACK

def find_nearest_region(lat: float, lon: float) -> str:
    """입력 좌표와 가장 가까운 Region_* 이름 반환"""
    coords = _region_coords()
    pt = (lat, lon)
    return min(coords, key=lambda r: geodesic(pt, coords[r]).km)

def get_region_coords() -> Dict[str, Tuple[float, float]]:
    """전체 지역 좌표 dict 반환(디버그/표시용)"""
    return dict(_region_coords())

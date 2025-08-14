"""
태양광 패널 성능 예측용 유틸리티 함수들
new_service에서 통합된 함수들
"""

import os
import csv
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from functools import lru_cache
import pandas as pd
from geopy.distance import geodesic
import logging

logger = logging.getLogger(__name__)

# === 데이터 파일 경로 유틸리티 ===

def find_data_file(filename: str) -> Optional[Path]:
    """데이터 파일을 여러 경로에서 찾기"""
    candidates = [
        Path("data") / filename,
        Path("new_service/data") / filename,
        Path.cwd() / "data" / filename,
    ]

    for path in candidates:
        if path.exists():
            return path
    return None


# === 지역 유틸리티 ===

# CSV 없을 때 기본 좌표
_FALLBACK_REGIONS: Dict[str, Tuple[float, float]] = {
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
def _load_region_coords() -> Dict[str, Tuple[float, float]]:
    """data/regions.csv가 있으면 로드, 없으면 폴백"""
    regions_file = find_data_file("regions.csv")
    if not regions_file:
        return _FALLBACK_REGIONS

    table: Dict[str, Tuple[float, float]] = {}
    try:
        with open(regions_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    table[row["region"]] = (float(row["lat"]), float(row["lon"]))
                except Exception:
                    continue
    except Exception as e:
        logger.warning(f"지역 파일 로드 실패, 기본값 사용: {e}")
        return _FALLBACK_REGIONS

    return table or _FALLBACK_REGIONS

def find_nearest_region(lat: float, lon: float) -> str:
    """입력 좌표와 가장 가까운 Region_* 이름 반환"""
    coords = _load_region_coords()
    pt = (lat, lon)
    return min(coords, key=lambda r: geodesic(pt, coords[r]).km)


# === 패널 스펙 유틸리티 ===

@lru_cache(maxsize=1)
def _load_model_aliases() -> Dict[str, str]:
    """모델 별칭 매핑 로드"""
    aliases_file = find_data_file("model_aliases.csv")
    if not aliases_file:
        return {}

    mapping: Dict[str, str] = {}
    try:
        df = pd.read_csv(aliases_file)
        if "alias" in df.columns and "canonical" in df.columns:
            for _, row in df.iterrows():
                alias = str(row.get("alias", "")).strip()
                canonical = str(row.get("canonical", "")).strip()
                if alias and canonical:
                    mapping[alias.lower()] = canonical
    except Exception as e:
        logger.warning(f"모델 별칭 파일 로드 실패: {e}")

    return mapping

def canonicalize_model_name(name: str) -> str:
    """별칭을 정규 모델명으로 변환"""
    if not name:
        return name
    return _load_model_aliases().get(name.strip().lower(), name.strip())

@lru_cache(maxsize=1)
def _load_panel_specs() -> Dict[str, Dict[str, float]]:
    """패널 스펙 파일 로드"""
    specs_file = find_data_file("panel_specs.xlsx") or find_data_file("panel_specs.csv")
    if not specs_file:
        return {}

    try:
        # 파일 읽기
        if str(specs_file).lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(specs_file)
        else:
            df = pd.read_csv(specs_file)

        # 헤더 자동 매핑
        rename = {}
        for col in df.columns:
            lc = col.lower()
            if "model" in lc or "모델" in lc:
                rename[col] = "model_name"
            elif "pmp" in lc or "pmpp" in lc or "정격" in lc:
                rename[col] = "PMPP_rated_W"
            elif "coeff" in lc or "온도" in lc:
                rename[col] = "Temp_Coeff_per_K"
            elif "degrad" in lc or "열화" in lc:
                rename[col] = "Annual_Degradation_Rate"

        df = df.rename(columns=rename)

        required_cols = {"model_name", "PMPP_rated_W", "Temp_Coeff_per_K", "Annual_Degradation_Rate"}
        if not required_cols.issubset(set(df.columns)):
            logger.warning("스펙 파일에 필수 컬럼이 없습니다")
            return {}

        specs: Dict[str, Dict[str, float]] = {}
        for _, row in df.iterrows():
            name = str(row.get("model_name", "")).strip()
            if not name:
                continue
            try:
                specs[name] = {
                    "PMPP_rated_W": float(row.get("PMPP_rated_W", 0) or 0),
                    "Temp_Coeff_per_K": float(row.get("Temp_Coeff_per_K", 0) or 0),
                    "Annual_Degradation_Rate": float(row.get("Annual_Degradation_Rate", 0) or 0),
                }
            except Exception:
                continue

        return specs

    except Exception as e:
        logger.warning(f"패널 스펙 파일 로드 실패: {e}")
        return {}

def get_model_specs(model_name: str) -> Optional[Dict[str, float]]:
    """정규화된 모델명의 스펙 dict 반환"""
    canonical_name = canonicalize_model_name(model_name)
    return _load_panel_specs().get(canonical_name)


# === 비용 계산 유틸리티 ===

# 기본 가격표
_DEFAULT_PRICES: Dict[str, Dict[str, int]] = {
    "Q.PEAK DUO ML-G11.5 / BFG 510W": {"base": 290_000, "disposal": 20_000, "labor": 30_000},
    "Q.PEAK DUO MS-G10.d/BGT 230W": {"base": 220_000, "disposal": 20_000, "labor": 30_000},
    "Q.PEAK DUO MS-G10.d/BGT 235W": {"base": 225_000, "disposal": 20_000, "labor": 30_000},
    "Q.PEAK DUO MS-G10.d/BGT 240W": {"base": 230_000, "disposal": 20_000, "labor": 30_000},
    "DEFAULT": {"base": 250_000, "disposal": 20_000, "labor": 30_000},
}

@lru_cache(maxsize=1)
def _load_price_table() -> Dict[str, Dict[str, int]]:
    """패널 가격 정보 로드"""
    price_file = find_data_file("panel_prices.csv")
    if not price_file:
        return _DEFAULT_PRICES

    try:
        table: Dict[str, Dict[str, int]] = {}
        with open(price_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    table[row["model_name"]] = {
                        "base": int(row["base_price_krw"]),
                        "disposal": int(row["disposal_cost_krw"]),
                        "labor": int(row["labor_cost_krw"]),
                    }
                except Exception:
                    continue
        if table:
            table.setdefault("DEFAULT", _DEFAULT_PRICES["DEFAULT"])
            return table
    except Exception as e:
        logger.warning(f"가격 파일 로드 실패, 기본값 사용: {e}")

    return _DEFAULT_PRICES

def estimate_panel_cost(model_name: str, status: str) -> int:
    """패널 교체 비용 추정"""
    price_table = _load_price_table()
    costs = price_table.get(model_name, price_table["DEFAULT"])

    total_cost = costs["base"] + costs["disposal"] + costs["labor"]

    # 상태에 따른 비용 적용
    if "degraded" in status.lower():
        return total_cost
    else:
        return 0  # 정상/우수 상태는 교체 불필요

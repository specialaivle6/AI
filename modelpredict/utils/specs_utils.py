# utils/specs_utils.py
from functools import lru_cache
from typing import Dict, Optional
import pandas as pd
from utils.data_paths import find_data_file

__all__ = ["canonicalize_model_name", "get_model_specs"]

@lru_cache(maxsize=1)
def _alias_map() -> Dict[str, str]:
    """
    data/model_aliases.csv (선택)에서 alias→canonical 매핑 로드.
    헤더: alias, canonical
    없으면 빈 dict 반환.
    """
    p = find_data_file("model_aliases.csv")
    m: Dict[str, str] = {}
    if not p:
        return m
    df = pd.read_csv(p)
    if "alias" in df.columns and "canonical" in df.columns:
        for _, r in df.iterrows():
            a = str(r.get("alias", "")).strip()
            c = str(r.get("canonical", "")).strip()
            if a and c:
                m[a.lower()] = c
    return m

def canonicalize_model_name(name: str) -> str:
    """별칭을 정규 모델명으로 변환(없으면 원본 반환)."""
    if not name:
        return name
    return _alias_map().get(name.strip().lower(), name.strip())

@lru_cache(maxsize=1)
def _specs() -> Dict[str, Dict[str, float]]:
    """
    data/panel_specs.csv 또는 data/panel_specs.xlsx에서 스펙 로드.
    허용 헤더(자동 매핑): model_name|모델명, PMPP_rated_W|정격,
                         Temp_Coeff_per_K|온도계수, Annual_Degradation_Rate|열화율
    없거나 매핑 실패 시 빈 dict.
    """
    p = find_data_file("panel_specs.csv") or find_data_file("panel_specs.xlsx")
    if not p:
        return {}

    # 파일 읽기
    if str(p).lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(p)
    else:
        df = pd.read_csv(p)

    # 헤더 자동 매핑
    rename = {}
    for col in df.columns:
        lc = col.lower()
        if "model" in lc or "모델" in lc:              rename[col] = "model_name"
        elif "pmp" in lc or "pmpp" in lc or "정격" in lc: rename[col] = "PMPP_rated_W"
        elif "coeff" in lc or "온도" in lc:            rename[col] = "Temp_Coeff_per_K"
        elif "degrad" in lc or "열화" in lc:           rename[col] = "Annual_Degradation_Rate"
    df = df.rename(columns=rename)

    need = {"model_name","PMPP_rated_W","Temp_Coeff_per_K","Annual_Degradation_Rate"}
    if not need.issubset(set(df.columns)):
        return {}

    out: Dict[str, Dict[str, float]] = {}
    for _, r in df.iterrows():
        name = str(r.get("model_name", "")).strip()
        if not name:
            continue
        try:
            out[name] = {
                "PMPP_rated_W": float(r.get("PMPP_rated_W", 0) or 0),
                "Temp_Coeff_per_K": float(r.get("Temp_Coeff_per_K", 0) or 0),
                "Annual_Degradation_Rate": float(r.get("Annual_Degradation_Rate", 0) or 0),
            }
        except Exception:
            continue
    return out

def get_model_specs(name: str) -> Optional[Dict[str, float]]:
    """정규화된 모델명의 스펙 dict 반환(없으면 None)."""
    return _specs().get(canonicalize_model_name(name))

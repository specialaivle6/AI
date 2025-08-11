# utils/cost_utils.py
import os, csv, datetime
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, List, Dict

@dataclass
class CostEstimate:
    immediate_cost: int                # '지금' 교체 총비용 (degraded)
    future_cost_year: Optional[int]    # 정상/우수 예상 교체연도
    future_cost_total: Optional[int]

# 기본 가격표(파일 없을 때 사용)
_FALLBACK_TABLE: Dict[str, Dict[str, int]] = {
    "Q.PEAK DUO ML-G11.5 / BFG 510W": {"base": 290_000, "disposal": 20_000, "labor": 30_000},
    "Q.PEAK DUO MS-G10.d/BGT 230W":    {"base": 220_000, "disposal": 20_000, "labor": 30_000},
    "Q.PEAK DUO MS-G10.d/BGT 235W":    {"base": 225_000, "disposal": 20_000, "labor": 30_000},
    "Q.PEAK DUO MS-G10.d/BGT 240W":    {"base": 230_000, "disposal": 20_000, "labor": 30_000},
    "Q.PEAK DUO XL-G11S.3 / BFG 590W": {"base": 300_000, "disposal": 20_000, "labor": 30_000},
    "Q.PEAK DUO XL-G11S.3 / BFG 595W": {"base": 305_000, "disposal": 20_000, "labor": 30_000},
    "Q.PEAK DUO XL-G11S.3 / BFG 600W": {"base": 310_000, "disposal": 20_000, "labor": 30_000},
    "Q.PEAK DUO XL-G11S.7 / BFG 585W": {"base": 295_000, "disposal": 20_000, "labor": 30_000},
    "Q.PEAK DUO XL-G11S.7 / BFG 590W": {"base": 300_000, "disposal": 20_000, "labor": 30_000},
    "Q.PEAK DUO XL-G11S.7 / BFG 595W": {"base": 305_000, "disposal": 20_000, "labor": 30_000},
    "Q.PEAK DUO XL-G11S.7 / BFG 600W": {"base": 310_000, "disposal": 20_000, "labor": 30_000},
    "Q.PEAK DUO XL-G11S.7 / BFG 605W": {"base": 315_000, "disposal": 20_000, "labor": 30_000},
    "Q.TRON XL-G2.13/BFG 620W":        {"base": 320_000, "disposal": 20_000, "labor": 30_000},
    "Q.TRON XL-G2.13/BFG 625W":        {"base": 325_000, "disposal": 20_000, "labor": 30_000},
    "Q.TRON XL-G2.13/BFG 630W":        {"base": 330_000, "disposal": 20_000, "labor": 30_000},
    "Q.TRON XL-G2.13/BFG 635W":        {"base": 335_000, "disposal": 20_000, "labor": 30_000},
    "Q.TRON XL-G2.7 / BFG 610W":       {"base": 315_000, "disposal": 20_000, "labor": 30_000},
    "Q.TRON XL-G2.7 / BFG 620W":       {"base": 320_000, "disposal": 20_000, "labor": 30_000},
    "Q.TRON XL-G2.7 / BFG 625W":       {"base": 325_000, "disposal": 20_000, "labor": 30_000},
    "Q.TRON XL-G2.7 / BFG 630W":       {"base": 330_000, "disposal": 20_000, "labor": 30_000},
    "Q.TRON XL-G2.7 / BFG 635W":       {"base": 335_000, "disposal": 20_000, "labor": 30_000},
    "Q.TRON XL-G2R.9 / BFG 635W":      {"base": 335_000, "disposal": 20_000, "labor": 30_000},
    "Q.TRON XL-G2R.9 / BFG 640W":      {"base": 340_000, "disposal": 20_000, "labor": 30_000},
    "Q.TRON XL-G2R.9 / BFG 645W":      {"base": 345_000, "disposal": 20_000, "labor": 30_000},
    "DEFAULT":                          {"base": 250_000, "disposal": 20_000, "labor": 30_000},
}

def _candidate_csv_paths() -> List[str]:
    env_path = os.environ.get("PANEL_PRICE_CSV")
    if env_path:
        return [env_path]
    here = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(here, ".."))
    return [
        os.path.join(project_root, "data", "panel_prices.csv"),
        os.path.join(here, "panel_prices.csv"),
        os.path.join(project_root, "panel_prices.csv"),
    ]

@lru_cache(maxsize=1)
def _load_price_table() -> Dict[str, Dict[str, int]]:
    for path in _candidate_csv_paths():
        if os.path.exists(path):
            table: Dict[str, Dict[str, int]] = {}
            with open(path, newline="", encoding="utf-8") as f:
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
                table.setdefault("DEFAULT", _FALLBACK_TABLE["DEFAULT"])
                return table
    return _FALLBACK_TABLE

def _lookup_cost(model_name: str) -> Dict[str, int]:
    t = _load_price_table()
    return t.get(model_name, t["DEFAULT"])

def _normalize_status(status: str) -> str:
    s = (status or "").lower()
    if "degraded" in s:
        return "degraded"
    if "excellent" in s:
        return "excellent"
    return "normal"

def estimate_cost(model_name: str, status: str, lifespan_years: Optional[float]) -> CostEstimate:
    kind = _normalize_status(status)
    c = _lookup_cost(model_name)
    total = c["base"] + c["disposal"] + c["labor"]

    if kind == "degraded":
        return CostEstimate(immediate_cost=total, future_cost_year=None, future_cost_total=None)

    if lifespan_years is None:
        return CostEstimate(immediate_cost=0, future_cost_year=None, future_cost_total=None)

    year = datetime.date.today().year + int(lifespan_years)
    return CostEstimate(immediate_cost=0, future_cost_year=year, future_cost_total=total)

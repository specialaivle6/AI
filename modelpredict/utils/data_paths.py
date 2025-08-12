# utils/data_paths.py
from pathlib import Path
from typing import Optional
import os

__all__ = ["project_root", "data_dir", "find_data_file"]

def project_root() -> Path:
    """프로젝트 루트(= utils/의 상위) 경로 반환"""
    return Path(__file__).resolve().parents[1]

def data_dir() -> Path:
    """
    데이터 기본 폴더:
    1) 환경변수 DATA_DIR 지정 시 그 경로
    2) 없으면 <프로젝트루트>/data
    """
    p = os.environ.get("DATA_DIR")
    return Path(p) if p else project_root() / "data"

def find_data_file(filename: str) -> Optional[Path]:
    """
    filename을 다음 우선순위로 탐색해 절대경로 반환:
    1) 같은 이름의 환경변수(예: panel_prices.csv → PANEL_PRICES_CSV)
    2) DATA_DIR/filename
    3) 프로젝트 루트/filename
    4) 프로젝트 루트/utils/filename
    없으면 None
    """
    env_key = filename.upper().replace(".", "_")  # "panel_prices.csv" -> "PANEL_PRICES_CSV"
    env_override = os.environ.get(env_key)

    candidates = []
    if env_override:
        candidates.append(Path(env_override))

    dd = data_dir()
    candidates += [
        dd / filename,
        project_root() / filename,
        project_root() / "utils" / filename,
    ]

    for c in candidates:
        if c.exists():
            return c.resolve()
    return None

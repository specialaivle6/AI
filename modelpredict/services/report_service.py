import pandas as pd
from datetime import datetime
from model.model_loader import model
from utils.region_utils import find_nearest_region
from utils.report_utils import generate_report, estimate_lifespan
from model.panel_request import PanelRequest
from utils.cost_utils import estimate_cost
from utils.specs_utils import canonicalize_model_name, get_model_specs

# 예측 모델의 피처 순서(학습 시 원-핫 열 순서와 동일해야 함)
model_features = [
    "PMPP_rated_W", "Temp_Coeff_per_K", "Annual_Degradation_Rate", "Install_Angle",
    "Avg_Temp", "Avg_Humidity", "Avg_Windspeed", "Avg_Sunshine", "Elapsed_Months",
    "Panel_Model_Q.PEAK DUO ML-G11.5 / BFG 510W", "Panel_Model_Q.PEAK DUO MS-G10.d/BGT 230W",
    "Panel_Model_Q.PEAK DUO MS-G10.d/BGT 235W", "Panel_Model_Q.PEAK DUO MS-G10.d/BGT 240W",
    "Panel_Model_Q.PEAK DUO XL-G11S.3 / BFG 590W", "Panel_Model_Q.PEAK DUO XL-G11S.3 / BFG 595W",
    "Panel_Model_Q.PEAK DUO XL-G11S.3 / BFG 600W", "Panel_Model_Q.PEAK DUO XL-G11S.7 / BFG 585W",
    "Panel_Model_Q.PEAK DUO XL-G11S.7 / BFG 590W", "Panel_Model_Q.PEAK DUO XL-G11S.7 / BFG 595W",
    "Panel_Model_Q.PEAK DUO XL-G11S.7 / BFG 600W", "Panel_Model_Q.PEAK DUO XL-G11S.7 / BFG 605W",
    "Panel_Model_Q.TRON XL-G2.13/BFG 620W", "Panel_Model_Q.TRON XL-G2.13/BFG 625W",
    "Panel_Model_Q.TRON XL-G2.13/BFG 630W", "Panel_Model_Q.TRON XL-G2.13/BFG 635W",
    "Panel_Model_Q.TRON XL-G2.7 / BFG 610W", "Panel_Model_Q.TRON XL-G2.7 / BFG 620W",
    "Panel_Model_Q.TRON XL-G2.7 / BFG 625W", "Panel_Model_Q.TRON XL-G2.7 / BFG 630W",
    "Panel_Model_Q.TRON XL-G2.7 / BFG 635W", "Panel_Model_Q.TRON XL-G2R.9 / BFG 635W",
    "Panel_Model_Q.TRON XL-G2R.9 / BFG 640W", "Panel_Model_Q.TRON XL-G2R.9 / BFG 645W",
    "Install_Direction_Southeast", "Install_Direction_Southwest",
    "Region_Daegu", "Region_Daejeon", "Region_Gangwon", "Region_Gwangju",
    "Region_Gyeongbuk", "Region_Gyeonggi", "Region_Gyeongnam", "Region_Incheon",
    "Region_Jeonbuk", "Region_Seoul", "Region_Ulsan"
]

def _avg(v):
    return (sum(v) / len(v)) if v else 0.0

def preprocess_features(data: PanelRequest) -> dict:
    """입력 + CSV 스펙/지역정보로 학습 피처 한 줄 생성"""
    # 모델명 정규화(별칭 매핑)
    model_name = canonicalize_model_name(data.model_name)

    # 환경 평균치
    avg_temp = _avg(data.temp)
    avg_humidity = _avg(data.humidity)
    avg_windspeed = _avg(data.windspeed)
    avg_sunshine = _avg(data.sunshine)

    install_date = pd.to_datetime(data.installed_at)
    elapsed_months = (pd.Timestamp.now() - install_date).days // 30
    nearest_region = find_nearest_region(data.lat, data.lon)

    # 스펙 자동 보정 (0/None이면 CSV/엑셀에서 보강)
    pmp = data.pmp_rated_w or 0
    tcoef = data.temp_coeff or 0
    degr = data.annual_degradation_rate or 0
    if pmp == 0 or tcoef == 0 or degr == 0:
        spec = get_model_specs(model_name)
        if spec:
            pmp   = pmp   or spec.get("PMPP_rated_W", 0)
            tcoef = tcoef or spec.get("Temp_Coeff_per_K", 0)
            degr  = degr  or spec.get("Annual_Degradation_Rate", 0)

    features = {
        "PMPP_rated_W": pmp,
        "Temp_Coeff_per_K": tcoef,
        "Annual_Degradation_Rate": degr,
        "Install_Angle": data.installed_angle,
        "Avg_Temp": avg_temp,
        "Avg_Humidity": avg_humidity,
        "Avg_Windspeed": avg_windspeed,
        "Avg_Sunshine": avg_sunshine,
        "Elapsed_Months": elapsed_months,
    }

    # 원-핫 인코딩(모델/방향/지역)
    for col in model_features:
        if "Panel_Model_" in col:
            features[col] = 1 if col == f"Panel_Model_{model_name}" else 0
        elif "Region_" in col:
            features[col] = 1 if col == nearest_region else 0
        elif "Install_Direction_" in col:
            features[col] = 1 if col == f"Install_Direction_{data.installed_direction}" else 0

    return features

def process_report(data: PanelRequest) -> dict:
    """전처리 → 예측 → 상태판정 → 비용계산 → PDF 생성 → 응답"""
    features = preprocess_features(data)
    df = pd.DataFrame([features]).reindex(columns=model_features).fillna(0)

    predicted = float(model.predict(df)[0])
    actual = float(data.actual_generation)
    performance_ratio = (actual / predicted) if predicted > 0 else 0.0

    install_date = pd.to_datetime(data.installed_at)
    current_date = pd.Timestamp.now()

    # 상태 판정 + 수명
    lifespan = None
    if actual > predicted:
        status = "Excellent (Performance above expected)"
        lifespan = estimate_lifespan(predicted, actual, install_date, current_date)
    elif performance_ratio >= 0.8:
        status = "Healthy (Performance within normal range)"
        lifespan = estimate_lifespan(predicted, actual, install_date, current_date)
    else:
        status = "Degraded (Requires image inspection)"

    # 비용 계산 (정상/우수는 0원으로 표기, 성능저하만 금액)
    cost = estimate_cost(data.model_name, status, lifespan)

    report_path = generate_report(
        predicted=predicted,
        actual=actual,
        status=status,
        user_id=data.user_id,
        lifespan=lifespan,
        cost=cost
    )

    return {
        "user_id": data.user_id,
        "address": report_path,
        "created_at": datetime.now().isoformat()
    }

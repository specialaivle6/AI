import pandas as pd
from datetime import datetime
from model.model_loader import model
from utils.geo import find_nearest_region
from utils.report_utils import generate_report, estimate_lifespan
from model.panel_request import PanelRequest
from utils.cost_utils import estimate_cost

# 예측 모델의 피처 순서 정의
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

def preprocess_features(data: PanelRequest) -> dict:
    avg_temp = sum(data.temp) / len(data.temp)
    avg_humidity = sum(data.humidity) / len(data.humidity)
    avg_windspeed = sum(data.windspeed) / len(data.windspeed)
    avg_sunshine = sum(data.sunshine) / len(data.sunshine)
    install_date = pd.to_datetime(data.installed_at)
    elapsed_months = (pd.Timestamp.now() - install_date).days // 30
    nearest_region = find_nearest_region(data.lat, data.lon)

    features = {
        "PMPP_rated_W": data.pmp_rated_w,
        "Temp_Coeff_per_K": data.temp_coeff,
        "Annual_Degradation_Rate": data.annual_degradation_rate,
        "Install_Angle": data.installed_angle,
        "Avg_Temp": avg_temp,
        "Avg_Humidity": avg_humidity,
        "Avg_Windspeed": avg_windspeed,
        "Avg_Sunshine": avg_sunshine,
        "Elapsed_Months": elapsed_months,
    }

    for col in model_features:
        if "Panel_Model_" in col:
            features[col] = 1 if col == f"Panel_Model_{data.model_name}" else 0
        elif "Region_" in col:
            features[col] = 1 if col == nearest_region else 0
        elif "Install_Direction_" in col:
            features[col] = 1 if col == f"Install_Direction_{data.installed_direction}" else 0

    return features

def process_report(data: PanelRequest) -> dict:
    features = preprocess_features(data)
    df = pd.DataFrame([features]).reindex(columns=model_features).fillna(0)

    predicted = model.predict(df)[0]
    actual = data.actual_generation
    performance_ratio = actual / predicted if predicted > 0 else 0

    install_date = pd.to_datetime(data.installed_at)
    current_date = pd.Timestamp.now()

    lifespan = None
    if actual > predicted:
        status = "Excellent (Performance above expected)"
        lifespan = estimate_lifespan(predicted, actual, install_date, current_date)
    elif performance_ratio >= 0.8:
        status = "Healthy (Performance within normal range)"
        lifespan = estimate_lifespan(predicted, actual, install_date, current_date)
    else:
        status = "Degraded (Requires image inspection)"

    # ★ 비용 계산 추가 (상태 문자열은 그대로 사용)
    cost = estimate_cost(data.model_name, status, lifespan)    

    report_path = generate_report(
        predicted=predicted,
        actual=actual,
        status=status,
        user_id=data.user_id,
        lifespan=lifespan,
        cost=cost, #추가
    )

    return {
        "user_id": data.user_id,
        "address": report_path,
        "created_at": datetime.now().isoformat()
    }

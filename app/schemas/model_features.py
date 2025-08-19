# model_features.py
# ML 모델의 피처 순서 정의 파일
# 이 파일은 학습 시 사용된 피처 순서와 정확히 일치해야 합니다.

"""
태양광 패널 성능 예측 모델의 피처 정의
- 학습 시 원-핫 인코딩된 피처 순서와 동일해야 함
- 모델 재학습 시 이 파일을 업데이트해야 함
"""

# 실제 학습된 모델의 정확한 피처 순서 (46개)
# MODEL_FEATURES = [
#     "PMPP_rated_W",
#     "Temp_Coeff_per_K",
#     "Annual_Degradation_Rate",
#     "Install_Angle",
#     "Avg_Temp",
#     "Avg_Humidity",
#     "Avg_Windspeed",
#     "Avg_Sunshine",
#     "Elapsed_Months",
#     "Panel_Model_Q.PEAK DUO ML-G11.5 / BFG 510W",
#     "Panel_Model_Q.PEAK DUO MS-G10.d/BGT 230W",
#     "Panel_Model_Q.PEAK DUO MS-G10.d/BGT 235W",
#     "Panel_Model_Q.PEAK DUO MS-G10.d/BGT 240W",
#     "Panel_Model_Q.PEAK DUO XL-G11S.3 / BFG 590W",
#     "Panel_Model_Q.PEAK DUO XL-G11S.3 / BFG 595W",
#     "Panel_Model_Q.PEAK DUO XL-G11S.3 / BFG 600W",
#     "Panel_Model_Q.PEAK DUO XL-G11S.7 / BFG 585W",
#     "Panel_Model_Q.PEAK DUO XL-G11S.7 / BFG 590W",
#     "Panel_Model_Q.PEAK DUO XL-G11S.7 / BFG 595W",
#     "Panel_Model_Q.PEAK DUO XL-G11S.7 / BFG 600W",
#     "Panel_Model_Q.PEAK DUO XL-G11S.7 / BFG 605W",
#     "Panel_Model_Q.TRON XL-G2.13/BFG 620W",
#     "Panel_Model_Q.TRON XL-G2.13/BFG 625W",
#     "Panel_Model_Q.TRON XL-G2.13/BFG 630W",
#     "Panel_Model_Q.TRON XL-G2.13/BFG 635W",
#     "Panel_Model_Q.TRON XL-G2.7 / BFG 610W",
#     "Panel_Model_Q.TRON XL-G2.7 / BFG 620W",
#     "Panel_Model_Q.TRON XL-G2.7 / BFG 625W",
#     "Panel_Model_Q.TRON XL-G2.7 / BFG 630W",
#     "Panel_Model_Q.TRON XL-G2.7 / BFG 635W",
#     "Panel_Model_Q.TRON XL-G2R.9 / BFG 635W",
#     "Panel_Model_Q.TRON XL-G2R.9 / BFG 640W",
#     "Panel_Model_Q.TRON XL-G2R.9 / BFG 645W",
#     "Install_Direction_Southeast",
#     "Install_Direction_Southwest",
#     "Region_Daegu",
#     "Region_Daejeon",
#     "Region_Gangwon",
#     "Region_Gwangju",
#     "Region_Gyeongbuk",
#     "Region_Gyeonggi",
#     "Region_Gyeongnam",
#     "Region_Incheon",
#     "Region_Jeonbuk",
#     "Region_Seoul",
#     "Region_Ulsan"
# ]

MODEL_FEATURES = [
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

# 피처 그룹별 분류
NUMERIC_FEATURES = MODEL_FEATURES[:9]
PANEL_MODEL_FEATURES = [f for f in MODEL_FEATURES if f.startswith("Panel_Model_")]
DIRECTION_FEATURES = [f for f in MODEL_FEATURES if f.startswith("Install_Direction_")]
REGION_FEATURES = [f for f in MODEL_FEATURES if f.startswith("Region_")]

# 검증 함수
def validate_features():
    """피처 개수 및 구성 검증"""
    total = len(MODEL_FEATURES)
    numeric = len(NUMERIC_FEATURES)
    panel = len(PANEL_MODEL_FEATURES)
    direction = len(DIRECTION_FEATURES)
    region = len(REGION_FEATURES)

    print(f"총 피처 개수: {total}")
    print(f"- 수치형: {numeric}")
    print(f"- 패널 모델: {panel}")
    print(f"- 설치 방향: {direction}")
    print(f"- 지역: {region}")
    print(f"검증 결과: {numeric + panel + direction + region == total}")

    return numeric + panel + direction + region == total

if __name__ == "__main__":
    validate_features()

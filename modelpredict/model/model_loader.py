import joblib
import os

# 모델 경로 설정
MODEL_PATH = os.path.join("model", "voting_ensemble_model.pkl")

# 모델 로드
model = joblib.load(MODEL_PATH)

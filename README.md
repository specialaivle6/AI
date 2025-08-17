# 🌞 Solar Panel AI Service v3.0

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg)](https://fastapi.tiangolo.com)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-orange.svg)](https://ultralytics.com)

태양광 패널 **손상 분석** 및 **성능 예측**을 위한 AI 서비스입니다.

## 🚀 주요 기능

- **🔍 손상 분석**: YOLOv8로 물리적 손상, 오염, 조류 배설물 등 감지
- **📊 성능 예측**: ML 앙상블로 발전량 예측 및 PDF 리포트 생성  
- **🔗 S3 연동**: AWS S3 이미지 자동 다운로드 및 분석
- **⚡ 고성능**: 1-3초 내 분석 완료, 정확도 85%+

## 📡 핵심 API

### 손상 분석
```http
POST /api/damage-analysis/analyze
```
```json
{
  "panel_id": 123,
  "user_id": "uuid",
  "panel_imageurl": "s3://bucket/image.jpg"
}
```

### 성능 예측  
```http
POST /api/performance/analyze
POST /api/performance/report
```
```json
{
    "user_id": "uuid",
    "id": 1,
    "model_name": "Q.PEAK DUO XL-G11S.7 / BFG 600W",
    "serial_number": 123456789,
    "pmp_rated_w": 600,
    "temp_coeff": -0.35,
    "annual_degradation_rate": 0.5,
    "lat": 37.5665,
    "lon": 126.9780,
    "installed_at": "2022-01-01",
    "installed_angle": 30.0,
    "installed_direction": "Southeast",
    "temp": [25.0, 26.0, 27.0],
    "humidity": [50.0, 55.0, 60.0],
    "windspeed": [3.0, 3.5, 4.0],
    "sunshine": [5.5, 6.0, 6.5],
    "actual_generation": 310.0
}
```

## 🚀 빠른 시작

### 1️⃣ 설치
```bash
git clone <repository-url>
cd AI
pip install -r requirements.txt
```

### 2️⃣ 모델 준비
```bash
# 모델 파일 배치 (다운로드 링크 별도 제공)
models/
├── yolov8_seg_0812_v0.1.pt
└── voting_ensemble_model.pkl
```

### 3️⃣ 실행
```bash
# 개발 서버
python app/main.py

# 또는 Docker
docker-compose up
```

### 4️⃣ 테스트
```bash
# 헬스체크
curl http://localhost:8000/api/damage-analysis/health

# API 테스트
python test_api.py
```

## ⚙️ 주요 설정

```bash
# .env 파일
HOST=0.0.0.0
PORT=8000
DEVICE=cpu
DAMAGE_MODEL_PATH=models/yolov8_seg_0812_v0.1.pt
PERFORMANCE_MODEL_PATH=models/voting_ensemble_model.pkl
```

## 🔗 백엔드 연동

### Spring Boot 예시
```java
@Autowired
private RestTemplate restTemplate;

public DamageAnalysisResponse analyzeDamage(Long panelId, String userId, String imageUrl) {
    Map<String, Object> request = Map.of(
        "panel_id", panelId,
        "user_id", userId,
        "panel_imageurl", imageUrl
    );
    
    return restTemplate.postForObject(
        aiServiceUrl + "/api/damage-analysis/analyze",
        request,
        DamageAnalysisResponse.class
    );
}
```

## 🧪 테스트

```bash
# 단위 테스트
pytest tests/ -v

# 커버리지 (현재 87%)
pytest tests/ --cov=app --cov-report=html
```

## 🐳 Docker 배포

```bash
# 개발환경
docker-compose up

# 프로덕션
docker-compose -f docker-compose.prod.yml up -d
```

## 📈 성능

- **처리 속도**: 평균 1.2초/이미지
- **메모리**: 평균 2GB  
- **정확도**: mAP@0.5 85.3%
- **처리량**: 분당 50개 이미지

## 🛠️ 문제 해결

### 모델 로딩 실패
```bash
# 파일 확인
ls -la models/
chmod 644 models/*.pt
```

### S3 연결 문제
```bash
# 타임아웃 증가
export S3_DOWNLOAD_TIMEOUT=60
```

### 메모리 부족
```bash
# Docker 메모리 확인
docker stats
```

## 📞 지원

- **문서**: [API 명세서](API_SPECIFICATION.md) | [상세 가이드](guide.md)
- **이슈**: GitHub Issues
- **개발팀**: Slack #solar-ai-dev

## 📊 버전

**v3.0.0** (현재)
- ✨ 성능 예측 서비스 추가
- ✨ PDF 리포트 생성  
- 🔧 오류 처리 개선
- 🐳 Docker 지원

---

**🔗 자세한 내용**: [완전한 README](README_FULL.md) | [API 명세서](API_SPECIFICATION.md)

---

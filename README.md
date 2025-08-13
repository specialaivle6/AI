# Solar Panel AI Service v3.0 - 백엔드 연동용 손상 분석 서비스

## 📋 개요

태양광 패널 이미지 손상 분석을 위한 AI 전용 서비스입니다. 백엔드 서버에서 S3 URL을 전송하면 AI가 이미지를 다운로드하여 정밀 손상 분석을 수행하고 결과를 반환합니다.

### 핵심 기능
- **S3 연동**: S3 URL로 이미지 자동 다운로드 및 분석
- **정밀 손상 분석**: YOLOv8 Segmentation 모델로 픽셀 단위 손상 비율 계산
- **실시간 처리**: 단일 이미지 1-3초 내 분석 완료
- **비즈니스 로직**: 심각도 평가, 조치사항 권장, 비용 예상
- **백엔드 연동**: REST API로 백엔드 서버와 완전 분리된 아키텍처

---

## 🏗️ 시스템 아키텍처

```
백엔드 서버 (Spring Boot/Node.js 등)
    ↓ POST /api/damage-analysis/analyze
AI Service (Python FastAPI)
    ↓ S3 URL로 이미지 다운로드
AWS S3 또는 호환 스토리지
    ↓ 이미지 분석 수행
YOLOv8 AI 모델
    ↓ 분석 결과 반환
백엔드 서버 (DB 저장, 사용자 응답)
```

### 데이터 흐름
1. 백엔드 → AI 서버: `{panel_id, user_id, panel_imageurl}`
2. AI 서버 → S3: 이미지 다운로드
3. AI 서버 → YOLOv8: 손상 분석 수행
4. AI 서버 → 백엔드: 상세 분석 결과 반환

---

## 🤖 AI 모델 사양

- **모델**: YOLOv8 Segmentation (Custom Trained)
- **입력**: 태양광 패널 이미지 (JPG, PNG 등)
- **출력**: 손상 영역 세그멘테이션 + 분류
- **지원 클래스**: 
  - Physical-Damage (물리적 손상)
  - Dusty (먼지/오염)
  - Bird-drop (조류 배설물)
  - Snow (눈 덮임)
- **정확도**: mAP@0.5 기준 85%+ (사내 테스트 데이터)

---

## 📡 API 엔드포인트

### 기본 엔드포인트
- `GET /` - 기본 헬스체크
- `GET /api/damage-analysis/health` - AI 서비스 상태 확인
- `GET /api/damage-analysis/status` - 서비스 정보 조회

### 핵심 분석 API
- `POST /api/damage-analysis/analyze` - S3 URL 기반 손상 분석

#### 요청 예시
```json
{
  "panel_id": 123,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "panel_imageurl": "https://s3.amazonaws.com/bucket/panel-image.jpg"
}
```

#### 응답 예시
```json
{
  "panel_id": 123,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "damage_analysis": {
    "overall_damage_percentage": 15.34,
    "critical_damage_percentage": 2.1,
    "contamination_percentage": 13.24,
    "healthy_percentage": 84.66,
    "status": "analyzed"
  },
  "business_assessment": {
    "priority": "MEDIUM",
    "risk_level": "LOW",
    "recommendations": ["패널 청소 필요", "물리적 손상 부위 점검 권장"]
  },
  "confidence_score": 0.892,
  "processing_time_seconds": 1.28
}
```

---

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# 가상환경 생성 및 활성화
python -m venv ai
ai\Scripts\activate  # Windows
source ai/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt
```

### 2. AI 모델 준비
```bash
# models 폴더에 YOLOv8 모델 파일 배치
models/yolov8_seg_0812_v0.1.pt
```

### 3. 서버 실행
```bash
# 개발 서버 실행
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는 직접 실행
python app/main.py
```

### 4. 테스트
```bash
# API 테스트 실행
python test_api.py
```

---

## 🔧 환경 변수

```bash
# 서버 설정
HOST=0.0.0.0
PORT=8000
DEBUG=False

# AI 모델 설정
MODEL_PATH=models/yolov8_seg_0812_v0.1.pt
CONFIDENCE_THRESHOLD=0.25
DEVICE=cpu

# S3 다운로드 설정
S3_DOWNLOAD_TIMEOUT=30
MAX_IMAGE_SIZE=20971520

# 로깅
LOG_LEVEL=INFO
```

---

## 📁 프로젝트 구조

```
AI/
├── app/
│   ├── main.py              # FastAPI 메인 애플리케이션
│   ├── models/
│   │   └── schemas.py       # API 요청/응답 모델
│   ├── services/
│   │   └── damage_analyzer.py  # YOLOv8 분석 서비스
│   ├── utils/
│   │   └── image_utils.py   # S3 다운로드, 이미지 처리
│   └── core/
│       └── config.py        # 설정 관리
├── models/
│   └── yolov8_seg_0812_v0.1.pt  # AI 모델 파일
├── requirements.txt         # Python 의존성
├── test_api.py             # API 테스트 스크립트
└── README.md
```

---

## 🔗 백엔드 연동 가이드

### Spring Boot 연동 예시
```java
@RestController
public class PanelAnalysisController {
    
    @Autowired
    private RestTemplate restTemplate;
    
    @PostMapping("/analyze-panel")
    public ResponseEntity<?> analyzePanel(@RequestBody AnalysisRequest request) {
        // AI 서버 호출
        String aiServerUrl = "http://ai-server:8000/api/damage-analysis/analyze";
        
        DamageAnalysisRequest aiRequest = new DamageAnalysisRequest(
            request.getPanelId(),
            request.getUserId(),
            request.getS3Url()
        );
        
        DamageAnalysisResponse result = restTemplate.postForObject(
            aiServerUrl, aiRequest, DamageAnalysisResponse.class
        );
        
        // 결과를 DB에 저장하고 사용자에게 응답
        return ResponseEntity.ok(result);
    }
}
```

---

## 📊 성능 정보

- **처리 속도**: 평균 1-3초/이미지
- **메모리 사용량**: 약 2-4GB (모델 로딩 시)
- **동시 처리**: 단일 요청 처리 (순차적)
- **지원 형식**: JPG, JPEG, PNG, BMP, TIFF, WEBP
- **최대 이미지 크기**: 20MB

---

## 🛠️ 개발 정보

- **Python**: 3.9+
- **FastAPI**: 0.104+
- **PyTorch**: 2.1+
- **YOLOv8**: Ultralytics 8.0+
- **라이센스**: Private (사내용)

---

## 📞 지원

문제가 발생하거나 질문이 있으시면 개발팀에 문의해주세요.

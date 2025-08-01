# 태양광 패널 AI 분석 서비스 v1.0

## 📋 개요

태양광 패널 이미지를 업로드하면 AI가 자동으로 상태를 분석하고 조치사항을 제공하는 RESTful API 서비스입니다.

### 핵심 기능
- **이미지 분석**: MobileNetV3 기반 딥러닝 모델로 패널 상태 6개 클래스 분류
- **비즈니스 로직**: 심각도 평가, 조치사항 권장, 비용 예상
- **REST API**: Spring Boot 백엔드와 연동 가능한 표준 API
- **실시간 처리**: 단일 이미지 1-3초 내 분석 완료

---

## 🏗️ 시스템 아키텍처

```
Frontend (React) 
    ↓
Spring Boot (Java) - 비즈니스 로직, DB 처리
    ↓ HTTP API 호출
FastAPI (Python) - AI 모델 서빙 [현재 구현완료]
```

---

## 🤖 AI 모델 사양

### 모델 정보
- **아키텍처**: MobileNetV3-Small + Custom Classifier
- **입력 크기**: 224x224 RGB 이미지
- **추론 환경**: CPU 최적화 (GPU 불필요)
- **성능**: 전체 정확도 77.4%

### 분류 클래스 (6개)
| 클래스 | 샘플 수 | 심각도 | 설명 |
|--------|---------|--------|------|
| Clean | 155개 | 0 | 정상 상태 |
| Bird-drop | 166개 | 1 | 조류 배설물 |
| Dusty | 152개 | 1 | 먼지/오염물질 |
| Snow-Covered | 98개 | 1 | 눈 덮임 |
| Electrical-damage | 82개 | 3 | 전기적 손상 (즉시조치) |
| Physical-Damage | 55개 | 3 | 물리적 손상 (즉시조치) |

---

## 🚀 환경 설정 및 실행

### 사전 요구사항
- **운영체제**: WSL/Linux 권장 (Windows 가능)
- **Python**: 3.11
- **메모리**: 최소 2GB RAM
- **디스크**: 1GB 여유공간

### 설치 방법

```bash
# 1. 저장소 클론
git clone [repository-url]
cd solar-panel-ai-service

# 2. Conda 환경 생성
conda create -n solar-panel-ai python=3.11 -y
conda activate solar-panel-ai

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 모델 파일 배치
# models/mobilenet_v3_small.pth 파일을 배치

# 5. 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 실행 확인
```bash
# 헬스체크
curl http://localhost:8000/health

# 웹 문서 접속
http://localhost:8000/docs
```

---

## 📡 API 명세서

### Base URL
```
http://localhost:8000
```

### 1. 헬스체크
```http
GET /health
```

**응답 예시:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0"
}
```

### 2. 이미지 분석 (핵심 API)
```http
POST /analyze-panel
Content-Type: multipart/form-data
```

**요청:**
- `file`: 이미지 파일 (JPG, PNG, BMP, TIFF)
- 최대 크기: 10MB

**응답 예시:**
```json
{
  "predicted_class": "Dusty",
  "confidence": 0.8234,
  "class_probabilities": {
    "Bird-drop": 0.0123,
    "Clean": 0.1205,
    "Dusty": 0.8234,
    "Electrical-damage": 0.0145,
    "Physical-Damage": 0.0089,
    "Snow-Covered": 0.0204
  },
  "severity_level": 1,
  "recommendations": {
    "action": "청소",
    "priority": "medium",
    "description": "먼지나 오염물질로 인한 성능 저하가 예상됩니다. 청소를 권장합니다.",
    "estimated_cost": 50000,
    "urgency": "1주일 내"
  },
  "requires_immediate_action": false,
  "confidence_warning": "높은 신뢰도입니다.",
  "alternative_possibilities": [
    {
      "class": "Clean",
      "probability": 0.1205,
      "severity": 0
    }
  ]
}
```

---

## 💻 Spring Boot 연동 가이드

### Java 클라이언트 예시

```java
@Service
public class AiAnalysisService {
    
    @Value("${ai.server.url:http://localhost:8000}")
    private String aiServerUrl;
    
    private final RestTemplate restTemplate;
    
    public PanelAnalysisResult analyzePanel(MultipartFile imageFile) {
        try {
            // MultiValueMap for multipart request
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", imageFile.getResource());
            
            // Headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);
            
            HttpEntity<MultiValueMap<String, Object>> requestEntity = 
                new HttpEntity<>(body, headers);
            
            // API 호출
            ResponseEntity<PanelAnalysisResult> response = restTemplate.postForEntity(
                aiServerUrl + "/analyze-panel",
                requestEntity,
                PanelAnalysisResult.class
            );
            
            return response.getBody();
            
        } catch (Exception e) {
            log.error("AI 분석 중 오류 발생", e);
            throw new AiAnalysisException("이미지 분석에 실패했습니다.", e);
        }
    }
}
```

### DTO 클래스

```java
@Data
public class PanelAnalysisResult {
    private String predictedClass;
    private Double confidence;
    private Map<String, Double> classProbabilities;
    private Integer severityLevel;
    private RecommendationDto recommendations;
    private Boolean requiresImmediateAction;
    private String confidenceWarning;
    private List<AlternativePossibility> alternativePossibilities;
}

@Data
public class RecommendationDto {
    private String action;
    private String priority;
    private String description;
    private Integer estimatedCost;
    private String urgency;
}
```

---

## 🧪 테스트 방법

### 1. 자동 테스트 스크립트
```bash
python test_api.py
```

### 2. cURL 테스트
```bash
curl -X POST "http://localhost:8000/analyze-panel" \
     -F "file=@test_image.jpg"
```

### 3. 웹 UI 테스트
브라우저에서 `http://localhost:8000/docs` 접속하여 Swagger UI 사용

---

## 📊 성능 및 제한사항

### 성능 지표
- **추론 시간**: 1-3초/이미지 (CPU 기준)
- **메모리 사용량**: ~500MB
- **동시 처리**: 단일 요청 처리 (동시성 추후 개선)

### 알려진 제한사항
1. **Physical-Damage 재현율 28.6%**: 심각한 손상 놓칠 위험
2. **Clean vs Dusty 혼동**: 비슷한 상태 구분 어려움
3. **데이터 부족**: 총 708개 이미지로 학습 (추가 데이터 수집 필요)

### 안전장치
- 신뢰도 60% 미만 시 재검증 권고
- 손상 클래스 20% 이상 확률 시 경고 메시지
- 보수적 접근: False Negative 최소화 우선

---

## 🔧 운영 및 모니터링

### 로그 위치
- **애플리케이션 로그**: `logs/ai_service.log`
- **콘솔 출력**: 실시간 로그 확인

### 주요 모니터링 포인트
1. **모델 로딩 상태**: `/health` 엔드포인트 확인
2. **예측 결과 분포**: 각 클래스별 예측 빈도
3. **신뢰도 분포**: 낮은 신뢰도 예측 빈도
4. **응답 시간**: API 레이턴시 모니터링

---

## 📂 프로젝트 구조

```
solar-panel-ai-service/
├── app/
│   ├── main.py                 # FastAPI 메인 애플리케이션
│   ├── models/
│   │   └── model_loader.py     # AI 모델 로딩 및 추론
│   ├── services/
│   │   ├── image_processor.py  # 이미지 전처리
│   │   └── result_processor.py # 결과 후처리 및 비즈니스 로직
│   └── core/
│       └── config.py          # 설정 관리
├── models/
│   └── mobilenet_v3_small.pth # 학습된 모델 파일
├── requirements.txt           # Python 의존성
├── test_api.py               # 테스트 스크립트
└── README.md
```

---

## 🚀 향후 개선 계획

### v1.1 (단기)
- [ ] Spring Boot 연동 완료 및 통합 테스트
- [ ] 배치 처리 (다중 이미지 동시 분석)
- [ ] 예측 결과 로깅 및 모니터링

### v1.2 (중기)
- [ ] Docker 컨테이너화
- [ ] AWS 배포 환경 구축
- [ ] 모델 성능 개선 (더 많은 학습 데이터)

### v2.0 (장기)
- [ ] 실시간 스트리밍 분석
- [ ] 모델 A/B 테스트 프레임워크
- [ ] 자동 재학습 파이프라인

---

## 🤝 팀 역할

| 역할 | 담당자 | 책임 범위 |
|------|---------|-----------|
| AI 개발 | [본인] | 모델 개발, AI 서버 구축, 성능 최적화 |
| 백엔드 | Spring Boot 팀 | 비즈니스 로직, DB 연동, API 통합 |
| 프론트엔드 | React 팀 | UI/UX, 이미지 업로드 기능 |

---

## 📄 변경 이력

| 버전 | 날짜 | 변경사항 |
|------|------|----------|
| v1.0 | 2024-08-01 | 초기 버전 릴리즈, 핵심 기능 완성 |

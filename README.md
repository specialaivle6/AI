# AI Services v2.0 - 태양광 패널 손상 분석 서비스

## 📋 개요

통합 AI 서비스 저장소의 첫 번째 서비스로, 태양광 패널 이미지를 업로드하면 AI가 자동으로 손상 상태를 정밀 분석하고 비즈니스 평가를 제공하는 RESTful API 서비스입니다.

### 핵심 기능
- **정밀 손상 분석**: YOLOv8 Segmentation 모델로 픽셀 단위 손상 비율 계산
- **실시간 처리**: 단일 이미지 1-2초 내 분석 완료
- **비즈니스 로직**: 심각도 평가, 조치사항 권장, 비용 예상, 유지보수 일정
- **REST API**: Spring Boot 백엔드와 연동 가능한 표준 API
- **일괄 분석**: 최대 10개 파일 동시 처리

---

## 🏗️ 시스템 아키텍처

```
Frontend (React) 
    ↓
Spring Boot (Java) - 비즈니스 로직, DB 처리
    ↓ HTTP API 호출
AI Service (Python) - YOLOv8 기반 손상 분석 서비스
  └── damage-analysis - 손상 분석 서비스 [현재 구현완료]
  └── (향후 추가 AI 서비스들)
```

---

## 🤖 AI 모델 사양

### 모델 정보
- **아키텍처**: YOLOv8 Segmentation (Instance Segmentation)
- **입력 크기**: 동적 크기 지원 (자동 리사이징)
- **추론 환경**: CPU 최적화 (GPU 선택적 사용 가능)
- **처리 방식**: 픽셀 단위 정밀 분석

### 검출 클래스
| 클래스 | 심각도 | 설명 | 조치사항 |
|--------|--------|------|----------|
| Non-Defective | 0 | 정상 상태 | 정기 점검 유지 |
| Defective | 1 | 일반 결함 | 모니터링 강화 |
| Bird-drop | 1 | 조류 배설물 | 청소 필요 |
| Dusty | 1 | 먼지/오염물질 | 청소 권장 |
| Snow-Covered | 1 | 눈 덮임 | 제설 작업 |
| Physical-Damage | 3 | 물리적 손상 | 즉시 수리 |
| Electrical-Damage | 3 | 전기적 손상 | 즉시 점검 |

---

## 🚀 환경 설정 및 실행

### 사전 요구사항
- **운영체제**: Windows/Linux/macOS
- **Python**: 3.11
- **메모리**: 최소 4GB RAM (권장 8GB)
- **디스크**: 2GB 여유공간

### 설치 방법

```bash
# 1. 저장소 클론
git clone [repository-url]
cd AI

# 2. Conda 환경 생성
conda create -n ai python=3.11 -y
conda activate ai

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 모델 파일 배치 (선택사항)
# models/mobilenet_v3_small.pt 파일을 배치 (없으면 기본 YOLOv8 모델 사용)
# 모델 다운 링크

# 5. 서버 실행
python -m app.main
```

### Docker 실행 (권장)
```bash
# 1. Docker 이미지 빌드
docker build -t solar-panel-ai .

# 2. 컨테이너 실행
docker run -p 8000:8000 solar-panel-ai
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
  "version": "2.0.0",
  "model_type": "YOLOv8"
}
```

### 2. 단일 이미지 손상 분석 (핵심 API)
```http
POST /analyze-damage
Content-Type: multipart/form-data
```

**요청:**
- `file`: 이미지 파일 (JPG, PNG, BMP, TIFF, WEBP)
- 최대 크기: 20MB

**응답 예시:**
```json
{
  "image_info": {
    "filename": "panel_image.jpg",
    "size": "1920x1080",
    "processing_time_seconds": 1.28
  },
  "damage_analysis": {
    "overall_damage_percentage": 15.34,
    "critical_damage_percentage": 2.1,
    "contamination_percentage": 13.24,
    "healthy_percentage": 84.66,
    "avg_confidence": 0.892,
    "detected_objects": 3,
    "class_breakdown": {
      "Dusty": 13.24,
      "Physical-Damage": 2.1
    },
    "status": "analyzed"
  },
  "business_assessment": {
    "priority": "MEDIUM",
    "risk_level": "LOW",
    "recommendations": [
      "패널 청소 필요",
      "물리적 손상 부위 점검 권장"
    ],
    "estimated_repair_cost_krw": 15340,
    "estimated_performance_loss_percent": 12.3,
    "maintenance_urgency_days": 30,
    "business_impact": "경미한 성능 영향 - 계획적 유지보수 권장"
  },
  "detection_details": {
    "total_detections": 3,
    "detections": [
      {
        "class_name": "Dusty",
        "confidence": 0.876,
        "bbox": [100, 150, 400, 300],
        "area_pixels": 45000
      }
    ]
  },
  "confidence_score": 0.892,
  "timestamp": "2024-08-12 14:30:25"
}
```

### 3. 일괄 분석
```http
POST /batch-analyze
Content-Type: multipart/form-data
```

**요청:**
- `files`: 최대 10개 이미지 파일

**응답 예시:**
```json
{
  "total_analyzed": 5,
  "results": [
    {
      "image_info": {...},
      "damage_analysis": {...},
      "business_assessment": {...}
    }
  ],
  "summary": {
    "total_analyzed_files": 5,
    "average_damage_percentage": 18.5,
    "critical_panels_count": 2,
    "critical_panels_percentage": 40.0,
    "priority_distribution": {
      "HIGH": 2,
      "MEDIUM": 2,
      "LOW": 1
    },
    "overall_fleet_status": "NEEDS_ATTENTION",
    "recommended_action": "우선순위 기반 단계적 수리 권장"
  }
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
    
    public DamageAnalysisResult analyzePanelDamage(MultipartFile imageFile) {
        try {
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", imageFile.getResource());
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);
            
            HttpEntity<MultiValueMap<String, Object>> requestEntity = 
                new HttpEntity<>(body, headers);
            
            ResponseEntity<DamageAnalysisResult> response = restTemplate.postForEntity(
                aiServerUrl + "/analyze-damage",
                requestEntity,
                DamageAnalysisResult.class
            );
            
            return response.getBody();
            
        } catch (Exception e) {
            log.error("AI 손상 분석 중 오류 발생", e);
            throw new AiAnalysisException("손상 분석에 실패했습니다.", e);
        }
    }
}
```

### DTO 클래스

```java
@Data
public class DamageAnalysisResult {
    private ImageInfo imageInfo;
    private DamageAnalysis damageAnalysis;
    private BusinessAssessment businessAssessment;
    private DetectionDetails detectionDetails;
    private Double confidenceScore;
    private String timestamp;
}

@Data
public class DamageAnalysis {
    private Double overallDamagePercentage;
    private Double criticalDamagePercentage;
    private Double contaminationPercentage;
    private Double healthyPercentage;
    private Double avgConfidence;
    private Integer detectedObjects;
    private Map<String, Double> classBreakdown;
    private String status;
}

@Data
public class BusinessAssessment {
    private String priority;  // LOW, MEDIUM, HIGH, URGENT
    private String riskLevel; // MINIMAL, LOW, MEDIUM, HIGH
    private List<String> recommendations;
    private Integer estimatedRepairCostKrw;
    private Double estimatedPerformanceLossPercent;
    private Integer maintenanceUrgencyDays;
    private String businessImpact;
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
# 단일 분석
curl -X POST "http://localhost:8000/analyze-damage" \
     -F "file=@test_image.jpg"

# 헬스체크
curl http://localhost:8000/health
```

### 3. 웹 UI 테스트
브라우저에서 `http://localhost:8000/docs` 접속하여 Swagger UI 사용

---

## 📊 성능 및 장점

### 성능 지표
- **추론 시간**: 1-2초/이미지 (CPU 기준)
- **메모리 사용량**: ~1GB (모델 로딩 시)
- **정확도**: 픽셀 단위 정밀 분석
- **동시 처리**: 일괄 분석 지원 (최대 10개)

### YOLOv8의 장점
1. **정밀한 손상 비율**: 픽셀 단위 Segmentation으로 정확한 손상률 계산
2. **다양한 객체 동시 검출**: 한 이미지에서 여러 손상 유형 동시 분석
3. **실시간 처리**: 빠른 추론 속도
4. **유연한 입력**: 다양한 해상도 이미지 처리 가능

### 비즈니스 가치
- **정량적 평가**: 정확한 손상 비율로 객관적 판단
- **비용 예측**: 손상 정도에 따른 수리 비용 산정
- **우선순위 관리**: 심각도에 따른 유지보수 우선순위
- **예방적 관리**: 조기 발견으로 큰 손실 방지

---

## 🔧 운영 및 모니터링

### 로그 위치
- **애플리케이션 로그**: `logs/ai_service.log`
- **콘솔 출력**: 실시간 로그 확인

### 주요 모니터링 포인트
1. **모델 로딩 상태**: `/health` 엔드포인트 확인
2. **손상률 분포**: 전체/심각 손상률 통계
3. **신뢰도 분포**: 예측 신뢰도 모니터링
4. **응답 시간**: API 레이턴시 추적
5. **우선순위 분포**: 긴급/높음/보통/낮음 비율

---

## 📂 프로젝트 구조

```
AI/
├── README.md                  # 프로젝트 개요 및 가이드
├── requirements.txt           # Python 의존성
├── Dockerfile                 # Docker 컨테이너 설정
├── API_SPECIFICATION.md       # 상세 API 명세서
├── guide.md                   # 빠른 시작 가이드
├── test_api.py               # API 테스트 스크립트
├── app/
│   ├── main.py                     # FastAPI 메인 애플리케이션
│   ├── services/
│   │   └── damage_analyzer.py      # YOLOv8 기반 손상 분석기
│   └── core/
│       └── config.py              # 설정 관리
├── models/
│   ├── best.pt                    # 커스텀 YOLOv8 모델 (선택사항)
│   └── yolov8n-seg.pt            # 기본 YOLOv8 모델
├── logs/                          # 로그 파일 저장소
├── temp/                          # 임시 파일 저장소
└── uploads/                       # 업로드 파일 저장소
```

---

## 🚀 향후 개선 계획

### v2.1 (단기 - 1개월)
- [ ] GPU 가속 지원 (CUDA)
- [ ] 실시간 스트리밍 분석
- [ ] 모델 성능 향상 (더 정확한 커스텀 모델)
- [ ] API 응답 속도 최적화

### v2.2 (중기 - 3개월)  
- [ ] 드론 영상 분석 서비스 추가
- [ ] 시계열 성능 모니터링 서비스
- [ ] 예측 유지보수 스케줄링 AI
- [ ] 에너지 효율 예측 서비스

### v3.0 (장기 - 6개월)
- [ ] 다중 AI 서비스 통합 관리 시스템
- [ ] 자동 재학습 파이프라인
- [ ] 클라우드 네이티브 배포 (Kubernetes)
- [ ] 실시간 대시보드 및 알림 시스템

---

## 📄 변경 이력

| 버전 | 날짜 | 변경사항 |
|------|------|----------|
| v2.0 | 2024-08-12 | YOLOv8 기반 손상 분석 서비스로 전면 개편, 픽셀 단위 정밀 분석, 비즈니스 평가 강화 |
| v1.0 | 2024-08-01 | 초기 버전 릴리즈, MobileNet 기반 패널 분석 서비스 |

---

## 🔗 참고 자료

- **YOLOv8 공식 문서**: https://docs.ultralytics.com/
- **FastAPI 문서**: https://fastapi.tiangolo.com/
- **API 테스트 도구**: http://localhost:8000/docs (Swagger UI)

---

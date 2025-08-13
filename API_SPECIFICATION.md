# Solar Panel AI Service - API 명세서 v3.0

## 개요
태양광 패널 손상 분석 AI 서비스의 REST API 명세서입니다. 백엔드 서버와 연동하여 S3 URL 기반 이미지 분석을 제공합니다.

- **Base URL**: `http://localhost:8000`
- **API 버전**: 3.0.0
- **Content-Type**: `application/json`
- **AI 모델**: YOLOv8 Segmentation
- **연동 방식**: 백엔드 서버 → AI 서버

---

## 엔드포인트 목록

### 1. 기본 헬스체크
**GET** `/`

서비스가 정상적으로 실행 중인지 확인하는 기본 헬스체크 엔드포인트입니다.

#### Response
```json
{
  "message": "Solar Panel AI Service is running",
  "version": "3.0.0",
  "model": "YOLOv8 Segmentation",
  "mode": "Backend Integration"
}
```

---

### 2. AI 서비스 헬스체크
**GET** `/api/damage-analysis/health`

AI 모델 로딩 상태를 포함한 상세한 서비스 상태를 확인합니다.

#### Response
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "3.0.0",
  "model_type": "YOLOv8"
}
```

---

### 3. 손상 분석 (핵심 API)
**POST** `/api/damage-analysis/analyze`

백엔드에서 전송받은 S3 URL로 태양광 패널 이미지를 다운로드하여 손상 분석을 수행합니다.

#### Request
```json
{
  "panel_id": 123,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "panel_imageurl": "https://s3.amazonaws.com/bucket/panel-image.jpg"
}
```

#### Request Fields
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `panel_id` | integer | Yes | 패널 ID |
| `user_id` | string(UUID) | Yes | 사용자 ID |
| `panel_imageurl` | string | Yes | S3 이미지 URL |

#### Response
```json
{
  "panel_id": 123,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "image_info": {
    "filename": "panel-image.jpg",
    "size": "1920x1080",
    "format": "JPEG",
    "file_size_bytes": 1048576
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
  "timestamp": "2024-12-13T14:30:25",
  "processing_time_seconds": 1.28
}
```

---

### 4. 서비스 상태 정보
**GET** `/api/damage-analysis/status`

AI 서비스의 상세 상태 정보를 제공합니다 (개발/디버깅용).

#### Response
```json
{
  "service": "damage-analysis",
  "model_loaded": true,
  "version": "3.0.0",
  "supported_formats": ["jpg", "jpeg", "png", "bmp", "tiff", "webp"],
  "max_image_size": "20MB"
}
```

---

## 에러 응답

모든 에러는 다음 형식으로 반환됩니다:

```json
{
  "detail": "에러 메시지",
  "timestamp": "2024-12-13T14:30:25"
}
```

### 주요 에러 코드
- **400 Bad Request**: 잘못된 요청 (S3 URL 다운로드 실패 등)
- **500 Internal Server Error**: AI 분석 실패 또는 내부 오류
- **503 Service Unavailable**: AI 모델이 로드되지 않음

---

## 백엔드 연동 가이드

### 데이터 흐름
1. 사용자가 백엔드에 이미지 업로드
2. 백엔드가 이미지를 S3에 저장
3. 백엔드가 AI 서버에 분석 요청 (`POST /api/damage-analysis/analyze`)
4. AI 서버가 S3에서 이미지 다운로드 및 분석 수행
5. AI 서버가 분석 결과를 백엔드에 반환
6. 백엔드가 결과를 DB에 저장하고 사용자에게 응답

### 연동 예시 (Spring Boot)
```java
@Service
public class PanelAnalysisService {
    
    @Value("${ai.server.url}")
    private String aiServerUrl;
    
    public DamageAnalysisResponse analyzePanel(Long panelId, UUID userId, String s3Url) {
        DamageAnalysisRequest request = new DamageAnalysisRequest();
        request.setPanelId(panelId);
        request.setUserId(userId);
        request.setPanelImageurl(s3Url);
        
        RestTemplate restTemplate = new RestTemplate();
        return restTemplate.postForObject(
            aiServerUrl + "/api/damage-analysis/analyze",
            request,
            DamageAnalysisResponse.class
        );
    }
}
```

---

## 성능 지표

- **평균 응답 시간**: 1-3초 (이미지 크기에 따라 차이)
- **최대 이미지 크기**: 20MB
- **지원 형식**: JPG, JPEG, PNG, BMP, TIFF, WEBP
- **동시 처리**: 순차적 처리 (단일 요청)
- **S3 다운로드 타임아웃**: 30초

---

## 변경 이력

### v3.0.0 (2024-12-13)
- 백엔드 연동 방식으로 아키텍처 변경
- S3 URL 기반 이미지 분석 지원
- DB 연동 기능 제거 (백엔드에서 처리)
- API 엔드포인트 구조 변경 (`/api/damage-analysis/` 패턴)

### v2.0.0 (이전 버전)
- 파일 업로드 방식
- DB 직접 연동
- 통합 분석 서비스

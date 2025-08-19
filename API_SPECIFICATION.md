# Solar Panel AI Service - API 명세서 v3.0

## 📋 개요
태양광 패널 **손상 분석** 및 **성능 예측**을 위한 AI 서비스의 REST API 명세서입니다.

- **Base URL**: `http://localhost:8000`
- **API 버전**: v3.0.0
- **Content-Type**: `application/json`
- **AI 모델**: YOLOv8 Segmentation + ML Ensemble
- **연동 방식**: 백엔드 서버 ↔ AI 서버 (마이크로서비스)

---

## 🔐 인증 및 보안

### 헤더 설정
```http
Content-Type: application/json
Accept: application/json
X-API-Version: 3.0
X-Request-ID: req_12345 (선택, 추적용)
```

### 보안 고려사항
- S3 URL은 임시 서명된 URL 사용 권장
- HTTPS 통신 필수 (프로덕션)
- 요청 크기 제한: 최대 1MB (JSON)

---

## 📡 API 엔드포인트

## 1. 🏥 헬스체크 및 상태

### 1.1 기본 서비스 상태
**GET** `/`

#### 응답
```json
{
  "service": "Solar Panel AI Service",
  "version": "3.0.0",
  "status": "running",
  "environment": "production",
  "models": {
    "damage_analysis": "YOLOv8 Segmentation",
    "performance_prediction": "Voting Ensemble"
  }
}
```

### 1.2 손상 분석 헬스체크
**GET** `/api/damage-analysis/health`

#### 응답
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "3.0.0",
  "model_type": "YOLOv8"
}
```

### 1.3 성능 예측 헬스체크
**GET** `/api/performance-analysis/health`

#### 응답
```json
{
  "status": "healthy", 
  "model_loaded": true,
  "service": "performance-analysis",
  "version": "3.0.0"
}
```

---

## 2. 🔍 손상 분석 API

### 2.1 패널 손상 분석
**POST** `/api/damage-analysis/analyze`

S3 URL로 패널 이미지를 분석하여 손상 정도와 비즈니스 권장사항을 제공합니다.

#### 요청
```json
{
  "panel_id": 123,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "panel_imageurl": "https://s3.amazonaws.com/bucket/panel-image.jpg"
}
```

#### 요청 필드
| 필드 | 타입 | 필수 | 설명 | 제약사항 |
|------|------|------|------|----------|
| `panel_id` | integer | ✅ | 패널 고유 ID | 1 이상 |
| `user_id` | string(UUID) | ✅ | 사용자 UUID | UUID v4 형식 |
| `panel_imageurl` | string | ✅ | S3 이미지 URL | https:// 또는 s3:// |

#### 응답
```json
{
  "panel_id": 123,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  
  "image_info": {
    "source_url": "https://s3.amazonaws.com/bucket/panel-image.jpg",
    "filename": "panel-image.jpg",
    "format": "JPEG",
    "mode": "RGB",
    "size": {"width": 1920, "height": 1080},
    "file_size_bytes": 1048576,
    "has_transparency": false
  },
  
  "damage_analysis": {
    "overall_damage_percentage": 15.34,
    "critical_damage_percentage": 2.1,
    "contamination_percentage": 13.24,
    "healthy_percentage": 84.66,
    "avg_confidence": 0.892,
    "detected_objects": 3,
    "class_breakdown": {
      "Clean": 84.66,
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
    "business_impact": "경미한 성능 영향 - 계획적 유지보수 권장",
    
    "status": "오염",
    "damage_degree": 25,
    "decision": "수리",
    "request_status": "요청 중"
  },
  
  "detection_details": [
    {
      "class_name": "Dusty",
      "confidence": 0.876,
      "bbox": [100, 150, 400, 300],
      "area_pixels": 45000
    }
  ],
  
  "confidence_score": 0.892,
  "timestamp": "2024-12-13T14:30:25.123Z",
  "processing_time_seconds": 1.28
}
```

#### 응답 필드 설명

**damage_analysis**
- `overall_damage_percentage`: 전체 손상 비율 (0-100)
- `critical_damage_percentage`: 심각한 손상 비율 (0-100)
- `class_breakdown`: 각 손상 유형별 비율

**business_assessment** (DB 매핑용)
- `status`: "정상", "오염", "손상" 중 하나
- `damage_degree`: 손상 정도 (0-100)
- `decision`: "정상", "단순 오염", "수리", "교체" 중 하나
- `request_status`: "요청 중", "요청확인", "처리중", "처리완료" 중 하나

---

## 3. 📊 성능 예측 API

### 3.1 성능 분석 (분석만)
**POST** `/api/performance-analysis/analyze`

패널 데이터를 기반으로 성능을 예측하고 분석 결과만 반환합니다.

#### 요청
```json
{
  "user_id": "user123",
  "id": 1,
  "model_name": "Q.PEAK DUO XL-G11S.3 / BFG 590W",
  "serial_number": 123456,
  "pmp_rated_w": 590.0,
  "temp_coeff": -0.0039,
  "annual_degradation_rate": 0.0055,
  "lat": 37.5665,
  "lon": 126.9780,
  "installed_at": "2020-03-15",
  "installed_angle": 30.0,
  "installed_direction": "Southeast",
  "temp": [25.1, 26.3, 24.8],
  "humidity": [65.2, 68.1, 62.4],
  "windspeed": [2.3, 1.8, 2.9],
  "sunshine": [8.2, 7.9, 8.5],
  "actual_generation": 450.2
}
```

#### 응답
```json
{
  "user_id": "이의형",
  "panel_id": 1,
  "performance_analysis": {
    "predicted_generation": 454.11,
    "actual_generation": 310,
    "performance_ratio": 0.683,
    "status": "미흡",
    "lifespan_months": 102.6018396846255,
    "estimated_cost": 1200000
  },
  "report_path": "",
  "created_at": "2025-08-17T12:24:52.624727",
  "processing_time_seconds": 0.015123844146728516,
  "panel_info": {
    "model_name": "Q.PEAK DUO XL-G11S.7 / BFG 600W",
    "serial_number": 123456789,
    "rated_power_w": 600,
    "temperature_coefficient": -0.35,
    "degradation_rate": 0.5,
    "installation": {
      "date": "2022-01-01",
      "angle": 30,
      "direction": "Southeast",
      "location": {
        "latitude": 37.5665,
        "longitude": 126.978
      }
    }
  },
  "environmental_data": {
    "temperature": {"average": 26, "min": 25, "max": 27},
    "humidity": {"average": 55, "min": 50, "max": 60},
    "wind_speed": {"average": 3.5, "min": 3, "max": 4},
    "sunshine": {"average": 6, "total": 18}
  }
}
```

### 3.2 성능 리포트 생성 (PDF 포함)
**POST** `/api/performance-analysis/report`

성능 분석과 함께 PDF 리포트를 생성합니다.

#### 요청
동일한 요청 형식 (`/analyze`와 같음)

#### 응답
```json
{
  "user_id": "user123",
  "address": "reports/user123_20241213_143025.pdf",
  "created_at": "2024-12-13T14:30:25.123Z"
}
```

---

## 4. ❌ 에러 응답

### 4.1 표준 에러 형식
```json
{
  "error": "MODEL_NOT_LOADED",
  "message": "YOLOv8 모델이 로드되지 않았습니다",
  "details": {
    "model_path": "models/yolov8_seg_0812_v0.1.pt",
    "timestamp": "2024-12-13T14:30:25.123Z"
  },
  "timestamp": "2024-12-13T14:30:25.123Z"
}
```

### 4.2 주요 에러 코드

| HTTP 코드 | 에러 코드 | 설명 | 해결방법 |
|-----------|-----------|------|----------|
| 400 | `INVALID_IMAGE_URL` | S3 URL 형식 오류 | URL 형식 확인 |
| 400 | `IMAGE_DOWNLOAD_FAILED` | S3 이미지 다운로드 실패 | URL 접근 권한 확인 |
| 400 | `INVALID_IMAGE_FORMAT` | 지원하지 않는 이미지 형식 | JPG, PNG 등 지원 형식 사용 |
| 400 | `IMAGE_TOO_LARGE` | 이미지 크기 초과 (20MB) | 이미지 크기 압축 |
| 422 | `VALIDATION_ERROR` | 요청 필드 검증 실패 | 필수 필드 및 형식 확인 |
| 500 | `MODEL_NOT_LOADED` | AI 모델 로드 실패 | 서버 재시작 또는 관리자 문의 |
| 500 | `ANALYSIS_FAILED` | AI 분석 처리 실패 | 다른 이미지로 재시도 |
| 503 | `SERVICE_UNAVAILABLE` | 서비스 일시 중단 | 잠시 후 재시도 |



## 5. 📊 변경 이력

### v3.0.0 (2024-12-13)
- ✨ 성능 예측 API 추가
- ✨ PDF 리포트 생성 기능
- 🔧 향상된 오류 처리
- 🔧 백엔드 연동 최적화
- 📚 완전한 API 문서화

### v2.1.0 (2024-11-15)
- 🔧 S3 연동 안정성 개선
- 🚀 성능 최적화 (30% 속도 향상)
- 🛡️ 보안 헤더 추가

### v2.0.0 (2024-10-01)
- ✨ S3 URL 기반 분석 지원
- ✨ 백엔드 연동 API 구현
- 🔧 마이크로서비스 아키텍처 전환

---
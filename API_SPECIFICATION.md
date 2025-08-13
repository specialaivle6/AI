# Solar Panel AI Service - API 명세서 v2.0

## 개요
태양광 패널 손상 분석 AI 서비스의 REST API 명세서입니다. YOLOv8 기반 정밀 손상 분석을 제공합니다.

- **Base URL**: `http://localhost:8000`
- **API 버전**: 2.0.0
- **Content-Type**: `application/json` (응답), `multipart/form-data` (요청)
- **AI 모델**: YOLOv8 Segmentation

---

## 엔드포인트 목록

### 1. 헬스체크 (기본)
**GET** `/`

서비스가 정상적으로 실행 중인지 확인하는 기본 헬스체크 엔드포인트입니다.

#### Request
- **Method**: GET
- **URL**: `/`
- **Parameters**: 없음

#### Response
```json
{
  "message": "Solar Panel Damage Analysis Service is running",
  "version": "2.0.0",
  "model": "YOLOv8 Segmentation"
}
```

---

### 2. 상세 헬스체크
**GET** `/health`

AI 모델 로딩 상태를 포함한 상세한 서비스 상태를 확인합니다.

#### Request
- **Method**: GET
- **URL**: `/health`
- **Parameters**: 없음

#### Response
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "2.0.0",
  "model_type": "YOLOv8"
}
```

#### Response Fields
| 필드 | 타입 | 설명 |
|------|------|------|
| `status` | string | 서비스 상태 ("healthy" 또는 "unhealthy") |
| `model_loaded` | boolean | YOLOv8 모델 로딩 상태 |
| `version` | string | API 버전 |
| `model_type` | string | 사용 중인 AI 모델 타입 |

---

### 3. 단일 이미지 손상 분석 (핵심 API)
**POST** `/analyze-damage`

태양광 패널 이미지를 업로드하여 YOLOv8 기반 정밀 손상 분석을 수행합니다.

#### Request
- **Method**: POST
- **URL**: `/analyze-damage`
- **Content-Type**: `multipart/form-data`

#### Request Parameters
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `file` | File | Yes | 분석할 태양광 패널 이미지 파일 |

#### File Requirements
- **지원 형식**: JPG, JPEG, PNG, BMP, TIFF, WEBP
- **최대 크기**: 20MB
- **권장 해상도**: 1024x1024 이상 (고해상도 권장)

#### Response
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
      },
      {
        "class_name": "Physical-Damage",
        "confidence": 0.923,
        "bbox": [450, 200, 600, 350],
        "area_pixels": 22500
      }
    ]
  },
  "confidence_score": 0.892,
  "timestamp": "2024-08-12 14:30:25"
}
```

#### Response Fields

##### image_info
| 필드 | 타입 | 설명 |
|------|------|------|
| `filename` | string | 업로드된 파일명 |
| `size` | string | 이미지 해상도 (width x height) |
| `processing_time_seconds` | number | 분석 처리 시간 (초) |

##### damage_analysis
| 필드 | 타입 | 설명 |
|------|------|------|
| `overall_damage_percentage` | number | 전체 손상률 (%) |
| `critical_damage_percentage` | number | 심각한 손상률 (%) |
| `contamination_percentage` | number | 오염 손상률 (%) |
| `healthy_percentage` | number | 정상 영역 비율 (%) |
| `avg_confidence` | number | 평균 신뢰도 (0~1) |
| `detected_objects` | integer | 검출된 객체 수 |
| `class_breakdown` | object | 클래스별 손상률 분포 |
| `status` | string | 분석 상태 ("analyzed", "no_detection") |

##### business_assessment
| 필드 | 타입 | 설명 |
|------|------|------|
| `priority` | string | 우선순위 (LOW, MEDIUM, HIGH, URGENT) |
| `risk_level` | string | 위험도 (MINIMAL, LOW, MEDIUM, HIGH) |
| `recommendations` | array | 권장 조치사항 목록 |
| `estimated_repair_cost_krw` | integer | 예상 수리 비용 (원) |
| `estimated_performance_loss_percent` | number | 예상 성능 저하율 (%) |
| `maintenance_urgency_days` | integer | 유지보수 긴급도 (일) |
| `business_impact` | string | 비즈니스 영향도 평가 |

##### detection_details
| 필드 | 타입 | 설명 |
|------|------|------|
| `total_detections` | integer | 총 검출 객체 수 |
| `detections` | array | 개별 검출 객체 상세 정보 |

##### detection 객체
| 필드 | 타입 | 설명 |
|------|------|------|
| `class_name` | string | 검출된 클래스명 |
| `confidence` | number | 신뢰도 (0~1) |
| `bbox` | array | 바운딩 박스 [x1, y1, x2, y2] |
| `area_pixels` | integer | 검출 영역 픽셀 수 |

---

### 4. 일괄 분석
**POST** `/batch-analyze`

여러 태양광 패널 이미지를 동시에 분석하고 통합 리포트를 제공합니다.

#### Request
- **Method**: POST
- **URL**: `/batch-analyze`
- **Content-Type**: `multipart/form-data`

#### Request Parameters
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `files` | File[] | Yes | 분석할 이미지 파일들 (최대 10개) |

#### Response
```json
{
  "total_analyzed": 5,
  "results": [
    {
      "image_info": {...},
      "damage_analysis": {...},
      "business_assessment": {...},
      "detection_details": {...},
      "confidence_score": 0.892,
      "timestamp": "2024-08-12 14:30:25"
    }
  ],
  "summary": {
    "total_analyzed_files": 5,
    "average_damage_percentage": 18.5,
    "critical_panels_count": 2,
    "critical_panels_percentage": 40.0,
    "priority_distribution": {
      "URGENT": 0,
      "HIGH": 2,
      "MEDIUM": 2,
      "LOW": 1
    },
    "overall_fleet_status": "NEEDS_ATTENTION",
    "recommended_action": "우선순위 기반 단계적 수리 권장"
  }
}
```

#### Summary Fields
| 필드 | 타입 | 설명 |
|------|------|------|
| `total_analyzed_files` | integer | 분석된 총 파일 수 |
| `average_damage_percentage` | number | 평균 손상률 (%) |
| `critical_panels_count` | integer | 심각한 손상 패널 수 |
| `critical_panels_percentage` | number | 심각한 손상 패널 비율 (%) |
| `priority_distribution` | object | 우선순위별 분포 |
| `overall_fleet_status` | string | 전체 시설 상태 (GOOD, FAIR, NEEDS_ATTENTION, CRITICAL) |
| `recommended_action` | string | 권장 조치 |

---

### 5. DB 연동 패널 분석 (신규)
**POST** `/panels/analyze`

패널 이미지 분석과 동시에 데이터베이스에 결과를 저장하는 통합 API입니다.

#### Request
- **Method**: POST
- **URL**: `/panels/analyze`
- **Content-Type**: `multipart/form-data`

#### Request Parameters
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `file` | File | Yes | 분석할 태양광 패널 이미지 파일 |
| `panel_id` | integer | Yes | 패널 고유 ID |
| `user_id` | string | Yes | 사용자 ID (UUID 형식 또는 일반 문자열) |

#### Response
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
      },
      {
        "class_name": "Physical-Damage",
        "confidence": 0.923,
        "bbox": [450, 200, 600, 350],
        "area_pixels": 22500
      }
    ]
  },
  "confidence_score": 0.892,
  "timestamp": "2024-08-12 14:30:25",
  "panel_image_id": 123,
  "panel_image_report_id": 456,
  "recommended_status": "손상",
  "recommended_decision": "수리"
}
```

#### Additional Response Fields
| 필드 | 타입 | 설명 |
|------|------|------|
| `panel_image_id` | integer | 생성된 PanelImage 레코드 ID |
| `panel_image_report_id` | integer | 생성된 PanelImageReport 레코드 ID |
| `recommended_status` | string | 권장 패널 상태 (손상, 오염, 정상) |
| `recommended_decision` | string | 권장 조치 결정 (단순 오염, 수리, 교체) |

---

### 6. 패널 분석 이력 조회
**GET** `/panels/{panel_id}/history`

특정 패널의 모든 분석 이력을 조회합니다.

#### Request
- **Method**: GET
- **URL**: `/panels/{panel_id}/history`
- **Parameters**: 없음

#### Path Parameters
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `panel_id` | integer | Yes | 조회할 패널 ID |

#### Response
```json
{
  "panel_id": 1234,
  "images": [
    {
      "id": 1,
      "panel_id": 1234,
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "film_date": "2024-08-12",
      "panel_imageurl": "uploads/panel_image.jpg",
      "is_analysis": true
    }
  ],
  "reports": [
    {
      "id": 1,
      "panel_id": 1234,
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "손상",
      "damage_degree": 7,
      "decision": "수리",
      "request_status": "요청 중",
      "created_at": "2024-08-12"
    }
  ],
  "total_analyses": 1
}
```

---

### 7. 리포트 상태 업데이트 (관리자용)
**PUT** `/reports/{report_id}/status`

패널 이미지 리포트의 처리 상태를 업데이트합니다.

#### Request
- **Method**: PUT
- **URL**: `/reports/{report_id}/status`
- **Content-Type**: `application/json`

#### Path Parameters
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `report_id` | integer | Yes | 업데이트할 리포트 ID |

#### Request Body
```json
{
  "status": "처리중"
}
```

#### Request Body Fields
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `status` | string | Yes | 새로운 상태 (요청 중, 요청확인, 처리중, 처리 완료) |

#### Response
```json
{
  "message": "리포트 상태가 업데이트되었습니다.",
  "report_id": 1,
  "new_status": "처리중"
}
```

---

## 에러 응답

### 4xx 클라이언트 에러

#### 400 Bad Request
```json
{
  "detail": "이미지 파일만 업로드 가능합니다."
}
```

#### 413 Payload Too Large
```json
{
  "detail": "파일 크기가 20MB를 초과합니다."
}
```

#### 422 Unprocessable Entity
```json
{
  "detail": "최대 10개 파일까지 업로드 가능합니다."
}
```

### 5xx 서버 에러

#### 500 Internal Server Error
```json
{
  "detail": "분석 중 오류가 발생했습니다: [구체적인 오류 메시지]"
}
```

#### 503 Service Unavailable
```json
{
  "detail": "AI 모델이 로딩되지 않았습니다. 잠시 후 다시 시도해주세요."
}
```

---

## 검출 가능한 클래스

YOLOv8 모델이 검출할 수 있는 태양광 패널 상태 클래스입니다.

| 클래스명 | 심각도 | 설명 | 일반적인 조치사항 |
|----------|--------|------|------------------|
| `Non-Defective` | 0 | 정상 상태 | 정기 점검 유지 |
| `Defective` | 1 | 일반적인 결함 | 모니터링 강화 |
| `Bird-drop` | 1 | 조류 배설물 | 청소 작업 |
| `Dusty` | 1 | 먼지/오염물질 | 청소 작업 |
| `Snow-Covered` | 1 | 눈 덮임 | 제설 작업 |
| `Physical-Damage` | 3 | 물리적 손상 | 즉시 수리 필요 |
| `Electrical-Damage` | 3 | 전기적 손상 | 즉시 전문가 점검 |

### 심각도 분류
- **0**: 정상 - 조치 불필요
- **1**: 경미 - 일반 유지보수
- **3**: 심각 - 즉시 조치 필요

---

## 사용 예시

### cURL 예시

#### 1. 헬스체크
```bash
curl -X GET "http://localhost:8000/health"
```

#### 2. 단일 이미지 분석
```bash
curl -X POST "http://localhost:8000/analyze-damage" \
     -F "file=@panel_image.jpg"
```

#### 3. 일괄 분석
```bash
curl -X POST "http://localhost:8000/batch-analyze" \
     -F "files=@panel1.jpg" \
     -F "files=@panel2.jpg" \
     -F "files=@panel3.jpg"
```

#### 4. DB 연동 패널 분석
```bash
curl -X POST "http://localhost:8000/panels/analyze" \
     -F "file=@panel_image.jpg" \
     -F "panel_id=123" \
     -F "user_id=example-user-id"
```

### JavaScript (Fetch) 예시

```javascript
// 단일 이미지 분석
const analyzePanel = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await fetch('http://localhost:8000/analyze-damage', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    console.log('분석 결과:', result);
    
    // 손상률 확인
    const damagePercentage = result.damage_analysis.overall_damage_percentage;
    const priority = result.business_assessment.priority;
    
    if (priority === 'URGENT') {
      alert('긴급! 즉시 조치가 필요합니다.');
    }
    
    return result;
  } catch (error) {
    console.error('분석 실패:', error);
    throw error;
  }
};
```

### Python Requests 예시

```python
import requests

def analyze_panel_damage(image_path):
    """태양광 패널 손상 분석"""
    
    url = "http://localhost:8000/analyze-damage"
    
    with open(image_path, 'rb') as file:
        files = {'file': file}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        result = response.json()
        
        # 결과 분석
        damage_analysis = result['damage_analysis']
        business_assessment = result['business_assessment']
        
        print(f"전체 손상률: {damage_analysis['overall_damage_percentage']:.2f}%")
        print(f"우선순위: {business_assessment['priority']}")
        print(f"권장사항: {', '.join(business_assessment['recommendations'])}")
        
        return result
    else:
        print(f"분석 실패: {response.status_code} - {response.text}")
        return None

# 사용 예시
result = analyze_panel_damage("panel_image.jpg")
```

---

## 성능 및 제한사항

### 성능 지표
- **응답 시간**: 1-3초 (이미지 크기 및 복잡도에 따라 변동)
- **동시 처리**: 권장 1개 요청 (순차 처리)
- **메모리 사용량**: ~1GB (모델 로딩 시)
- **CPU 사용률**: 분석 중 80-100% (일시적)

### 제한사항
- **파일 크기**: 최대 20MB
- **일괄 처리**: 최대 10개 파일
- **동시 요청**: 권장하지 않음 (순차 처리)
- **지원 형식**: 이미지 파일만 지원

### 최적화 권장사항
1. **이미지 크기**: 1024x1024 ~ 2048x2048 권장
2. **파일 형식**: JPG 권장 (용량 효율성)
3. **요청 간격**: 이전 요청 완료 후 다음 요청 전송
4. **타임아웃**: 최소 60초 설정

---

## 업데이트 내역

| 버전 | 날짜 | 주요 변경사항 |
|------|------|---------------|
| v2.0.0 | 2024-08-12 | YOLOv8 기반 전면 개편, 픽셀 단위 정밀 분석, 일괄 처리 추가 |
| v1.0.0 | 2024-08-01 | 초기 버전, MobileNet 기반 기본 분류 |

---

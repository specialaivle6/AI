# 🚀 AI Services v2.0 - 손상 분석 빠른 시작 가이드

## 📋 체크리스트 (5분만에 실행)

### ✅ 1단계: 환경 확인
```bash
# Python 3.11 설치 확인
python --version  # Python 3.11.x 여야 함

# Windows/Linux/macOS 모두 지원
```

### ✅ 2단계: 서버 실행
```bash
# 저장소 이동
cd AI

# 환경 활성화
conda activate ai

# 서버 시작 (YOLOv8 모델 자동 다운로드)
python -m app.main
```

### ✅ 3단계: 동작 확인
```bash
# 헬스체크 (새 터미널에서)
curl http://localhost:8000/health

# 예상 결과: {"status":"healthy","model_loaded":true,"model_type":"YOLOv8"}
```

### ✅ 4단계: API 테스트
브라우저에서 접속: **http://localhost:8000/docs**

---

## 🔥 핵심 API 사용법

### Spring Boot에서 손상 분석 호출하는 방법

```java
// 의존성 추가 필요: spring-boot-starter-web

@RestController
public class PanelController {
    
    @PostMapping("/panel/analyze-damage")
    public ResponseEntity<?> analyzePanelDamage(@RequestParam("file") MultipartFile file) {
        
        // AI 서버 호출
        RestTemplate restTemplate = new RestTemplate();
        
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", file.getResource());
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        
        HttpEntity<MultiValueMap<String, Object>> requestEntity = 
            new HttpEntity<>(body, headers);
        
        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(
                "http://localhost:8000/analyze-damage",  // 새로운 엔드포인트
                requestEntity,
                Map.class
            );
            
            return ResponseEntity.ok(response.getBody());
            
        } catch (Exception e) {
            return ResponseEntity.status(500)
                .body("AI 손상 분석 실패: " + e.getMessage());
        }
    }
    
    @PostMapping("/panel/batch-analyze")
    public ResponseEntity<?> batchAnalyzePanels(@RequestParam("files") MultipartFile[] files) {
        
        RestTemplate restTemplate = new RestTemplate();
        
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        for (MultipartFile file : files) {
            body.add("files", file.getResource());
        }
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        
        HttpEntity<MultiValueMap<String, Object>> requestEntity = 
            new HttpEntity<>(body, headers);
        
        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(
                "http://localhost:8000/batch-analyze",
                requestEntity,
                Map.class
            );
            
            return ResponseEntity.ok(response.getBody());
            
        } catch (Exception e) {
            return ResponseEntity.status(500)
                .body("일괄 분석 실패: " + e.getMessage());
        }
    }
}
```

### Spring Boot에서 새로운 DB 연동 API 사용법

```java
// 의존성 추가 필요: spring-boot-starter-web

@RestController
public class PanelController {
    
    @PostMapping("/panel/analyze-with-db")
    public ResponseEntity<?> analyzePanelWithDatabase(
            @RequestParam("file") MultipartFile file,
            @RequestParam("panel_id") Integer panelId,
            @RequestParam("user_id") String userId) {
        
        // 새로운 DB 연동 API 호출
        RestTemplate restTemplate = new RestTemplate();
        
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", file.getResource());
        
        UriComponentsBuilder builder = UriComponentsBuilder
                .fromHttpUrl("http://localhost:8000/panels/analyze")
                .queryParam("panel_id", panelId)
                .queryParam("user_id", userId);
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        
        HttpEntity<MultiValueMap<String, Object>> requestEntity = 
            new HttpEntity<>(body, headers);
        
        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(
                builder.toUriString(),
                requestEntity,
                Map.class
            );
            
            return ResponseEntity.ok(response.getBody());
            
        } catch (Exception e) {
            return ResponseEntity.status(500)
                .body("DB 연동 분석 실패: " + e.getMessage());
        }
    }
    
    @GetMapping("/panel/{panelId}/history")
    public ResponseEntity<?> getPanelHistory(@PathVariable Integer panelId) {
        
        RestTemplate restTemplate = new RestTemplate();
        
        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(
                "http://localhost:8000/panels/" + panelId + "/history",
                Map.class
            );
            
            return ResponseEntity.ok(response.getBody());
            
        } catch (Exception e) {
            return ResponseEntity.status(500)
                .body("패널 이력 조회 실패: " + e.getMessage());
        }
    }
    
    @PutMapping("/report/{reportId}/status")
    public ResponseEntity<?> updateReportStatus(
            @PathVariable Integer reportId,
            @RequestBody Map<String, String> statusUpdate) {
        
        RestTemplate restTemplate = new RestTemplate();
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        HttpEntity<Map<String, String>> requestEntity = 
            new HttpEntity<>(statusUpdate, headers);
        
        try {
            ResponseEntity<Map> response = restTemplate.exchange(
                "http://localhost:8000/reports/" + reportId + "/status",
                HttpMethod.PUT,
                requestEntity,
                Map.class
            );
            
            return ResponseEntity.ok(response.getBody());
            
        } catch (Exception e) {
            return ResponseEntity.status(500)
                .body("리포트 상태 업데이트 실패: " + e.getMessage());
        }
    }
}
```

---

## 📊 응답 데이터 해석 (YOLOv8 기반)

### 핵심 필드 설명
```json
{
  "damage_analysis": {
    "overall_damage_percentage": 15.34,      // 전체 손상률 (%)
    "critical_damage_percentage": 2.1,       // 심각한 손상률 (%)
    "contamination_percentage": 13.24,       // 오염 손상률 (%)
    "healthy_percentage": 84.66,             // 정상 영역 비율 (%)
    "avg_confidence": 0.892,                 // 평균 신뢰도 (0~1)
    "detected_objects": 3,                   // 검출된 객체 수
    "class_breakdown": {                     // 클래스별 손상률
      "Dusty": 13.24,
      "Physical-Damage": 2.1
    }
  },
  "business_assessment": {
    "priority": "MEDIUM",                    // 우선순위: LOW/MEDIUM/HIGH/URGENT
    "risk_level": "LOW",                     // 위험도: MINIMAL/LOW/MEDIUM/HIGH
    "estimated_repair_cost_krw": 15340,      // 예상 수리 비용 (원)
    "maintenance_urgency_days": 30,          // 유지보수 긴급도 (일)
    "recommendations": [                     // 권장 조치사항
      "패널 청소 필요",
      "물리적 손상 부위 점검 권장"
    ]
  }
}
```

### 비즈니스 로직 활용
```java
// 우선순위 판단
Map<String, Object> assessment = (Map<String, Object>) result.get("business_assessment");
String priority = (String) assessment.get("priority");

if ("URGENT".equals(priority)) {
    // 즉시 알림 발송 및 작업 중단
    sendUrgentAlert(result);
    shutdownPanel(panelId);
} else if ("HIGH".equals(priority)) {
    // 빠른 대응 스케줄링
    scheduleHighPriorityMaintenance(result);
} else if ("MEDIUM".equals(priority)) {
    // 일반 유지보수 계획
    scheduleRegularMaintenance(result);
}

// 비용 계산 및 예산 관리
Integer estimatedCost = (Integer) assessment.get("estimated_repair_cost_krw");
Integer urgencyDays = (Integer) assessment.get("maintenance_urgency_days");

// 손상률 기반 성능 예측
Map<String, Object> damage = (Map<String, Object>) result.get("damage_analysis");
Double overallDamage = (Double) damage.get("overall_damage_percentage");
Double criticalDamage = (Double) damage.get("critical_damage_percentage");

// 발전 효율 계산
Double efficiencyLoss = Math.min(overallDamage * 0.8, 95.0);  // 최대 95% 손실
```

---

## ⚠️ 주요 변경사항 및 주의사항

### 🚨 API 엔드포인트 변경
| 기존 (v1.0) | 새로운 (v2.0) | 변경사항 |
|-------------|---------------|----------|
| `/analyze-panel` | `/analyze-damage` | 엔드포인트 이름 변경 |
| - | `/batch-analyze` | 일괄 분석 기능 추가 |
| `/health` | `/health` | 동일 (응답 구조 변경) |

### 🔄 응답 구조 변경
```java
// v1.0 (MobileNet) 응답 구조
{
  "predicted_class": "Dusty",
  "confidence": 0.8234,
  "severity_level": 1,
  "recommendations": {...}
}

// v2.0 (YOLOv8) 응답 구조  
{
  "image_info": {...},
  "damage_analysis": {
    "overall_damage_percentage": 15.34,
    "critical_damage_percentage": 2.1,
    // ...
  },
  "business_assessment": {
    "priority": "MEDIUM",
    "risk_level": "LOW",
    // ...
  },
  "detection_details": {...}
}
```

### 💡 마이그레이션 가이드
```java
// 기존 코드를 새로운 구조로 변경하는 방법

// Before (v1.0)
String predictedClass = (String) result.get("predicted_class");
Double confidence = (Double) result.get("confidence");

// After (v2.0)
Map<String, Object> damageAnalysis = (Map<String, Object>) result.get("damage_analysis");
Double overallDamage = (Double) damageAnalysis.get("overall_damage_percentage");
Double avgConfidence = (Double) damageAnalysis.get("avg_confidence");

Map<String, Object> businessAssessment = (Map<String, Object>) result.get("business_assessment");
String priority = (String) businessAssessment.get("priority");
```

### 💡 베스트 프랙티스
```java
// 1. 타임아웃 설정 (YOLOv8는 더 많은 처리 시간 필요)
RestTemplate restTemplate = new RestTemplate();
HttpComponentsClientHttpRequestFactory factory = new HttpComponentsClientHttpRequestFactory();
factory.setConnectTimeout(15000);  // 15초로 증가
factory.setReadTimeout(60000);     // 60초로 증가
restTemplate.setRequestFactory(factory);

// 2. 신뢰도 체크 (평균 신뢰도 사용)
Map<String, Object> damageAnalysis = (Map<String, Object>) result.get("damage_analysis");
Double avgConfidence = (Double) damageAnalysis.get("avg_confidence");
if (avgConfidence < 0.7) {  // 임계값 상향 조정
    return "신뢰도가 낮습니다. 더 선명한 이미지로 다시 시도해주세요.";
}

// 3. 심각한 손상 우선 처리
Double criticalDamage = (Double) damageAnalysis.get("critical_damage_percentage");
if (criticalDamage > 5.0) {  // 5% 이상 심각한 손상
    // 즉시 알림 및 긴급 대응
    sendCriticalAlert(result);
}

// 4. 에러 처리 강화
try {
    ResponseEntity<Map> response = restTemplate.postForEntity(...);
    
    // 검출 객체 수 확인
    Map<String, Object> damageAnalysis = (Map<String, Object>) response.getBody().get("damage_analysis");
    Integer detectedObjects = (Integer) damageAnalysis.get("detected_objects");
    
    if (detectedObjects == 0) {
        return "패널이 검출되지 않았습니다. 이미지를 다시 확인해주세요.";
    }
    
} catch (ResourceAccessException e) {
    return "AI 서버 연결 시간 초과. 잠시 후 다시 시도해주세요.";
} catch (HttpServerErrorException e) {
    return "AI 분석 중 오류가 발생했습니다. 관리자에게 문의하세요.";
}
```

---

## 🐛 트러블슈팅

| 문제 | 해결책 |
|------|--------|
| `model_loaded: false` | YOLOv8 모델 다운로드 대기 (첫 실행 시 시간 소요) |
| 서버 연결 안됨 | `python -m app.main` 실행 확인 |
| NumPy 호환성 오류 | `pip install "numpy<2"` 실행 |
| 이미지 업로드 실패 | 파일 크기 20MB 이하, 지원 형식 확인 (JPG, PNG, BMP, TIFF, WEBP) |
| 503 에러 | AI 서버 재시작 필요 |
| 처리 시간 느림 | 첫 번째 요청은 모델 로딩으로 인해 느릴 수 있음 |

### 🔧 성능 최적화 팁
```bash
# 1. 메모리 사용량 모니터링
htop  # Linux/WSL
Task Manager  # Windows

# 2. 로그 확인
tail -f logs/ai_service.log

# 3. Docker 사용 (안정성 향상)
docker build -t solar-panel-ai .
docker run -p 8000:8000 --memory=2g solar-panel-ai
```

---

## 🔗 유용한 링크

- **API 문서**: http://localhost:8000/docs (Swagger UI)
- **헬스체크**: http://localhost:8000/health  
- **기본 정보**: http://localhost:8000/
- **테스트 스크립트**: `python test_api.py`

### 📱 새로운 테스트 방법
```bash
# 단일 이미지 테스트
curl -X POST "http://localhost:8000/analyze-damage" \
     -F "file=@test_panel.jpg"

# 일괄 분석 테스트
curl -X POST "http://localhost:8000/batch-analyze" \
     -F "files=@panel1.jpg" \
     -F "files=@panel2.jpg" \
     -F "files=@panel3.jpg"

# 헬스체크
curl http://localhost:8000/health
```

---

## 🎯 주요 개선사항 요약

### ✅ v2.0에서 새로 추가된 기능
1. **픽셀 단위 정밀 분석**: 정확한 손상률 계산
2. **일괄 분석**: 최대 10개 파일 동시 처리
3. **상세 비즈니스 평가**: 우선순위, 위험도, 비용 예측
4. **검출 상세 정보**: 바운딩 박스, 신뢰도, 영역 크기
5. **강화된 모니터링**: 처리 시간, 검출 통계

### 🚀 성능 향상
- **처리 속도**: 1-2초로 개선
- **정확도**: 픽셀 단위 정밀 분석
- **안정성**: 비동기 처리, 에러 핸들링 강화
- **확장성**: 일괄 분석, 다양한 이미지 형식 지원

---
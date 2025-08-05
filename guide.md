# 🚀 AI Services - 패널 분석 빠른 시작 가이드

## 📋 체크리스트 (5분만에 실행)

### ✅ 1단계: 환경 확인
```bash
# Python 3.11 설치 확인
python --version  # Python 3.11.x 여야 함

# WSL/Linux 권장 (Windows도 가능)
```

### ✅ 2단계: 서버 실행
```bash
# 저장소 이동
cd ai-service/panel-analysis

# 환경 활성화
conda activate solar-panel-ai

# 서버 시작
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### ✅ 3단계: 동작 확인
```bash
# 헬스체크 (새 터미널에서)
curl http://localhost:8000/health

# 예상 결과: {"status":"healthy","model_loaded":true}
```

### ✅ 4단계: API 테스트
브라우저에서 접속: **http://localhost:8000/docs**

---

## 🔥 핵심 API 사용법

### Spring Boot에서 호출하는 방법

```java
// 의존성 추가 필요: spring-boot-starter-web

@RestController
public class PanelController {
    
    @PostMapping("/panel/analyze")
    public ResponseEntity<?> analyzePanel(@RequestParam("file") MultipartFile file) {
        
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
                "http://localhost:8000/analyze-panel",
                requestEntity,
                Map.class
            );
            
            return ResponseEntity.ok(response.getBody());
            
        } catch (Exception e) {
            return ResponseEntity.status(500)
                .body("AI 분석 실패: " + e.getMessage());
        }
    }
}
```

---

## 📊 응답 데이터 해석

### 핵심 필드 설명
```json
{
  "predicted_class": "Dusty",           // 예측된 상태
  "confidence": 0.8234,                 // 신뢰도 (0~1)
  "severity_level": 1,                  // 심각도 (0:정상, 1:경미, 3:심각)
  "recommendations": {
    "action": "청소",                   // 권장 조치
    "estimated_cost": 50000,            // 예상 비용 (원)
    "urgency": "1주일 내"              // 긴급도
  },
  "requires_immediate_action": false    // 즉시 조치 필요 여부
}
```

### 비즈니스 로직 활용
```java
// 우선순위 판단
if (result.get("requires_immediate_action").equals(true)) {
    // 즉시 알림 발송
    sendUrgentAlert(result);
} else if (result.get("severity_level").equals(1)) {
    // 일반 알림 발송  
    sendNormalAlert(result);
}

// 비용 계산
Integer estimatedCost = (Integer) result.get("recommendations").get("estimated_cost");
```

---

## ⚠️ 주의사항

### 🚨 중요한 제한사항
1. **단일 요청만 처리**: 동시에 여러 이미지 분석 불가
2. **물리적 손상 놓칠 위험**: 재현율 28.6%로 낮음
3. **이미지 크기 제한**: 최대 10MB

### 💡 베스트 프랙티스
```java
// 1. 타임아웃 설정
RestTemplate restTemplate = new RestTemplate();
restTemplate.setRequestFactory(new HttpComponentsClientHttpRequestFactory());
((HttpComponentsClientHttpRequestFactory) restTemplate.getRequestFactory())
    .setConnectTimeout(10000);
((HttpComponentsClientHttpRequestFactory) restTemplate.getRequestFactory())
    .setReadTimeout(30000);

// 2. 신뢰도 체크
Double confidence = (Double) result.get("confidence");
if (confidence < 0.6) {
    // 낮은 신뢰도 - 재검토 요청
    return "신뢰도가 낮습니다. 더 선명한 이미지로 다시 시도해주세요.";
}

// 3. 에러 처리
try {
    // AI API 호출
} catch (ResourceAccessException e) {
    return "AI 서버에 연결할 수 없습니다. 관리자에게 문의하세요.";
} catch (HttpServerErrorException e) {
    return "AI 분석 중 오류가 발생했습니다.";
}
```

---

## 🐛 트러블슈팅

| 문제 | 해결책 |
|------|--------|
| `model_loaded: false` | 모델 파일 경로 확인 (`models/mobilenet_v3_small.pth`) |
| 서버 연결 안됨 | `uvicorn app.main:app --host 0.0.0.0 --port 8000` 실행 확인 |
| 이미지 업로드 실패 | 파일 크기 10MB 이하, 이미지 형식 확인 |
| 503 에러 | AI 서버 재시작 필요 |

---

## 🔗 유용한 링크

- **API 문서**: http://localhost:8000/docs
- **헬스체크**: http://localhost:8000/health  
- **테스트 스크립트**: `python test_api.py`

---
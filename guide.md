# 🚀 Solar Panel AI Service v3.0 - 백엔드 연동 빠른 시작 가이드

## 📋 체크리스트 (5분만에 실행)

### ✅ 1단계: 환경 확인
```bash
# Python 3.9+ 설치 확인
python --version  # Python 3.9+ 여야 함

# 가상환경 활성화
cd AI
ai\Scripts\activate  # Windows
source ai/bin/activate  # Linux/Mac
```

### ✅ 2단계: 의존성 설치
```bash
# 패키지 설치
pip install -r requirements.txt

# AI 모델 파일 확인
# models/yolov8_seg_0812_v0.1.pt 파일이 있는지 확인
```

### ✅ 3단계: 서버 실행
```bash
# 방법 1: uvicorn으로 실행 (권장)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 방법 2: 직접 실행
python app/main.py
```

### ✅ 4단계: 동작 확인
```bash
# 기본 헬스체크
curl http://localhost:8000/

# AI 서비스 헬스체크
curl http://localhost:8000/api/damage-analysis/health

# 예상 결과: {"status":"healthy","model_loaded":true,"version":"3.0.0"}
```

### ✅ 5단계: API 테스트
```bash
# 테스트 스크립트 실행
python test_api.py

# 또는 백엔드에서 직접 호출 (PanelImageReport 매핑 지원)
curl -X POST http://localhost:8000/api/damage-analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "panel_id": 123,
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "panel_imageurl": "https://your-s3-bucket.com/panel-image.jpg"
  }'
```

### ✅ 6단계: Docker 배포 (선택사항)
```bash
# 환경변수 설정
cp .env.example .env

# 개발 환경 배포
docker-compose up -d

# 또는 자동 배포 스크립트 사용
chmod +x deploy.sh
./deploy.sh

# 프로덕션 환경 배포
./deploy.sh production
```

---

## 🔧 백엔드 연동 설정

### Spring Boot 연동 예시
```java
@Configuration
public class AIServiceConfig {
    
    @Value("${ai.service.url:http://localhost:8000}")
    private String aiServiceUrl;
    
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
    
    @Bean
    public AIServiceClient aiServiceClient() {
        return new AIServiceClient(aiServiceUrl, restTemplate());
    }
}

@Service
public class PanelAnalysisService {
    
    @Autowired
    private AIServiceClient aiClient;
    
    public AnalysisResult analyzePanelDamage(Long panelId, UUID userId, String s3Url) {
        DamageAnalysisRequest request = new DamageAnalysisRequest();
        request.setPanelId(panelId);
        request.setUserId(userId);
        request.setPanelImageurl(s3Url);
        
        return aiClient.analyzeDamage(request);
    }
}
```

### Node.js 연동 예시
```javascript
const axios = require('axios');

class AIServiceClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async analyzeDamage(panelId, userId, s3Url) {
        try {
            const response = await axios.post(`${this.baseUrl}/api/damage-analysis/analyze`, {
                panel_id: panelId,
                user_id: userId,
                panel_imageurl: s3Url
            });
            
            return response.data;
        } catch (error) {
            console.error('AI 분석 실패:', error);
            throw error;
        }
    }
}

module.exports = AIServiceClient;
```

---

## 🐳 Docker 실행 (선택사항)

```bash
# Docker 이미지 빌드
docker build -t solar-panel-ai .

# Docker 컨테이너 실행
docker run -p 8000:8000 solar-panel-ai

# 또는 docker-compose 사용
docker-compose up -d
```

---

## 🚨 문제 해결

### AI 모델 로딩 실패
```bash
# 모델 파일 확인
ls -la models/yolov8_seg_0812_v0.1.pt

# 모델 파일이 없는 경우 문의 또는 다운로드
```

### S3 연결 문제
```bash
# 네트워크 연결 확인
curl -I https://your-s3-bucket.com/test-image.jpg

# 권한 문제인 경우 S3 URL이 공개되어 있는지 확인
```

### 메모리 부족
```bash
# 시스템 메모리 확인 (최소 4GB 권장)
free -h  # Linux
Get-ComputerInfo | Select-Object TotalPhysicalMemory  # Windows PowerShell

# 메모리 부족시 스왑 메모리 설정 또는 하드웨어 업그레이드
```

### 포트 충돌
```bash
# 포트 8000 사용 중인 프로세스 확인
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac

# 다른 포트로 실행
python -m uvicorn app.main:app --port 8001
```

---

## 📊 성능 모니터링

### 로그 확인
```bash
# 실시간 로그 모니터링
tail -f logs/app.log

# 에러 로그만 확인
grep ERROR logs/app.log
```

### 메모리 사용량 확인
```python
# Python에서 메모리 사용량 확인
import psutil
print(f"메모리 사용량: {psutil.virtual_memory().percent}%")
```

### API 응답 시간 측정
```bash
# curl로 응답 시간 측정
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/damage-analysis/health
```

---

## 🔄 업데이트 가이드

### 코드 업데이트
```bash
# Git에서 최신 코드 가져오기
git pull origin main

# 의존성 업데이트
pip install -r requirements.txt --upgrade

# 서버 재시작
```

### 모델 업데이트
```bash
# 새 모델 파일로 교체
cp new_model.pt models/yolov8_seg_0812_v0.1.pt

# 서버 재시작으로 새 모델 로드
```

---

## 📞 지원 및 문의

- **개발팀 연락처**: [개발팀 이메일]
- **이슈 리포팅**: GitHub Issues 또는 내부 이슈 트래커
- **긴급 문의**: [긴급 연락처]

---

## 📚 추가 문서

- [API 명세서](API_SPECIFICATION.md)
- [README.md](README.md)
- [백엔드 연동 가이드](README.md#백엔드-연동-가이드)

---

## 🔗 PanelImageReport 테이블 매핑

AI 서버는 백엔드의 PanelImageReport 테이블에 저장할 모든 데이터를 제공합니다:

```json
{
  "business_assessment": {
    "panel_status": "오염",        // DB: status 필드
    "damage_degree": 25,           // DB: damage_degree 필드  
    "decision": "단순 오염"        // DB: decision 필드
  }
}
```

### 백엔드 DB 매핑 예시
```java
public PanelImageReport mapToEntity(DamageAnalysisResponse response) {
    return PanelImageReport.builder()
        .panelId(response.getPanelId())
        .userId(response.getUserId())
        .status(response.getBusinessAssessment().getPanelStatus())
        .damageDegree(response.getBusinessAssessment().getDamageDegree())
        .decision(response.getBusinessAssessment().getDecision())
        .requestStatus("처리 완료")  // 백엔드에서 설정
        .createdAt(response.getTimestamp().toLocalDate())
        .build();
}
```

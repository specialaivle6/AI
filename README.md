# AI Services

> 통합 AI 서비스 저장소

## 🚀 서비스 목록

### 1. panel-analysis ✅
- **기능**: 태양광 패널 상태 분석 (6개 클래스 분류)
- **기술**: MobileNetV3 + FastAPI
- **정확도**: 77.4%
- **상태**: 운영 준비 완료

### 2. 향후 계획
- 추가 AI 서비스들 개발 예정

## 🏗️ 전체 아키텍처

```
Frontend (React) 
    ↓
Spring Boot (Java)
    ↓
AI Services
  ├── panel-analysis [완료]
  └── future-services
```

## 🚀 빠른 시작

### panel-analysis 실행
```bash
cd panel-analysis
conda create -n solar-panel-ai python=3.11 -y
conda activate solar-panel-ai
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API 문서: http://localhost:8000/docs

## 📊 성능

- **전체 정확도**: 77.4%
- **추론 시간**: 1-3초/이미지 (CPU)
- **메모리 사용량**: ~500MB

## 🏗️ 프로젝트 구조

```
solar-panel-ai-service/
├── app/
│   ├── main.py                 # FastAPI 메인 애플리케이션
│   ├── models/model_loader.py  # AI 모델 로딩 및 추론
│   ├── services/              # 이미지 처리 및 비즈니스 로직
│   └── core/config.py         # 설정 관리
├── models/                    # 학습된 모델 파일 (별도 제공)
├── requirements.txt
└── test_api.py               # API 테스트 스크립트
```

## 🤝 연동 가이드

### Spring Boot에서 호출
```java
@PostMapping("/panel/analyze")
public ResponseEntity<?> analyzePanel(@RequestParam("file") MultipartFile file) {
    // AI 서버 호출 코드
    // 상세한 예시는 docs/ 폴더 참조
}
```

## 📞 문의

- **AI 개발**: [담당자 연락처]
- **API 연동**: 이 README 및 /docs 엔드포인트 참조

## 📄 라이센스

Private - 조직 내부 사용만 허용
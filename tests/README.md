# 태양광 패널 AI 서비스 테스트 시스템

## 📋 개요

이 문서는 태양광 패널 AI 서비스의 테스트 시스템에 대한 종합적인 가이드입니다. 손상 분석과 성능 예측 AI 서비스의 품질을 보장하기 위한 포괄적인 테스트 환경을 제공합니다.

## 🏗️ 테스트 아키텍처

### 테스트 구조
```
tests/
├── conftest.py              # pytest 설정 및 공통 픽스처
├── pytest.ini               # pytest 구성 파일  
├── run_tests.py             # 테스트 실행 스크립트
├── test_image_generator.py  # 테스트용 이미지 생성기
├── test_image_server.py     # 로컬 이미지 서빙 서버
├── unit/                    # 단위 테스트
│   ├── test_core.py         # 핵심 모듈 테스트
│   └── test_image_utils.py  # 이미지 처리 테스트
├── integration/             # 통합 테스트
│   └── test_ai_services.py  # AI 서비스 통합 테스트
└── test_images/            # 테스트용 이미지 데이터
    ├── valid/              # 유효한 테스트 이미지들
    └── invalid/            # 무효한 테스트 이미지들
```

## 🧪 테스트 카테고리

### 1. 단위 테스트 (Unit Tests)

#### 📁 `tests/unit/test_core.py`
**핵심 시스템 구성 요소 테스트**

- **설정 관리 테스트** (6개)
  - `test_settings_initialization`: 기본 설정 초기화 검증
  - `test_environment_detection`: 개발/프로덕션 환경 감지
  - `test_damage_constants`: 손상 분석 상수 검증
  - `test_performance_constants`: 성능 예측 상수 검증
  - `test_create_directories`: 디렉토리 생성 기능
  - `test_validate_settings_missing_models`: 모델 파일 검증

- **예외 처리 테스트** (5개)
  - `test_ai_service_exception_basic`: 기본 AI 서비스 예외
  - `test_model_not_loaded_exception`: 모델 미로드 예외
  - `test_image_download_exception`: 이미지 다운로드 예외
  - `test_damage_analysis_exception`: 손상 분석 예외
  - `test_http_status_code_mapping`: HTTP 상태 코드 매핑

- **로깅 시스템 테스트** (3개)
  - `test_logger_creation`: 로거 생성 검증
  - `test_logger_mixin`: 로거 믹스인 클래스
  - `test_performance_logging`: 성능 로깅 기능

#### 📁 `tests/unit/test_image_utils.py`
**이미지 처리 유틸리티 테스트**

- **이미지 검증 테스트** (5개)
  - `test_validate_valid_image`: 유효한 이미지 검증
  - `test_validate_unsupported_extension`: 지원하지 않는 확장자
  - `test_validate_small_image`: 최소 크기 미달 이미지
  - `test_validate_corrupted_data`: 손상된 이미지 데이터
  - `test_get_image_info`: 이미지 메타데이터 추출

- **이미지 처리 테스트** (4개)
  - `test_preprocess_image_for_ai`: AI용 이미지 전처리
  - `test_optimize_image_for_storage`: 저장용 이미지 최적화
  - `test_create_thumbnail`: 썸네일 생성
  - `test_extract_image_metadata`: 메타데이터 추출

- **Mock S3 다운로드 테스트** (4개)
  - `test_download_success_mock`: 성공적인 다운로드
  - `test_download_http_error_mock`: HTTP 오류 처리
  - `test_download_timeout_mock`: 타임아웃 처리
  - `test_download_oversized_image_mock`: 크기 초과 이미지

### 2. 통합 테스트 (Integration Tests)

#### 📁 `tests/integration/test_ai_services.py`
**AI 서비스 전체 워크플로우 테스트**

- **손상 분석 통합 테스트**
  - API 엔드포인트 헬스체크
  - 실제 이미지 분석 워크플로우 (Mock S3 사용)
  - 다양한 손상 타입별 분석 검증
  - 오류 상황 처리 검증

- **성능 예측 통합 테스트**
  - 성능 분석 API 테스트
  - PDF 리포트 생성 테스트
  - 입력 데이터 검증

- **End-to-End 테스트**
  - 전체 애플리케이션 상태 확인
  - 일관된 에러 처리 검증

## 🛠️ 테스트 지원 도구

### 1. 테스트 이미지 생성기 (`test_image_generator.py`)

**기능:**
- 다양한 손상 타입의 가짜 태양광 패널 이미지 생성
- 정상, 균열, 새 배설물, 먼지, 눈 등 5가지 손상 타입
- 유효/무효 이미지 모두 포함한 테스트 데이터셋

**생성되는 이미지:**
- `panel_normal_*.jpg` - 정상 패널 이미지
- `panel_crack_*.jpg` - 균열 손상 이미지
- `panel_bird_drop_*.jpg` - 새 배설물 오염 이미지
- `panel_dusty_*.jpg` - 먼지 오염 이미지
- `panel_snow_*.jpg` - 눈 덮임 이미지

### 2. 로컬 이미지 서버 (`test_image_server.py`)

**기능:**
- 실제 S3 URL 대신 로컬 파일을 서빙하는 Mock 서버
- 테스트 환경에서 네트워크 의존성 제거
- `/test-images/{image_name}` 엔드포인트 제공

### 3. 테스트 실행 스크립트 (`run_tests.py`)

**사용법:**
```bash
# 테스트 환경 확인
python run_tests.py check

# 테스트 이미지 생성 및 환경 설정
python run_tests.py setup

# 단위 테스트 실행
python run_tests.py unit

# 통합 테스트 실행
python run_tests.py integration

# 전체 테스트 실행
python run_tests.py all

# 빠른 테스트 (느린 테스트 제외)
python run_tests.py fast

# 커버리지 포함 테스트
python run_tests.py coverage
```

## ⚙️ 테스트 설정

### pytest.ini 설정
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
    --durations=10
markers =
    unit: 단위 테스트
    integration: 통합 테스트  
    slow: 느린 테스트 (모델 로딩 등)
    requires_models: 실제 모델 파일이 필요한 테스트
asyncio_mode = auto
```

### conftest.py 주요 기능
- 자동 테스트 환경 설정
- 테스트 이미지 자동 생성
- 공통 픽스처 제공
- 테스트 결과 요약 출력

## 📊 테스트 커버리지

### 현재 테스트 현황
- **총 단위 테스트**: 27개
  - Core 모듈: 14개 ✅
  - Image Utils: 13개 ✅
- **통합 테스트**: 11개
  - API 엔드포인트 테스트 포함
  - 실제 워크플로우 검증

### 커버리지 대상 모듈
- `app.core.*` - 설정, 예외, 로깅
- `app.utils.image_utils` - 이미지 처리
- `app.services.*` - AI 분석 서비스 (부분적)
- `app.models.schemas` - 데이터 모델 검증

## 🔧 테스트 환경 요구사항

### 필수 패키지
```
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov (커버리지 측정용)
PIL (Pillow)
httpx
```

### 환경 변수
- `DEBUG=True` - 테스트 모드 활성화
- `LOG_LEVEL=WARNING` - 테스트 중 로그 최소화

## 🎯 테스트 시나리오

### 1. 로컬 개발 환경
```bash
# 1. 테스트 환경 설정
python run_tests.py setup

# 2. 단위 테스트 실행
python run_tests.py unit

# 3. 전체 테스트 실행
python run_tests.py all
```

### 2. CI/CD 환경
```bash
# 빠른 테스트만 실행 (모델 파일 불필요)
python run_tests.py fast

# 커버리지 포함 테스트
python run_tests.py coverage
```

### 3. 프로덕션 검증
```bash
# 통합 테스트로 전체 워크플로우 검증
python run_tests.py integration
```

## 🚨 알려진 제한사항

### 1. AI 모델 의존성
- 실제 YOLO 모델 파일이 없으면 AI 분석 테스트는 건너뛰기 됨
- Mock을 통한 기본 구조 검증은 가능

### 2. Windows 환경 고려사항
- 이모지 문자 사용 시 cp949 인코딩 오류 발생 가능
- 모든 출력 메시지를 ASCII 호환 텍스트로 구성

### 3. 네트워크 의존성
- S3 다운로드는 Mock으로 처리
- 실제 외부 API 호출은 테스트에 포함되지 않음

## 📈 향후 개선 계획

### 1. 테스트 확장
- [ ] 성능 테스트 추가 (로드 테스트)
- [ ] 보안 테스트 (인증, 인가)
- [ ] API 계약 테스트 (OpenAPI 스키마 검증)

### 2. 자동화 개선
- [ ] GitHub Actions CI/CD 통합
- [ ] 자동 커버리지 리포트
- [ ] 테스트 결과 알림

### 3. 도구 개선
- [ ] 테스트 데이터 생성 도구 고도화
- [ ] 성능 벤치마크 도구
- [ ] 시각적 테스트 리포트

## 🔍 문제 해결

### 일반적인 문제들

**1. 테스트 이미지가 없음**
```bash
python run_tests.py setup
```

**2. 인코딩 오류 (Windows)**
- 모든 출력에서 이모지 문자 제거됨
- UTF-8 환경 변수 설정 권장

**3. 모델 파일 없음**
- 테스트는 자동으로 건너뛰기 됨
- Mock을 통한 기본 검증은 계속 진행

**4. 패키지 의존성 문제**
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov
```

## 📝 테스트 작성 가이드

### 새로운 테스트 추가 시

1. **단위 테스트**: `tests/unit/` 에 추가
2. **통합 테스트**: `tests/integration/` 에 추가
3. **파일 명명 규칙**: `test_*.py`
4. **클래스 명명 규칙**: `Test*`
5. **함수 명명 규칙**: `test_*`

### 테스트 작성 원칙
- 하나의 테스트는 하나의 기능만 검증
- 테스트 간 독립성 보장
- Mock 사용으로 외부 의존성 제거
- 명확한 테스트 이름과 문서화

## 🎉 결론

이 테스트 시스템은 태양광 패널 AI 서비스의 품질을 보장하기 위한 포괄적인 검증 환경을 제공합니다. 단위 테스트부터 통합 테스트까지 다양한 레벨에서 시스템의 안정성과 신뢰성을 검증하며, 개발 생산성을 높이는 자동화된 도구들을 포함하고 있습니다.

---

**마지막 업데이트**: 2025년 8월 14일  
**테스트 시스템 버전**: 3.0.0  
**총 테스트 수**: 27개 단위 테스트 + 11개 통합 테스트

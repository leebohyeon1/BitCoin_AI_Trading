# Firebase Cloud 로깅 설정 가이드

비트코인 자동매매 프로그램은 이제 로컬 파일 시스템뿐만 아니라 Firebase Cloud Firestore를 사용하여 로그를 저장할 수 있습니다. 이 기능을 통해 원격으로 로그를 확인하고, 여러 시스템에서 실행 중인 프로그램의 로그를 중앙 집중식으로 관리할 수 있습니다.

## 설정 방법

### 1. Firebase 프로젝트 생성

1. [Firebase 콘솔](https://console.firebase.google.com/)에 접속하세요.
2. '프로젝트 추가'를 클릭하여 새 프로젝트를 생성합니다.
3. 프로젝트 이름(예: 'bitcoin-ai-trading')을 입력하고 안내에 따라 프로젝트를 생성합니다.
4. 프로젝트가 생성되면, 왼쪽 메뉴에서 'Firestore Database'를 클릭하고 데이터베이스를 생성합니다.

### 2. 서비스 계정 설정

1. Firebase 프로젝트 설정 페이지로 이동합니다.
2. '서비스 계정' 탭을 선택합니다.
3. 'Firebase Admin SDK' 섹션에서 '새 비공개 키 생성'을 클릭합니다.
4. 다운로드된 JSON 파일을 `config/firebase_credentials.json`으로 저장합니다.

### 3. 라이브러리 설치

필요한 라이브러리를 설치합니다:

```bash
pip install -r requirements.txt
```

### 4. 설정 확인

`config/firebase_config.py` 파일에서 다음 설정을 확인합니다:

```python
FIREBASE_CONFIG = {
    "use_firebase": True,
    "credentials_file": "config/firebase_credentials.json",
    "project_id": "bitcoin-ai-trading",  # 자신의 프로젝트 ID로 변경
    ...
}
```

## 로그 확인 방법

### Firebase 콘솔에서 로그 확인

1. [Firebase 콘솔](https://console.firebase.google.com/)에 접속합니다.
2. 해당 프로젝트를 선택합니다.
3. 왼쪽 메뉴에서 'Firestore Database'를 클릭합니다.
4. 다음 컬렉션에서 로그를 확인할 수 있습니다:
   - `app_logs`: 애플리케이션 일반 로그
   - `trade_logs`: 거래 관련 로그
   - `analysis_logs`: 시장 분석 결과 로그
   - `error_logs`: 오류 로그

## 클라우드 로깅 비활성화

클라우드 로깅을 비활성화하려면 다음과 같이 설정합니다:

1. `config/firebase_config.py` 파일에서 `use_firebase` 값을 `False`로 변경합니다.
2. 또는 프로그램 시작 시 Logger 클래스 초기화 시 `use_cloud=False` 파라미터를 전달합니다:

```python
from utils import Logger
logger = Logger(use_cloud=False)
```

## 로그 저장 데이터 구조

각 로그는 다음과 같은 기본 구조로 저장됩니다:

```json
{
  "timestamp": "2025-04-12T14:30:45.123456",  // 로그 생성 시간
  "message": "분석 결과: buy (신뢰도: 0.75)",    // 로그 메시지
  "level": "info",                           // 로그 레벨
  
  // 추가 데이터 (로그 유형에 따라 다름)
  "decision": "buy",
  "confidence": 0.75,
  ...
}
```

## 주의사항

1. Firebase는 일정 사용량까지는 무료이지만, 대량의 로그 데이터를 저장하면 요금이 발생할 수 있습니다.
2. 민감한 정보(예: API 키, 금융 정보)는 로그에 저장하지 않도록 주의하세요.
3. `firebase_credentials.json` 파일에는 중요한 인증 정보가 포함되어 있으므로 안전하게 관리하세요.

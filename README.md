# BitCoin AI Trading

비트코인 자동매매 프로그램입니다. 다양한 기술적 지표와 시장 데이터를 분석하여 업비트에서 비트코인을 자동으로 매매합니다.

## 주요 기능

- 다양한 기술적 지표 분석 (이동평균선, RSI, MACD, 볼린저 밴드 등)
- 시장 데이터 분석 (호가창, 체결 데이터, 김프 등)
- 시장 심리 분석 (공포&탐욕 지수 등)
- Claude AI 통합 (선택 사항)
- 커스터마이징 가능한 매매 전략
- 상세한 거래 로깅 및 분석
- Firebase Cloud Firestore를 통한 클라우드 로깅 (원격 모니터링 지원)

## 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/yourusername/BitCoin_AI_Trading.git
cd BitCoin_AI_Trading
```

### 2. 환경 설정

```bash
pip install -r requirements.txt
```

### 3. 기본 설정 파일 생성

```bash
# .env 파일 생성 (업비트 API 키 입력)
echo "UPBIT_ACCESS_KEY=your_access_key" > .env
echo "UPBIT_SECRET_KEY=your_secret_key" >> .env
echo "CLAUDE_API_KEY=your_claude_api_key" >> .env
echo "ENABLE_TRADE=false" >> .env
```

### 4. 클라우드 로깅 설정 (선택 사항)

클라우드 로깅을 사용하면 로그를 Firebase Cloud Firestore에 저장하여 어디서든 모니터링할 수 있습니다.

```bash
# 간단한 설정 예제
python -m src.utils.cloud_logging_setup --create-sample

# Firebase 설정 확인
python -m src.utils.cloud_logging_setup --check

# Firebase 연결 테스트
python -m src.utils.cloud_logging_setup --test
```

자세한 설정 방법은 `CLOUD_LOGGING.md` 파일을 참조하세요.

## 실행 방법

### 기본 실행

```bash
python -m src.main
```

### 클라우드 로깅 테스트

```bash
python examples/cloud_logging_example.py
```

### 대시보드 실행

```bash
# Windows
dashboard\run_dashboard.bat

# macOS/Linux
cd dashboard && python -m http.server 8000
```

## 구성 파일 설명

- `config/trading_config.py`: 매매 전략 및 지표 가중치 설정
- `config/app_config.py`: 애플리케이션 기본 설정
- `config/firebase_config.py`: 클라우드 로깅 설정
- `.env`: API 키 및 환경 변수

## 커스터마이징

자리한 매매 전략을 구현하고 싶다면 `config/trading_config.py` 파일을 수정하여 지표의 가중치와 현금화 설정 등을 조정하세요.

## 로깅 및 모니터링

### 로컬 로그

- `logs/app.log`: 애플리케이션 로그
- `logs/trade.log`: 매매 로그
- `logs/error.log`: 오류 로그
- `logs/trading_log_YYYYMMDD.json`: 일별 분석 결과 로그
- `logs/trade_history_YYYYMMDD.json`: 일별 거래 기록

### 클라우드 로그

Firebase Firestore에서 다음 콜렉션에서 확인 가능합니다:

- `app_logs`: 애플리케이션 로그
- `trade_logs`: 매매 로그
- `analysis_logs`: 분석 결과 로그
- `error_logs`: 오류 로그

## 문제 해결 및 지원

이슈나 제안은 GitHub 이슈에 등록해주세요.

## 라이센스

MIT License
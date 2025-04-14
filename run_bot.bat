@echo off
@chcp 65001 1>NULL 2>NUL
echo 비트코인 자동매매 프로그램 시작 (AI 모드)
echo 설정된 간격에 따라 매매 분석과 거래가 진행됩니다.
echo.

REM 환경 변수 설정 (.env 파일이 없는 경우 확인)
if not exist ".env" (
  echo API 키 설정이 필요합니다.
  echo .env 파일을 수정하여 API 키를 설정하세요:
  echo.
  echo UPBIT_ACCESS_KEY=여기에_업비트_액세스키_입력
  echo UPBIT_SECRET_KEY=여기에_업비트_시크릿키_입력
  echo CLAUDE_API_KEY=여기에_클로드_API키_입력
  echo ENABLE_TRADE=true
  echo.
  pause
  exit
)

REM 프로그램 실행
echo.
echo 비트코인 자동매매 프로그램을 시작합니다...
echo 설정된 간격: config/trading_config.py에서 확인 가능
echo 종료하려면 CTRL+C를 누르세요.
echo.
python src/main.py

pause
@echo off
@chcp 65001 1>NULL 2>NUL
echo 비트코인 자동매매 프로그램 시작 (이중 간격 모드)
echo 1분마다 일반 분석, 30분마다 AI 분석을 수행합니다.
echo.

REM 환경 변수 설정 (.env 파일이 없는 경우 확인)
if not exist ".env" (
  echo API 키 설정이 필요합니다.
  echo API 키를 수동으로 설정하거나 .env 파일을 만드세요.
  echo 예시: .env 파일에 다음 내용을 입력하세요.
  echo UPBIT_ACCESS_KEY=your_key_here
  echo UPBIT_SECRET_KEY=your_secret_here
  echo CLAUDE_API_KEY=your_claude_key_here
  echo ENABLE_TRADE=false
  pause
  exit
)

REM 프로그램 실행
echo.
echo 비트코인 자동매매 프로그램을 시작합니다...
python src/main_dual.py

pause

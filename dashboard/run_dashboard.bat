@echo off
@chcp 65001 1>NULL 2>NUL
echo 비트코인 자동매매 대시보드 실행
echo.

:: 테스트 데이터 유무 확인
if not exist "..\logs\trading_log_*.json" (
  echo 테스트 데이터가 없습니다. 테스트 데이터를 생성합니다...
  python data-loader.py
)

:: 브라우저로 index.html 열기
echo 대시보드를 웹 브라우저로 엽니다...
start "" index.html

echo.
echo 완료! 브라우저가 자동으로 열리지 않으면 index.html 파일을 직접 열어주세요.
echo.
pause

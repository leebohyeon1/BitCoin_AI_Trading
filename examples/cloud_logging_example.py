#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
클라우드 로깅 사용 예제
Firebase Cloud Firestore를 사용한 로깅 기능 사용법을 보여줍니다.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 경로를 sys.path에 추가하여 모듈을 가져올 수 있도록 설정
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

# utils 모듈 가져오기
from src.utils import Logger
from src.utils import check_firebase_setup

# 클라우드 로깅 설정을 먼저 확인
print("Firebase 설정 확인 중...")
if not check_firebase_setup():
    print("\n[알림] Firebase를 설정하지 않으면 로컬 파일 시스템에만 로그가 저장됩니다.")
    print("Firebase를 설정하려면 CLOUD_LOGGING.md 문서를 참조하세요.")
    use_cloud = False
else:
    use_cloud = True

# 로거 인스턴스 생성 (클라우드 로깅 활성화)
logger = Logger(use_cloud=use_cloud)

# 기본 로그 출력
logger.log_app("클라우드 로깅 예제 시작")

# 앱 로그 (일반 정보)
logger.log_app("시스템 시작", level="info")
logger.log_app(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 추가 데이터가 있는 로그 (클라우드에만 저장됨)
system_info = {
    "os": sys.platform,
    "python_version": sys.version,
    "timestamp": datetime.now().isoformat()
}
logger.log_app("시스템 정보", data=system_info)

# 거래 로그 예제
for i in range(3):
    # 가상의 거래 데이터
    trade_data = {
        "trade_id": f"trade_{i}",
        "ticker": "KRW-BTC",
        "type": "buy" if i % 2 == 0 else "sell", 
        "price": 50000000 + (i * 100000),  # 가상 가격
        "amount": 0.01,
        "timestamp": datetime.now().isoformat()
    }
    
    # 거래 로그 기록
    action = "매수" if trade_data["type"] == "buy" else "매도"
    logger.log_trade(
        f"{action} 주문 실행: {trade_data['ticker']} {trade_data['amount']} BTC @ {trade_data['price']:,}원", 
        data=trade_data
    )
    
    time.sleep(1)  # 로그 간 시간차를 위한 지연

# 에러 로그 예제
try:
    # 의도적 오류 발생
    result = 10 / 0
except Exception as e:
    error_data = {
        "error_type": type(e).__name__,
        "location": "cloud_logging_example.py:70",
        "timestamp": datetime.now().isoformat()
    }
    logger.log_error(f"계산 오류 발생: {str(e)}", data=error_data)

# 완료 메시지 출력
logger.log_app("클라우드 로깅 예제 완료")

print(f"\n로그 생성 완료!")
print(f"로컬 로그 파일: {project_root}/logs/")
if use_cloud:
    print("클라우드 로그: Firebase Firestore 콘솔에서 확인하세요.")
    print("컬렉션: app_logs, trade_logs, error_logs")
else:
    print("클라우드 로깅이 비활성화되어 로컬 로그 파일만 생성되었습니다.")

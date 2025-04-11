#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
데이터 로더 스크립트
대시보드 테스트를 위해 가상의 거래 데이터를 생성합니다.
"""

import os
import json
import random
from datetime import datetime, timedelta
import argparse

def generate_test_data(days=7, base_dir='../logs'):
    """
    테스트용 거래 데이터 생성
    
    Args:
        days: 생성할 날짜 수
        base_dir: 로그 디렉토리 경로
    """
    # 로그 디렉토리 확인
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    # 현재 날짜
    now = datetime.now()
    
    # 일자별 데이터 생성
    for i in range(days):
        # 날짜 계산 (최근 날짜부터)
        date = now - timedelta(days=i)
        date_str = date.strftime("%Y%m%d")
        
        # 트레이딩 로그 파일 경로
        log_file = f"{base_dir}/trading_log_{date_str}.json"
        
        # 이미 파일이 있으면 건너뜀
        if os.path.exists(log_file):
            print(f"{log_file} 파일이 이미 존재합니다.")
            continue
        
        # 하루 동안의 로그 생성 (4시간 간격으로 6개)
        logs = []
        
        # 시작 가격 (약 5천만원 전후)
        base_price = random.randint(48000000, 52000000)
        
        for j in range(6):
            hour = j * 4
            log_time = date.replace(hour=hour, minute=0, second=0)
            
            # 가격 변동 (이전 가격 기준 -2%~+2%)
            price_change_pct = random.uniform(-0.02, 0.02)
            current_price = base_price * (1 + price_change_pct)
            base_price = current_price  # 다음 로그의 기준 가격
            
            # 무작위 신호 생성
            buy_count = random.randint(1, 5)
            sell_count = random.randint(1, 5)
            hold_count = random.randint(3, 8)
            
            # 실제 결정 (가장 많은 신호 또는 무작위)
            if buy_count > sell_count and buy_count > hold_count:
                decision = "buy"
                decision_kr = "매수"
                confidence = random.uniform(0.6, 0.9)
            elif sell_count > buy_count and sell_count > hold_count:
                decision = "sell"
                decision_kr = "매도"
                confidence = random.uniform(0.6, 0.9)
            else:
                decision = "hold"
                decision_kr = "홀드"
                confidence = random.uniform(0.4, 0.6)
            
            # 신호 목록 생성
            signals = []
            
            # 기술적 지표 신호
            indicators = [
                "이동평균선(MA)", "장기추세(MA60)", "볼린저밴드(BB)",
                "RSI(상대강도지수)", "MACD", "스토캐스틱",
                "호가창(매수/매도비율)", "체결데이터", "김프(한국 프리미엄)",
                "시장심리(공포&탐욕지수)"
            ]
            
            # 지표별 무작위 신호 생성
            for indicator in indicators:
                # 신호 종류
                if random.random() < 0.33:
                    signal = "buy"
                    strength = random.uniform(0.3, 0.8)
                    if indicator == "RSI(상대강도지수)":
                        description = f"과매도 상태 (RSI: {random.uniform(10, 30):.1f} < 30)"
                    elif indicator == "MACD":
                        description = "MACD 골든크로스 발생"
                    else:
                        description = "매수 신호"
                elif random.random() < 0.5:
                    signal = "sell"
                    strength = random.uniform(0.3, 0.8)
                    if indicator == "RSI(상대강도지수)":
                        description = f"과매수 상태 (RSI: {random.uniform(70, 90):.1f} > 70)"
                    elif indicator == "MACD":
                        description = "MACD 데드크로스 발생"
                    else:
                        description = "매도 신호"
                else:
                    signal = "hold"
                    strength = random.uniform(0, 0.3)
                    if indicator == "RSI(상대강도지수)":
                        description = f"중립적 (RSI: {random.uniform(40, 60):.1f})"
                    elif indicator == "MACD":
                        description = "MACD 중립적 상태"
                    else:
                        description = "중립 신호"
                
                # 지표별 가중치 (임의 설정)
                weight = 1.0
                if indicator in ["RSI(상대강도지수)", "MACD"]:
                    weight = 1.2
                elif indicator in ["호가창(매수/매도비율)", "체결데이터", "김프(한국 프리미엄)"]:
                    weight = 0.8
                
                signals.append({
                    "source": indicator,
                    "signal": signal,
                    "strength": strength,
                    "description": description,
                    "weight": weight
                })
            
            # 로그 항목 생성
            log_entry = {
                "timestamp": log_time.strftime("%Y-%m-%d %H:%M:%S"),
                "decision": decision,
                "decision_kr": decision_kr,
                "confidence": confidence,
                "avg_signal_strength": random.uniform(0, 0.3),
                "signals": signals,
                "signal_counts": {
                    "buy": buy_count,
                    "sell": sell_count,
                    "hold": hold_count
                },
                "current_price": [
                    {
                        "market": "KRW-BTC",
                        "trade_price": current_price,
                        "signed_change_rate": price_change_pct
                    }
                ],
                "price_change_24h": f"{price_change_pct * 100:.2f}%"
            }
            
            logs.append(log_entry)
        
        # 로그 파일 저장
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        
        print(f"{log_file} 파일 생성 완료")
        
        # 거래 기록 생성 (일부 날짜에만)
        if random.random() < 0.3 or i == 0:  # 30% 확률 또는 가장 최근 날짜
            generate_trade_history(date, base_dir)

def generate_trade_history(date, base_dir):
    """
    거래 기록 생성
    
    Args:
        date: 날짜
        base_dir: 로그 디렉토리 경로
    """
    date_str = date.strftime("%Y%m%d")
    trade_file = f"{base_dir}/trade_history_{date_str}.json"
    
    # 이미 파일이 있으면 건너뜀
    if os.path.exists(trade_file):
        print(f"{trade_file} 파일이 이미 존재합니다.")
        return
    
    # 거래 기록 (0~3개)
    trades = []
    trade_count = random.randint(0, 3)
    
    for i in range(trade_count):
        # 거래 시간
        hour = random.randint(9, 21)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        trade_time = date.replace(hour=hour, minute=minute, second=second)
        
        # 거래 종류
        trade_type = "buy" if random.random() < 0.5 else "sell"
        
        # 거래 금액 및 수량
        price = random.randint(48000000, 52000000)  # 현재가
        
        if trade_type == "buy":
            amount = random.uniform(0.001, 0.01)  # 매수량 (BTC)
            total = price * amount
        else:
            total = random.uniform(100000, 1000000)  # 매도 금액
            amount = total / price
        
        # 거래 기록 생성
        trade = {
            "type": trade_type,
            "ticker": "KRW-BTC",
            "price": price,
            "amount": amount,
            "total": total,
            "timestamp": trade_time.strftime("%Y-%m-%d %H:%M:%S"),
            "confidence": random.uniform(0.5, 0.9),
            "order_id": f"uuid-{random.randint(100000, 999999)}"
        }
        
        trades.append(trade)
    
    # 거래 기록 파일 저장 (거래가 있는 경우에만)
    if trades:
        with open(trade_file, 'w', encoding='utf-8') as f:
            json.dump(trades, f, ensure_ascii=False, indent=2)
        
        print(f"{trade_file} 파일 생성 완료 (거래 {len(trades)}건)")

def generate_error_log(base_dir='../logs'):
    """
    에러 로그 생성 (이미 있으면 건너뜀)
    """
    error_log_file = f"{base_dir}/error.log"
    
    if os.path.exists(error_log_file):
        print(f"{error_log_file} 파일이 이미 존재합니다.")
        return
    
    # 현재 날짜
    now = datetime.now()
    
    # 에러 메시지 목록
    error_messages = [
        "트레이딩 작업 오류: 'NoneType' object is not subscriptable",
        "API 호출 오류: Timeout waiting for response",
        "데이터 처리 오류: Invalid JSON response",
        "거래소 연결 오류: Connection refused",
        "인증 오류: Invalid API credentials",
    ]
    
    # 에러 로그 생성 (3개)
    with open(error_log_file, 'w', encoding='utf-8') as f:
        for i in range(3):
            error_time = now - timedelta(hours=i*8)
            error_msg = random.choice(error_messages)
            log_line = f"{error_time.strftime('%Y-%m-%d %H:%M:%S')},123 - error - ERROR - {error_msg}\n"
            f.write(log_line)
    
    print(f"{error_log_file} 파일 생성 완료")

def generate_trade_log(base_dir='../logs'):
    """
    거래 로그 생성 (이미 있으면 건너뜀)
    """
    trade_log_file = f"{base_dir}/trade.log"
    
    if os.path.exists(trade_log_file):
        print(f"{trade_log_file} 파일이 이미 존재합니다.")
        return
    
    # 현재 날짜
    now = datetime.now()
    
    # 거래 메시지 목록
    trade_messages = [
        "거래 실행: KRW-BTC 100000원 매수 시도",
        "거래 성공: KRW-BTC 0.002 BTC 매수 완료",
        "거래 실행: KRW-BTC 0.001 BTC 매도 시도",
        "거래 성공: KRW-BTC 0.001 BTC 매도 완료",
        "거래 결과: {'status': 'success', 'action': 'buy', 'amount': 100000, 'price': 50000000, 'message': 'KRW-BTC 100000원 매수 완료'}",
        "거래 결과: {'status': 'error', 'message': '거래 실행 오류: 최소 주문 금액 미달'}"
    ]
    
    # 거래 로그 생성 (5개)
    with open(trade_log_file, 'w', encoding='utf-8') as f:
        for i in range(5):
            trade_time = now - timedelta(hours=i*6)
            trade_msg = random.choice(trade_messages)
            log_line = f"{trade_time.strftime('%Y-%m-%d %H:%M:%S')},123 - trade - INFO - {trade_msg}\n"
            f.write(log_line)
    
    print(f"{trade_log_file} 파일 생성 완료")

def generate_app_log(base_dir='../logs'):
    """
    앱 로그 생성 (이미 있으면 건너뜀)
    """
    app_log_file = f"{base_dir}/app.log"
    
    if os.path.exists(app_log_file):
        print(f"{app_log_file} 파일이 이미 존재합니다.")
        return
    
    # 현재 날짜
    now = datetime.now()
    
    # 앱 메시지 목록
    app_messages = [
        "비트코인 자동매매 프로그램 시작",
        "시장 데이터 업데이트: KRW-BTC",
        "분석 결과: buy (신뢰도: 0.72)",
        "분석 결과: sell (신뢰도: 0.68)",
        "분석 결과: hold (신뢰도: 0.44)",
        "현재가: 50,123,000원",
        "트레이딩 스케줄러 시작 (간격: 60분)"
    ]
    
    # 앱 로그 생성 (7개)
    with open(app_log_file, 'w', encoding='utf-8') as f:
        for i in range(7):
            app_time = now - timedelta(hours=i*4)
            app_msg = app_messages[i] if i < len(app_messages) else random.choice(app_messages)
            log_line = f"{app_time.strftime('%Y-%m-%d %H:%M:%S')},123 - app - INFO - {app_msg}\n"
            f.write(log_line)
    
    print(f"{app_log_file} 파일 생성 완료")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='비트코인 자동매매 테스트 데이터 생성')
    parser.add_argument('--days', type=int, default=7, help='생성할 일수 (기본: 7일)')
    parser.add_argument('--dir', type=str, default='../logs', help='로그 디렉토리 경로 (기본: ../logs)')
    
    args = parser.parse_args()
    
    print(f"테스트 데이터 생성 시작 ({args.days}일치, 경로: {args.dir})")
    
    # 로그 데이터 생성
    generate_test_data(args.days, args.dir)
    generate_error_log(args.dir)
    generate_trade_log(args.dir)
    generate_app_log(args.dir)
    
    print("테스트 데이터 생성 완료")

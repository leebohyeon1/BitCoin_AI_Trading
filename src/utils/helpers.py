import os
import json
import yaml
import time
from datetime import datetime, timedelta

def load_config(config_file="config/trading_config.py"):
    """
    설정 파일 로드
    
    Args:
        config_file: 설정 파일 경로
        
    Returns:
        dict: 설정 정보
    """
    config = {}
    
    # 베이스 설정 파일 로드
    if config_file.endswith(".py"):
        with open(config_file, "r", encoding="utf-8") as f:
            exec(f.read(), config)
        
        # __builtins__ 등 불필요한 항목 제거
        for key in list(config.keys()):
            if key.startswith("__"):
                del config[key]
    
    # JSON 설정 파일 로드
    elif config_file.endswith(".json"):
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    
    # YAML 설정 파일 로드
    elif config_file.endswith((".yaml", ".yml")):
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    
    return config

def format_currency(amount, currency="KRW"):
    """
    통화 형식으로 포맷팅
    
    Args:
        amount: 금액
        currency: 통화 코드 (기본: KRW)
        
    Returns:
        str: 포맷팅된 금액
    """
    if currency == "KRW":
        return f"{amount:,.0f}원"
    elif currency == "BTC":
        return f"{amount:.8f} BTC"
    else:
        return f"{amount:,.2f} {currency}"

def calculate_profit(buy_price, sell_price, amount, fee_rate=0.0005):
    """
    매매 수익 계산
    
    Args:
        buy_price: 매수 가격
        sell_price: 매도 가격
        amount: 거래 수량
        fee_rate: 거래 수수료율 (기본: 0.05%)
        
    Returns:
        tuple: (수익금, 수익률)
    """
    # 매수 금액
    buy_amount = buy_price * amount
    buy_fee = buy_amount * fee_rate
    
    # 매도 금액
    sell_amount = sell_price * amount
    sell_fee = sell_amount * fee_rate
    
    # 순수익
    profit = sell_amount - buy_amount - buy_fee - sell_fee
    
    # 수익률
    profit_rate = (profit / buy_amount) * 100
    
    return profit, profit_rate

def send_notification(title, message, notification_config=None):
    """
    알림 발송 (예: 텔레그램, 이메일 등)
    
    Args:
        title: 알림 제목
        message: 알림 내용
        notification_config: 알림 설정
        
    Returns:
        bool: 성공 여부
    """
    if not notification_config:
        return False
    
    # 텔레그램 알림
    if notification_config.get("telegram", {}).get("enabled", False):
        try:
            import telegram
            
            bot_token = notification_config["telegram"]["bot_token"]
            chat_id = notification_config["telegram"]["chat_id"]
            
            bot = telegram.Bot(token=bot_token)
            bot.send_message(chat_id=chat_id, text=f"*{title}*\n{message}", parse_mode="Markdown")
            
            return True
        except Exception as e:
            print(f"텔레그램 알림 발송 실패: {e}")
            return False
    
    return False

def retry(func, retries=3, delay=1):
    """
    함수 실행 재시도 데코레이터
    
    Args:
        func: 실행할 함수
        retries: 재시도 횟수
        delay: 재시도 간격 (초)
        
    Returns:
        함수 실행 결과
    """
    def wrapper(*args, **kwargs):
        for attempt in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == retries - 1:
                    raise
                
                print(f"함수 실행 실패 ({attempt+1}/{retries}): {e}")
                time.sleep(delay)
    
    return wrapper

def get_korean_market_hours():
    """
    한국 주식 거래 시간 조회
    
    Returns:
        tuple: (시작 시간, 종료 시간)
    """
    now = datetime.now()
    
    # 오전 9시 ~ 오후 3시 30분
    start_time = datetime(now.year, now.month, now.day, 9, 0, 0)
    end_time = datetime(now.year, now.month, now.day, 15, 30, 0)
    
    # 주말 체크
    if now.weekday() >= 5:  # 5: 토요일, 6: 일요일
        return None, None
    
    return start_time, end_time

def is_korean_market_open():
    """
    한국 주식 거래 시간 여부 확인
    
    Returns:
        bool: 거래 시간이면 True, 아니면 False
    """
    start_time, end_time = get_korean_market_hours()
    
    if not start_time or not end_time:
        return False
    
    now = datetime.now()
    return start_time <= now <= end_time
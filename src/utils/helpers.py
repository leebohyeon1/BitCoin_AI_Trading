import os
import json
import yaml
import time
from datetime import datetime, timedelta

def load_config(config_file="config/trading_config.py"):
    """
    ���� ���� �ε�
    
    Args:
        config_file: ���� ���� ���
        
    Returns:
        dict: ���� ����
    """
    config = {}
    
    # ���̽� ���� ���� �ε�
    if config_file.endswith(".py"):
        with open(config_file, "r", encoding="utf-8") as f:
            exec(f.read(), config)
        
        # __builtins__ �� ���ʿ��� �׸� ����
        for key in list(config.keys()):
            if key.startswith("__"):
                del config[key]
    
    # JSON ���� ���� �ε�
    elif config_file.endswith(".json"):
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    
    # YAML ���� ���� �ε�
    elif config_file.endswith((".yaml", ".yml")):
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    
    return config

def format_currency(amount, currency="KRW"):
    """
    ��ȭ �������� ������
    
    Args:
        amount: �ݾ�
        currency: ��ȭ �ڵ� (�⺻: KRW)
        
    Returns:
        str: �����õ� �ݾ�
    """
    if currency == "KRW":
        return f"{amount:,.0f}��"
    elif currency == "BTC":
        return f"{amount:.8f} BTC"
    else:
        return f"{amount:,.2f} {currency}"

def calculate_profit(buy_price, sell_price, amount, fee_rate=0.0005):
    """
    �Ÿ� ���� ���
    
    Args:
        buy_price: �ż� ����
        sell_price: �ŵ� ����
        amount: �ŷ� ����
        fee_rate: �ŷ� �������� (�⺻: 0.05%)
        
    Returns:
        tuple: (���ͱ�, ���ͷ�)
    """
    # �ż� �ݾ�
    buy_amount = buy_price * amount
    buy_fee = buy_amount * fee_rate
    
    # �ŵ� �ݾ�
    sell_amount = sell_price * amount
    sell_fee = sell_amount * fee_rate
    
    # ������
    profit = sell_amount - buy_amount - buy_fee - sell_fee
    
    # ���ͷ�
    profit_rate = (profit / buy_amount) * 100
    
    return profit, profit_rate

def send_notification(title, message, notification_config=None):
    """
    �˸� ���� (��: �ڷ��׷�, �̸��� ��)
    
    Args:
        title: �˸� ����
        message: �˸� ����
        notification_config: �˸� ����
        
    Returns:
        bool: ���� ����
    """
    if not notification_config:
        return False
    
    # �ڷ��׷� �˸�
    if notification_config.get("telegram", {}).get("enabled", False):
        try:
            import telegram
            
            bot_token = notification_config["telegram"]["bot_token"]
            chat_id = notification_config["telegram"]["chat_id"]
            
            bot = telegram.Bot(token=bot_token)
            bot.send_message(chat_id=chat_id, text=f"*{title}*\n{message}", parse_mode="Markdown")
            
            return True
        except Exception as e:
            print(f"�ڷ��׷� �˸� ���� ����: {e}")
            return False
    
    return False

def retry(func, retries=3, delay=1):
    """
    �Լ� ���� ��õ� ���ڷ�����
    
    Args:
        func: ������ �Լ�
        retries: ��õ� Ƚ��
        delay: ��õ� ���� (��)
        
    Returns:
        �Լ� ���� ���
    """
    def wrapper(*args, **kwargs):
        for attempt in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == retries - 1:
                    raise
                
                print(f"�Լ� ���� ���� ({attempt+1}/{retries}): {e}")
                time.sleep(delay)
    
    return wrapper

def get_korean_market_hours():
    """
    �ѱ� ���� �ŷ� �ð� ��ȸ
    
    Returns:
        tuple: (���� �ð�, ���� �ð�)
    """
    now = datetime.now()
    
    # ���� 9�� ~ ���� 3�� 30��
    start_time = datetime(now.year, now.month, now.day, 9, 0, 0)
    end_time = datetime(now.year, now.month, now.day, 15, 30, 0)
    
    # �ָ� üũ
    if now.weekday() >= 5:  # 5: �����, 6: �Ͽ���
        return None, None
    
    return start_time, end_time

def is_korean_market_open():
    """
    �ѱ� ���� �ŷ� �ð� ���� Ȯ��
    
    Returns:
        bool: �ŷ� �ð��̸� True, �ƴϸ� False
    """
    start_time, end_time = get_korean_market_hours()
    
    if not start_time or not end_time:
        return False
    
    now = datetime.now()
    return start_time <= now <= end_time
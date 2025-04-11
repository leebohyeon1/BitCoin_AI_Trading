# ?��?��리�???��?�� 기본 ?��?��
APP_CONFIG = {
    "app_name": "BitCoin AI Trading",
    "version": "1.0.0",
    "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "log_directory": "logs",
    "data_directory": "data",
    "timezone": "Asia/Seoul",
}

# 거래?�� ?��?��
EXCHANGE_CONFIG = {
    "default_exchange": "upbit",
    "default_market": "KRW-BTC",  # 기본 마켓 (BTC/KRW)
    "available_markets": [
        "KRW-BTC",  # 비트코인
        "KRW-ETH",  # ?��?��리�??
        "KRW-XRP",  # 리플
    ],
    "request_timeout": 10,  # API ?���? ????��?��?�� (�?)
    "max_retries": 3,       # ?��?�� ?�� ?��?��?�� ?��?��
}

# ?��?��?�� ?���? ?��?��
DATA_CONFIG = {
    "default_interval": "minute60",  # 기본 차트 간격 (1?���?)
    "available_intervals": [
        "minute1", 
        "minute3", 
        "minute5", 
        "minute10", 
        "minute15", 
        "minute30", 
        "minute60", 
        "minute240", 
        "day", 
        "week", 
        "month"
    ],
    "candle_count": 200,  # 분석?�� ?��?��?�� 캔들 ?��
    "update_interval": 60,  # ?��?��?�� ?��?��?��?�� 주기 (�?)
}

# 백테?��?�� ?��?��
BACKTEST_CONFIG = {
    "enabled": False,
    "start_date": "2024-01-01",
    "end_date": "2024-04-10",
    "initial_balance": 1000000,  # 백테?��?�� 초기 ?���? (1,000,000?��)
    "fee_rate": 0.0005,  # 거래 ?��?��료율 (0.05%)
}

# 애플리케이션 기본 설정
APP_CONFIG = {
    "app_name": "BitCoin AI Trading",
    "version": "1.0.0",
    "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "log_directory": "logs",
    "data_directory": "data",
    "timezone": "Asia/Seoul",
}

# 거래소 설정
EXCHANGE_CONFIG = {
    "default_exchange": "upbit",
    "default_market": "KRW-BTC",  # 기본 마켓 (BTC/KRW)
    "available_markets": [
        "KRW-BTC",  # 비트코인
        "KRW-ETH",  # 이더리움
        "KRW-XRP",  # 리플
    ],
    "request_timeout": 10,  # API 요청 타임아웃 (초)
    "max_retries": 3,       # 요청 시 재시도 횟수
}

# 데이터 관련 설정
DATA_CONFIG = {
    "default_interval": "minute60",  # 기본 차트 간격 (1시간)
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
    "candle_count": 200,  # 분석에 사용할 캔들 수
    "update_interval": 60,  # 데이터 업데이트 주기 (초)
}

# 이중 간격 모드 설정
DUAL_TRADING_CONFIG = {
    "normal_interval_seconds": 10,  # 일반 분석 간격 (초)
    "ai_interval_minutes": 30,     # AI 분석 간격 (분)
    "log_regular_analysis": False,  # 일반 분석 로그 상세 출력 여부
    "log_ai_analysis": True        # AI 분석 로그 상세 출력 여부
}

# 백테스팅 설정
BACKTEST_CONFIG = {
    "enabled": False,
    "start_date": "2024-01-01",
    "end_date": "2024-04-10",
    "initial_balance": 1000000,  # 백테스팅 초기 자금 (1,000,000원)
    "fee_rate": 0.0005,  # 거래 수수료율 (0.05%)
}
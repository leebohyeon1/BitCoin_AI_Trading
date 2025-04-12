# 비트코인 자동매매 설정 파일
# 사용자가 원하는 대로 수치를 조정하여 매매 전략을 개인화할 수 있습니다.

# 기본 매매 결정 임계값 설정
DECISION_THRESHOLDS = {
    "buy_threshold": 0.15,    # 평균 신호가 이 값보다 크면 매수 (기본값: 0.2)
    "sell_threshold": -0.15,  # 평균 신호가 이 값보다 작으면 매도 (기본값: -0.2)
}

# 투자 비율 설정
INVESTMENT_RATIOS = {
    "min_ratio": 0.2,  # 최소 투자 비율 (보유 자산의 %) (기본값: 0.2)
    "max_ratio": 0.7,  # 최대 투자 비율 (보유 자산의 %) (기본값: 0.5)
}

# 기술적 지표별 신호 강도 설정
# 값 범위: 0.0 ~ 1.0 (높을수록 해당 지표의 영향력이 커짐)
SIGNAL_STRENGTHS = {
    # 이동평균선 관련
    "ma_crossover": 0.6,     # 이동평균선 골든크로스/데드크로스 (기본값: 0.6)
    "ma_long_trend": 0.4,    # 장기 이동평균선(MA60) 추세 (기본값: 0.4)
    
    # 볼린저 밴드 관련
    "bb_extreme": 0.7,       # 볼린저 밴드 상/하단 돌파 (기본값: 0.7)
    "bb_middle": 0.3,        # 볼린저 밴드 내부 위치 (기본값: 0.3)
    
    # RSI 관련
    "rsi_extreme": 0.8,      # RSI 과매수/과매도 (기본값: 0.8)
    "rsi_middle": 0.2,       # RSI 중간 영역 (기본값: 0.2)
    
    # MACD 관련
    "macd_crossover": 0.7,   # MACD 골든크로스/데드크로스 (기본값: 0.7)
    "macd_trend": 0.3,       # MACD 추세 유지 (기본값: 0.3)
    
    # 스토캐스틱 관련
    "stoch_extreme": 0.6,    # 스토캐스틱 과매수/과매도 (기본값: 0.6)
    "stoch_middle": 0.3,     # 스토캐스틱 중간 반전 신호 (기본값: 0.3)
    
    # 기타 지표 관련
    "orderbook": 0.6,        # 호가창 매수/매도 비율 (기본값: 0.6)
    "trade_data": 0.5,       # 체결 데이터 분석 (기본값: 0.5)
    "korea_premium": 0.5,    # 김프(한국 프리미엄) (기본값: 0.5)
    "fear_greed_extreme": 0.7, # 극단적 공포/탐욕 (기본값: 0.7)
    "fear_greed_middle": 0.4,  # 보통 수준 공포/탐욕 (기본값: 0.4)
    "onchain_sopr": 0.6,     # 온체인 SOPR 지표 (기본값: 0.6)
    "onchain_active_addr": 0.4, # 온체인 활성 주소 (기본값: 0.4)
}

# 지표 가중치 설정 (각 지표의 중요도, 합이 1이 되도록 설정 권장)
# 중요하다고 생각하는 지표에 더 높은 가중치 부여
INDICATOR_WEIGHTS = {
    "MA": 1.2,           # 이동평균선
    "MA60": 1.0,         # 장기 이동평균선
    "BB": 1.2,           # 볼린저 밴드
    "RSI": 1.5,          # RSI (상대강도지수) - 중요도 높음
    "MACD": 1.5,         # MACD - 중요도 높음
    "Stochastic": 1.0,   # 스토캐스틱
    "Orderbook": 0.8,    # 호가창 분석
    "Trades": 0.8,       # 체결 데이터
    "KIMP": 1.0,         # 김프(한국 프리미엄)
    "FearGreed": 1.2,    # 공포&탐욕 지수
    "SOPR": 0.7,         # 온체인 SOPR
    "ActiveAddr": 0.6    # 온체인 활성 주소
}

# 지표 사용 여부 설정 (True: 사용, False: 미사용)
# 사용하지 않을 지표는 False로 설정하여 분석에서 제외
INDICATOR_USAGE = {
    "MA": True,          # 이동평균선
    "MA60": True,        # 장기 이동평균선
    "BB": True,          # 볼린저 밴드
    "RSI": True,         # RSI (상대강도지수)
    "MACD": True,        # MACD
    "Stochastic": True,  # 스토캐스틱
    "Orderbook": True,   # 호가창 분석
    "Trades": True,      # 체결 데이터
    "KIMP": True,        # 김프(한국 프리미엄)
    "FearGreed": True,   # 공포&탐욕 지수
    "SOPR": True,        # 온체인 SOPR
    "ActiveAddr": True   # 온체인 활성 주소
}

# 매매 관련 추가 설정
TRADING_SETTINGS = {
    "min_order_amount": 5000,  # 최소 주문 금액 (원) (기본값: 5000)
    "max_slippage": 0.005,     # 최대 허용 슬리피지 (주문가 대비 %) (기본값: 0.5%)
    "trading_interval": 1,    # 매매 분석 간격 (분) (기본값: 60)
    "trading_hours": {         # 매매 허용 시간대 (24시간제)
        "enabled": False,      # 시간대 제한 사용 여부
        "start_hour": 9,       # 매매 시작 시간 (예: 오전 9시)
        "end_hour": 23,        # 매매 종료 시간 (예: 오후 11시)
    }
}

# Claude AI 관련 설정
CLAUDE_SETTINGS = {
    "use_claude": False,       # Claude AI 분석 사용 여부
    "weight": 1.5,             # Claude AI 분석 결과 가중치
    "confidence_boost": 0.1,   # 일치 시 신뢰도 상승 값 (기본값: 0.1)
}

# 이전 거래 이력 참고 설정
HISTORICAL_SETTINGS = {
    "use_historical_data": True,  # 이전 거래 이력 참고 여부
    "history_length": 10,           # 참고할 이전 거래 수
    "avoid_repeated_signals": True, # 연속 동일 신호 발생 시 강도 감소
}

# 알림 설정
NOTIFICATION_SETTINGS = {
    "enable_notifications": True,  # 알림 기능 사용 여부
    "notify_on_trade": True,        # 실제 거래 발생 시 알림
    "notify_on_signal": True,       # 강한 매매 신호 발생 시 알림
    "notify_on_error": True,        # 오류 발생 시 알림
    "min_signal_strength_for_notification": 0.7  # 알림 발생 최소 신호 강도
}

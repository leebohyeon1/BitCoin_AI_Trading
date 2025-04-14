# 비트코인 자동매매 설정 파일
# 사용자가 원하는 대로 수치를 조정하여 매매 전략을 개인화할 수 있습니다.

# 기본 매매 결정 임계값 설정
DECISION_THRESHOLDS = {
    "buy_threshold": 0.05,    # 평균 신호가 이 값보다 크면 매수 (AI가 권장하는 대로 매수하기 위해 낮게 설정)
    "sell_threshold": -0.05,  # 평균 신호가 이 값보다 작으면 매도 (AI가 권장하는 대로 매도하기 위해 높게 설정)
}

# 투자 비율 설정
INVESTMENT_RATIOS = {
    "min_ratio": 0.2,  # 최소 투자 비율 (보유 자산의 %) (기본값: 0.2)
    "max_ratio": 0.7,  # 최대 투자 비율 (보유 자산의 %) (기본값: 0.5)
}

# 기술적 지표별 신호 강도 설정 (손해를 적게 보고 수익은 많이 내는 방향으로 최적화)
# 값 범위: 0.0 ~ 1.0 (높을수록 해당 지표의 영향력이 커짐)
SIGNAL_STRENGTHS = {
    # 이동평균선 관련 - 추세 추종형 지표라 반응이 느림
    "ma_crossover": 0.45,     # 이동평균선 골든크로스/데드크로스 (매수 신호보다 매도 신호에 더 반응)
    "ma_long_trend": 0.30,    # 장기 이동평균선(MA60) 추세 (약한 신호로 조정)
    
    # 볼린저 밴드 관련 - 반전 신호 파악에 유용
    "bb_extreme": 0.75,       # 볼린저 밴드 상/하단 돌파 (특히 상단 돌파 시 매도 강화)
    "bb_middle": 0.30,        # 볼린저 밴드 내부 위치
    
    # RSI 관련 - 과매수 신호 감지에 높은 가중치 부여하여 손실 방지
    "rsi_extreme": 0.90,      # RSI 과매수/과매도 (특히 과매수 상태 감지에 강화)
    "rsi_middle": 0.35,       # RSI 중간 영역 (약한 신호지만 중요도 증가)
    
    # MACD 관련 - 추세 전환 감지에 효과적
    "macd_crossover": 0.85,   # MACD 골든크로스/데드크로스 (특히 데드크로스 감지 강화)
    "macd_trend": 0.40,       # MACD 추세 유지 (추세 유지 신호 강화)
    
    # 스토캐스틱 관련 - 가격 반전 감지
    "stoch_extreme": 0.70,    # 스토캐스틱 과매수/과매도 (특히 과매수 상태 감지에 강화)
    "stoch_middle": 0.30,     # 스토캐스틱 중간 반전 신호
    
    # 기타 지표 관련
    "orderbook": 0.65,        # 호가창 매수/매도 비율 (단기 시장 심리 반영)
    "trade_data": 0.50,       # 체결 데이터 분석 (매도 체결 압력 감지에 중요)
    "korea_premium": 0.50,    # 김프(한국 프리미엄) (한국 시장 특성 반영)
    "fear_greed_extreme": 0.85, # 극단적 공포/탐욕 (특히 '극단적 탐욕' 상태 감지 강화)
    "fear_greed_middle": 0.50,  # 보통 수준 공포/탐욕
    "onchain_sopr": 0.60,     # 온체인 SOPR 지표 (약화)
    "onchain_active_addr": 0.45 # 온체인 활성 주소 (약화)
}

# 지표 가중치 설정 (손해를 적게 보고 수익은 많이 내는 방향으로 최적화)
# AI 분석과 비교했을 때 참고 자료로만 활용되도록 가중치 조정
INDICATOR_WEIGHTS = {
    "MA": 0.8,           # 이동평균선 (추세 추종 성격이 강해 지연되는 경향이 있음)
    "MA60": 0.7,         # 장기 이동평균선 (현재는 참고용으로만 활용)
    "BB": 1.3,           # 볼린저 밴드 (반전 포인트 감지에 유용)
    "RSI": 1.5,          # RSI (매도 시그널 감지에 높은 가중치 부여하여 손실 최소화)
    "MACD": 1.5,         # MACD (추세 확인과 반전 지점 감지)
    "Stochastic": 1.3,   # 스토캐스틱 (과매수/과매도 신호 포착에 유용)
    "Orderbook": 1.1,    # 호가창 분석 (실시간 수요 공급 확인)
    "Trades": 0.9,       # 체결 데이터 (단기 노이즈가 많아 가중치 낮춤)
    "KIMP": 1.2,         # 김프(한국 프리미엄) (한국 시장 특성 반영)
    "FearGreed": 1.4,    # 공포&탐욕 지수 (매수/매도 타이밍에 효과적)
    "SOPR": 0.6,         # 온체인 SOPR (참고용)
    "ActiveAddr": 0.5    # 온체인 활성 주소 (참고용)
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
    "trading_interval": 5,    # 매매 분석 간격 (분) (더 빈번한 매매를 위해 10분으로 단축)
    "trade_cooldown_minutes": 5, # 거래 후 쿨다운 시간 (분) (더 빈번한 매매를 위해 5분으로 단축)
    "trading_hours": {         # 매매 허용 시간대 (24시간제)
        "enabled": False,      # 시간대 제한 사용 여부 (24시간 매매 가능)
        "start_hour": 0,       # 매매 시작 시간 (0시)
        "end_hour": 23,        # 매매 종료 시간 (23시)
    }
}

# Claude AI 관련 설정
CLAUDE_SETTINGS = {
    "use_claude": True,        # Claude AI 분석 사용 여부
    "weight": 500,             # Claude AI 분석 결과 가중치 (최대한 증가시켜 결정권을 AI에게 부여)
    "confidence_boost": 0.0,   # 일치 시 신뢰도 상승 값 (AI가 주도적으로 판단하도록 0으로 설정)
    "override_reasoning": True, # Claude의 분석 이유로 기존 내용 대체 여부
    "ai_primary_decision": True # AI가 1차적 결정을 내리고 기술적 분석은 참고용으로만 사용
}

# 이전 거래 이력 참고 설정
HISTORICAL_SETTINGS = {
    "use_historical_data": True,  # 이전 거래 이력 참고 여부
    "history_length": 30,           # 참고할 이전 거래 수
    "avoid_repeated_signals": True, # 연속 동일 신호 발생 시 강도 감소
}

# 알림 설정
NOTIFICATION_SETTINGS = {
    "enable_notifications": True,  # 알림 기능 사용 여부
    "notify_on_trade": True,        # 실제 거래 발생 시 알림
    "notify_on_signal": True,       # 강한 매매 신호 발생 시 알림
    "notify_on_error": True,        # 오류 발생 시 알림
    "min_signal_strength_for_notification": 0.8  # 알림 발생 최소 신호 강도
}
# 비트코인 자동매매 프로그램 사용 설명서

이 프로그램은 업비트에서 비트코인 자동매매를 수행하는 시스템입니다. 다양한 기술적 지표와 시장 데이터를 분석하여 매수, 매도, 홀드 결정을 내립니다.

## 1. 설정 방법

### 환경 설정

1. `.env` 파일에 다음 정보를 입력하세요:
   ```
   UPBIT_ACCESS_KEY=your_access_key
   UPBIT_SECRET_KEY=your_secret_key
   ENABLE_TRADE=false  # 실제 거래 활성화 여부 (true/false)
   ```

2. `trading_config.py` 파일을 편집하여 매매 전략을 커스터마이징할 수 있습니다.

### 필요한 라이브러리 설치

```bash
pip install pyupbit dotenv pandas numpy requests
```

## 2. 커스텀 설정 가이드

`trading_config.py` 파일에서 다음 설정을 조정할 수 있습니다:

### 매매 결정 임계값 설정

```python
DECISION_THRESHOLDS = {
    "buy_threshold": 0.1,    # 평균 신호가 이 값보다 크면 매수 (기본값: 0.2)
    "sell_threshold": -0.1,  # 평균 신호가 이 값보다 작으면 매도 (기본값: -0.2)
}
```

- 임계값을 0에 가깝게 설정할수록 더 자주 매매가 발생합니다.
- 기본값(0.2/-0.2)보다 작은 값(0.1/-0.1)을 사용하면 매매 빈도가 증가합니다.

### 투자 비율 설정

```python
INVESTMENT_RATIOS = {
    "min_ratio": 0.1,  # 최소 투자 비율 (보유 자산의 %) (기본값: 0.2)
    "max_ratio": 0.5,  # 최대 투자 비율 (보유 자산의 %) (기본값: 0.5)
}
```

- 신뢰도에 따라 투자 비율이 조정됩니다.
- `min_ratio`를 낮추면 신뢰도가 낮은 경우에도 소액으로 매매합니다.
- `max_ratio`를 높이면 신뢰도가 높을 때 더 많은 자산으로 매매합니다.

### 기술적 지표별 신호 강도 설정

```python
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
```

- 각 지표의 신호 강도를 0.0~1.0 사이에서 조정할 수 있습니다.
- 값이 클수록 해당 지표의 매매 신호가 더 강하게 반영됩니다.

### 지표 가중치 설정

```python
INDICATOR_WEIGHTS = {
    "MA": 1.0,           # 이동평균선
    "MA60": 1.0,         # 장기 이동평균선
    "BB": 1.0,           # 볼린저 밴드
    "RSI": 1.2,          # RSI (상대강도지수) - 중요도 높음
    "MACD": 1.2,         # MACD - 중요도 높음
    "Stochastic": 1.0,   # 스토캐스틱
    "Orderbook": 0.8,    # 호가창 분석
    "Trades": 0.8,       # 체결 데이터
    "KIMP": 0.7,         # 김프(한국 프리미엄)
    "FearGreed": 1.0,    # 공포&탐욕 지수
    "SOPR": 0.7,         # 온체인 SOPR
    "ActiveAddr": 0.6    # 온체인 활성 주소
}
```

- 가중치가 높은 지표가 최종 매매 결정에 더 큰 영향을 미칩니다.
- 중요하다고 생각하는 지표의 가중치를 더 크게 설정하세요.

### 지표 사용 여부 설정

```python
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
```

- 사용하지 않을 지표는 `False`로 설정하여 분석에서 제외할 수 있습니다.
- 지표 수를 줄이면 더 명확한 매매 신호를 얻을 수 있습니다.

### 매매 관련 추가 설정

```python
TRADING_SETTINGS = {
    "min_order_amount": 5000,  # 최소 주문 금액 (원) (기본값: 5000)
    "max_slippage": 0.005,     # 최대 허용 슬리피지 (주문가 대비 %) (기본값: 0.5%)
    "trading_interval": 60,    # 매매 분석 간격 (분) (기본값: 60)
    "trading_hours": {         # 매매 허용 시간대 (24시간제)
        "enabled": False,      # 시간대 제한 사용 여부
        "start_hour": 9,       # 매매 시작 시간 (예: 오전 9시)
        "end_hour": 23,        # 매매 종료 시간 (예: 오후 11시)
    }
}
```

- `min_order_amount`: 최소 주문 금액(업비트 최소 주문액: 5,000원)
- `trading_interval`: 매매 분석 주기(분 단위)

## 3. 실행 방법

```bash
python mvp.py
```

## 4. 결과 해석

매매 분석 결과는 다음과 같이 출력됩니다:

```
===== 최종 분석 결과 =====
{
  "decision": "buy",  // 매수, 매도, 홀드 중 하나
  "confidence": 0.65,  // 신뢰도 (0.0~1.0)
  ...
}
```

## 5. 로그 확인

거래 로그는 `logs` 폴더에 일별로 저장됩니다.

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import time
import pyupbit
import logging
import requests
import importlib.util
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# 로깅 설정
logger = logging.getLogger('analyzer')

# trading_config.py 불러오기
try:
    spec = importlib.util.spec_from_file_location(
        "trading_config", 
        Path(__file__).parent.parent.parent / "config" / "trading_config.py"
    )
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    
    # 설정값 가져오기
    SIGNAL_STRENGTHS = config.SIGNAL_STRENGTHS
    INDICATOR_WEIGHTS = config.INDICATOR_WEIGHTS
    INDICATOR_USAGE = config.INDICATOR_USAGE
    DECISION_THRESHOLDS = config.DECISION_THRESHOLDS
    TRADING_SETTINGS = config.TRADING_SETTINGS
except Exception as e:
    logger.error(f"설정 파일 로드 오류: {e}")
    # 기본 설정값
    SIGNAL_STRENGTHS = {
        "ma_crossover": 0.6, "ma_long_trend": 0.4, "bb_extreme": 0.7, 
        "bb_middle": 0.3, "rsi_extreme": 0.8, "rsi_middle": 0.2,
        "macd_crossover": 0.7, "macd_trend": 0.3, "stoch_extreme": 0.6, 
        "stoch_middle": 0.3, "orderbook": 0.6, "trade_data": 0.5, 
        "korea_premium": 0.5
    }
    INDICATOR_WEIGHTS = {
        "MA": 1.0, "BB": 1.0, "RSI": 1.2, "MACD": 1.2, "Stochastic": 1.0,
        "Orderbook": 0.8, "Trades": 0.8, "KIMP": 0.7
    }
    INDICATOR_USAGE = {
        "MA": True, "BB": True, "RSI": True, "MACD": True, "Stochastic": True,
        "Orderbook": True, "Trades": True, "KIMP": True
    }
    DECISION_THRESHOLDS = {"buy_threshold": 0.2, "sell_threshold": -0.2}
    TRADING_SETTINGS = {"trading_interval": 60}

class MarketAnalyzer:
    """시장 분석 클래스"""
    
    def __init__(self):
        """초기화"""
        self.upbit_access_key = os.getenv('UPBIT_ACCESS_KEY', '')
        self.upbit_secret_key = os.getenv('UPBIT_SECRET_KEY', '')
        
    def get_market_data(self, ticker="KRW-BTC", interval="minute60", count=100):
        """시장 데이터 조회"""
        try:
            # 캔들스틱 데이터 조회
            df = pyupbit.get_ohlcv(ticker, interval=interval, count=count)
            return df
        except Exception as e:
            logger.error(f"시장 데이터 조회 오류: {e}")
            return None
    
    def get_current_price(self, ticker="KRW-BTC"):
        """현재 가격 조회"""
        try:
            ticker_data = pyupbit.get_ticker(ticker)
            return ticker_data
        except Exception as e:
            logger.error(f"시장 데이터 조회 오류: {e}")
            return None
    
    def calculate_technical_indicators(self, df):
        """기술적 지표 계산"""
        try:
            # 데이터프레임 복사
            df = df.copy()
            
            # 이동평균선
            df['MA5'] = df['close'].rolling(window=5).mean()
            df['MA20'] = df['close'].rolling(window=20).mean()
            df['MA60'] = df['close'].rolling(window=60).mean()
            
            # 볼린저 밴드
            df['BB_middle'] = df['close'].rolling(window=20).mean()
            df['BB_std'] = df['close'].rolling(window=20).std()
            df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
            df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)
            
            # RSI
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = ema12 - ema26
            df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_hist'] = df['MACD'] - df['MACD_signal']
            
            # 스토캐스틱
            df['lowest_14'] = df['low'].rolling(window=14).min()
            df['highest_14'] = df['high'].rolling(window=14).max()
            df['STOCH_K'] = 100 * ((df['close'] - df['lowest_14']) / 
                                  (df['highest_14'] - df['lowest_14']))
            df['STOCH_D'] = df['STOCH_K'].rolling(window=3).mean()
            
            return df.dropna()
        except Exception as e:
            logger.error(f"기술적 지표 계산 오류: {e}")
            return df
    
    def analyze_orderbook(self, ticker="KRW-BTC"):
        """호가창 분석"""
        try:
            # 호가창 데이터 조회
            orderbook = pyupbit.get_orderbook(ticker)
            
            # 매수/매도 호가 합계 계산
            bid_total = sum([x['price'] * x['quantity'] for x in orderbook['bids']])
            ask_total = sum([x['price'] * x['quantity'] for x in orderbook['asks']])
            
            # 매수/매도 비율 계산
            if ask_total > 0:
                ratio = bid_total / ask_total
            else:
                ratio = 1.0
                
            return ratio
        except Exception as e:
            logger.error(f"호가창 비율 계산 오류: {e}")
            return 1.0  # 오류 발생 시 중립적 값 반환
    
    def analyze_trades(self, ticker="KRW-BTC"):
        """체결 데이터 분석"""
        try:
            # 최근 체결 데이터 조회
            trades = pyupbit.get_trades(ticker, count=100)
            
            if not trades:
                return 0.0
                
            # 매수/매도 거래량 계산
            buy_volume = sum([x['trade_volume'] for x in trades if x['type'] == 'bid'])
            sell_volume = sum([x['trade_volume'] for x in trades if x['type'] == 'ask'])
            
            # 매수 거래량 / 전체 거래량 비율 계산 (0.5가 중립)
            total_volume = buy_volume + sell_volume
            if total_volume > 0:
                buy_ratio = buy_volume / total_volume
                # -1 ~ 1 범위로 변환 (0.5가 중립)
                signal = (buy_ratio - 0.5) * 2
            else:
                signal = 0.0
                
            return signal
        except Exception as e:
            logger.error(f"체결 데이터 분석 오류: {e}")
            return 0.0  # 오류 발생 시 중립적 값 반환
    
    def calculate_kimchi_premium(self):
        """김프(한국 프리미엄) 계산"""
        try:
            # 업비트 BTC 가격
            kr_price = pyupbit.get_current_price("KRW-BTC")
            
            # 해외 거래소 BTC 가격 (바이낸스 API 대신 다른 방법 사용)
            # 환율 정보 조회
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(
                "https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD",
                headers=headers,
                timeout=10
            )
            
            exchange_data = response.json()
            usd_krw = exchange_data[0]['basePrice']
            
            # 바이낸스 API는 제한이 있으므로, 공개 API 사용
            binance_response = requests.get(
                "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
                timeout=10
            )
            binance_data = binance_response.json()
            us_price_in_usd = float(binance_data['price'])
            
            # USD 가격을 KRW로 변환
            us_price_in_krw = us_price_in_usd * usd_krw
            
            # 김프 계산
            kimchi_premium = ((kr_price - us_price_in_krw) / us_price_in_krw) * 100
            
            return kimchi_premium
        except Exception as e:
            logger.error(f"김프 계산 오류: {e}")
            return 0.0  # 오류 발생 시 중립적 값 반환
    
    def get_fear_greed_index(self):
        """공포 & 탐욕 지수 조회"""
        try:
            # 실제로는 API를 통해 가져오지만, 여기서는 임의의 값 반환
            # 범위: 0(극단적 공포)~100(극단적 탐욕)
            return 39  # 예시값, 실제로는 API에서 가져옴
        except Exception as e:
            logger.error(f"공포&탐욕 지수 조회 오류: {e}")
            return 50  # 중립값 반환
    
    def generate_trading_signals(self, df, current_price, orderbook_ratio, trade_signal, kimchi_premium):
        """트레이딩 신호 생성"""
        signals = []
        last_row = df.iloc[-1]
        
        # 1. 이동평균선(MA) 분석
        if INDICATOR_USAGE.get("MA", True):
            # 골든크로스/데드크로스 확인
            if last_row['MA5'] > last_row['MA20']:
                signals.append({
                    "source": "이동평균선(MA)",
                    "signal": "buy",
                    "strength": SIGNAL_STRENGTHS.get("ma_crossover", 0.6),
                    "description": "골든크로스 상태 (5일 이동평균선이 20일 이동평균선 위에 위치)"
                })
            else:
                signals.append({
                    "source": "이동평균선(MA)",
                    "signal": "sell",
                    "strength": SIGNAL_STRENGTHS.get("ma_crossover", 0.6),
                    "description": "데드크로스 상태 (5일 이동평균선이 20일 이동평균선 아래에 위치)"
                })
        
        # 2. 장기 이동평균선(MA60) 분석
        if INDICATOR_USAGE.get("MA60", True):
            if last_row['close'] > last_row['MA60']:
                signals.append({
                    "source": "장기추세(MA60)",
                    "signal": "buy",
                    "strength": SIGNAL_STRENGTHS.get("ma_long_trend", 0.4),
                    "description": "장기 상승 추세 (현재가가 60일 이동평균선 위에 위치)"
                })
            else:
                signals.append({
                    "source": "장기추세(MA60)",
                    "signal": "sell",
                    "strength": SIGNAL_STRENGTHS.get("ma_long_trend", 0.4),
                    "description": "장기 하락 추세 (현재가가 60일 이동평균선 아래에 위치)"
                })
            
        # 3. 볼린저 밴드(BB) 분석
        if INDICATOR_USAGE.get("BB", True):
            # 밴드 내 위치 계산 (0~100%)
            band_width = last_row['BB_upper'] - last_row['BB_lower']
            if band_width > 0:
                position_pct = ((last_row['close'] - last_row['BB_lower']) / band_width) * 100
                
                if position_pct < 20:  # 하단 20% 이내
                    signals.append({
                        "source": "볼린저밴드(BB)",
                        "signal": "buy",
                        "strength": SIGNAL_STRENGTHS.get("bb_extreme", 0.7),
                        "description": f"하단 돌파/접근 (밴드 내 위치: 하위 {position_pct:.0f}%)"
                    })
                elif position_pct > 80:  # 상단 20% 이내
                    signals.append({
                        "source": "볼린저밴드(BB)",
                        "signal": "sell",
                        "strength": SIGNAL_STRENGTHS.get("bb_extreme", 0.7),
                        "description": f"상단 돌파/접근 (밴드 내 위치: 상위 {position_pct:.0f}%)"
                    })
                elif 20 <= position_pct < 40:  # 하단 20~40%
                    signals.append({
                        "source": "볼린저밴드(BB)",
                        "signal": "buy",
                        "strength": SIGNAL_STRENGTHS.get("bb_middle", 0.3),
                        "description": f"하단 접근중 (밴드 내 위치: 하위 {position_pct:.0f}%)"
                    })
                elif 60 < position_pct <= 80:  # 상단 60~80%
                    signals.append({
                        "source": "볼린저밴드(BB)",
                        "signal": "sell",
                        "strength": SIGNAL_STRENGTHS.get("bb_middle", 0.3),
                        "description": f"상단 접근중 (밴드 내 위치: 상위 {position_pct:.0f}%)"
                    })
                else:  # 중앙 40~60%
                    signals.append({
                        "source": "볼린저밴드(BB)",
                        "signal": "hold",
                        "strength": 0,
                        "description": "밴드 중앙 부근 (중립적 위치)"
                    })
            else:
                signals.append({
                    "source": "볼린저밴드(BB)",
                    "signal": "hold",
                    "strength": 0,
                    "description": "밴드 계산 오류 (중립적 위치)"
                })
                
        # 4. RSI 분석
        if INDICATOR_USAGE.get("RSI", True):
            rsi = last_row['RSI']
            
            if rsi <= 30:  # 과매도 상태
                signals.append({
                    "source": "RSI(상대강도지수)",
                    "signal": "buy",
                    "strength": SIGNAL_STRENGTHS.get("rsi_extreme", 0.8),
                    "description": f"과매도 상태 (RSI: {rsi:.1f} < 30)"
                })
            elif rsi >= 70:  # 과매수 상태
                signals.append({
                    "source": "RSI(상대강도지수)",
                    "signal": "sell",
                    "strength": SIGNAL_STRENGTHS.get("rsi_extreme", 0.8),
                    "description": f"과매수 상태 (RSI: {rsi:.1f} > 70)"
                })
            elif 30 < rsi < 45:  # 매도세 우세
                signals.append({
                    "source": "RSI(상대강도지수)",
                    "signal": "buy",
                    "strength": SIGNAL_STRENGTHS.get("rsi_middle", 0.2),
                    "description": f"매도세 우세 (RSI: {rsi:.1f})"
                })
            elif 55 < rsi < 70:  # 매수세 우세
                signals.append({
                    "source": "RSI(상대강도지수)",
                    "signal": "sell",
                    "strength": SIGNAL_STRENGTHS.get("rsi_middle", 0.2),
                    "description": f"매수세 우세 (RSI: {rsi:.1f})"
                })
            else:  # 중립
                signals.append({
                    "source": "RSI(상대강도지수)",
                    "signal": "hold",
                    "strength": 0,
                    "description": f"중립적 (RSI: {rsi:.1f})"
                })
                
        # 5. MACD 분석
        if INDICATOR_USAGE.get("MACD", True):
            # MACD 골든크로스/데드크로스
            if last_row['MACD'] > last_row['MACD_signal']:
                if df['MACD'].iloc[-2] <= df['MACD_signal'].iloc[-2]:  # 교차 발생
                    signals.append({
                        "source": "MACD",
                        "signal": "buy",
                        "strength": SIGNAL_STRENGTHS.get("macd_crossover", 0.7),
                        "description": "MACD 골든크로스 발생"
                    })
                else:  # 유지
                    signals.append({
                        "source": "MACD",
                        "signal": "buy",
                        "strength": SIGNAL_STRENGTHS.get("macd_trend", 0.3),
                        "description": "MACD 상승 추세 유지중"
                    })
            elif last_row['MACD'] < last_row['MACD_signal']:
                if df['MACD'].iloc[-2] >= df['MACD_signal'].iloc[-2]:  # 교차 발생
                    signals.append({
                        "source": "MACD",
                        "signal": "sell",
                        "strength": SIGNAL_STRENGTHS.get("macd_crossover", 0.7),
                        "description": "MACD 데드크로스 발생"
                    })
                else:  # 유지
                    signals.append({
                        "source": "MACD",
                        "signal": "sell",
                        "strength": SIGNAL_STRENGTHS.get("macd_trend", 0.3),
                        "description": "MACD 하락 추세 유지중"
                    })
            else:  # MACD와 시그널 라인이 같은 경우 (드물지만)
                signals.append({
                    "source": "MACD",
                    "signal": "hold",
                    "strength": 0,
                    "description": "MACD 중립적 상태"
                })
                
        # 6. 스토캐스틱 분석
        if INDICATOR_USAGE.get("Stochastic", True):
            k = last_row['STOCH_K']
            d = last_row['STOCH_D']
            
            # 과매수/과매도 영역 확인
            if k <= 20 and d <= 20:  # 과매도 영역
                if k > d:  # K가 D를 상향돌파 (반등 신호)
                    signals.append({
                        "source": "스토캐스틱",
                        "signal": "buy",
                        "strength": SIGNAL_STRENGTHS.get("stoch_extreme", 0.6),
                        "description": f"과매도 반등 신호 (K: {k:.1f}, D: {d:.1f})"
                    })
                else:
                    signals.append({
                        "source": "스토캐스틱",
                        "signal": "buy",
                        "strength": SIGNAL_STRENGTHS.get("stoch_middle", 0.3),
                        "description": f"과매도 영역 (K: {k:.1f}, D: {d:.1f})"
                    })
            elif k >= 80 and d >= 80:  # 과매수 영역
                if k < d:  # K가 D를 하향돌파 (하락 반전 신호)
                    signals.append({
                        "source": "스토캐스틱",
                        "signal": "sell",
                        "strength": SIGNAL_STRENGTHS.get("stoch_extreme", 0.6),
                        "description": f"과매수 반전 신호 (K: {k:.1f}, D: {d:.1f})"
                    })
                else:
                    signals.append({
                        "source": "스토캐스틱",
                        "signal": "sell",
                        "strength": SIGNAL_STRENGTHS.get("stoch_middle", 0.3),
                        "description": f"과매수 영역 (K: {k:.1f}, D: {d:.1f})"
                    })
            elif k > d:  # K가 D보다 위 (상승 모멘텀)
                signals.append({
                    "source": "스토캐스틱",
                    "signal": "buy",
                    "strength": SIGNAL_STRENGTHS.get("stoch_middle", 0.3),
                    "description": f"상승 모멘텀 (K: {k:.1f} > D: {d:.1f})"
                })
            elif k < d:  # K가 D보다 아래 (하락 모멘텀)
                signals.append({
                    "source": "스토캐스틱",
                    "signal": "sell",
                    "strength": SIGNAL_STRENGTHS.get("stoch_middle", 0.3),
                    "description": f"하락 모멘텀 (K: {k:.1f} < D: {d:.1f})"
                })
            else:  # K와 D가 같은 경우
                signals.append({
                    "source": "스토캐스틱",
                    "signal": "hold",
                    "strength": 0,
                    "description": f"중립적 (K: {k:.1f}, D: {d:.1f})"
                })
        
        # 7. 호가창 분석
        if INDICATOR_USAGE.get("Orderbook", True):
            if orderbook_ratio > 1.2:  # 매수세가 강함
                strength = min(0.6, (orderbook_ratio - 1) / 2)  # 최대 0.6
                signals.append({
                    "source": "호가창(매수/매도비율)",
                    "signal": "buy",
                    "strength": strength,
                    "description": f"매수세 강함 (매수/매도 비율: {orderbook_ratio:.2f})"
                })
            elif orderbook_ratio < 0.8:  # 매도세가 강함
                strength = min(0.6, (1 - orderbook_ratio) / 2)  # 최대 0.6
                signals.append({
                    "source": "호가창(매수/매도비율)",
                    "signal": "sell",
                    "strength": strength,
                    "description": f"매도세 강함 (매수/매도 비율: {orderbook_ratio:.2f})"
                })
            else:  # 중립적
                signals.append({
                    "source": "호가창(매수/매도비율)",
                    "signal": "hold",
                    "strength": 0,
                    "description": f"중립적 호가창 (매수/매도 비율: {orderbook_ratio:.2f})"
                })
                
        # 8. 체결 데이터 분석
        if INDICATOR_USAGE.get("Trades", True):
            if trade_signal > 0.3:  # 매수세 우세
                signals.append({
                    "source": "체결데이터",
                    "signal": "buy",
                    "strength": SIGNAL_STRENGTHS.get("trade_data", 0.5) * min(1, trade_signal),
                    "description": f"매수 체결 우세 (신호 강도: {trade_signal:.2f})"
                })
            elif trade_signal < -0.3:  # 매도세 우세
                signals.append({
                    "source": "체결데이터",
                    "signal": "sell",
                    "strength": SIGNAL_STRENGTHS.get("trade_data", 0.5) * min(1, abs(trade_signal)),
                    "description": f"매도 체결 우세 (신호 강도: {trade_signal:.2f})"
                })
            else:  # 중립적
                signals.append({
                    "source": "체결데이터",
                    "signal": "hold",
                    "strength": 0,
                    "description": f"중립적 체결 (신호 강도: {trade_signal:.2f})"
                })
                
        # 9. 김프(한국 프리미엄) 분석
        if INDICATOR_USAGE.get("KIMP", True):
            if kimchi_premium < -1.0:  # 역프리미엄 1% 이상 (한국 가격이 저평가)
                strength = min(0.5, abs(kimchi_premium) / 10)  # 최대 0.5
                signals.append({
                    "source": "김프(한국 프리미엄)",
                    "signal": "buy",
                    "strength": strength,
                    "description": f"역프리미엄 발생 (김프: {kimchi_premium:.2f}%)"
                })
            elif kimchi_premium > 4.0:  # 프리미엄 4% 이상 (한국 가격이 고평가)
                strength = min(0.5, kimchi_premium / 10)  # 최대 0.5
                signals.append({
                    "source": "김프(한국 프리미엄)",
                    "signal": "sell",
                    "strength": strength,
                    "description": f"높은 프리미엄 (김프: {kimchi_premium:.2f}%)"
                })
            else:  # 적정 수준의 프리미엄
                signals.append({
                    "source": "김프(한국 프리미엄)",
                    "signal": "hold",
                    "strength": 0,
                    "description": f"적정 프리미엄 수준 (김프: {kimchi_premium:.2f}%)"
                })
                
        # 10. 공포&탐욕 지수 분석
        if INDICATOR_USAGE.get("FearGreed", True):
            fear_greed_value = self.get_fear_greed_index()
            
            if fear_greed_value <= 25:  # 극도의 공포 (0-25)
                signals.append({
                    "source": "시장심리(공포&탐욕지수)",
                    "signal": "buy",
                    "strength": SIGNAL_STRENGTHS.get("fear_greed_extreme", 0.7),
                    "description": f"극도의 공포 상태 (Fear & Greed: {fear_greed_value}, Extreme Fear)"
                })
            elif fear_greed_value <= 40:  # 공포 (26-40)
                signals.append({
                    "source": "시장심리(공포&탐욕지수)",
                    "signal": "buy",
                    "strength": SIGNAL_STRENGTHS.get("fear_greed_middle", 0.4),
                    "description": f"공포 우세 상태 (Fear & Greed: {fear_greed_value}, Fear)"
                })
            elif fear_greed_value >= 75:  # 극도의 탐욕 (75-100)
                signals.append({
                    "source": "시장심리(공포&탐욕지수)",
                    "signal": "sell",
                    "strength": SIGNAL_STRENGTHS.get("fear_greed_extreme", 0.7),
                    "description": f"극도의 탐욕 상태 (Fear & Greed: {fear_greed_value}, Extreme Greed)"
                })
            elif fear_greed_value >= 60:  # 탐욕 (60-74)
                signals.append({
                    "source": "시장심리(공포&탐욕지수)",
                    "signal": "sell",
                    "strength": SIGNAL_STRENGTHS.get("fear_greed_middle", 0.4),
                    "description": f"탐욕 우세 상태 (Fear & Greed: {fear_greed_value}, Greed)"
                })
            else:  # 중립 (41-59)
                signals.append({
                    "source": "시장심리(공포&탐욕지수)",
                    "signal": "hold",
                    "strength": 0,
                    "description": f"중립적 시장 심리 (Fear & Greed: {fear_greed_value}, Neutral)"
                })
                
        # 최종 매매 신호 계산
        buy_signals = []
        sell_signals = []
        hold_signals = []
        
        # 신호 분류 및 가중치 적용
        total_weight = 0
        weighted_signal_sum = 0
        
        for signal in signals:
            source = signal["source"].split("(")[0].strip()
            weight = INDICATOR_WEIGHTS.get(source, 1.0)
            total_weight += weight
            
            if signal["signal"] == "buy":
                buy_signals.append(signal)
                weighted_signal_sum += signal["strength"] * weight
            elif signal["signal"] == "sell":
                sell_signals.append(signal)
                weighted_signal_sum -= signal["strength"] * weight
            else:  # hold
                hold_signals.append(signal)
        
        # 평균 신호 강도 계산 (-1 ~ 1 범위)
        avg_signal_strength = weighted_signal_sum / total_weight if total_weight > 0 else 0
        
        # 신호 카운트
        signal_counts = {
            "buy": len(buy_signals),
            "sell": len(sell_signals),
            "hold": len(hold_signals)
        }
        
        # 신뢰도 계산 (0.5 ~ 1.0 범위)
        confidence = 0.5 + abs(avg_signal_strength) / 2
        
        # 최종 결정
        if avg_signal_strength >= DECISION_THRESHOLDS["buy_threshold"]:
            decision = "buy"
            decision_kr = "매수" if avg_signal_strength >= 0.4 else "약한 매수"
        elif avg_signal_strength <= DECISION_THRESHOLDS["sell_threshold"]:
            decision = "sell"
            decision_kr = "매도" if avg_signal_strength <= -0.4 else "약한 매도"
        else:
            decision = "hold"
            decision_kr = "홀드" if abs(avg_signal_strength) < 0.05 else "약한 홀드"
        
        # 결과 반환
        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "decision": decision,
            "decision_kr": decision_kr,
            "confidence": confidence,
            "avg_signal_strength": avg_signal_strength,
            "signals": signals,
            "signal_counts": signal_counts,
            "current_price": current_price,
            "price_change_24h": self._calculate_price_change_24h(df) if df is not None else "N/A"
        }
        
        return result
    
    def _calculate_price_change_24h(self, df):
        """24시간 가격 변화율 계산"""
        try:
            if len(df) >= 2:
                current_price = df['close'].iloc[-1]
                prev_price = df['close'].iloc[-24] if len(df) >= 24 else df['close'].iloc[0]
                change_pct = ((current_price / prev_price) - 1) * 100
                return f"{change_pct:.2f}%"
            return "N/A"
        except Exception as e:
            logger.error(f"가격 변화율 계산 오류: {e}")
            return "N/A"
    
    def analyze(self, ticker="KRW-BTC"):
        """종합 시장 분석 수행"""
        try:
            # 1. 시장 데이터 조회
            df = self.get_market_data(ticker)
            if df is None or len(df) < 20:
                logger.error("충분한 시장 데이터를 조회할 수 없습니다.")
                return {"decision": "hold", "confidence": 0.5, "reason": "데이터 부족"}
            
            # 2. 기술적 지표 계산
            df = self.calculate_technical_indicators(df)
            
            # 3. 현재가 조회
            current_price = self.get_current_price(ticker)
            
            # 4. 호가창 분석
            orderbook_ratio = self.analyze_orderbook(ticker)
            
            # 5. 체결 데이터 분석
            trade_signal = self.analyze_trades(ticker)
            
            # 6. 김프 계산
            kimchi_premium = self.calculate_kimchi_premium()
            
            # 7. 종합 신호 생성
            result = self.generate_trading_signals(
                df, current_price, orderbook_ratio, trade_signal, kimchi_premium
            )
            
            return result
            
        except Exception as e:
            logger.error(f"시장 분석 오류: {e}")
            return {"decision": "hold", "confidence": 0.5, "reason": f"분석 오류: {str(e)}"}


class SignalAnalyzer(MarketAnalyzer):
    """신호 분석 클래스 (MarketAnalyzer 상속)"""
    
    def __init__(self, config, technical_indicators=None, market_indicators=None, claude_api=None):
        """초기화"""
        super().__init__()
        self.config = config
        self.technical_indicators = technical_indicators
        self.market_indicators = market_indicators
        self.claude_api = claude_api
        
    def analyze(self, market_data, ticker="KRW-BTC"):
        """시장 분석 및 매매 신호 생성"""
        # 기존 MarketAnalyzer의 analyze 메서드 사용
        market_analysis = super().analyze(ticker)
        
        # Claude AI 분석 통합 (설정된 경우)
        claude_settings = self.config.get("CLAUDE_SETTINGS", {})
        if claude_settings.get("use_claude", False) and self.claude_api is not None:
            try:
                # 기술적 지표 데이터 준비
                technical_data = {}
                if self.technical_indicators is not None:
                    # 여기에 기술적 지표 데이터 구성 코드 추가
                    pass
                
                # 시장 지표 데이터 준비
                market_indicator_data = {}
                if self.market_indicators is not None:
                    # 여기에 시장 지표 데이터 구성 코드 추가
                    pass
                
                # Claude API 호출
                claude_analysis = self.claude_api.analyze_market(market_data, technical_data)
                
                # Claude의 신뢰도가 높은 경우 신호 강화
                if claude_analysis["signal"] == market_analysis["decision"]:
                    market_analysis["confidence"] = min(
                        1.0, 
                        market_analysis["confidence"] + claude_settings.get("confidence_boost", 0.1)
                    )
                    market_analysis["claude_agrees"] = True
                else:
                    market_analysis["claude_agrees"] = False
                
                # Claude 분석 결과 저장
                market_analysis["claude_analysis"] = claude_analysis
                
            except Exception as e:
                logger.error(f"Claude 분석 오류: {e}")
                market_analysis["claude_error"] = str(e)
        
        return market_analysis
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
        Path(__file__).parent.parent / "trading_config.py"
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
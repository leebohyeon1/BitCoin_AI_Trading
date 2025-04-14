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

# 모듈 가져오기
from .technical_signals import (
    analyze_moving_averages, analyze_bollinger_bands, analyze_rsi, 
    analyze_macd, analyze_stochastic, analyze_orderbook_data, 
    analyze_trade_data, analyze_kimchi_premium, analyze_fear_greed_index
)
from .signal_generator import SignalGenerator

# 로깅 설정
logger = logging.getLogger('market_analyzer')

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
        
        # 신호 생성기 초기화
        self.signal_generator = SignalGenerator(
            SIGNAL_STRENGTHS, 
            INDICATOR_WEIGHTS, 
            DECISION_THRESHOLDS
        )
        
    def get_market_data(self, ticker="KRW-BTC", interval="minute60", count=100):
        """시장 데이터 조회"""
        try:
            # 캔들스틱 데이터 조회
            df = pyupbit.get_ohlcv(ticker, interval=interval, count=count)
            return df
        except Exception as e:
            logger.error(f"시장 데이터 조회 오류: {e}")
            # None 대신 빈 데이터프레임 반환
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume', 'value'])
    
    def get_current_price(self, ticker="KRW-BTC"):
        """현재 가격 조회"""
        try:
            # get_ticker 대신 get_current_price 사용
            current_price = pyupbit.get_current_price(ticker)
            if current_price is None:
                raise ValueError("현재가 조회 실패")
            # 현재가를 딕셔너리 형태로 반환
            return [{"market": ticker, "trade_price": current_price}]
        except Exception as e:
            logger.error(f"시장 데이터 조회 오류: {e}")
            # None 대신 오류 정보가 담긴 기본값 반환
            return [{"market": ticker, "trade_price": 0, "error": f"시장 데이터 조회 오류: {e}"}]
    
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
            
            if not orderbook or len(orderbook) == 0:
                logger.error("호가창 데이터가 비어있습니다.")
                return 1.0
                
            # 데이터 구조 확인 (list 형태인 경우)
            if isinstance(orderbook, list):
                orderbook_data = orderbook[0]
            else:
                orderbook_data = orderbook
            
            # 구조에 따라 매수/매도 호가 합계 계산
            if 'bids' in orderbook_data and 'asks' in orderbook_data:
                bid_total = sum([x['price'] * x['quantity'] for x in orderbook_data['bids']])
                ask_total = sum([x['price'] * x['quantity'] for x in orderbook_data['asks']])
            elif 'orderbook_units' in orderbook_data:
                units = orderbook_data['orderbook_units']
                bid_total = sum([x['bid_price'] * x['bid_size'] for x in units])
                ask_total = sum([x['ask_price'] * x['ask_size'] for x in units])
            else:
                logger.error(f"알 수 없는 호가창 구조: {list(orderbook_data.keys())}")
                return 1.0
            
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
            # get_trades 함수가 없으므로 requests를 직접 사용해 API 호출
            # 실패하면 중립값 반환
            try:
                url = f"https://api.upbit.com/v1/trades/ticks?market={ticker}&count=100"
                headers = {'Accept': 'application/json'}
                response = requests.get(url, headers=headers, timeout=5)
                trades = response.json()
            except Exception as e:
                logger.warning(f"거래 데이터 API 호출 실패: {e}")
                return 0.0
            
            if not trades:
                return 0.0
                
            # 매수/매도 거래량 계산
            try:
                buy_volume = sum([float(x.get('trade_volume', 0)) for x in trades if x.get('ask_bid') == 'bid'])
                sell_volume = sum([float(x.get('trade_volume', 0)) for x in trades if x.get('ask_bid') == 'ask'])
            except Exception as e:
                logger.warning(f"거래량 계산 오류: {e}")
                return 0.0
            
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
            if kr_price is None:
                logger.warning("업비트 가격을 가져올 수 없습니다")
                return 0.0
            
            # 환율 정보 및 바이낸스 가격 조회 시도
            try:
                # 환율 정보 조회 (오류 발생 시 고정값 사용)
                try:
                    url = "https://open.er-api.com/v6/latest/USD"
                    response = requests.get(url, timeout=5)
                    data = response.json()
                    usd_krw = data['rates']['KRW']
                except Exception as e:
                    logger.warning(f"ExchangeRate-API 환율 정보 조회 실패: {e}")
                    usd_krw = 1350.0  # 기본값
                
                # 바이낸스 API 조회
                try:
                    binance_response = requests.get(
                        "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
                        timeout=5
                    )
                    binance_data = binance_response.json()
                    us_price_in_usd = float(binance_data['price'])
                except Exception as e:
                    logger.warning(f"바이낸스 가격 조회 실패: {e}, 기본값 사용")
                    us_price_in_usd = kr_price / usd_krw  # 김프 0%로 가정
                
                # USD 가격을 KRW로 변환
                us_price_in_krw = us_price_in_usd * usd_krw
                
                # 김프 계산
                kimchi_premium = ((kr_price - us_price_in_krw) / us_price_in_krw) * 100
                
                return round(kimchi_premium, 2)
            except Exception as e:
                logger.warning(f"김프 계산 중 오류: {e}")
                return 0.0
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
            
    def generate_trading_signals(self, df, current_price, orderbook_ratio, trade_signal, kimchi_premium):
        """트레이딩 신호 생성 - 모듈 함수 사용"""
        signals = []
        
        # 1. 이동평균선(MA) 분석
        if INDICATOR_USAGE.get("MA", True):
            ma_signals = analyze_moving_averages(df, SIGNAL_STRENGTHS)
            signals.extend(ma_signals)
            
        # 2. 볼린저 밴드(BB) 분석
        if INDICATOR_USAGE.get("BB", True):
            bb_signals = analyze_bollinger_bands(df, SIGNAL_STRENGTHS)
            signals.extend(bb_signals)
            
        # 3. RSI 분석
        if INDICATOR_USAGE.get("RSI", True):
            rsi_signals = analyze_rsi(df, SIGNAL_STRENGTHS)
            signals.extend(rsi_signals)
            
        # 4. MACD 분석
        if INDICATOR_USAGE.get("MACD", True):
            macd_signals = analyze_macd(df, SIGNAL_STRENGTHS)
            signals.extend(macd_signals)
            
        # 5. 스토캐스틱 분석
        if INDICATOR_USAGE.get("Stochastic", True):
            stoch_signals = analyze_stochastic(df, SIGNAL_STRENGTHS)
            signals.extend(stoch_signals)
            
        # 6. 호가창 분석
        if INDICATOR_USAGE.get("Orderbook", True):
            orderbook_signals = analyze_orderbook_data(orderbook_ratio, SIGNAL_STRENGTHS)
            signals.extend(orderbook_signals)
            
        # 7. 체결 데이터 분석
        if INDICATOR_USAGE.get("Trades", True):
            trade_signals = analyze_trade_data(trade_signal, SIGNAL_STRENGTHS)
            signals.extend(trade_signals)
            
        # 8. 김프(한국 프리미엄) 분석
        if INDICATOR_USAGE.get("KIMP", True):
            kimp_signals = analyze_kimchi_premium(kimchi_premium, SIGNAL_STRENGTHS)
            signals.extend(kimp_signals)
            
        # 9. 공포 & 탐욕 지수 분석
        if INDICATOR_USAGE.get("FearGreed", True):
            fear_greed_value = self.get_fear_greed_index()
            fear_greed_signals = analyze_fear_greed_index(fear_greed_value, SIGNAL_STRENGTHS)
            signals.extend(fear_greed_signals)
            
        # 신호 생성기를 사용하여 최종 결정 계산
        result = self.signal_generator.generate_final_decision(signals)
        
        # 현재가와 가격 변동 정보 추가
        result["current_price"] = current_price
        result["price_change_24h"] = self._calculate_price_change_24h(df) if df is not None else "N/A"
        
        return result
    
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
            try:
                # 현재가 조회 안전하게 처리
                current_price = self.get_current_price(ticker)
                # None 또는 빈 리스트인 경우 기본값 설정
                if current_price is None or len(current_price) == 0:
                    current_price = [{"market": ticker, "trade_price": df['close'].iloc[-1]}]
                    logger.warning(f"현재가 조회 실패, 최근 종가 사용: {current_price[0]['trade_price']}")
            except Exception as e:
                logger.error(f"현재가 조회 오류: {e}, 최근 종가 사용")
                current_price = [{"market": ticker, "trade_price": df['close'].iloc[-1]}]
            
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

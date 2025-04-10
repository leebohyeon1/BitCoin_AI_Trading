import os
from dotenv import load_dotenv
load_dotenv()

# 기본 설정값 정의
DECISION_THRESHOLDS = {"buy_threshold": 0.2, "sell_threshold": -0.2}
INVESTMENT_RATIOS = {"min_ratio": 0.2, "max_ratio": 0.5}
SIGNAL_STRENGTHS = {}
INDICATOR_WEIGHTS = {}
INDICATOR_USAGE = {}
TRADING_SETTINGS = {"min_order_amount": 5000, "trading_interval": 60}
CLAUDE_SETTINGS = {"use_claude": False, "weight": 1.0, "confidence_boost": 0.1}
HISTORICAL_SETTINGS = {"use_historical_data": False}

# 사용자 설정 파일 불러오기 시도
try:
    from trading_config import *
    print("사용자 설정 파일을 성공적으로 불러왔습니다.")
except ImportError:
    print("사용자 설정 파일을 찾을 수 없습니다. 기본 설정을 사용합니다.")

# 필요한 라이브러리 임포트
import pyupbit
import json
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import requests
import traceback

# 추가 거래소 API (바이낸스, 바이트) - 필요시 설치
# pip install python-binance ccxt

# 1. 거래소 데이터 가져오기 - 향상된 버전
def get_enhanced_market_data():
    """다양한 거래소의 포괄적인 시장 데이터를 가져옵니다."""
    try:
        result = {}
        
        # 1.1 업비트 데이터
        print("업비트 데이터 가져오기 시작...")
        
        # OHLCV 데이터 (일봉, 시간봉, 분봉)

        # 일봉 데이터: 200일로 확장 (약 6-7개월)
        result["upbit_daily_ohlcv"] = pyupbit.get_ohlcv("KRW-BTC", count=200, interval="day")
        
        # 주봉 데이터 추가 (52주 = 약 1년)
        result["upbit_hourly_ohlcv"] = pyupbit.get_ohlcv("KRW-BTC", count=24, interval="week")
        
        # 월봉 데이터 추가 (24개월 = 2년)
        result["upbit_minute_ohlcv"] = pyupbit.get_ohlcv("KRW-BTC", count=60, interval="minute5")
        
        # 현재 호가 정보 (orderbook)
        result["upbit_orderbook"] = pyupbit.get_orderbook("KRW-BTC")
        
        # 최근 체결 데이터
        result["upbit_trades"] = []
        
        # 시장 전체 정보 (티커)
        result["upbit_ticker"] = pyupbit.get_current_price("KRW-BTC", verbose=True)
        
        # 업비트 시장 전체 코인 정보
        result["upbit_market_all"] = []
        
        print("업비트 데이터 가져오기 성공")
        
        # 1.2 바이낸스 데이터 (선택적)
        try:
            import ccxt
            
            # CCXT를 통한 바이낸스 연결
            binance = ccxt.binance()
            
            # OHLCV 데이터

            # 바이낸스 일봉 200일
            binance_ohlcv = binance.fetch_ohlcv('BTC/USDT', '1d', limit=200)
            df_binance = pd.DataFrame(binance_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df_binance['timestamp'] = pd.to_datetime(df_binance['timestamp'], unit='ms')
            df_binance.set_index('timestamp', inplace=True)
            result["binance_daily_ohlcv"] = df_binance
            
            # 현재가 정보
            binance_ticker = binance.fetch_ticker('BTC/USDT')
            result["binance_ticker"] = binance_ticker
            
            # 호가창 데이터
            binance_orderbook = binance.fetch_order_book('BTC/USDT')
            result["binance_orderbook"] = binance_orderbook
            
            print("바이낸스 데이터 가져오기 성공")
        except Exception as e:
            print(f"바이낸스 데이터 가져오기 실패 (무시하고 계속): {e}")
        
        # 1.3 Fear & Greed 지수 가져오기 (암호화폐 시장 심리 지수)
        try:
            fg_url = "https://api.alternative.me/fng/"
            fg_response = requests.get(fg_url)
            if fg_response.status_code == 200:
                fg_data = fg_response.json()
                result["fear_greed_index"] = fg_data
                print("Fear & Greed 지수 가져오기 성공")
        except Exception as e:
            print(f"Fear & Greed 지수 가져오기 실패 (무시하고 계속): {e}")
        
        # 1.4 온체인 데이터 (선택적) - Glassnode 또는 다른 서비스 API 필요
        try:
            # API 키가 설정된 경우에만 실행
            glassnode_api_key = os.getenv("GLASSNODE_API_KEY")
            if glassnode_api_key:
                # 예: 액티브 주소 수 
                active_addresses_url = f"https://api.glassnode.com/v1/metrics/addresses/active_count?api_key={glassnode_api_key}&a=BTC"
                response = requests.get(active_addresses_url)
                if response.status_code == 200:
                    result["onchain_active_addresses"] = response.json()
                
                # 예: SOPR (Spent Output Profit Ratio)
                sopr_url = f"https://api.glassnode.com/v1/metrics/indicators/sopr?api_key={glassnode_api_key}&a=BTC"
                response = requests.get(sopr_url)
                if response.status_code == 200:
                    result["onchain_sopr"] = response.json()
                
                print("온체인 데이터 가져오기 성공")
        except Exception as e:
            print(f"온체인 데이터 가져오기 실패 (무시하고 계속): {e}")
            
        return result
    
    except Exception as e:
        print(f"시장 데이터 가져오기 오류: {e}")
        traceback.print_exc()
        return None

# 2. 데이터 처리 및 지표 계산 함수
def calculate_technical_indicators(data):
    """가져온 데이터에서 기술적 지표 계산"""
    try:
        indicators = {}
        
        # 2.1 기본 OHLCV 데이터에서 지표 계산
        df = data["upbit_daily_ohlcv"].copy()
        
        # 이동평균선 계산
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA60'] = df['close'].rolling(window=60).mean() if len(df) >= 60 else None
        df['MA120'] = df['close'].rolling(window=120).mean() if len(df) >= 120 else None
        
        # 볼린저 밴드
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['stddev'] = df['close'].rolling(window=20).std()
        df['upper_band'] = df['MA20'] + (df['stddev'] * 2)
        df['lower_band'] = df['MA20'] - (df['stddev'] * 2)
        df['bandwidth'] = (df['upper_band'] - df['lower_band']) / df['MA20']
        
        # RSI 계산 (Relative Strength Index, 상대강도지수)
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD 계산
        df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_hist'] = df['MACD'] - df['Signal']
        
        # 스토캐스틱 지표
        high_14 = df['high'].rolling(window=14).max()
        low_14 = df['low'].rolling(window=14).min()
        df['K'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
        df['D'] = df['K'].rolling(window=3).mean()
        
        # ATR (Average True Range)
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift())
        tr3 = abs(df['low'] - df['close'].shift())
        df['TR'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR'] = df['TR'].rolling(window=14).mean()
        
        # OBV (On-Balance Volume)
        df['OBV'] = np.where(df['close'] > df['close'].shift(), 
                            df['volume'], 
                            np.where(df['close'] < df['close'].shift(), 
                                    -df['volume'], 0)).cumsum()
        
        # 일봉 기술적 지표 저장
        indicators["daily_indicators"] = df
        
        # 2.2 시간봉 데이터에서 지표 계산
        df_hourly = data["upbit_hourly_ohlcv"].copy()
        
        # 간단한 이동평균 및 RSI만 계산
        df_hourly['MA5'] = df_hourly['close'].rolling(window=5).mean()
        df_hourly['MA10'] = df_hourly['close'].rolling(window=10).mean()
        
        delta = df_hourly['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df_hourly['RSI'] = 100 - (100 / (1 + rs))
        
        # 시간봉 기술적 지표 저장
        indicators["hourly_indicators"] = df_hourly
        
        # 2.3 거래량 프로필 계산 (가격대별 거래량 분포)
        # - 일별 OHLCV 데이터로 간단한 거래량 프로필 생성
        daily_data = data["upbit_daily_ohlcv"]
        
        # 가격 구간 정의 (최저가에서 최고가까지 10개 구간)
        price_min = daily_data['low'].min()
        price_max = daily_data['high'].max()
        price_ranges = np.linspace(price_min, price_max, 11)  # 10개 구간 경계 생성
        
        # 각 가격 구간별 거래량 합계
        volume_profile = []
        for i in range(len(price_ranges) - 1):
            price_low = price_ranges[i]
            price_high = price_ranges[i+1]
            
            # 해당 가격 구간에 속하는 날들의 거래량 합계
            total_volume = daily_data[(daily_data['low'] <= price_high) & 
                                      (daily_data['high'] >= price_low)]['volume'].sum()
            
            volume_profile.append({
                'price_range': f"{price_low:.0f} - {price_high:.0f}",
                'mid_price': (price_low + price_high) / 2,
                'volume': total_volume
            })
        
        # 거래량 프로필 저장
        indicators["volume_profile"] = volume_profile
        
       # 호가창 분석
        if "upbit_orderbook" in data and data["upbit_orderbook"]:
            try:
                orderbook = data["upbit_orderbook"]
                
                # pyupbit 0.2.34 버전 호가창 구조 확인
                if isinstance(orderbook, dict) and "ask_price" in orderbook:
                    # 단일 딕셔너리이고 직접 가격 정보가 있는 경우
                    best_bid = orderbook.get("bid_price", 0)
                    best_ask = orderbook.get("ask_price", 0)
                    
                    # 수량 정보
                    bid_quantity = orderbook.get("bid_size", 0)
                    ask_quantity = orderbook.get("ask_size", 0)
                    
                    # 간단한 매수/매도 비율 계산
                    total_bids_amount = best_bid * bid_quantity
                    total_asks_amount = best_ask * ask_quantity
                elif isinstance(orderbook, list) and len(orderbook) > 0:
                    # 리스트인 경우 첫 번째 요소 사용
                    first_item = orderbook[0]
                    if "orderbook_units" in first_item:
                        units = first_item["orderbook_units"]
                        
                        # 매수/매도 총액 계산
                        total_bids_amount = sum(unit.get("bid_price", 0) * unit.get("bid_size", 0) for unit in units)
                        total_asks_amount = sum(unit.get("ask_price", 0) * unit.get("ask_size", 0) for unit in units)
                        
                        # 호가창 스프레드
                        best_bid = units[0].get("bid_price", 0) if units else 0
                        best_ask = units[0].get("ask_price", 0) if units else 0
                    else:
                        # 다른 구조인 경우 기본값 설정
                        total_bids_amount = 0
                        total_asks_amount = 0
                        best_bid = 0
                        best_ask = 0
                else:
                    # 다른 형태인 경우 기본값 설정
                    total_bids_amount = 0
                    total_asks_amount = 0
                    best_bid = 0
                    best_ask = 0
                
                # 기본 분석 실행
                buy_sell_ratio = total_bids_amount / total_asks_amount if total_asks_amount > 0 else 1.0
                spread = best_ask - best_bid if best_bid > 0 else 0
                spread_percentage = (spread / best_bid) * 100 if best_bid > 0 else 0
                
                # 결과 저장
                indicators["orderbook_analysis"] = {
                    "buy_sell_ratio": buy_sell_ratio,
                    "spread": spread,
                    "spread_percentage": spread_percentage
                }
                
            except Exception as e:
                print(f"호가창 분석 중 오류 발생: {e}")
                # 오류 발생 시 기본값 설정
                indicators["orderbook_analysis"] = {
                    "buy_sell_ratio": 1.0,
                    "spread": 0,
                    "spread_percentage": 0
                }
            
        # 2.5 최근 체결 분석
        if "upbit_trades" in data and data["upbit_trades"]:
            trades = data["upbit_trades"]
            
            # 매수/매도 체결 분류
            buy_trades = [trade for trade in trades if trade['ask_bid'] == 'BID']
            sell_trades = [trade for trade in trades if trade['ask_bid'] == 'ASK']
            
            # 매수/매도 체결 비율
            buy_count = len(buy_trades)
            sell_count = len(sell_trades)
            buy_sell_count_ratio = buy_count / sell_count if sell_count > 0 else float('inf')
            
            # 매수/매도 체결 총량
            buy_volume = sum(float(trade['trade_volume']) for trade in buy_trades)
            sell_volume = sum(float(trade['trade_volume']) for trade in sell_trades)
            buy_sell_volume_ratio = buy_volume / sell_volume if sell_volume > 0 else float('inf')
            
            # 평균 체결 크기
            avg_trade_size = sum(float(trade['trade_volume']) for trade in trades) / len(trades) if trades else 0
            
            # 거래 시간 간격 (초 단위)
            if len(trades) >= 2:
                trade_times = [datetime.strptime(trade['trade_time'], '%H:%M:%S') for trade in trades]
                time_diffs = [(trade_times[i] - trade_times[i+1]).total_seconds() 
                             for i in range(len(trade_times)-1)]
                avg_time_between_trades = sum(time_diffs) / len(time_diffs) if time_diffs else None
            else:
                avg_time_between_trades = None
            
            # 결과 저장
            indicators["trade_analysis"] = {
                "buy_sell_count_ratio": buy_sell_count_ratio,
                "buy_sell_volume_ratio": buy_sell_volume_ratio,
                "avg_trade_size": avg_trade_size,
                "avg_time_between_trades": avg_time_between_trades
            }
            
        # 2.6 바이낸스 데이터 분석 (있는 경우)
        # 바이낸스 데이터 분석 (있는 경우)
        if "binance_daily_ohlcv" in data:
            try:
                binance_df = data["binance_daily_ohlcv"]
                
                # 데이터가 비어있지 않은지 확인
                if binance_df is not None and not (isinstance(binance_df, pd.DataFrame) and binance_df.empty):
                    # 간단한 이동평균
                    if isinstance(binance_df, pd.DataFrame):
                        binance_df['MA5'] = binance_df['close'].rolling(window=5).mean()
                        binance_df['MA20'] = binance_df['close'].rolling(window=20).mean()
                        
                        # USDT/KRW 가격 가정 (1 USDT = 약 1350원으로 가정)
                        usdt_krw_rate = 1350  # 실제로는 API로 환율을 가져오는 것이 좋음
                        
                        # 마지막 바이낸스 가격과 업비트 가격 비교
                        if "upbit_ticker" in data and data["upbit_ticker"]:
                            try:
                                # 바이낸스 가격 추출
                                try:
                                    binance_last_price = binance_df['close'].iloc[-1]
                                    if isinstance(binance_last_price, list):
                                        binance_last_price = binance_last_price[0] if binance_last_price else 0
                                except Exception as e:
                                    print(f"바이낸스 가격 추출 오류: {e}")
                                    binance_last_price = 0
                                
                                # 업비트 가격 추출
                                try:
                                    upbit_last_price = data["upbit_ticker"]
                                    if isinstance(upbit_last_price, dict):
                                        # 딕셔너리에서 가격 추출
                                        for key in ["trade_price", "close", "last", "price"]:
                                            if key in upbit_last_price:
                                                upbit_last_price = upbit_last_price[key]
                                                break
                                        else:
                                            # 키를 찾지 못한 경우 첫 번째 숫자 사용
                                            for k, v in upbit_last_price.items():
                                                if isinstance(v, (int, float)):
                                                    upbit_last_price = v
                                                    break
                                            else:
                                                upbit_last_price = 0
                                    elif isinstance(upbit_last_price, list):
                                        # 리스트인 경우 첫 번째 값 시도
                                        upbit_last_price = upbit_last_price[0] if upbit_last_price else 0
                                        if isinstance(upbit_last_price, dict):
                                            for key in ["trade_price", "close", "last", "price"]:
                                                if key in upbit_last_price:
                                                    upbit_last_price = upbit_last_price[key]
                                                    break
                                except Exception as e:
                                    print(f"업비트 가격 추출 오류: {e}")
                                    upbit_last_price = 0
                                
                                # 김프 계산
                                try:
                                    if binance_last_price > 0 and upbit_last_price > 0:
                                        binance_krw_price = binance_last_price * usdt_krw_rate
                                        kimp_percentage = ((upbit_last_price - binance_krw_price) / binance_krw_price) * 100
                                        
                                        try:
                                            indicators["exchange_comparison"] = {
                                                "binance_price_usdt": binance_last_price,
                                                "binance_price_krw_estimated": binance_krw_price,
                                                "upbit_price_krw": upbit_last_price,
                                                "korea_premium_percentage": kimp_percentage
                                            }
                                        except Exception as e:
                                            print(f"exchange_comparison 저장 중 오류: {e}")
                                except Exception as e:
                                    print(f"김프 계산 중 오류 발생: {e}")
                                    binance_krw_price = 0
                                    kimp_percentage = 0
                                    
                                    # 기본값으로 저장
                                    try:
                                        indicators["exchange_comparison"] = {
                                            "binance_price_usdt": 0,
                                            "binance_price_krw_estimated": 0,
                                            "upbit_price_krw": 0,
                                            "korea_premium_percentage": 0
                                        }
                                    except Exception as e:
                                        print(f"exchange_comparison 기본값 저장 중 오류: {e}")
                            except Exception as e:
                                print(f"김프 계산 중 오류: {e}")
                        
                        # 바이낸스 기술적 지표 저장
                        indicators["binance_indicators"] = binance_df
            except Exception as e:
                print(f"바이낸스 데이터 분석 중 오류: {e}")
            
        # 2.7 시장 심리 지수 (Fear & Greed)
        if "fear_greed_index" in data and data["fear_greed_index"]:
            fg_data = data["fear_greed_index"]
            current_value = fg_data['data'][0]['value'] if 'data' in fg_data and fg_data['data'] else None
            current_classification = fg_data['data'][0]['value_classification'] if 'data' in fg_data and fg_data['data'] else None
            
            indicators["market_sentiment"] = {
                "fear_greed_value": current_value,
                "fear_greed_classification": current_classification
            }
            
        # 2.8 온체인 데이터 분석 (있는 경우)
        if "onchain_active_addresses" in data and data["onchain_active_addresses"]:
            # 최근 액티브 주소 수 추출
            active_addresses = data["onchain_active_addresses"]
            recent_active = active_addresses[-7:] if active_addresses else []
            
            # 최근 7일간 추세 계산
            if recent_active and len(recent_active) >= 7:
                first_value = recent_active[0]['v']
                last_value = recent_active[-1]['v']
                active_addr_trend = ((last_value - first_value) / first_value) * 100
            else:
                active_addr_trend = None
                
            # SOPR 분석 (Spent Output Profit Ratio)
            if "onchain_sopr" in data and data["onchain_sopr"]:
                sopr_data = data["onchain_sopr"]
                recent_sopr = sopr_data[-7:] if sopr_data else []
                
                if recent_sopr and len(recent_sopr) >= 1:
                    current_sopr = recent_sopr[-1]['v']
                    # SOPR > 1 : 이익 실현, SOPR < 1 : 손실 실현
                    sopr_signal = "이익 실현중" if current_sopr > 1 else "손실 실현중"
                else:
                    current_sopr = None
                    sopr_signal = None
                    
                indicators["onchain_analysis"] = {
                    "active_addresses_7d_trend": active_addr_trend,
                    "current_sopr": current_sopr,
                    "sopr_signal": sopr_signal
                }
        
        return indicators
        
    except Exception as e:
        print(f"기술적 지표 계산 오류: {e}")
        traceback.print_exc()
        return None

# 3. 통합 매매 결정 분석 함수
def perform_integrated_analysis(market_data, indicators):
    """다양한 데이터 소스를 종합하여 매매 결정을 내립니다."""
    try:
        signals = []
        signal_strengths = {}  # 신호 강도 저장
        
        # 3.1 일봉 기술적 지표 분석
        if "daily_indicators" in indicators and not indicators["daily_indicators"].empty:
            daily_df = indicators["daily_indicators"]
            last_row = daily_df.iloc[-1]  # 가장 최근 데이터
            
            # 이동평균선 분석 (골든크로스/데드크로스)
            ma5 = last_row['MA5']
            ma10 = last_row['MA10']
            ma20 = last_row['MA20']
            ma60 = last_row['MA60'] if 'MA60' in last_row and not pd.isna(last_row['MA60']) else None
            
            # 단기 이동평균선 분석
            if ma5 > ma20:
                signals.append({
                    "source": "이동평균선(MA)",
                    "signal": "buy",
                    "strength": 0.6,
                    "description": "골든크로스 상태 (5일 이동평균선이 20일 이동평균선 위에 위치)"
                })
                signal_strengths["MA"] = 0.6
            elif ma5 < ma20:
                signals.append({
                    "source": "이동평균선(MA)",
                    "signal": "sell",
                    "strength": 0.6,
                    "description": "데드크로스 상태 (5일 이동평균선이 20일 이동평균선 아래에 위치)"
                })
                signal_strengths["MA"] = -0.6
            else:
                signals.append({
                    "source": "이동평균선(MA)",
                    "signal": "hold",
                    "strength": 0,
                    "description": "이동평균선 중립 상태"
                })
                signal_strengths["MA"] = 0
                
            # 장기 이동평균선 추세 (존재하는 경우)
            if ma60 is not None:
                if last_row['close'] > ma60:
                    signals.append({
                        "source": "장기추세(MA60)",
                        "signal": "buy",
                        "strength": 0.4,
                        "description": "장기 상승 추세 (현재가가 60일 이동평균선 위에 위치)"
                    })
                    signal_strengths["MA60"] = 0.4
                else:
                    signals.append({
                        "source": "장기추세(MA60)",
                        "signal": "sell",
                        "strength": 0.4,
                        "description": "장기 하락 추세 (현재가가 60일 이동평균선 아래에 위치)"
                    })
                    signal_strengths["MA60"] = -0.4
            
            # 볼린저 밴드 분석
            upper_band = last_row['upper_band']
            lower_band = last_row['lower_band']
            mid_band = last_row['MA20']  # 중앙선은 20일 이동평균선
            
            if last_row['close'] > upper_band:
                signals.append({
                    "source": "볼린저밴드(BB)",
                    "signal": "sell",
                    "strength": 0.7,
                    "description": "과매수 상태 (볼린저 밴드 상단 돌파)"
                })
                signal_strengths["BB"] = -0.7
            elif last_row['close'] < lower_band:
                signals.append({
                    "source": "볼린저밴드(BB)",
                    "signal": "buy",
                    "strength": 0.7,
                    "description": "과매도 상태 (볼린저 밴드 하단 돌파)"
                })
                signal_strengths["BB"] = 0.7
            else:
                # 밴드 내에서의 위치를 백분율로 계산 (-1: 하단, 0: 중앙, 1: 상단)
                band_position = 2 * (last_row['close'] - mid_band) / (upper_band - lower_band) if (upper_band - lower_band) != 0 else 0
                
                if band_position > 0.5:
                    signals.append({
                        "source": "볼린저밴드(BB)",
                        "signal": "sell",
                        "strength": 0.3,
                        "description": f"상단 접근중 (밴드 내 위치: 상위 {(band_position*50):.0f}%)"
                    })
                    signal_strengths["BB"] = -0.3
                elif band_position < -0.5:
                    signals.append({
                        "source": "볼린저밴드(BB)",
                        "signal": "buy",
                        "strength": 0.3,
                        "description": f"하단 접근중 (밴드 내 위치: 하위 {(abs(band_position)*50):.0f}%)"
                    })
                    signal_strengths["BB"] = 0.3
                else:
                    signals.append({
                        "source": "볼린저밴드(BB)",
                        "signal": "hold",
                        "strength": 0,
                        "description": "밴드 중앙 부근 (중립적 위치)"
                    })
                    signal_strengths["BB"] = 0
            
            # RSI 분석 (과매수/과매도)
            rsi = last_row['RSI']
            
            if rsi > 70:
                signals.append({
                    "source": "RSI(상대강도지수)",
                    "signal": "sell",
                    "strength": 0.8,
                    "description": f"과매수 상태 (RSI: {rsi:.1f} > 70)"
                })
                signal_strengths["RSI"] = -0.8
            elif rsi < 30:
                signals.append({
                    "source": "RSI(상대강도지수)",
                    "signal": "buy",
                    "strength": 0.8,
                    "description": f"과매도 상태 (RSI: {rsi:.1f} < 30)"
                })
                signal_strengths["RSI"] = 0.8
            else:
                # RSI 중간 영역 (30-70) 내에서의 위치
                rsi_normalized = (rsi - 30) / 40  # 0(=30) 에서 1(=70) 사이로 정규화
                if rsi_normalized > 0.75:  # RSI > 60
                    signals.append({
                        "source": "RSI(상대강도지수)",
                        "signal": "sell",
                        "strength": 0.2,
                        "description": f"매수세 우세 (RSI: {rsi:.1f})"
                    })
                    signal_strengths["RSI"] = -0.2
                elif rsi_normalized < 0.25:  # RSI < 40
                    signals.append({
                        "source": "RSI(상대강도지수)",
                        "signal": "buy",
                        "strength": 0.2,
                        "description": f"매도세 우세 (RSI: {rsi:.1f})"
                    })
                    signal_strengths["RSI"] = 0.2
                else:
                    signals.append({
                        "source": "RSI(상대강도지수)",
                        "signal": "hold",
                        "strength": 0,
                        "description": f"중립적 (RSI: {rsi:.1f})"
                    })
                    signal_strengths["RSI"] = 0
            
            # MACD 분석
            macd = last_row['MACD']
            signal_line = last_row['Signal']
            macd_hist = last_row['MACD_hist']
            
            # MACD 히스토그램 부호 변화 확인 (매매 신호)
            prev_macd_hist = daily_df.iloc[-2]['MACD_hist'] if len(daily_df) > 1 else 0
            
            if macd_hist > 0 and prev_macd_hist <= 0:
                # 골든크로스 (매수 신호)
                signals.append({
                    "source": "MACD",
                    "signal": "buy",
                    "strength": 0.7,
                    "description": "MACD 골든크로스 (MACD 선이 신호선 상향 돌파)"
                })
                signal_strengths["MACD"] = 0.7
            elif macd_hist < 0 and prev_macd_hist >= 0:
                # 데드크로스 (매도 신호)
                signals.append({
                    "source": "MACD",
                    "signal": "sell",
                    "strength": 0.7,
                    "description": "MACD 데드크로스 (MACD 선이 신호선 하향 돌파)"
                })
                signal_strengths["MACD"] = -0.7
            elif macd_hist > 0:
                signals.append({
                    "source": "MACD",
                    "signal": "buy",
                    "strength": 0.3,
                    "description": "MACD 상승 추세 유지중"
                })
                signal_strengths["MACD"] = 0.3
            else:
                signals.append({
                    "source": "MACD",
                    "signal": "sell",
                    "strength": 0.3,
                    "description": "MACD 하락 추세 유지중"
                })
                signal_strengths["MACD"] = -0.3
                
            # 스토캐스틱 분석
            k = last_row['K']
            d = last_row['D']
            
            if k > 80 and d > 80:
                signals.append({
                    "source": "스토캐스틱",
                    "signal": "sell",
                    "strength": 0.6,
                    "description": f"과매수 구간 (K: {k:.1f}, D: {d:.1f})"
                })
                signal_strengths["Stochastic"] = -0.6
            elif k < 20 and d < 20:
                signals.append({
                    "source": "스토캐스틱",
                    "signal": "buy",
                    "strength": 0.6,
                    "description": f"과매도 구간 (K: {k:.1f}, D: {d:.1f})"
                })
                signal_strengths["Stochastic"] = 0.6
            elif k > d and k < 80 and d < 80:
                signals.append({
                    "source": "스토캐스틱",
                    "signal": "buy",
                    "strength": 0.3,
                    "description": f"상승 반전 신호 (K > D, K: {k:.1f}, D: {d:.1f})"
                })
                signal_strengths["Stochastic"] = 0.3
            elif k < d and k > 20 and d > 20:
                signals.append({
                    "source": "스토캐스틱",
                    "signal": "sell",
                    "strength": 0.3,
                    "description": f"하락 반전 신호 (K < D, K: {k:.1f}, D: {d:.1f})"
                })
                signal_strengths["Stochastic"] = -0.3
            else:
                signals.append({
                    "source": "스토캐스틱",
                    "signal": "hold",
                    "strength": 0,
                    "description": f"중립 (K: {k:.1f}, D: {d:.1f})"
                })
                signal_strengths["Stochastic"] = 0
                
        # 3.2 호가창 분석
        if "orderbook_analysis" in indicators:
            order_analysis = indicators["orderbook_analysis"]
            
            buy_sell_ratio = order_analysis.get("buy_sell_ratio")
            if buy_sell_ratio is not None:
                if buy_sell_ratio > 1.5:
                    signals.append({
                        "source": "호가창(매수/매도비율)",
                        "signal": "buy",
                        "strength": 0.6,
                        "description": f"강한 매수세 (매수/매도 비율: {buy_sell_ratio:.2f})"
                    })
                    signal_strengths["Orderbook"] = 0.6
                elif buy_sell_ratio < 0.7:
                    signals.append({
                        "source": "호가창(매수/매도비율)",
                        "signal": "sell",
                        "strength": 0.6,
                        "description": f"강한 매도세 (매수/매도 비율: {buy_sell_ratio:.2f})"
                    })
                    signal_strengths["Orderbook"] = -0.6
                else:
                    signals.append({
                        "source": "호가창(매수/매도비율)",
                        "signal": "hold",
                        "strength": 0,
                        "description": f"중립적 호가창 (매수/매도 비율: {buy_sell_ratio:.2f})"
                    })
                    signal_strengths["Orderbook"] = 0
        
        # 3.3 체결 분석
        if "trade_analysis" in indicators:
            trade_analysis = indicators["trade_analysis"]
            
            buy_sell_volume_ratio = trade_analysis.get("buy_sell_volume_ratio")
            if buy_sell_volume_ratio is not None:
                if buy_sell_volume_ratio > 1.5:
                    signals.append({
                        "source": "체결데이터(매수/매도량)",
                        "signal": "buy",
                        "strength": 0.5,
                        "description": f"매수 체결 우세 (매수/매도 거래량 비율: {buy_sell_volume_ratio:.2f})"
                    })
                    signal_strengths["Trades"] = 0.5
                elif buy_sell_volume_ratio < 0.7:
                    signals.append({
                        "source": "체결데이터(매수/매도량)",
                        "signal": "sell",
                        "strength": 0.5,
                        "description": f"매도 체결 우세 (매수/매도 거래량 비율: {buy_sell_volume_ratio:.2f})"
                    })
                    signal_strengths["Trades"] = -0.5
                else:
                    signals.append({
                        "source": "체결데이터(매수/매도량)",
                        "signal": "hold",
                        "strength": 0,
                        "description": f"중립적 체결 흐름 (매수/매도 거래량 비율: {buy_sell_volume_ratio:.2f})"
                    })
                    signal_strengths["Trades"] = 0
                    
        # 3.4 김프(KIMP) 분석
        if "exchange_comparison" in indicators:
            exc_comparison = indicators["exchange_comparison"]
            
            korea_premium = exc_comparison.get("korea_premium_percentage")
            if korea_premium is not None:
                if korea_premium > 5.0:
                    signals.append({
                        "source": "김프(한국 프리미엄)",
                        "signal": "sell",
                        "strength": 0.5,
                        "description": f"높은 한국 프리미엄 (김프: {korea_premium:.2f}%)"
                    })
                    signal_strengths["KIMP"] = -0.5
                elif korea_premium < -1.0:
                    signals.append({
                        "source": "김프(한국 프리미엄)",
                        "signal": "buy",
                        "strength": 0.5,
                        "description": f"한국 프리미엄 역전 (김프: {korea_premium:.2f}%)"
                    })
                    signal_strengths["KIMP"] = 0.5
                else:
                    signals.append({
                        "source": "김프(한국 프리미엄)",
                        "signal": "hold",
                        "strength": 0,
                        "description": f"보통 수준의 한국 프리미엄 (김프: {korea_premium:.2f}%)"
                    })
                    signal_strengths["KIMP"] = 0
        
        # 3.5 시장 심리 지수 분석
        if "market_sentiment" in indicators:
            sentiment = indicators["market_sentiment"]
            
            fear_greed_value = sentiment.get("fear_greed_value")
            fear_greed_class = sentiment.get("fear_greed_classification")
            
            if fear_greed_value is not None:
                fear_greed_value = int(fear_greed_value)
                
                if fear_greed_value <= 25:  # 극도의 공포
                    signals.append({
                        "source": "시장심리(공포&탐욕지수)",
                        "signal": "buy",
                        "strength": 0.7,
                        "description": f"극도의 공포 상태 (Fear & Greed: {fear_greed_value}, {fear_greed_class})"
                    })
                    signal_strengths["FearGreed"] = 0.7
                elif fear_greed_value >= 75:  # 극도의 탐욕
                    signals.append({
                        "source": "시장심리(공포&탐욕지수)",
                        "signal": "sell",
                        "strength": 0.7,
                        "description": f"극도의 탐욕 상태 (Fear & Greed: {fear_greed_value}, {fear_greed_class})"
                    })
                    signal_strengths["FearGreed"] = -0.7
                elif fear_greed_value < 40:  # 공포
                    signals.append({
                        "source": "시장심리(공포&탐욕지수)",
                        "signal": "buy",
                        "strength": 0.4,
                        "description": f"공포 우세 상태 (Fear & Greed: {fear_greed_value}, {fear_greed_class})"
                    })
                    signal_strengths["FearGreed"] = 0.4
                elif fear_greed_value > 60:  # 탐욕
                    signals.append({
                        "source": "시장심리(공포&탐욕지수)",
                        "signal": "sell",
                        "strength": 0.4,
                        "description": f"탐욕 우세 상태 (Fear & Greed: {fear_greed_value}, {fear_greed_class})"
                    })
                    signal_strengths["FearGreed"] = -0.4
                else:
                    signals.append({
                        "source": "시장심리(공포&탐욕지수)",
                        "signal": "hold",
                        "strength": 0,
                        "description": f"중립적 시장 심리 (Fear & Greed: {fear_greed_value}, {fear_greed_class})"
                    })
                    signal_strengths["FearGreed"] = 0
                    
        # 3.6 온체인 데이터 분석
        if "onchain_analysis" in indicators:
            onchain = indicators["onchain_analysis"]
            
            current_sopr = onchain.get("current_sopr")
            sopr_signal = onchain.get("sopr_signal")
            
            if current_sopr is not None and sopr_signal is not None:
                if current_sopr < 0.95:
                    signals.append({
                        "source": "온체인(SOPR)",
                        "signal": "buy",
                        "strength": 0.6,
                        "description": f"손실 상태에서 매도 중 (SOPR: {current_sopr:.3f})"
                    })
                    signal_strengths["SOPR"] = 0.6
                elif current_sopr > 1.05:
                    signals.append({
                        "source": "온체인(SOPR)",
                        "signal": "sell",
                        "strength": 0.6,
                        "description": f"이익 상태에서 매도 중 (SOPR: {current_sopr:.3f})"
                    })
                    signal_strengths["SOPR"] = -0.6
                else:
                    signals.append({
                        "source": "온체인(SOPR)",
                        "signal": "hold",
                        "strength": 0,
                        "description": f"중립적 매도 패턴 (SOPR: {current_sopr:.3f})"
                    })
                    signal_strengths["SOPR"] = 0
            
            # 액티브 주소 추세
            active_addr_trend = onchain.get("active_addresses_7d_trend")
            if active_addr_trend is not None:
                if active_addr_trend > 10:
                    signals.append({
                        "source": "온체인(활성주소)",
                        "signal": "buy",
                        "strength": 0.4,
                        "description": f"네트워크 활성 증가 (7일 활성주소 변화: {active_addr_trend:.1f}%)"
                    })
                    signal_strengths["ActiveAddr"] = 0.4
                elif active_addr_trend < -10:
                    signals.append({
                        "source": "온체인(활성주소)",
                        "signal": "sell",
                        "strength": 0.4,
                        "description": f"네트워크 활성 감소 (7일 활성주소 변화: {active_addr_trend:.1f}%)"
                    })
                    signal_strengths["ActiveAddr"] = -0.4
                else:
                    signals.append({
                        "source": "온체인(활성주소)",
                        "signal": "hold",
                        "strength": 0,
                        "description": f"네트워크 활성 안정적 (7일 활성주소 변화: {active_addr_trend:.1f}%)"
                    })
                    signal_strengths["ActiveAddr"] = 0
        
        # 3.7 종합 신호 계산
        # 가중 평균 신호 계산
        total_strength = 0
        weighted_sum = 0
        count = 0
        
        for source, strength in signal_strengths.items():
            count += 1
            weighted_sum += strength
            total_strength += abs(strength)
        
        if count > 0:
            avg_signal = weighted_sum / count
            confidence = min(total_strength / count / 0.8, 1.0)  # 최대 신뢰도는 1.0
        else:
            avg_signal = 0
            confidence = 0
        
        # 최종 매매 결정
        if avg_signal > 0.2:
            decision = "buy"
            decision_kr = "매수"
        elif avg_signal < -0.2:
            decision = "sell"
            decision_kr = "매도"
        else:
            decision = "hold"
            decision_kr = "홀드"
        
        # 거래 강도에 따른 추가 결정 (강한 매수/매도/홀드)
        if abs(avg_signal) > 0.5:
            strength_prefix = "강한 "
        elif abs(avg_signal) > 0.3:
            strength_prefix = "보통 "
        else:
            strength_prefix = "약한 "
        
        decision_with_strength = strength_prefix + decision_kr
        
        # 현재 시장 상태 요약
        current_price = None
        price_change_24h = None
        
        if "upbit_ticker" in market_data and market_data["upbit_ticker"]:
            current_price = market_data["upbit_ticker"]
            if "upbit_daily_ohlcv" in market_data and not market_data["upbit_daily_ohlcv"].empty:
                df = market_data["upbit_daily_ohlcv"]
                if len(df) >= 2:
                    yesterday_close = df.iloc[-2]['close']
                    today_close = df.iloc[-1]['close']
                    price_change_24h = ((today_close - yesterday_close) / yesterday_close) * 100
        
        # 결과 조합
        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "decision": decision,
            "decision_kr": decision_with_strength,
            "confidence": confidence,
            "avg_signal_strength": avg_signal,
            "signals": signals,
            "signal_counts": {
                "buy": len([s for s in signals if s["signal"] == "buy"]),
                "sell": len([s for s in signals if s["signal"] == "sell"]),
                "hold": len([s for s in signals if s["signal"] == "hold"])
            }
        }
        
        # 현재 가격 및 변동률 추가
        if current_price is not None:
            result["current_price"] = current_price
        if price_change_24h is not None:
            result["price_change_24h"] = f"{price_change_24h:.2f}%"
        
        return result
        
    except Exception as e:
        print(f"분석 오류: {e}")
        traceback.print_exc()
        return None

# 4. AI 기반 분석 함수
def get_claude_analysis(market_data):
    """Claude AI를 사용하여 비트코인 데이터 분석"""
    try:
        import anthropic
        
        ANTHROPIC_API_KEY = os.getenv("CLAUDE_API_KEY")
        if not ANTHROPIC_API_KEY:
            print("Claude API 키가 설정되지 않았습니다.")
            return None
            
        client = anthropic.Anthropic(
            api_key=ANTHROPIC_API_KEY,
        )
        
        # 분석용 데이터 준비
        # OHLCV 데이터
        ohlcv_data = None
        if "upbit_daily_ohlcv" in market_data and not market_data["upbit_daily_ohlcv"].empty:
            ohlcv_data = market_data["upbit_daily_ohlcv"].to_json()
        
        # 기타 지표 데이터 (간결성을 위해 일부만 포함)
        data_for_claude = {
            "ohlcv_data": ohlcv_data,
            "current_price": market_data.get("upbit_ticker"),
        }
        
        # 호가창 데이터 추가
        if "upbit_orderbook" in market_data and market_data["upbit_orderbook"]:
            orderbook_simple = {
                "bid_prices": [unit['bid_price'] for unit in market_data["upbit_orderbook"][0]['orderbook_units'][:5]],
                "bid_sizes": [unit['bid_size'] for unit in market_data["upbit_orderbook"][0]['orderbook_units'][:5]],
                "ask_prices": [unit['ask_price'] for unit in market_data["upbit_orderbook"][0]['orderbook_units'][:5]],
                "ask_sizes": [unit['ask_size'] for unit in market_data["upbit_orderbook"][0]['orderbook_units'][:5]]
            }
            data_for_claude["orderbook"] = orderbook_simple
        
        # 김프 데이터 추가
        if "exchange_comparison" in market_data and market_data["exchange_comparison"]:
            data_for_claude["korea_premium"] = market_data["exchange_comparison"]
        
        # Fear & Greed 지수 추가
        if "market_sentiment" in market_data and market_data["market_sentiment"]:
            data_for_claude["fear_greed"] = market_data["market_sentiment"]
        
        # 온체인 데이터 추가
        if "onchain_analysis" in market_data and market_data["onchain_analysis"]:
            data_for_claude["onchain"] = market_data["onchain_analysis"]
        
        # Claude API 호출
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            temperature=0.7,
            system="You are an expert in Bitcoin investing and technical analysis. Analyze the provided Bitcoin market data and give a clear buy, sell, or hold recommendation. Your response must be in valid JSON format with exactly this structure: {\"decision\": \"buy|sell|hold\", \"confidence\": 0.1-1.0, \"reason\": \"explanation\", \"price_target\": {\"short_term\": value, \"medium_term\": value}}. Provide insightful reasoning for your decision based on the technical indicators, market sentiment, and on-chain data if available. Please be sure to write the reason for your decision in Korean.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Here is Bitcoin market data: {json.dumps(data_for_claude)}. Provide your analysis and recommendation."
                        }
                    ]
                }
            ]
        )
        
        # 응답 추출 및 처리
        result_text = response.content[0].text  # 텍스트 내용 추출
        print("Claude 응답 원본:", result_text)
        
        # JSON 문자열 추출 (응답에 다른 텍스트가 포함된 경우를 대비)
        import re
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                result = json.loads(json_str)
                return result
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류: {e}")
                return None
        else:
            print("응답에서 JSON 형식을 찾을 수 없습니다.")
            return None
            
    except Exception as e:
        print(f"Claude API 오류: {e}")
        traceback.print_exc()
        return None

# 5. 매매 실행 함수
def execute_trade(decision, confidence, market_data):
    """매매 결정에 따라 실제 거래를 실행합니다."""
    print(f"\n===== 매매 결정: {decision} (신뢰도: {confidence:.2f}) =====")
    
    try:
        # 업비트 API 연결
        import pyupbit
        access = os.getenv("UPBIT_ACCESS_KEY")
        secret = os.getenv("UPBIT_SECRET_KEY")
        
        if not access or not secret:
            print("업비트 API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
            return
            
        upbit = pyupbit.Upbit(access, secret)
        
        # 현재 자산 정보 확인
        my_krw = upbit.get_balance("KRW")
        my_btc = upbit.get_balance("KRW-BTC")
        
        # 타입 검사 및 변환 추가
        if my_krw and not isinstance(my_krw, (int, float)):
            try:
                my_krw = float(my_krw) if my_krw else 0
            except (TypeError, ValueError):
                my_krw = 0
                print("원화 잔고를 숫자로 변환할 수 없습니다. 0으로 설정합니다.")
            
        if my_btc and not isinstance(my_btc, (int, float)):
            try:
                my_btc = float(my_btc) if my_btc else 0
            except (TypeError, ValueError):
                my_btc = 0
                print("비트코인 잔고를 숫자로 변환할 수 없습니다. 0으로 설정합니다.")
        
        # 현재가 처리 - 타입에 따라 적절히 처리
        current_price = 0
        try:
            # 직접 현재가 조회
            current_price_direct = pyupbit.get_current_price("KRW-BTC")
            if isinstance(current_price_direct, (int, float)):
                current_price = current_price_direct
            elif isinstance(current_price_direct, dict) and "trade_price" in current_price_direct:
                current_price = current_price_direct["trade_price"]
            else:
                print(f"직접 조회한 현재가 형식 확인: {type(current_price_direct)}")
                # 리스트일 경우 첫 번째 항목 시도
                if isinstance(current_price_direct, list) and len(current_price_direct) > 0:
                    if isinstance(current_price_direct[0], (int, float)):
                        current_price = current_price_direct[0]
                    elif isinstance(current_price_direct[0], dict) and "trade_price" in current_price_direct[0]:
                        current_price = current_price_direct[0]["trade_price"]
        except Exception as e:
            print(f"현재가 직접 조회 중 오류: {e}")
            
        # 값이 없으면 임의의 가격 사용 (테스트용)
        if current_price == 0:
            current_price = 80000000  # 임의의 비트코인 가격 (테스트용)
            print(f"현재가를 가져올 수 없어 임의의 가격({current_price})을 사용합니다.")
        
        # 이제 수치 계산 가능
        estimated_btc_value = my_btc * current_price if my_btc and current_price else 0
        
        print(f"현재 보유 자산: {my_krw:.0f}원 + {my_btc} BTC (약 {estimated_btc_value:.0f}원)")
        print(f"총 자산 가치: 약 {my_krw + estimated_btc_value:.0f}원")
        
        # 나머지 함수 코드는 그대로 유지...
        
        # 사용자 설정 값으로 투자 비율 조정
        # 신뢰도가 높을수록 더 많은 비율로 투자/매도
        min_ratio = INVESTMENT_RATIOS.get("min_ratio", 0.2)  # 최소 투자 비율 (기본값: 20%)
        max_ratio = INVESTMENT_RATIOS.get("max_ratio", 0.5)  # 최대 투자 비율 (기본값: 50%)
        # 신뢰도에 따라 min_ratio~max_ratio 사이의 값으로 스케일링
        trade_ratio = min_ratio + (confidence * (max_ratio - min_ratio))
        
        # 결정에 따라 매매 실행
        if decision == "buy":
            # 신뢰도에 따라 투자 비율 결정
            invest_amount = my_krw * trade_ratio
            
            min_order_amount = TRADING_SETTINGS.get("min_order_amount", 5000)  # 최소 주문 금액 사용자 설정
            
            if invest_amount > min_order_amount:  # 최소 주문 금액 이상
                print(f"매수 시도: {invest_amount:.0f}원 (보유 KRW의 {trade_ratio*100:.0f}%)")
                order = upbit.buy_market_order("KRW-BTC", invest_amount)
                print(f"매수 주문 결과: {order}")
            else:
                print(f"매수 실패: 주문 금액이 {min_order_amount}원 미만입니다 (현재 보유 KRW: {my_krw}원)")
                
        elif decision == "sell":
            # 신뢰도에 따라 매도 비율 결정
            sell_ratio = trade_ratio
            sell_amount = my_btc * sell_ratio
            
            # 현재가 확인 (매도 금액 계산용)
            estimated_value = sell_amount * current_price
            
            min_order_amount = TRADING_SETTINGS.get("min_order_amount", 5000)  # 최소 주문 금액 사용자 설정
            
            if estimated_value > min_order_amount:  # 최소 주문 금액 이상
                print(f"매도 시도: {sell_amount} BTC (약 {estimated_value:.0f}원, 보유량의 {sell_ratio*100:.0f}%)")
                order = upbit.sell_market_order("KRW-BTC", sell_amount)
                print(f"매도 주문 결과: {order}")
            else:
                print(f"매도 실패: 주문 금액이 {min_order_amount}원 미만입니다 (현재 보유 BTC: {my_btc}, 추정가치: {estimated_value:.0f}원)")
        else:  # hold
            print("현재 포지션 유지 (홀드)")
    
    except Exception as e:
        print(f"매매 실행 중 오류 발생: {e}")
        traceback.print_exc()
        print("테스트 모드로 실행: 실제 매매는 이루어지지 않았습니다.")

# 6. 통합 거래 함수 (메인 함수)
def integrated_trading():
    """확장된 데이터와 분석을 통한 비트코인 자동매매의 전체 프로세스를 실행합니다."""
    try:
        # 1. 다양한 거래소 데이터 가져오기
        print("\n== 거래소 데이터 수집 시작 ==")
        market_data = get_enhanced_market_data()
        if market_data is None:
            print("데이터를 가져오지 못했습니다. 다음 실행을 기다립니다.")
            return
            
        # 2. 기술적 지표 계산
        print("\n== 기술적 지표 계산 시작 ==")
        indicators = calculate_technical_indicators(market_data)
        if indicators is None:
            print("지표 계산에 실패했습니다. 다음 실행을 기다립니다.")
            return
            
        # 3. 통합 분석 실행
        print("\n== 통합 분석 실행 ==")
        analysis_result = perform_integrated_analysis(market_data, indicators)
        
        # 4. Claude AI로 분석 시도 (선택적)
        claude_result = None
        use_claude = CLAUDE_SETTINGS.get("use_claude", False)
        
        if use_claude:
            print("\n== Claude AI로 분석 시도 ==")
            claude_result = get_claude_analysis(market_data)
        
        # 5. 최종 결정 및 결과 출력
        final_result = None
        
        if analysis_result and claude_result:
            print("\n===== 분석 결과 비교 =====")
            print("자체 분석:", analysis_result["decision"], f"(신뢰도: {analysis_result['confidence']:.2f})")
            print("Claude 분석:", claude_result["decision"], f"(신뢰도: {claude_result.get('confidence', 0.5):.2f})")
            
            # Claude의 분석 이유도 출력
            if "reason" in claude_result:
                print(f"\nClaude 분석 이유: {claude_result['reason']}")
                
            # 가격 목표가 있다면 출력
            if "price_target" in claude_result and claude_result["price_target"]:
                price_target = claude_result["price_target"]
                print("\nClaude 가격 전망:")
                if "short_term" in price_target:
                    print(f"  단기: {price_target['short_term']:,}원")
                if "medium_term" in price_target:
                    print(f"  중기: {price_target['medium_term']:,}원")
            
            # 두 분석이 일치하면 신뢰도 상승
            if analysis_result["decision"] == claude_result["decision"]:
                confidence_boost = CLAUDE_SETTINGS.get("confidence_boost", 0.1)
                boosted_confidence = min(0.95, (analysis_result["confidence"] + claude_result.get("confidence", 0.5)) / 2 + confidence_boost)
                final_decision = analysis_result["decision"]
                reason = f"자체 분석과 Claude AI 분석 결과가 일치 ({final_decision}). 신뢰도 상승."
            else:
                # 신뢰도가 더 높은 분석 선택
                claude_weight = CLAUDE_SETTINGS.get("weight", 1.0)
                analysis_weight = 1.0
                total_weight = analysis_weight + claude_weight
                
                if analysis_result["confidence"] >= claude_result.get("confidence", 0.5):
                    final_decision = analysis_result["decision"]
                    boosted_confidence = (analysis_result["confidence"] * analysis_weight) / total_weight
                    reason = f"자체 분석 신뢰도({analysis_result['confidence']:.2f})가 더 높아 채택"
                else:
                    final_decision = claude_result["decision"]
                    boosted_confidence = (claude_result.get("confidence", 0.5) * claude_weight) / total_weight
                    reason = f"Claude 분석 신뢰도({claude_result.get('confidence', 0.5):.2f})가 더 높아 채택"
            
            final_result = {
                "decision": final_decision,
                "confidence": boosted_confidence,
                "reason": reason,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "price": market_data.get("upbit_ticker")
            }
        elif analysis_result:
            final_decision = analysis_result["decision"]
            final_confidence = analysis_result["confidence"]
            final_result = analysis_result
            print("\n===== 분석 결과 =====")
            print(f"결정: {final_decision} (신뢰도: {final_confidence:.2f})")
        else:
            print("모든 분석 방법이 실패했습니다. 다음 실행을 기다립니다.")
            return
        
        # 6. 결과 출력
        print("\n===== 최종 분석 결과 =====")
        print(json.dumps(final_result, indent=2, ensure_ascii=False))
        
        # 상세 결정 이유 출력
        print("\n===== 상세 결정 이유 =====")
        print(f"결정: {final_result['decision_kr']} (신뢰도: {final_result['confidence']:.2f})")
        
        print("\n[개별 지표 신호]")
        for signal in final_result['signals']:
            signal_icon = "🔴" if signal['signal'] == 'sell' else "🟢" if signal['signal'] == 'buy' else "⚪"
            print(f"{signal_icon} {signal['source']}: {signal['description']} (강도: {signal['strength']:.2f})")
        
        print(f"\n총 신호 수: 매수 {final_result['signal_counts']['buy']}개, 매도 {final_result['signal_counts']['sell']}개, 홀드 {final_result['signal_counts']['hold']}개")
        print(f"종합 신호 강도: {final_result['avg_signal_strength']:.3f}")
        
        # 7. 매매 실행
        trade_enabled = os.getenv("ENABLE_TRADE", "").lower() == "true"
        
        if trade_enabled:
            print("\n== 자동 매매 실행 ==")
            execute_trade(final_result["decision"], final_result["confidence"], market_data)
        else:
            print("\n== 자동 매매 비활성화됨 (테스트 모드) ==")
            print(f"실행될 매매: {final_result['decision']} (신뢰도: {final_result['confidence']:.2f})")
            
        # 8. 결과 저장 (로그 또는 DB)
        try:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, f"trading_log_{datetime.now().strftime('%Y%m%d')}.json")
            
            # 기존 로그가 있으면 로드
            existing_logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    existing_logs = json.load(f)
            
            # 새 로그 추가
            existing_logs.append(final_result)
            
            # 로그 저장
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(existing_logs, f, indent=2, ensure_ascii=False)
                
            print(f"\n거래 로그가 저장되었습니다: {log_file}")
        except Exception as e:
            print(f"로그 저장 중 오류 발생: {e}")
        
    except Exception as e:
        print(f"거래 프로세스 중 예상치 못한 오류 발생: {e}")
        traceback.print_exc()

# 메인 실행 부분
if __name__ == "__main__":
    print("확장된 비트코인 자동매매 시스템을 시작합니다...")
    print("이 프로그램은 다양한 거래소 데이터와 온체인 데이터를 활용합니다.")
    print("Ctrl+C를 눌러 언제든지 종료할 수 있습니다.\n")
    
    # 환경 변수 설정 확인
    required_vars = {
        "UPBIT_ACCESS_KEY": "업비트 API 접근 키",
        "UPBIT_SECRET_KEY": "업비트 API 비밀 키"
    }
    
    optional_vars = {
        "CLAUDE_API_KEY": "Claude AI API 키 (선택 사항)",
        "GLASSNODE_API_KEY": "Glassnode API 키 (선택 사항)",
        "USE_CLAUDE": "Claude AI 사용 여부 (true/false)",
        "ENABLE_TRADE": "실제 매매 활성화 여부 (true/false)"
    }
    
    # 필수 환경 변수 확인
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("⚠️ 다음 필수 환경 변수가 설정되지 않았습니다:")
        for var in missing_vars:
            print(f"  - {var}: {required_vars[var]}")
        print("\n.env 파일을 확인하거나 환경 변수를 설정하세요.")
        
    # 선택적 환경 변수 확인
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        status = "✓ 설정됨" if value else "✗ 설정되지 않음"
        print(f"{var}: {desc} - {status}")
    
    # 환경 변수 안내
    if not os.getenv("USE_CLAUDE", "").lower() == "true":
        print("\n📌 Claude AI를 사용하려면 .env 파일에 USE_CLAUDE=true와 CLAUDE_API_KEY를 설정하세요.")
    
    if not os.getenv("ENABLE_TRADE", "").lower() == "true":
        print("\n📌 실제 매매를 활성화하려면 .env 파일에 ENABLE_TRADE=true를 설정하세요.")
        print("   현재는 테스트 모드로 실행됩니다. (실제 매매 없음)")
    else:
        print("\n⚠️ 실제 매매가 활성화되었습니다. 자동으로 실제 거래가 이루어집니다!")
    
    # 무한 루프로 일정 시간마다 매매 분석 및 실행
    interval_minutes = TRADING_SETTINGS.get("trading_interval", 60)  # 기본값 60분
    
    try:
        while True:
            print(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 매매 분석 시작")
            integrated_trading()
            
            next_run = datetime.now() + timedelta(minutes=interval_minutes)
            print(f"\n다음 분석 예정 시간: {next_run.strftime('%Y-%m-%d %H:%M:%S')} ({interval_minutes}분 후)")
            
            for i in range(interval_minutes):
                time.sleep(60)  # 1분씩 대기
                minutes_left = interval_minutes - i - 1
                if minutes_left > 0 and minutes_left % 5 == 0:  # 5분 간격으로 상태 메시지
                    print(f"다음 분석까지 {minutes_left}분 남았습니다...")
    
    except KeyboardInterrupt:
        print("\n프로그램이 사용자에 의해 종료되었습니다.")
    except Exception as e:
        print(f"\n예상치 못한 오류로 프로그램이 종료됩니다: {e}")
        traceback.print_exc()
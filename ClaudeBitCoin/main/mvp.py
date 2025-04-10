import os
from dotenv import load_dotenv
load_dotenv()

# �⺻ ������ ����
DECISION_THRESHOLDS = {"buy_threshold": 0.2, "sell_threshold": -0.2}
INVESTMENT_RATIOS = {"min_ratio": 0.2, "max_ratio": 0.5}
SIGNAL_STRENGTHS = {}
INDICATOR_WEIGHTS = {}
INDICATOR_USAGE = {}
TRADING_SETTINGS = {"min_order_amount": 5000, "trading_interval": 60}
CLAUDE_SETTINGS = {"use_claude": False, "weight": 1.0, "confidence_boost": 0.1}
HISTORICAL_SETTINGS = {"use_historical_data": False}

# ����� ���� ���� �ҷ����� �õ�
try:
    from trading_config import *
    print("����� ���� ������ ���������� �ҷ��Խ��ϴ�.")
except ImportError:
    print("����� ���� ������ ã�� �� �����ϴ�. �⺻ ������ ����մϴ�.")

# �ʿ��� ���̺귯�� ����Ʈ
import pyupbit
import json
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import requests
import traceback

# �߰� �ŷ��� API (���̳���, ����Ʈ) - �ʿ�� ��ġ
# pip install python-binance ccxt

# 1. �ŷ��� ������ �������� - ���� ����
def get_enhanced_market_data():
    """�پ��� �ŷ����� �������� ���� �����͸� �����ɴϴ�."""
    try:
        result = {}
        
        # 1.1 ����Ʈ ������
        print("����Ʈ ������ �������� ����...")
        
        # OHLCV ������ (�Ϻ�, �ð���, �к�)

        # �Ϻ� ������: 200�Ϸ� Ȯ�� (�� 6-7����)
        result["upbit_daily_ohlcv"] = pyupbit.get_ohlcv("KRW-BTC", count=200, interval="day")
        
        # �ֺ� ������ �߰� (52�� = �� 1��)
        result["upbit_hourly_ohlcv"] = pyupbit.get_ohlcv("KRW-BTC", count=24, interval="week")
        
        # ���� ������ �߰� (24���� = 2��)
        result["upbit_minute_ohlcv"] = pyupbit.get_ohlcv("KRW-BTC", count=60, interval="minute5")
        
        # ���� ȣ�� ���� (orderbook)
        result["upbit_orderbook"] = pyupbit.get_orderbook("KRW-BTC")
        
        # �ֱ� ü�� ������
        result["upbit_trades"] = []
        
        # ���� ��ü ���� (ƼĿ)
        result["upbit_ticker"] = pyupbit.get_current_price("KRW-BTC", verbose=True)
        
        # ����Ʈ ���� ��ü ���� ����
        result["upbit_market_all"] = []
        
        print("����Ʈ ������ �������� ����")
        
        # 1.2 ���̳��� ������ (������)
        try:
            import ccxt
            
            # CCXT�� ���� ���̳��� ����
            binance = ccxt.binance()
            
            # OHLCV ������

            # ���̳��� �Ϻ� 200��
            binance_ohlcv = binance.fetch_ohlcv('BTC/USDT', '1d', limit=200)
            df_binance = pd.DataFrame(binance_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df_binance['timestamp'] = pd.to_datetime(df_binance['timestamp'], unit='ms')
            df_binance.set_index('timestamp', inplace=True)
            result["binance_daily_ohlcv"] = df_binance
            
            # ���簡 ����
            binance_ticker = binance.fetch_ticker('BTC/USDT')
            result["binance_ticker"] = binance_ticker
            
            # ȣ��â ������
            binance_orderbook = binance.fetch_order_book('BTC/USDT')
            result["binance_orderbook"] = binance_orderbook
            
            print("���̳��� ������ �������� ����")
        except Exception as e:
            print(f"���̳��� ������ �������� ���� (�����ϰ� ���): {e}")
        
        # 1.3 Fear & Greed ���� �������� (��ȣȭ�� ���� �ɸ� ����)
        try:
            fg_url = "https://api.alternative.me/fng/"
            fg_response = requests.get(fg_url)
            if fg_response.status_code == 200:
                fg_data = fg_response.json()
                result["fear_greed_index"] = fg_data
                print("Fear & Greed ���� �������� ����")
        except Exception as e:
            print(f"Fear & Greed ���� �������� ���� (�����ϰ� ���): {e}")
        
        # 1.4 ��ü�� ������ (������) - Glassnode �Ǵ� �ٸ� ���� API �ʿ�
        try:
            # API Ű�� ������ ��쿡�� ����
            glassnode_api_key = os.getenv("GLASSNODE_API_KEY")
            if glassnode_api_key:
                # ��: ��Ƽ�� �ּ� �� 
                active_addresses_url = f"https://api.glassnode.com/v1/metrics/addresses/active_count?api_key={glassnode_api_key}&a=BTC"
                response = requests.get(active_addresses_url)
                if response.status_code == 200:
                    result["onchain_active_addresses"] = response.json()
                
                # ��: SOPR (Spent Output Profit Ratio)
                sopr_url = f"https://api.glassnode.com/v1/metrics/indicators/sopr?api_key={glassnode_api_key}&a=BTC"
                response = requests.get(sopr_url)
                if response.status_code == 200:
                    result["onchain_sopr"] = response.json()
                
                print("��ü�� ������ �������� ����")
        except Exception as e:
            print(f"��ü�� ������ �������� ���� (�����ϰ� ���): {e}")
            
        return result
    
    except Exception as e:
        print(f"���� ������ �������� ����: {e}")
        traceback.print_exc()
        return None

# 2. ������ ó�� �� ��ǥ ��� �Լ�
def calculate_technical_indicators(data):
    """������ �����Ϳ��� ����� ��ǥ ���"""
    try:
        indicators = {}
        
        # 2.1 �⺻ OHLCV �����Ϳ��� ��ǥ ���
        df = data["upbit_daily_ohlcv"].copy()
        
        # �̵���ռ� ���
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA60'] = df['close'].rolling(window=60).mean() if len(df) >= 60 else None
        df['MA120'] = df['close'].rolling(window=120).mean() if len(df) >= 120 else None
        
        # ������ ���
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['stddev'] = df['close'].rolling(window=20).std()
        df['upper_band'] = df['MA20'] + (df['stddev'] * 2)
        df['lower_band'] = df['MA20'] - (df['stddev'] * 2)
        df['bandwidth'] = (df['upper_band'] - df['lower_band']) / df['MA20']
        
        # RSI ��� (Relative Strength Index, ��밭������)
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD ���
        df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_hist'] = df['MACD'] - df['Signal']
        
        # ����ĳ��ƽ ��ǥ
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
        
        # �Ϻ� ����� ��ǥ ����
        indicators["daily_indicators"] = df
        
        # 2.2 �ð��� �����Ϳ��� ��ǥ ���
        df_hourly = data["upbit_hourly_ohlcv"].copy()
        
        # ������ �̵���� �� RSI�� ���
        df_hourly['MA5'] = df_hourly['close'].rolling(window=5).mean()
        df_hourly['MA10'] = df_hourly['close'].rolling(window=10).mean()
        
        delta = df_hourly['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df_hourly['RSI'] = 100 - (100 / (1 + rs))
        
        # �ð��� ����� ��ǥ ����
        indicators["hourly_indicators"] = df_hourly
        
        # 2.3 �ŷ��� ������ ��� (���ݴ뺰 �ŷ��� ����)
        # - �Ϻ� OHLCV �����ͷ� ������ �ŷ��� ������ ����
        daily_data = data["upbit_daily_ohlcv"]
        
        # ���� ���� ���� (���������� �ְ����� 10�� ����)
        price_min = daily_data['low'].min()
        price_max = daily_data['high'].max()
        price_ranges = np.linspace(price_min, price_max, 11)  # 10�� ���� ��� ����
        
        # �� ���� ������ �ŷ��� �հ�
        volume_profile = []
        for i in range(len(price_ranges) - 1):
            price_low = price_ranges[i]
            price_high = price_ranges[i+1]
            
            # �ش� ���� ������ ���ϴ� ������ �ŷ��� �հ�
            total_volume = daily_data[(daily_data['low'] <= price_high) & 
                                      (daily_data['high'] >= price_low)]['volume'].sum()
            
            volume_profile.append({
                'price_range': f"{price_low:.0f} - {price_high:.0f}",
                'mid_price': (price_low + price_high) / 2,
                'volume': total_volume
            })
        
        # �ŷ��� ������ ����
        indicators["volume_profile"] = volume_profile
        
       # ȣ��â �м�
        if "upbit_orderbook" in data and data["upbit_orderbook"]:
            try:
                orderbook = data["upbit_orderbook"]
                
                # pyupbit 0.2.34 ���� ȣ��â ���� Ȯ��
                if isinstance(orderbook, dict) and "ask_price" in orderbook:
                    # ���� ��ųʸ��̰� ���� ���� ������ �ִ� ���
                    best_bid = orderbook.get("bid_price", 0)
                    best_ask = orderbook.get("ask_price", 0)
                    
                    # ���� ����
                    bid_quantity = orderbook.get("bid_size", 0)
                    ask_quantity = orderbook.get("ask_size", 0)
                    
                    # ������ �ż�/�ŵ� ���� ���
                    total_bids_amount = best_bid * bid_quantity
                    total_asks_amount = best_ask * ask_quantity
                elif isinstance(orderbook, list) and len(orderbook) > 0:
                    # ����Ʈ�� ��� ù ��° ��� ���
                    first_item = orderbook[0]
                    if "orderbook_units" in first_item:
                        units = first_item["orderbook_units"]
                        
                        # �ż�/�ŵ� �Ѿ� ���
                        total_bids_amount = sum(unit.get("bid_price", 0) * unit.get("bid_size", 0) for unit in units)
                        total_asks_amount = sum(unit.get("ask_price", 0) * unit.get("ask_size", 0) for unit in units)
                        
                        # ȣ��â ��������
                        best_bid = units[0].get("bid_price", 0) if units else 0
                        best_ask = units[0].get("ask_price", 0) if units else 0
                    else:
                        # �ٸ� ������ ��� �⺻�� ����
                        total_bids_amount = 0
                        total_asks_amount = 0
                        best_bid = 0
                        best_ask = 0
                else:
                    # �ٸ� ������ ��� �⺻�� ����
                    total_bids_amount = 0
                    total_asks_amount = 0
                    best_bid = 0
                    best_ask = 0
                
                # �⺻ �м� ����
                buy_sell_ratio = total_bids_amount / total_asks_amount if total_asks_amount > 0 else 1.0
                spread = best_ask - best_bid if best_bid > 0 else 0
                spread_percentage = (spread / best_bid) * 100 if best_bid > 0 else 0
                
                # ��� ����
                indicators["orderbook_analysis"] = {
                    "buy_sell_ratio": buy_sell_ratio,
                    "spread": spread,
                    "spread_percentage": spread_percentage
                }
                
            except Exception as e:
                print(f"ȣ��â �м� �� ���� �߻�: {e}")
                # ���� �߻� �� �⺻�� ����
                indicators["orderbook_analysis"] = {
                    "buy_sell_ratio": 1.0,
                    "spread": 0,
                    "spread_percentage": 0
                }
            
        # 2.5 �ֱ� ü�� �м�
        if "upbit_trades" in data and data["upbit_trades"]:
            trades = data["upbit_trades"]
            
            # �ż�/�ŵ� ü�� �з�
            buy_trades = [trade for trade in trades if trade['ask_bid'] == 'BID']
            sell_trades = [trade for trade in trades if trade['ask_bid'] == 'ASK']
            
            # �ż�/�ŵ� ü�� ����
            buy_count = len(buy_trades)
            sell_count = len(sell_trades)
            buy_sell_count_ratio = buy_count / sell_count if sell_count > 0 else float('inf')
            
            # �ż�/�ŵ� ü�� �ѷ�
            buy_volume = sum(float(trade['trade_volume']) for trade in buy_trades)
            sell_volume = sum(float(trade['trade_volume']) for trade in sell_trades)
            buy_sell_volume_ratio = buy_volume / sell_volume if sell_volume > 0 else float('inf')
            
            # ��� ü�� ũ��
            avg_trade_size = sum(float(trade['trade_volume']) for trade in trades) / len(trades) if trades else 0
            
            # �ŷ� �ð� ���� (�� ����)
            if len(trades) >= 2:
                trade_times = [datetime.strptime(trade['trade_time'], '%H:%M:%S') for trade in trades]
                time_diffs = [(trade_times[i] - trade_times[i+1]).total_seconds() 
                             for i in range(len(trade_times)-1)]
                avg_time_between_trades = sum(time_diffs) / len(time_diffs) if time_diffs else None
            else:
                avg_time_between_trades = None
            
            # ��� ����
            indicators["trade_analysis"] = {
                "buy_sell_count_ratio": buy_sell_count_ratio,
                "buy_sell_volume_ratio": buy_sell_volume_ratio,
                "avg_trade_size": avg_trade_size,
                "avg_time_between_trades": avg_time_between_trades
            }
            
        # 2.6 ���̳��� ������ �м� (�ִ� ���)
        # ���̳��� ������ �м� (�ִ� ���)
        if "binance_daily_ohlcv" in data:
            try:
                binance_df = data["binance_daily_ohlcv"]
                
                # �����Ͱ� ������� ������ Ȯ��
                if binance_df is not None and not (isinstance(binance_df, pd.DataFrame) and binance_df.empty):
                    # ������ �̵����
                    if isinstance(binance_df, pd.DataFrame):
                        binance_df['MA5'] = binance_df['close'].rolling(window=5).mean()
                        binance_df['MA20'] = binance_df['close'].rolling(window=20).mean()
                        
                        # USDT/KRW ���� ���� (1 USDT = �� 1350������ ����)
                        usdt_krw_rate = 1350  # �����δ� API�� ȯ���� �������� ���� ����
                        
                        # ������ ���̳��� ���ݰ� ����Ʈ ���� ��
                        if "upbit_ticker" in data and data["upbit_ticker"]:
                            try:
                                # ���̳��� ���� ����
                                try:
                                    binance_last_price = binance_df['close'].iloc[-1]
                                    if isinstance(binance_last_price, list):
                                        binance_last_price = binance_last_price[0] if binance_last_price else 0
                                except Exception as e:
                                    print(f"���̳��� ���� ���� ����: {e}")
                                    binance_last_price = 0
                                
                                # ����Ʈ ���� ����
                                try:
                                    upbit_last_price = data["upbit_ticker"]
                                    if isinstance(upbit_last_price, dict):
                                        # ��ųʸ����� ���� ����
                                        for key in ["trade_price", "close", "last", "price"]:
                                            if key in upbit_last_price:
                                                upbit_last_price = upbit_last_price[key]
                                                break
                                        else:
                                            # Ű�� ã�� ���� ��� ù ��° ���� ���
                                            for k, v in upbit_last_price.items():
                                                if isinstance(v, (int, float)):
                                                    upbit_last_price = v
                                                    break
                                            else:
                                                upbit_last_price = 0
                                    elif isinstance(upbit_last_price, list):
                                        # ����Ʈ�� ��� ù ��° �� �õ�
                                        upbit_last_price = upbit_last_price[0] if upbit_last_price else 0
                                        if isinstance(upbit_last_price, dict):
                                            for key in ["trade_price", "close", "last", "price"]:
                                                if key in upbit_last_price:
                                                    upbit_last_price = upbit_last_price[key]
                                                    break
                                except Exception as e:
                                    print(f"����Ʈ ���� ���� ����: {e}")
                                    upbit_last_price = 0
                                
                                # ���� ���
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
                                            print(f"exchange_comparison ���� �� ����: {e}")
                                except Exception as e:
                                    print(f"���� ��� �� ���� �߻�: {e}")
                                    binance_krw_price = 0
                                    kimp_percentage = 0
                                    
                                    # �⺻������ ����
                                    try:
                                        indicators["exchange_comparison"] = {
                                            "binance_price_usdt": 0,
                                            "binance_price_krw_estimated": 0,
                                            "upbit_price_krw": 0,
                                            "korea_premium_percentage": 0
                                        }
                                    except Exception as e:
                                        print(f"exchange_comparison �⺻�� ���� �� ����: {e}")
                            except Exception as e:
                                print(f"���� ��� �� ����: {e}")
                        
                        # ���̳��� ����� ��ǥ ����
                        indicators["binance_indicators"] = binance_df
            except Exception as e:
                print(f"���̳��� ������ �м� �� ����: {e}")
            
        # 2.7 ���� �ɸ� ���� (Fear & Greed)
        if "fear_greed_index" in data and data["fear_greed_index"]:
            fg_data = data["fear_greed_index"]
            current_value = fg_data['data'][0]['value'] if 'data' in fg_data and fg_data['data'] else None
            current_classification = fg_data['data'][0]['value_classification'] if 'data' in fg_data and fg_data['data'] else None
            
            indicators["market_sentiment"] = {
                "fear_greed_value": current_value,
                "fear_greed_classification": current_classification
            }
            
        # 2.8 ��ü�� ������ �м� (�ִ� ���)
        if "onchain_active_addresses" in data and data["onchain_active_addresses"]:
            # �ֱ� ��Ƽ�� �ּ� �� ����
            active_addresses = data["onchain_active_addresses"]
            recent_active = active_addresses[-7:] if active_addresses else []
            
            # �ֱ� 7�ϰ� �߼� ���
            if recent_active and len(recent_active) >= 7:
                first_value = recent_active[0]['v']
                last_value = recent_active[-1]['v']
                active_addr_trend = ((last_value - first_value) / first_value) * 100
            else:
                active_addr_trend = None
                
            # SOPR �м� (Spent Output Profit Ratio)
            if "onchain_sopr" in data and data["onchain_sopr"]:
                sopr_data = data["onchain_sopr"]
                recent_sopr = sopr_data[-7:] if sopr_data else []
                
                if recent_sopr and len(recent_sopr) >= 1:
                    current_sopr = recent_sopr[-1]['v']
                    # SOPR > 1 : ���� ����, SOPR < 1 : �ս� ����
                    sopr_signal = "���� ������" if current_sopr > 1 else "�ս� ������"
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
        print(f"����� ��ǥ ��� ����: {e}")
        traceback.print_exc()
        return None

# 3. ���� �Ÿ� ���� �м� �Լ�
def perform_integrated_analysis(market_data, indicators):
    """�پ��� ������ �ҽ��� �����Ͽ� �Ÿ� ������ �����ϴ�."""
    try:
        signals = []
        signal_strengths = {}  # ��ȣ ���� ����
        
        # 3.1 �Ϻ� ����� ��ǥ �м�
        if "daily_indicators" in indicators and not indicators["daily_indicators"].empty:
            daily_df = indicators["daily_indicators"]
            last_row = daily_df.iloc[-1]  # ���� �ֱ� ������
            
            # �̵���ռ� �м� (���ũ�ν�/����ũ�ν�)
            ma5 = last_row['MA5']
            ma10 = last_row['MA10']
            ma20 = last_row['MA20']
            ma60 = last_row['MA60'] if 'MA60' in last_row and not pd.isna(last_row['MA60']) else None
            
            # �ܱ� �̵���ռ� �м�
            if ma5 > ma20:
                signals.append({
                    "source": "�̵���ռ�(MA)",
                    "signal": "buy",
                    "strength": 0.6,
                    "description": "���ũ�ν� ���� (5�� �̵���ռ��� 20�� �̵���ռ� ���� ��ġ)"
                })
                signal_strengths["MA"] = 0.6
            elif ma5 < ma20:
                signals.append({
                    "source": "�̵���ռ�(MA)",
                    "signal": "sell",
                    "strength": 0.6,
                    "description": "����ũ�ν� ���� (5�� �̵���ռ��� 20�� �̵���ռ� �Ʒ��� ��ġ)"
                })
                signal_strengths["MA"] = -0.6
            else:
                signals.append({
                    "source": "�̵���ռ�(MA)",
                    "signal": "hold",
                    "strength": 0,
                    "description": "�̵���ռ� �߸� ����"
                })
                signal_strengths["MA"] = 0
                
            # ��� �̵���ռ� �߼� (�����ϴ� ���)
            if ma60 is not None:
                if last_row['close'] > ma60:
                    signals.append({
                        "source": "����߼�(MA60)",
                        "signal": "buy",
                        "strength": 0.4,
                        "description": "��� ��� �߼� (���簡�� 60�� �̵���ռ� ���� ��ġ)"
                    })
                    signal_strengths["MA60"] = 0.4
                else:
                    signals.append({
                        "source": "����߼�(MA60)",
                        "signal": "sell",
                        "strength": 0.4,
                        "description": "��� �϶� �߼� (���簡�� 60�� �̵���ռ� �Ʒ��� ��ġ)"
                    })
                    signal_strengths["MA60"] = -0.4
            
            # ������ ��� �м�
            upper_band = last_row['upper_band']
            lower_band = last_row['lower_band']
            mid_band = last_row['MA20']  # �߾Ӽ��� 20�� �̵���ռ�
            
            if last_row['close'] > upper_band:
                signals.append({
                    "source": "���������(BB)",
                    "signal": "sell",
                    "strength": 0.7,
                    "description": "���ż� ���� (������ ��� ��� ����)"
                })
                signal_strengths["BB"] = -0.7
            elif last_row['close'] < lower_band:
                signals.append({
                    "source": "���������(BB)",
                    "signal": "buy",
                    "strength": 0.7,
                    "description": "���ŵ� ���� (������ ��� �ϴ� ����)"
                })
                signal_strengths["BB"] = 0.7
            else:
                # ��� �������� ��ġ�� ������� ��� (-1: �ϴ�, 0: �߾�, 1: ���)
                band_position = 2 * (last_row['close'] - mid_band) / (upper_band - lower_band) if (upper_band - lower_band) != 0 else 0
                
                if band_position > 0.5:
                    signals.append({
                        "source": "���������(BB)",
                        "signal": "sell",
                        "strength": 0.3,
                        "description": f"��� ������ (��� �� ��ġ: ���� {(band_position*50):.0f}%)"
                    })
                    signal_strengths["BB"] = -0.3
                elif band_position < -0.5:
                    signals.append({
                        "source": "���������(BB)",
                        "signal": "buy",
                        "strength": 0.3,
                        "description": f"�ϴ� ������ (��� �� ��ġ: ���� {(abs(band_position)*50):.0f}%)"
                    })
                    signal_strengths["BB"] = 0.3
                else:
                    signals.append({
                        "source": "���������(BB)",
                        "signal": "hold",
                        "strength": 0,
                        "description": "��� �߾� �α� (�߸��� ��ġ)"
                    })
                    signal_strengths["BB"] = 0
            
            # RSI �м� (���ż�/���ŵ�)
            rsi = last_row['RSI']
            
            if rsi > 70:
                signals.append({
                    "source": "RSI(��밭������)",
                    "signal": "sell",
                    "strength": 0.8,
                    "description": f"���ż� ���� (RSI: {rsi:.1f} > 70)"
                })
                signal_strengths["RSI"] = -0.8
            elif rsi < 30:
                signals.append({
                    "source": "RSI(��밭������)",
                    "signal": "buy",
                    "strength": 0.8,
                    "description": f"���ŵ� ���� (RSI: {rsi:.1f} < 30)"
                })
                signal_strengths["RSI"] = 0.8
            else:
                # RSI �߰� ���� (30-70) �������� ��ġ
                rsi_normalized = (rsi - 30) / 40  # 0(=30) ���� 1(=70) ���̷� ����ȭ
                if rsi_normalized > 0.75:  # RSI > 60
                    signals.append({
                        "source": "RSI(��밭������)",
                        "signal": "sell",
                        "strength": 0.2,
                        "description": f"�ż��� �켼 (RSI: {rsi:.1f})"
                    })
                    signal_strengths["RSI"] = -0.2
                elif rsi_normalized < 0.25:  # RSI < 40
                    signals.append({
                        "source": "RSI(��밭������)",
                        "signal": "buy",
                        "strength": 0.2,
                        "description": f"�ŵ��� �켼 (RSI: {rsi:.1f})"
                    })
                    signal_strengths["RSI"] = 0.2
                else:
                    signals.append({
                        "source": "RSI(��밭������)",
                        "signal": "hold",
                        "strength": 0,
                        "description": f"�߸��� (RSI: {rsi:.1f})"
                    })
                    signal_strengths["RSI"] = 0
            
            # MACD �м�
            macd = last_row['MACD']
            signal_line = last_row['Signal']
            macd_hist = last_row['MACD_hist']
            
            # MACD ������׷� ��ȣ ��ȭ Ȯ�� (�Ÿ� ��ȣ)
            prev_macd_hist = daily_df.iloc[-2]['MACD_hist'] if len(daily_df) > 1 else 0
            
            if macd_hist > 0 and prev_macd_hist <= 0:
                # ���ũ�ν� (�ż� ��ȣ)
                signals.append({
                    "source": "MACD",
                    "signal": "buy",
                    "strength": 0.7,
                    "description": "MACD ���ũ�ν� (MACD ���� ��ȣ�� ���� ����)"
                })
                signal_strengths["MACD"] = 0.7
            elif macd_hist < 0 and prev_macd_hist >= 0:
                # ����ũ�ν� (�ŵ� ��ȣ)
                signals.append({
                    "source": "MACD",
                    "signal": "sell",
                    "strength": 0.7,
                    "description": "MACD ����ũ�ν� (MACD ���� ��ȣ�� ���� ����)"
                })
                signal_strengths["MACD"] = -0.7
            elif macd_hist > 0:
                signals.append({
                    "source": "MACD",
                    "signal": "buy",
                    "strength": 0.3,
                    "description": "MACD ��� �߼� ������"
                })
                signal_strengths["MACD"] = 0.3
            else:
                signals.append({
                    "source": "MACD",
                    "signal": "sell",
                    "strength": 0.3,
                    "description": "MACD �϶� �߼� ������"
                })
                signal_strengths["MACD"] = -0.3
                
            # ����ĳ��ƽ �м�
            k = last_row['K']
            d = last_row['D']
            
            if k > 80 and d > 80:
                signals.append({
                    "source": "����ĳ��ƽ",
                    "signal": "sell",
                    "strength": 0.6,
                    "description": f"���ż� ���� (K: {k:.1f}, D: {d:.1f})"
                })
                signal_strengths["Stochastic"] = -0.6
            elif k < 20 and d < 20:
                signals.append({
                    "source": "����ĳ��ƽ",
                    "signal": "buy",
                    "strength": 0.6,
                    "description": f"���ŵ� ���� (K: {k:.1f}, D: {d:.1f})"
                })
                signal_strengths["Stochastic"] = 0.6
            elif k > d and k < 80 and d < 80:
                signals.append({
                    "source": "����ĳ��ƽ",
                    "signal": "buy",
                    "strength": 0.3,
                    "description": f"��� ���� ��ȣ (K > D, K: {k:.1f}, D: {d:.1f})"
                })
                signal_strengths["Stochastic"] = 0.3
            elif k < d and k > 20 and d > 20:
                signals.append({
                    "source": "����ĳ��ƽ",
                    "signal": "sell",
                    "strength": 0.3,
                    "description": f"�϶� ���� ��ȣ (K < D, K: {k:.1f}, D: {d:.1f})"
                })
                signal_strengths["Stochastic"] = -0.3
            else:
                signals.append({
                    "source": "����ĳ��ƽ",
                    "signal": "hold",
                    "strength": 0,
                    "description": f"�߸� (K: {k:.1f}, D: {d:.1f})"
                })
                signal_strengths["Stochastic"] = 0
                
        # 3.2 ȣ��â �м�
        if "orderbook_analysis" in indicators:
            order_analysis = indicators["orderbook_analysis"]
            
            buy_sell_ratio = order_analysis.get("buy_sell_ratio")
            if buy_sell_ratio is not None:
                if buy_sell_ratio > 1.5:
                    signals.append({
                        "source": "ȣ��â(�ż�/�ŵ�����)",
                        "signal": "buy",
                        "strength": 0.6,
                        "description": f"���� �ż��� (�ż�/�ŵ� ����: {buy_sell_ratio:.2f})"
                    })
                    signal_strengths["Orderbook"] = 0.6
                elif buy_sell_ratio < 0.7:
                    signals.append({
                        "source": "ȣ��â(�ż�/�ŵ�����)",
                        "signal": "sell",
                        "strength": 0.6,
                        "description": f"���� �ŵ��� (�ż�/�ŵ� ����: {buy_sell_ratio:.2f})"
                    })
                    signal_strengths["Orderbook"] = -0.6
                else:
                    signals.append({
                        "source": "ȣ��â(�ż�/�ŵ�����)",
                        "signal": "hold",
                        "strength": 0,
                        "description": f"�߸��� ȣ��â (�ż�/�ŵ� ����: {buy_sell_ratio:.2f})"
                    })
                    signal_strengths["Orderbook"] = 0
        
        # 3.3 ü�� �м�
        if "trade_analysis" in indicators:
            trade_analysis = indicators["trade_analysis"]
            
            buy_sell_volume_ratio = trade_analysis.get("buy_sell_volume_ratio")
            if buy_sell_volume_ratio is not None:
                if buy_sell_volume_ratio > 1.5:
                    signals.append({
                        "source": "ü�ᵥ����(�ż�/�ŵ���)",
                        "signal": "buy",
                        "strength": 0.5,
                        "description": f"�ż� ü�� �켼 (�ż�/�ŵ� �ŷ��� ����: {buy_sell_volume_ratio:.2f})"
                    })
                    signal_strengths["Trades"] = 0.5
                elif buy_sell_volume_ratio < 0.7:
                    signals.append({
                        "source": "ü�ᵥ����(�ż�/�ŵ���)",
                        "signal": "sell",
                        "strength": 0.5,
                        "description": f"�ŵ� ü�� �켼 (�ż�/�ŵ� �ŷ��� ����: {buy_sell_volume_ratio:.2f})"
                    })
                    signal_strengths["Trades"] = -0.5
                else:
                    signals.append({
                        "source": "ü�ᵥ����(�ż�/�ŵ���)",
                        "signal": "hold",
                        "strength": 0,
                        "description": f"�߸��� ü�� �帧 (�ż�/�ŵ� �ŷ��� ����: {buy_sell_volume_ratio:.2f})"
                    })
                    signal_strengths["Trades"] = 0
                    
        # 3.4 ����(KIMP) �м�
        if "exchange_comparison" in indicators:
            exc_comparison = indicators["exchange_comparison"]
            
            korea_premium = exc_comparison.get("korea_premium_percentage")
            if korea_premium is not None:
                if korea_premium > 5.0:
                    signals.append({
                        "source": "����(�ѱ� �����̾�)",
                        "signal": "sell",
                        "strength": 0.5,
                        "description": f"���� �ѱ� �����̾� (����: {korea_premium:.2f}%)"
                    })
                    signal_strengths["KIMP"] = -0.5
                elif korea_premium < -1.0:
                    signals.append({
                        "source": "����(�ѱ� �����̾�)",
                        "signal": "buy",
                        "strength": 0.5,
                        "description": f"�ѱ� �����̾� ���� (����: {korea_premium:.2f}%)"
                    })
                    signal_strengths["KIMP"] = 0.5
                else:
                    signals.append({
                        "source": "����(�ѱ� �����̾�)",
                        "signal": "hold",
                        "strength": 0,
                        "description": f"���� ������ �ѱ� �����̾� (����: {korea_premium:.2f}%)"
                    })
                    signal_strengths["KIMP"] = 0
        
        # 3.5 ���� �ɸ� ���� �м�
        if "market_sentiment" in indicators:
            sentiment = indicators["market_sentiment"]
            
            fear_greed_value = sentiment.get("fear_greed_value")
            fear_greed_class = sentiment.get("fear_greed_classification")
            
            if fear_greed_value is not None:
                fear_greed_value = int(fear_greed_value)
                
                if fear_greed_value <= 25:  # �ص��� ����
                    signals.append({
                        "source": "����ɸ�(����&Ž������)",
                        "signal": "buy",
                        "strength": 0.7,
                        "description": f"�ص��� ���� ���� (Fear & Greed: {fear_greed_value}, {fear_greed_class})"
                    })
                    signal_strengths["FearGreed"] = 0.7
                elif fear_greed_value >= 75:  # �ص��� Ž��
                    signals.append({
                        "source": "����ɸ�(����&Ž������)",
                        "signal": "sell",
                        "strength": 0.7,
                        "description": f"�ص��� Ž�� ���� (Fear & Greed: {fear_greed_value}, {fear_greed_class})"
                    })
                    signal_strengths["FearGreed"] = -0.7
                elif fear_greed_value < 40:  # ����
                    signals.append({
                        "source": "����ɸ�(����&Ž������)",
                        "signal": "buy",
                        "strength": 0.4,
                        "description": f"���� �켼 ���� (Fear & Greed: {fear_greed_value}, {fear_greed_class})"
                    })
                    signal_strengths["FearGreed"] = 0.4
                elif fear_greed_value > 60:  # Ž��
                    signals.append({
                        "source": "����ɸ�(����&Ž������)",
                        "signal": "sell",
                        "strength": 0.4,
                        "description": f"Ž�� �켼 ���� (Fear & Greed: {fear_greed_value}, {fear_greed_class})"
                    })
                    signal_strengths["FearGreed"] = -0.4
                else:
                    signals.append({
                        "source": "����ɸ�(����&Ž������)",
                        "signal": "hold",
                        "strength": 0,
                        "description": f"�߸��� ���� �ɸ� (Fear & Greed: {fear_greed_value}, {fear_greed_class})"
                    })
                    signal_strengths["FearGreed"] = 0
                    
        # 3.6 ��ü�� ������ �м�
        if "onchain_analysis" in indicators:
            onchain = indicators["onchain_analysis"]
            
            current_sopr = onchain.get("current_sopr")
            sopr_signal = onchain.get("sopr_signal")
            
            if current_sopr is not None and sopr_signal is not None:
                if current_sopr < 0.95:
                    signals.append({
                        "source": "��ü��(SOPR)",
                        "signal": "buy",
                        "strength": 0.6,
                        "description": f"�ս� ���¿��� �ŵ� �� (SOPR: {current_sopr:.3f})"
                    })
                    signal_strengths["SOPR"] = 0.6
                elif current_sopr > 1.05:
                    signals.append({
                        "source": "��ü��(SOPR)",
                        "signal": "sell",
                        "strength": 0.6,
                        "description": f"���� ���¿��� �ŵ� �� (SOPR: {current_sopr:.3f})"
                    })
                    signal_strengths["SOPR"] = -0.6
                else:
                    signals.append({
                        "source": "��ü��(SOPR)",
                        "signal": "hold",
                        "strength": 0,
                        "description": f"�߸��� �ŵ� ���� (SOPR: {current_sopr:.3f})"
                    })
                    signal_strengths["SOPR"] = 0
            
            # ��Ƽ�� �ּ� �߼�
            active_addr_trend = onchain.get("active_addresses_7d_trend")
            if active_addr_trend is not None:
                if active_addr_trend > 10:
                    signals.append({
                        "source": "��ü��(Ȱ���ּ�)",
                        "signal": "buy",
                        "strength": 0.4,
                        "description": f"��Ʈ��ũ Ȱ�� ���� (7�� Ȱ���ּ� ��ȭ: {active_addr_trend:.1f}%)"
                    })
                    signal_strengths["ActiveAddr"] = 0.4
                elif active_addr_trend < -10:
                    signals.append({
                        "source": "��ü��(Ȱ���ּ�)",
                        "signal": "sell",
                        "strength": 0.4,
                        "description": f"��Ʈ��ũ Ȱ�� ���� (7�� Ȱ���ּ� ��ȭ: {active_addr_trend:.1f}%)"
                    })
                    signal_strengths["ActiveAddr"] = -0.4
                else:
                    signals.append({
                        "source": "��ü��(Ȱ���ּ�)",
                        "signal": "hold",
                        "strength": 0,
                        "description": f"��Ʈ��ũ Ȱ�� ������ (7�� Ȱ���ּ� ��ȭ: {active_addr_trend:.1f}%)"
                    })
                    signal_strengths["ActiveAddr"] = 0
        
        # 3.7 ���� ��ȣ ���
        # ���� ��� ��ȣ ���
        total_strength = 0
        weighted_sum = 0
        count = 0
        
        for source, strength in signal_strengths.items():
            count += 1
            weighted_sum += strength
            total_strength += abs(strength)
        
        if count > 0:
            avg_signal = weighted_sum / count
            confidence = min(total_strength / count / 0.8, 1.0)  # �ִ� �ŷڵ��� 1.0
        else:
            avg_signal = 0
            confidence = 0
        
        # ���� �Ÿ� ����
        if avg_signal > 0.2:
            decision = "buy"
            decision_kr = "�ż�"
        elif avg_signal < -0.2:
            decision = "sell"
            decision_kr = "�ŵ�"
        else:
            decision = "hold"
            decision_kr = "Ȧ��"
        
        # �ŷ� ������ ���� �߰� ���� (���� �ż�/�ŵ�/Ȧ��)
        if abs(avg_signal) > 0.5:
            strength_prefix = "���� "
        elif abs(avg_signal) > 0.3:
            strength_prefix = "���� "
        else:
            strength_prefix = "���� "
        
        decision_with_strength = strength_prefix + decision_kr
        
        # ���� ���� ���� ���
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
        
        # ��� ����
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
        
        # ���� ���� �� ������ �߰�
        if current_price is not None:
            result["current_price"] = current_price
        if price_change_24h is not None:
            result["price_change_24h"] = f"{price_change_24h:.2f}%"
        
        return result
        
    except Exception as e:
        print(f"�м� ����: {e}")
        traceback.print_exc()
        return None

# 4. AI ��� �м� �Լ�
def get_claude_analysis(market_data):
    """Claude AI�� ����Ͽ� ��Ʈ���� ������ �м�"""
    try:
        import anthropic
        
        ANTHROPIC_API_KEY = os.getenv("CLAUDE_API_KEY")
        if not ANTHROPIC_API_KEY:
            print("Claude API Ű�� �������� �ʾҽ��ϴ�.")
            return None
            
        client = anthropic.Anthropic(
            api_key=ANTHROPIC_API_KEY,
        )
        
        # �м��� ������ �غ�
        # OHLCV ������
        ohlcv_data = None
        if "upbit_daily_ohlcv" in market_data and not market_data["upbit_daily_ohlcv"].empty:
            ohlcv_data = market_data["upbit_daily_ohlcv"].to_json()
        
        # ��Ÿ ��ǥ ������ (���Ἲ�� ���� �Ϻθ� ����)
        data_for_claude = {
            "ohlcv_data": ohlcv_data,
            "current_price": market_data.get("upbit_ticker"),
        }
        
        # ȣ��â ������ �߰�
        if "upbit_orderbook" in market_data and market_data["upbit_orderbook"]:
            orderbook_simple = {
                "bid_prices": [unit['bid_price'] for unit in market_data["upbit_orderbook"][0]['orderbook_units'][:5]],
                "bid_sizes": [unit['bid_size'] for unit in market_data["upbit_orderbook"][0]['orderbook_units'][:5]],
                "ask_prices": [unit['ask_price'] for unit in market_data["upbit_orderbook"][0]['orderbook_units'][:5]],
                "ask_sizes": [unit['ask_size'] for unit in market_data["upbit_orderbook"][0]['orderbook_units'][:5]]
            }
            data_for_claude["orderbook"] = orderbook_simple
        
        # ���� ������ �߰�
        if "exchange_comparison" in market_data and market_data["exchange_comparison"]:
            data_for_claude["korea_premium"] = market_data["exchange_comparison"]
        
        # Fear & Greed ���� �߰�
        if "market_sentiment" in market_data and market_data["market_sentiment"]:
            data_for_claude["fear_greed"] = market_data["market_sentiment"]
        
        # ��ü�� ������ �߰�
        if "onchain_analysis" in market_data and market_data["onchain_analysis"]:
            data_for_claude["onchain"] = market_data["onchain_analysis"]
        
        # Claude API ȣ��
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
        
        # ���� ���� �� ó��
        result_text = response.content[0].text  # �ؽ�Ʈ ���� ����
        print("Claude ���� ����:", result_text)
        
        # JSON ���ڿ� ���� (���信 �ٸ� �ؽ�Ʈ�� ���Ե� ��츦 ���)
        import re
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                result = json.loads(json_str)
                return result
            except json.JSONDecodeError as e:
                print(f"JSON �Ľ� ����: {e}")
                return None
        else:
            print("���信�� JSON ������ ã�� �� �����ϴ�.")
            return None
            
    except Exception as e:
        print(f"Claude API ����: {e}")
        traceback.print_exc()
        return None

# 5. �Ÿ� ���� �Լ�
def execute_trade(decision, confidence, market_data):
    """�Ÿ� ������ ���� ���� �ŷ��� �����մϴ�."""
    print(f"\n===== �Ÿ� ����: {decision} (�ŷڵ�: {confidence:.2f}) =====")
    
    try:
        # ����Ʈ API ����
        import pyupbit
        access = os.getenv("UPBIT_ACCESS_KEY")
        secret = os.getenv("UPBIT_SECRET_KEY")
        
        if not access or not secret:
            print("����Ʈ API Ű�� �������� �ʾҽ��ϴ�. .env ������ Ȯ���ϼ���.")
            return
            
        upbit = pyupbit.Upbit(access, secret)
        
        # ���� �ڻ� ���� Ȯ��
        my_krw = upbit.get_balance("KRW")
        my_btc = upbit.get_balance("KRW-BTC")
        
        # Ÿ�� �˻� �� ��ȯ �߰�
        if my_krw and not isinstance(my_krw, (int, float)):
            try:
                my_krw = float(my_krw) if my_krw else 0
            except (TypeError, ValueError):
                my_krw = 0
                print("��ȭ �ܰ� ���ڷ� ��ȯ�� �� �����ϴ�. 0���� �����մϴ�.")
            
        if my_btc and not isinstance(my_btc, (int, float)):
            try:
                my_btc = float(my_btc) if my_btc else 0
            except (TypeError, ValueError):
                my_btc = 0
                print("��Ʈ���� �ܰ� ���ڷ� ��ȯ�� �� �����ϴ�. 0���� �����մϴ�.")
        
        # ���簡 ó�� - Ÿ�Կ� ���� ������ ó��
        current_price = 0
        try:
            # ���� ���簡 ��ȸ
            current_price_direct = pyupbit.get_current_price("KRW-BTC")
            if isinstance(current_price_direct, (int, float)):
                current_price = current_price_direct
            elif isinstance(current_price_direct, dict) and "trade_price" in current_price_direct:
                current_price = current_price_direct["trade_price"]
            else:
                print(f"���� ��ȸ�� ���簡 ���� Ȯ��: {type(current_price_direct)}")
                # ����Ʈ�� ��� ù ��° �׸� �õ�
                if isinstance(current_price_direct, list) and len(current_price_direct) > 0:
                    if isinstance(current_price_direct[0], (int, float)):
                        current_price = current_price_direct[0]
                    elif isinstance(current_price_direct[0], dict) and "trade_price" in current_price_direct[0]:
                        current_price = current_price_direct[0]["trade_price"]
        except Exception as e:
            print(f"���簡 ���� ��ȸ �� ����: {e}")
            
        # ���� ������ ������ ���� ��� (�׽�Ʈ��)
        if current_price == 0:
            current_price = 80000000  # ������ ��Ʈ���� ���� (�׽�Ʈ��)
            print(f"���簡�� ������ �� ���� ������ ����({current_price})�� ����մϴ�.")
        
        # ���� ��ġ ��� ����
        estimated_btc_value = my_btc * current_price if my_btc and current_price else 0
        
        print(f"���� ���� �ڻ�: {my_krw:.0f}�� + {my_btc} BTC (�� {estimated_btc_value:.0f}��)")
        print(f"�� �ڻ� ��ġ: �� {my_krw + estimated_btc_value:.0f}��")
        
        # ������ �Լ� �ڵ�� �״�� ����...
        
        # ����� ���� ������ ���� ���� ����
        # �ŷڵ��� �������� �� ���� ������ ����/�ŵ�
        min_ratio = INVESTMENT_RATIOS.get("min_ratio", 0.2)  # �ּ� ���� ���� (�⺻��: 20%)
        max_ratio = INVESTMENT_RATIOS.get("max_ratio", 0.5)  # �ִ� ���� ���� (�⺻��: 50%)
        # �ŷڵ��� ���� min_ratio~max_ratio ������ ������ �����ϸ�
        trade_ratio = min_ratio + (confidence * (max_ratio - min_ratio))
        
        # ������ ���� �Ÿ� ����
        if decision == "buy":
            # �ŷڵ��� ���� ���� ���� ����
            invest_amount = my_krw * trade_ratio
            
            min_order_amount = TRADING_SETTINGS.get("min_order_amount", 5000)  # �ּ� �ֹ� �ݾ� ����� ����
            
            if invest_amount > min_order_amount:  # �ּ� �ֹ� �ݾ� �̻�
                print(f"�ż� �õ�: {invest_amount:.0f}�� (���� KRW�� {trade_ratio*100:.0f}%)")
                order = upbit.buy_market_order("KRW-BTC", invest_amount)
                print(f"�ż� �ֹ� ���: {order}")
            else:
                print(f"�ż� ����: �ֹ� �ݾ��� {min_order_amount}�� �̸��Դϴ� (���� ���� KRW: {my_krw}��)")
                
        elif decision == "sell":
            # �ŷڵ��� ���� �ŵ� ���� ����
            sell_ratio = trade_ratio
            sell_amount = my_btc * sell_ratio
            
            # ���簡 Ȯ�� (�ŵ� �ݾ� ����)
            estimated_value = sell_amount * current_price
            
            min_order_amount = TRADING_SETTINGS.get("min_order_amount", 5000)  # �ּ� �ֹ� �ݾ� ����� ����
            
            if estimated_value > min_order_amount:  # �ּ� �ֹ� �ݾ� �̻�
                print(f"�ŵ� �õ�: {sell_amount} BTC (�� {estimated_value:.0f}��, �������� {sell_ratio*100:.0f}%)")
                order = upbit.sell_market_order("KRW-BTC", sell_amount)
                print(f"�ŵ� �ֹ� ���: {order}")
            else:
                print(f"�ŵ� ����: �ֹ� �ݾ��� {min_order_amount}�� �̸��Դϴ� (���� ���� BTC: {my_btc}, ������ġ: {estimated_value:.0f}��)")
        else:  # hold
            print("���� ������ ���� (Ȧ��)")
    
    except Exception as e:
        print(f"�Ÿ� ���� �� ���� �߻�: {e}")
        traceback.print_exc()
        print("�׽�Ʈ ���� ����: ���� �ŸŴ� �̷������ �ʾҽ��ϴ�.")

# 6. ���� �ŷ� �Լ� (���� �Լ�)
def integrated_trading():
    """Ȯ��� �����Ϳ� �м��� ���� ��Ʈ���� �ڵ��Ÿ��� ��ü ���μ����� �����մϴ�."""
    try:
        # 1. �پ��� �ŷ��� ������ ��������
        print("\n== �ŷ��� ������ ���� ���� ==")
        market_data = get_enhanced_market_data()
        if market_data is None:
            print("�����͸� �������� ���߽��ϴ�. ���� ������ ��ٸ��ϴ�.")
            return
            
        # 2. ����� ��ǥ ���
        print("\n== ����� ��ǥ ��� ���� ==")
        indicators = calculate_technical_indicators(market_data)
        if indicators is None:
            print("��ǥ ��꿡 �����߽��ϴ�. ���� ������ ��ٸ��ϴ�.")
            return
            
        # 3. ���� �м� ����
        print("\n== ���� �м� ���� ==")
        analysis_result = perform_integrated_analysis(market_data, indicators)
        
        # 4. Claude AI�� �м� �õ� (������)
        claude_result = None
        use_claude = CLAUDE_SETTINGS.get("use_claude", False)
        
        if use_claude:
            print("\n== Claude AI�� �м� �õ� ==")
            claude_result = get_claude_analysis(market_data)
        
        # 5. ���� ���� �� ��� ���
        final_result = None
        
        if analysis_result and claude_result:
            print("\n===== �м� ��� �� =====")
            print("��ü �м�:", analysis_result["decision"], f"(�ŷڵ�: {analysis_result['confidence']:.2f})")
            print("Claude �м�:", claude_result["decision"], f"(�ŷڵ�: {claude_result.get('confidence', 0.5):.2f})")
            
            # Claude�� �м� ������ ���
            if "reason" in claude_result:
                print(f"\nClaude �м� ����: {claude_result['reason']}")
                
            # ���� ��ǥ�� �ִٸ� ���
            if "price_target" in claude_result and claude_result["price_target"]:
                price_target = claude_result["price_target"]
                print("\nClaude ���� ����:")
                if "short_term" in price_target:
                    print(f"  �ܱ�: {price_target['short_term']:,}��")
                if "medium_term" in price_target:
                    print(f"  �߱�: {price_target['medium_term']:,}��")
            
            # �� �м��� ��ġ�ϸ� �ŷڵ� ���
            if analysis_result["decision"] == claude_result["decision"]:
                confidence_boost = CLAUDE_SETTINGS.get("confidence_boost", 0.1)
                boosted_confidence = min(0.95, (analysis_result["confidence"] + claude_result.get("confidence", 0.5)) / 2 + confidence_boost)
                final_decision = analysis_result["decision"]
                reason = f"��ü �м��� Claude AI �м� ����� ��ġ ({final_decision}). �ŷڵ� ���."
            else:
                # �ŷڵ��� �� ���� �м� ����
                claude_weight = CLAUDE_SETTINGS.get("weight", 1.0)
                analysis_weight = 1.0
                total_weight = analysis_weight + claude_weight
                
                if analysis_result["confidence"] >= claude_result.get("confidence", 0.5):
                    final_decision = analysis_result["decision"]
                    boosted_confidence = (analysis_result["confidence"] * analysis_weight) / total_weight
                    reason = f"��ü �м� �ŷڵ�({analysis_result['confidence']:.2f})�� �� ���� ä��"
                else:
                    final_decision = claude_result["decision"]
                    boosted_confidence = (claude_result.get("confidence", 0.5) * claude_weight) / total_weight
                    reason = f"Claude �м� �ŷڵ�({claude_result.get('confidence', 0.5):.2f})�� �� ���� ä��"
            
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
            print("\n===== �м� ��� =====")
            print(f"����: {final_decision} (�ŷڵ�: {final_confidence:.2f})")
        else:
            print("��� �м� ����� �����߽��ϴ�. ���� ������ ��ٸ��ϴ�.")
            return
        
        # 6. ��� ���
        print("\n===== ���� �м� ��� =====")
        print(json.dumps(final_result, indent=2, ensure_ascii=False))
        
        # �� ���� ���� ���
        print("\n===== �� ���� ���� =====")
        print(f"����: {final_result['decision_kr']} (�ŷڵ�: {final_result['confidence']:.2f})")
        
        print("\n[���� ��ǥ ��ȣ]")
        for signal in final_result['signals']:
            signal_icon = "?" if signal['signal'] == 'sell' else "?" if signal['signal'] == 'buy' else "?"
            print(f"{signal_icon} {signal['source']}: {signal['description']} (����: {signal['strength']:.2f})")
        
        print(f"\n�� ��ȣ ��: �ż� {final_result['signal_counts']['buy']}��, �ŵ� {final_result['signal_counts']['sell']}��, Ȧ�� {final_result['signal_counts']['hold']}��")
        print(f"���� ��ȣ ����: {final_result['avg_signal_strength']:.3f}")
        
        # 7. �Ÿ� ����
        trade_enabled = os.getenv("ENABLE_TRADE", "").lower() == "true"
        
        if trade_enabled:
            print("\n== �ڵ� �Ÿ� ���� ==")
            execute_trade(final_result["decision"], final_result["confidence"], market_data)
        else:
            print("\n== �ڵ� �Ÿ� ��Ȱ��ȭ�� (�׽�Ʈ ���) ==")
            print(f"����� �Ÿ�: {final_result['decision']} (�ŷڵ�: {final_result['confidence']:.2f})")
            
        # 8. ��� ���� (�α� �Ǵ� DB)
        try:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, f"trading_log_{datetime.now().strftime('%Y%m%d')}.json")
            
            # ���� �αװ� ������ �ε�
            existing_logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    existing_logs = json.load(f)
            
            # �� �α� �߰�
            existing_logs.append(final_result)
            
            # �α� ����
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(existing_logs, f, indent=2, ensure_ascii=False)
                
            print(f"\n�ŷ� �αװ� ����Ǿ����ϴ�: {log_file}")
        except Exception as e:
            print(f"�α� ���� �� ���� �߻�: {e}")
        
    except Exception as e:
        print(f"�ŷ� ���μ��� �� ����ġ ���� ���� �߻�: {e}")
        traceback.print_exc()

# ���� ���� �κ�
if __name__ == "__main__":
    print("Ȯ��� ��Ʈ���� �ڵ��Ÿ� �ý����� �����մϴ�...")
    print("�� ���α׷��� �پ��� �ŷ��� �����Ϳ� ��ü�� �����͸� Ȱ���մϴ�.")
    print("Ctrl+C�� ���� �������� ������ �� �ֽ��ϴ�.\n")
    
    # ȯ�� ���� ���� Ȯ��
    required_vars = {
        "UPBIT_ACCESS_KEY": "����Ʈ API ���� Ű",
        "UPBIT_SECRET_KEY": "����Ʈ API ��� Ű"
    }
    
    optional_vars = {
        "CLAUDE_API_KEY": "Claude AI API Ű (���� ����)",
        "GLASSNODE_API_KEY": "Glassnode API Ű (���� ����)",
        "USE_CLAUDE": "Claude AI ��� ���� (true/false)",
        "ENABLE_TRADE": "���� �Ÿ� Ȱ��ȭ ���� (true/false)"
    }
    
    # �ʼ� ȯ�� ���� Ȯ��
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("?? ���� �ʼ� ȯ�� ������ �������� �ʾҽ��ϴ�:")
        for var in missing_vars:
            print(f"  - {var}: {required_vars[var]}")
        print("\n.env ������ Ȯ���ϰų� ȯ�� ������ �����ϼ���.")
        
    # ������ ȯ�� ���� Ȯ��
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        status = "? ������" if value else "? �������� ����"
        print(f"{var}: {desc} - {status}")
    
    # ȯ�� ���� �ȳ�
    if not os.getenv("USE_CLAUDE", "").lower() == "true":
        print("\n? Claude AI�� ����Ϸ��� .env ���Ͽ� USE_CLAUDE=true�� CLAUDE_API_KEY�� �����ϼ���.")
    
    if not os.getenv("ENABLE_TRADE", "").lower() == "true":
        print("\n? ���� �ŸŸ� Ȱ��ȭ�Ϸ��� .env ���Ͽ� ENABLE_TRADE=true�� �����ϼ���.")
        print("   ����� �׽�Ʈ ���� ����˴ϴ�. (���� �Ÿ� ����)")
    else:
        print("\n?? ���� �ŸŰ� Ȱ��ȭ�Ǿ����ϴ�. �ڵ����� ���� �ŷ��� �̷�����ϴ�!")
    
    # ���� ������ ���� �ð����� �Ÿ� �м� �� ����
    interval_minutes = TRADING_SETTINGS.get("trading_interval", 60)  # �⺻�� 60��
    
    try:
        while True:
            print(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - �Ÿ� �м� ����")
            integrated_trading()
            
            next_run = datetime.now() + timedelta(minutes=interval_minutes)
            print(f"\n���� �м� ���� �ð�: {next_run.strftime('%Y-%m-%d %H:%M:%S')} ({interval_minutes}�� ��)")
            
            for i in range(interval_minutes):
                time.sleep(60)  # 1�о� ���
                minutes_left = interval_minutes - i - 1
                if minutes_left > 0 and minutes_left % 5 == 0:  # 5�� �������� ���� �޽���
                    print(f"���� �м����� {minutes_left}�� ���ҽ��ϴ�...")
    
    except KeyboardInterrupt:
        print("\n���α׷��� ����ڿ� ���� ����Ǿ����ϴ�.")
    except Exception as e:
        print(f"\n����ġ ���� ������ ���α׷��� ����˴ϴ�: {e}")
        traceback.print_exc()
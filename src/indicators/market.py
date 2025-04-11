import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MarketIndicators:
    """
    시장 지표 계산 클래스
    호가창, 체결 데이터, 김프 등 시장 관련 지표를 계산합니다.
    """
    
    def __init__(self, upbit_api=None):
        """
        시장 지표 계산기 초기화
        
        Args:
            upbit_api: UpbitAPI 인스턴스 (없으면 API 호출 기능 제한)
        """
        self.upbit_api = upbit_api
    
    # get_orderbook_ratio 함수 수정
    def get_orderbook_ratio(self, ticker="KRW-BTC"):
        """
        호가창 매수/매도 비율 계산
        
        Args:
            ticker: 티커 (예: KRW-BTC)
                
        Returns:
            float: 매수/매도 비율 (1보다 크면 매수세 강함, 1보다 작으면 매도세 강함)
        """
        if self.upbit_api is None:
            return 1.0
        
        try:
            orderbook = self.upbit_api.get_orderbook(ticker)
            
            # 데이터 구조 확인 및 안전한 처리
            if not orderbook or not isinstance(orderbook, list) or len(orderbook) == 0:
                print("Expected orderbook to be a non-empty list but got:", type(orderbook))
                return 1.0
                
            # 처리 방법 1: orderbook_units 키 있는 경우
            if 'orderbook_units' in orderbook[0]:
                units = orderbook[0].get("orderbook_units", [])
                # 총 매수 금액 (bid)
                total_bid = sum([x['price'] * x['quantity'] for x in units])
                # 총 매도 금액 (ask)
                total_ask = sum([x['price'] * x['quantity'] for x in units])
            # 처리 방법 2: bids/asks 키 있는 경우
            elif 'bids' in orderbook[0] and 'asks' in orderbook[0]:
                # 총 매수 금액 (bid)
                total_bid = sum([x['price'] * x['quantity'] for x in orderbook[0]['bids']])
                # 총 매도 금액 (ask)
                total_ask = sum([x['price'] * x['quantity'] for x in orderbook[0]['asks']])
            else:
                # 호가창 구조를 확인하고 디버깅
                print("Unexpected orderbook structure:", orderbook[0].keys())
                return 1.0
            
            # 매수/매도 비율
            if total_ask == 0:
                return 2.0  # 매도 주문이 없으면 매수세가 강함
            
            return total_bid / total_ask
        except Exception as e:
            print(f"호가창 비율 계산 오류: {e}")
            return 1.0
    
    def get_orderbook_signal(self, ticker="KRW-BTC", threshold=0.2):
        """
        호가창 매수/매도 신호 계산
        
        Args:
            ticker: 티커 (예: KRW-BTC)
            threshold: 신호 발생 임계값 (기본: 0.2)
            
        Returns:
            tuple: (신호, 강도, 설명)
                신호: "buy", "sell", "hold" 중 하나
                강도: 0.0~1.0 사이의 신호 강도
                설명: 신호에 대한 설명
        """
        ratio = self.get_orderbook_ratio(ticker)
        
        # 매수/매도 비율이 1+threshold보다 크면 매수세 강함
        if ratio > 1 + threshold:
            strength = min(0.6, (ratio - 1) / 2)  # 최대 강도: 0.6
            return "buy", strength, f"매수세 강함 (매수/매도 비율: {ratio:.2f})"
        
        # 매수/매도 비율이 1-threshold보다 작으면 매도세 강함
        elif ratio < 1 - threshold:
            strength = min(0.6, (1 - ratio) / 2)  # 최대 강도: 0.6
            return "sell", strength, f"매도세 강함 (매수/매도 비율: {ratio:.2f})"
        
        # 그 외에는 중립적
        else:
            return "hold", 0, f"중립적 호가창 (매수/매도 비율: {ratio:.2f})"
    
    def get_trade_volume_analysis(self, ticker="KRW-BTC", timeframe_minutes=10):
        """
        최근 체결 데이터 분석
        
        Args:
            ticker: 티커 (예: KRW-BTC)
            timeframe_minutes: 분석 시간 프레임 (분)
            
        Returns:
            tuple: (신호, 강도, 설명)
                신호: "buy", "sell", "hold" 중 하나
                강도: 0.0~1.0 사이의 신호 강도
                설명: 신호에 대한 설명
        """
        if self.upbit_api is None:
            return "hold", 0, "API 인스턴스가 없어 체결 데이터를 분석할 수 없습니다."
        
        try:
            # 최근 체결 내역 조회 (최대 100개)
            trades = None
            try:
                # 직접 API 요청으로 체결 데이터 가져오기
                url = f"https://api.upbit.com/v1/trades/ticks?market={ticker}&count=100"
                response = requests.get(url, timeout=10)  # 타임아웃 추가
                trades = response.json()
            except Exception as e:
                print(f"체결 데이터 API 요청 오류: {e}")
                # API 요청 실패 시, 더미 데이터 사용 또는 오류 대체
                return "hold", 0, "체결 데이터를 가져올 수 없습니다."
            
            # 현재 시간 기준으로 timeframe_minutes분 이내의 체결만 필터링
            now = datetime.now()
            cutoff_time = now - timedelta(minutes=timeframe_minutes)
            
            # 시간 필터링
            recent_trades = []
            try:
                for trade in trades:
                    try:
                        trade_time = datetime.strptime(trade['trade_time_utc'], '%Y-%m-%dT%H:%M:%S')
                        if trade_time >= cutoff_time:
                            recent_trades.append(trade)
                    except (KeyError, ValueError) as e:
                        print(f"체결 데이터 형식 오류: {e}")
                        continue
            except Exception as e:
                print(f"체결 데이터 시간 필터링 오류: {e}")
                return "hold", 0, "체결 데이터 처리 오류"
            
            if not recent_trades:
                return "hold", 0, "최근 체결 데이터가 없습니다."
            
            # 매수/매도 체결량 계산
            try:
                ask_volume = sum([float(trade.get('trade_volume', 0)) for trade in recent_trades if trade.get('ask_bid') == 'ASK'])
                bid_volume = sum([float(trade.get('trade_volume', 0)) for trade in recent_trades if trade.get('ask_bid') == 'BID'])
                
                total_volume = ask_volume + bid_volume
                if total_volume == 0:
                    return "hold", 0, "최근 체결 데이터가 없습니다."
                
                # 매수 비율 계산
                bid_ratio = bid_volume / total_volume
            except Exception as e:
                print(f"체결량 계산 오류: {e}")
                return "hold", 0, "체결량 계산 오류"
            
            # 신호 판단
            if bid_ratio > 0.6:  # 매수 비율이 60% 이상이면 매수세 강함
                strength = min(0.5, (bid_ratio - 0.5) * 2)  # 최대 강도: 0.5
                return "buy", strength, f"매수세 강함 (매수 비율: {bid_ratio:.2%})"
            elif bid_ratio < 0.4:  # 매수 비율이 40% 이하이면 매도세 강함
                strength = min(0.5, (0.5 - bid_ratio) * 2)  # 최대 강도: 0.5
                return "sell", strength, f"매도세 강함 (매수 비율: {bid_ratio:.2%})"
            else:
                return "hold", 0, f"중립적 체결 (매수 비율: {bid_ratio:.2%})"
        except Exception as e:
            print(f"체결 데이터 분석 오류: {e}")
            return "hold", 0, "체결 데이터 분석 오류"
    
    def get_korea_premium(self):
        """
        한국 프리미엄(김프) 계산
        
        Returns:
            tuple: (신호, 강도, 설명, 김프 비율)
                신호: "buy", "sell", "hold" 중 하나
                강도: 0.0~1.0 사이의 신호 강도
                설명: 신호에 대한 설명
                김프 비율: 한국 프리미엄 비율 (%)
        """
        if self.upbit_api is None:
            return "hold", 0, "API 인스턴스가 없어 김프를 계산할 수 없습니다.", 0
        
        try:
            # 업비트 BTC 가격 (원)
            krw_btc = self.upbit_api.get_current_price("KRW-BTC")
            if not krw_btc:  # None 체크 추가
                return "hold", 0, "업비트 가격 조회 실패", 0
            
            # 바이낸스 BTC 가격 (달러)
            try:
                url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
                response = requests.get(url, timeout=5)  # 타임아웃 설정
                binance_btc_usdt = float(response.json()["price"])
            except Exception as e:
                print(f"바이낸스 API 오류: {e}")
                return "hold", 0, "바이낸스 가격 조회 실패", 0
            
            # 달러 환율 (USD/KRW)
            try:
                url = "https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD"
                response = requests.get(url, timeout=5)  # 타임아웃 설정
                usd_krw = float(response.json()[0]["basePrice"])
            except Exception as e:
                print(f"환율 API 오류: {e}")
                # 환율 API 실패 시 고정 환율 사용
                usd_krw = 1350.0  # 임시 환율 값
                print(f"환율 API 실패로 임시 환율 사용: {usd_krw}")
            
            # 바이낸스 BTC 가격 (원)
            binance_btc_krw = binance_btc_usdt * usd_krw
            
            # 김프 계산 (%)
            kimp = ((krw_btc / binance_btc_krw) - 1) * 100
            kimp_rounded = round(kimp, 2)
            
            # 신호 판단
            if kimp < -1.0:  # 역프리미엄 1% 이상이면 매수 신호
                strength = min(0.5, abs(kimp) / 10)
                return "buy", strength, f"낮은 한국 프리미엄 (김프: {kimp_rounded:.2f}%)", kimp_rounded
            elif kimp > 5.0:  # 프리미엄 5% 이상이면 매도 신호
                strength = min(0.5, kimp / 10)
                return "sell", strength, f"높은 한국 프리미엄 (김프: {kimp_rounded:.2f}%)", kimp_rounded
            else:
                return "hold", 0, f"적정 한국 프리미엄 (김프: {kimp_rounded:.2f}%)", kimp_rounded
        except Exception as e:
            print(f"김프 계산 오류: {e}")
            return "hold", 0, "김프 계산 오류", 0
    
    def get_fear_greed_index(self):
        """
        공포&탐욕 지수 조회
        
        Returns:
            tuple: (신호, 강도, 설명, 지수 값)
                신호: "buy", "sell", "hold" 중 하나
                강도: 0.0~1.0 사이의 신호 강도
                설명: 신호에 대한 설명
                지수 값: 공포&탐욕 지수 (0-100)
        """
        try:
            # Alternative.me 공포&탐욕 지수 API
            url = "https://api.alternative.me/fng/"
            response = requests.get(url)
            data = response.json()
            
            # 지수 값 추출
            fear_greed_value = int(data['data'][0]['value'])
            fear_greed_classification = data['data'][0]['value_classification']
            
            # 신호 판단
            if fear_greed_value <= 25:  # 극도의 공포 (0-25)
                strength = 0.7  # 매수 신호 강도
                return "buy", strength, f"극도의 공포 상태 (Fear & Greed: {fear_greed_value}, {fear_greed_classification})", fear_greed_value
            elif fear_greed_value <= 40:  # 공포 (26-40)
                strength = 0.4  # 약한 매수 신호
                return "buy", strength, f"공포 우세 상태 (Fear & Greed: {fear_greed_value}, {fear_greed_classification})", fear_greed_value
            elif fear_greed_value >= 75:  # 극도의 탐욕 (75-100)
                strength = 0.7  # 매도 신호 강도
                return "sell", strength, f"극도의 탐욕 상태 (Fear & Greed: {fear_greed_value}, {fear_greed_classification})", fear_greed_value
            elif fear_greed_value >= 60:  # 탐욕 (60-74)
                strength = 0.4  # 약한 매도 신호
                return "sell", strength, f"탐욕 우세 상태 (Fear & Greed: {fear_greed_value}, {fear_greed_classification})", fear_greed_value
            else:  # 중립 (41-59)
                return "hold", 0, f"중립적 시장 심리 (Fear & Greed: {fear_greed_value}, {fear_greed_classification})", fear_greed_value
        except Exception as e:
            print(f"공포&탐욕 지수 조회 오류: {e}")
            return "hold", 0, "공포&탐욕 지수 조회 오류", 50
    
    def get_all_market_signals(self):
        """
        모든 시장 지표 신호 계산
        
        Returns:
            dict: 지표별 신호
        """
        signals = {}
        
        # 호가창 분석
        orderbook_signal, orderbook_strength, orderbook_desc = self.get_orderbook_signal()
        signals["Orderbook"] = {
            "signal": orderbook_signal,
            "strength": orderbook_strength,
            "description": orderbook_desc
        }
        
        # 체결 데이터 분석
        trade_signal, trade_strength, trade_desc = self.get_trade_volume_analysis()
        signals["Trades"] = {
            "signal": trade_signal,
            "strength": trade_strength,
            "description": trade_desc
        }
        
        # 김프 분석
        kimp_signal, kimp_strength, kimp_desc, kimp_value = self.get_korea_premium()
        signals["KIMP"] = {
            "signal": kimp_signal,
            "strength": kimp_strength,
            "description": kimp_desc,
            "value": kimp_value
        }
        
        # 공포&탐욕 지수
        fg_signal, fg_strength, fg_desc, fg_value = self.get_fear_greed_index()
        signals["FearGreed"] = {
            "signal": fg_signal,
            "strength": fg_strength,
            "description": fg_desc,
            "value": fg_value
        }
        
        return signals

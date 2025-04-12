import os
import time
import uuid
import jwt
import hashlib
import requests
import pandas as pd
import pyupbit
from urllib.parse import urlencode

class UpbitAPI:
    """
    업비트 API 래퍼 클래스
    업비트 API를 사용하여 시세 조회, 주문, 잔고 조회 등의 기능을 제공합니다.
    """
    
    def __init__(self, access_key=None, secret_key=None):
        """
        업비트 API 초기화
        
        Args:
            access_key: 업비트 API 액세스 키 (없으면 환경변수에서 로드)
            secret_key: 업비트 API 시크릿 키 (없으면 환경변수에서 로드)
        """
        self.access_key = access_key or os.getenv("UPBIT_ACCESS_KEY")
        self.secret_key = secret_key or os.getenv("UPBIT_SECRET_KEY")
        self.base_url = "https://api.upbit.com/v1"
        
        # PyUpbit 클라이언트 초기화
        if self.access_key and self.secret_key:
            self.client = pyupbit.Upbit(self.access_key, self.secret_key)
        else:
            self.client = None
            
    def _get_headers(self, query=None):
        """
        API 요청 헤더 생성
        
        Args:
            query: 쿼리 파라미터 (dict)
            
        Returns:
            dict: API 요청 헤더
        """
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }

        if query:
            m = hashlib.sha512()
            m.update(urlencode(query).encode())
            query_hash = m.hexdigest()
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'

        jwt_token = jwt.encode(payload, self.secret_key)
        return {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
    
    def get_current_price(self, ticker="KRW-BTC"):
        """
        현재가 조회 - 여러 방법으로 시도
        
        Args:
            ticker: 티커 (예: KRW-BTC)
            
        Returns:
            float: 현재가 (원) 혹은 실패 시 None
        """
        # 여러 방법으로 조회 시도
        methods = [
            "pyupbit.get_current_price",
            "pyupbit.get_orderbook", 
            "direct_api_call"
        ]
        
        last_error = None
        
        for method in methods:
            try:
                print(f"현재가 조회 시도 ({method})...")
                
                # 방법 1: 기본 PyUpbit 현재가 조회
                if method == "pyupbit.get_current_price":
                    current_price = pyupbit.get_current_price(ticker)
                    if current_price is not None and current_price > 0:
                        print(f"{method} 성공: {current_price}")
                        return current_price
                
                # 방법 2: 호가창에서 정보 추출
                elif method == "pyupbit.get_orderbook":
                    orderbook = pyupbit.get_orderbook(ticker)
                    if orderbook and len(orderbook) > 0:
                        # 호가창 정보에서 중앙값 추출
                        if 'orderbook_units' in orderbook[0] and orderbook[0]['orderbook_units']:
                            units = orderbook[0]['orderbook_units']
                            if units:
                                # 첫 번째 호가 정보에서 추출
                                first_unit = units[0]
                                ask_price = first_unit.get('ask_price')
                                bid_price = first_unit.get('bid_price')
                                
                                if ask_price and bid_price:
                                    # 매수/매도가의 중간값 사용
                                    avg_price = (ask_price + bid_price) / 2
                                    if avg_price > 0:
                                        print(f"{method} 성공: {avg_price} (매수-매도 호가 중간값)")
                                        return avg_price
                                        
                        # 최신 PyUpbit 버전 호가창 구조 지원 (최근 업데이트 반영)
                        elif 'asks' in orderbook[0] and 'bids' in orderbook[0]:
                            asks = orderbook[0].get('asks', [])
                            bids = orderbook[0].get('bids', [])
                            
                            if asks and bids:
                                ask_price = asks[0][0] if asks else None
                                bid_price = bids[0][0] if bids else None
                                
                                if ask_price and bid_price:
                                    avg_price = (ask_price + bid_price) / 2
                                    if avg_price > 0:
                                        print(f"{method} 성공: {avg_price} (매수-매도 호가 중간값)")
                                        return avg_price
                
                # 방법 3: 직접 API 요청
                elif method == "direct_api_call":
                    # 티커 API 요청
                    url = f"{self.base_url}/ticker?markets={ticker}"
                    headers = self._get_headers()
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data and len(data) > 0:
                            price = data[0].get('trade_price')
                            if price is not None and price > 0:
                                print(f"{method} 성공: {price}")
                                return price
                    
                    # 다른 URL도 시도
                    url = f"{self.base_url}/trades/ticks?market={ticker}&count=1"
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data and len(data) > 0:
                            price = data[0].get('trade_price')
                            if price is not None and price > 0:
                                print(f"{method} 성공 (trades/ticks): {price}")
                                return price
                    
            except Exception as e:
                print(f"{method} 실패: {e}")
                last_error = e
        
        # 모든 방법 실패 시
        error_msg = str(last_error) if last_error else "알 수 없는 오류"
        print(f"모든 방법으로 현재가 조회 실패: {error_msg}")
        return None
        
    def get_balance(self, ticker=None):
        """
        잔고 조회
        
        Args:
            ticker: 티커 (예: KRW-BTC, None이면 전체 잔고 조회)
            
        Returns:
            float or dict: 특정 티커의 잔고 또는 전체 잔고
        """
        if not self.client:
            raise ValueError("API 키 정보가 필요합니다.")
        
        if ticker:
            return self.client.get_balance(ticker)
        else:
            return self.client.get_balances()
    
    def get_orderbook(self, ticker="KRW-BTC"):
        """
        호가창 조회
        
        Args:
            ticker: 티커 (예: KRW-BTC)
                
        Returns:
            dict or list: 호가창 정보
        """
        try:
            # 호가창 조회 시도
            orderbook = pyupbit.get_orderbook(ticker)
            
            # 데이터 구조 확인
            if orderbook is None or len(orderbook) == 0:
                return [{
                    "market": ticker,
                    "orderbook_units": []
                }]
            
            # PyUpbit 0.2.33 버전 구조: orderbook_units 포함
            if isinstance(orderbook, list) and "orderbook_units" in orderbook[0]:
                return orderbook
            
            # 최신 PyUpbit 버전 구조: asks, bids 포함
            elif isinstance(orderbook, list) and "asks" in orderbook[0] and "bids" in orderbook[0]:
                # 안전하게 새 구조로 변환
                asks = orderbook[0].get("asks", [])
                bids = orderbook[0].get("bids", [])
                
                formatted_orderbook = [{
                    "market": ticker,
                    "timestamp": orderbook[0].get("timestamp", 0),
                    "total_ask_size": sum([ask[1] for ask in asks]) if asks else 0,
                    "total_bid_size": sum([bid[1] for bid in bids]) if bids else 0,
                    "orderbook_units": [
                        {
                            "ask_price": ask[0],
                            "ask_size": ask[1],
                            "bid_price": bid[0] if idx < len(bids) else 0,
                            "bid_size": bid[1] if idx < len(bids) else 0
                        } for idx, (ask, bid) in enumerate(zip(asks, bids))
                    ] if asks and bids else []
                }]
                return formatted_orderbook
            
            # 알 수 없는 형태
            else:
                return [{
                    "market": ticker,
                    "orderbook_units": []
                }]
                
        except Exception as e:
            print(f"호가창 조회 오류: {e}")
            # 오류 발생 시 빈 호가창 반환
            return [{
                "market": ticker,
                "orderbook_units": []
            }]
    
    def get_ohlcv(self, ticker="KRW-BTC", interval="minute60", count=200):
        """
        캔들 데이터 조회
        
        Args:
            ticker: 티커 (예: KRW-BTC)
            interval: 차트 간격 (분/시간/일/주/월)
            count: 가져올 캔들 개수
            
        Returns:
            pandas.DataFrame: 캔들 데이터
        """
        return pyupbit.get_ohlcv(ticker, interval=interval, count=count)
    
    def buy_market_order(self, ticker, amount_krw):
        """
        시장가 매수
        
        Args:
            ticker: 티커 (예: KRW-BTC)
            amount_krw: 매수 금액 (원)
            
        Returns:
            dict: 주문 결과
        """
        if not self.client:
            raise ValueError("API 키 정보가 필요합니다.")
        
        return self.client.buy_market_order(ticker, amount_krw)
    
    def sell_market_order(self, ticker, volume):
        """
        시장가 매도
        
        Args:
            ticker: 티커 (예: KRW-BTC)
            volume: 매도 수량 (BTC)
            
        Returns:
            dict: 주문 결과
        """
        if not self.client:
            raise ValueError("API 키 정보가 필요합니다.")
        
        return self.client.sell_market_order(ticker, volume)
    
    def get_avg_buy_price(self, ticker):
        """
        평균 매수가 조회
        
        Args:
            ticker: 티커 (예: KRW-BTC)
            
        Returns:
            float: 평균 매수가
        """
        if not self.client:
            raise ValueError("API 키 정보가 필요합니다.")
        
        return self.client.get_avg_buy_price(ticker)
    
    def get_ticker_lists(self):
        """
        모든 티커 목록 조회
        
        Returns:
            list: 티커 목록
        """
        return pyupbit.get_tickers(fiat="KRW")
    
    def get_korea_premium(self):
        """
        한국 프리미엄(김프) 계산
        
        Returns:
            float: 김프 비율 (%)
        """
        try:
            # 업비트 BTC 가격 (원)
            krw_btc = self.get_current_price("KRW-BTC")
            if krw_btc is None:
                print("업비트 가격을 가져올 수 없습니다.")
                return 0
                
            # 바이낸스 BTC 가격 및 환율 정보 조회 시도
            try:
                # 바이낸스 BTC 가격 (달러)
                try:
                    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
                    response = requests.get(url, timeout=5)
                    binance_btc_usdt = float(response.json()["price"])
                except Exception as e:
                    print(f"바이낸스 가격 조회 오류: {e}, 기본값 사용")
                    # 환율 정보가 없으므로 임의의 가격 설정 (김프 0%로 가정)
                    binance_btc_usdt = 50000  # 임시 BTC 가격 (USD)
                
                # 달러 환율 (USD/KRW) 조회
                try:
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    url = "https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD"
                    response = requests.get(url, headers=headers, timeout=5)
                    usd_krw = float(response.json()[0]["basePrice"])
                except Exception as e:
                    print(f"환율 정보 조회 오류: {e}, 기본값 사용")
                    usd_krw = 1350.0  # 임시 환율 값
                
                # 바이낸스 BTC 가격 (원)
                binance_btc_krw = binance_btc_usdt * usd_krw
                
                # 김프 계산 (%)
                if binance_btc_krw > 0:
                    kimp = ((krw_btc / binance_btc_krw) - 1) * 100
                    return round(kimp, 2)
                else:
                    print("환산된 바이낸스 가격이 유효하지 않습니다.")
                    return 0
            except Exception as e:
                print(f"김프 계산 중 오류: {e}")
                return 0
        except Exception as e:
            print(f"김프 계산 오류: {e}")
            return 0

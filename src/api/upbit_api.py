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
        현재가 조회
        
        Args:
            ticker: 티커 (예: KRW-BTC)
            
        Returns:
            float: 현재가 (원)
        """
        return pyupbit.get_current_price(ticker)
    
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
            dict: 호가창 정보
        """
        return pyupbit.get_orderbook(ticker)
    
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
            
            # 바이낸스 BTC 가격 (달러)
            url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
            response = requests.get(url)
            binance_btc_usdt = float(response.json()["price"])
            
            # 달러 환율 (USD/KRW)
            url = "https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD"
            response = requests.get(url)
            usd_krw = float(response.json()[0]["basePrice"])
            
            # 바이낸스 BTC 가격 (원)
            binance_btc_krw = binance_btc_usdt * usd_krw
            
            # 김프 계산 (%)
            kimp = ((krw_btc / binance_btc_krw) - 1) * 100
            
            return round(kimp, 2)
        except Exception as e:
            print(f"김프 계산 오류: {e}")
            return 0

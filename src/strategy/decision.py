import os
import json
from datetime import datetime

class TradingEngine:
    """
    트레이딩 엔진 클래스
    신호 분석 결과를 바탕으로 실제 매매 결정 및 주문을 수행합니다.
    """
    
    def __init__(self, config, upbit_api, signal_analyzer):
        """
        트레이딩 엔진 초기화
        
        Args:
            config: 트레이딩 설정
            upbit_api: UpbitAPI 인스턴스
            signal_analyzer: SignalAnalyzer 인스턴스
        """
        self.config = config
        self.upbit_api = upbit_api
        self.signal_analyzer = signal_analyzer
        
        # 설정값 추출
        self.trading_settings = config.get("TRADING_SETTINGS", {})
        self.investment_ratios = config.get("INVESTMENT_RATIOS", {})
        self.enable_trade = os.getenv("ENABLE_TRADE", "false").lower() == "true"
        
        # 거래 기록
        self.trade_history = []
    
    def get_market_data(self, ticker="KRW-BTC"):
        """
        시장 데이터 조회
        
        Args:
            ticker: 티커 (예: KRW-BTC)
            
        Returns:
            dict: 시장 데이터
        """
        # 기본 데이터 구조 정의
        market_data = {
            "current_price": None,
            "price_change_24h": "N/A"
        }
        
        # 1. 현재가 조회
        current_price = None
        try:
            current_price = self.upbit_api.get_current_price(ticker)
            if current_price is not None:
                print(f"현재가 조회 성공: {current_price}")
                market_data["current_price"] = [
                    {"market": ticker, "trade_price": current_price}
                ]
            else:
                print("현재가 조회 실패: None 반환")
        except Exception as e:
            print(f"현재가 조회 오류: {e}")
            
        # 2. 일봉 데이터 조회 (24시간 가격 변화율 계산용)
        try:
            ohlcv = self.upbit_api.get_ohlcv(ticker, interval="day", count=2)
            if ohlcv is not None and not ohlcv.empty and len(ohlcv) >= 2:
                print(f"일봉 데이터 조회 성공: {len(ohlcv)} 개 데이터")
                
                # 24시간 가격 변화율 계산
                prev_close = ohlcv['close'].iloc[-2]
                if current_price is not None and prev_close > 0:
                    price_change = ((current_price / prev_close) - 1) * 100
                    market_data["price_change_24h"] = f"{price_change:.2f}%"
                    print(f"24시간 가격 변화율: {market_data['price_change_24h']}")
            else:
                print("일봉 데이터 없거나 불충분")
        except Exception as e:
            print(f"일봉 데이터 조회 오류: {e}")
            
        # 3. 현재가가 없으면 데이터 표시 처리
        if market_data["current_price"] is None:
            # 현재가 없을 때는 윈시리스트 추가 - 나중에 재시도할 수 있도록
            market_data["current_price"] = [
                {"market": ticker, "trade_price": None, "error": "현재가 정보 없음"}
            ]
        
        print(f"반환되는 시장 데이터: {market_data}")
        return market_data
    
    def analyze_market(self, ticker="KRW-BTC"):
        """
        시장 분석 수행
        
        Args:
            ticker: 티커 (예: KRW-BTC)
            
        Returns:
            dict: 분석 결과
        """
        # 시장 데이터 조회
        market_data = self.get_market_data(ticker)
        
        # 신호 분석
        analysis_result = self.signal_analyzer.analyze(market_data)
        
        # 분석 결과 로깅
        self._log_analysis(analysis_result)
        
        return analysis_result
    
    def execute_trade(self, analysis_result, ticker="KRW-BTC"):
        """
        분석 결과에 따라 실제 거래 실행
        
        Args:
            analysis_result: 분석 결과 (dict)
            ticker: 티커 (예: KRW-BTC)
            
        Returns:
            dict: 거래 결과
        """
        if not self.enable_trade:
            return {"status": "disabled", "message": "거래 기능이 비활성화되어 있습니다."}
        
        decision = analysis_result.get("decision")
        confidence = analysis_result.get("confidence", 0.5)
        
        # 최소 주문 금액
        min_order_amount = self.trading_settings.get("min_order_amount", 5000)
        
        try:
            # 현재 잔고 조회
            krw_balance = self.upbit_api.get_balance("KRW")
            btc_balance = self.upbit_api.get_balance(ticker)
            
            # 현재가 조회 - 안전하게 처리
            current_price = None
            
            # 1. 분석 결과에서 현재가 추출 시도
            try:
                if analysis_result.get("current_price") and isinstance(analysis_result.get("current_price"), list) and len(analysis_result.get("current_price")) > 0:
                    current_price = analysis_result.get("current_price")[0].get("trade_price")
                    print(f"분석 결과에서 추출한 현재가: {current_price}")
            except Exception as e:
                print(f"분석 결과에서 현재가 추출 오류: {e}")
                
            # 2. current_price가 None이면 직접 API로 조회 시도
            if not current_price:
                try:
                    current_price = self.upbit_api.get_current_price(ticker)
                    print(f"API에서 직접 조회한 현재가: {current_price}")
                except Exception as e:
                    print(f"API에서 현재가 조회 오류: {e}")
            
            # 3. 여전히 None이면 거래 실패
            if not current_price:
                print("현재가 정보를 가져올 수 없어 거래를 중단합니다.")
                return {"status": "error", "message": "현재가 정보를 가져올 수 없습니다."}
            
            # 투자 비율 계산 (신뢰도에 따라 조정)
            min_ratio = self.investment_ratios.get("min_ratio", 0.1)
            max_ratio = self.investment_ratios.get("max_ratio", 0.5)
            
            # 신뢰도에 따른 투자 비율 결정 (선형 보간)
            investment_ratio = min_ratio + (max_ratio - min_ratio) * (confidence - 0.5) * 2
            investment_ratio = max(min_ratio, min(max_ratio, investment_ratio))
            
            # 매매 실행
            trade_result = {"status": "no_action", "message": "조건에 맞는 거래가 없습니다."}
            
            if decision == "buy" and krw_balance > min_order_amount:
                # 매수할 금액 계산
                buy_amount = krw_balance * investment_ratio
                
                # 최소 주문 금액 확인
                if buy_amount < min_order_amount:
                    buy_amount = min_order_amount
                
                # 최대 가용 금액 확인
                buy_amount = min(buy_amount, krw_balance)
                
                # 시장가 매수 주문
                order = self.upbit_api.buy_market_order(ticker, buy_amount)
                
                # 거래 기록 저장
                trade_info = {
                    "type": "buy",
                    "ticker": ticker,
                    "price": current_price,
                    "amount": buy_amount / current_price,
                    "total": buy_amount,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "confidence": confidence,
                    "order_id": order.get("uuid")
                }
                
                self.trade_history.append(trade_info)
                self._log_trade(trade_info)
                
                trade_result = {
                    "status": "success",
                    "action": "buy",
                    "amount": buy_amount,
                    "price": current_price,
                    "message": f"{ticker} {buy_amount:.0f}원 매수 완료"
                }
                
            elif decision == "sell" and btc_balance > 0:
                # 전체 보유량의 일부만 매도
                sell_amount = btc_balance * investment_ratio
                
                # 최소 금액 확인 (현재가 기준)
                if sell_amount * current_price < min_order_amount and btc_balance * current_price >= min_order_amount:
                    sell_amount = min_order_amount / current_price
                
                # 시장가 매도 주문
                if sell_amount > 0:
                    order = self.upbit_api.sell_market_order(ticker, sell_amount)
                    
                    # 거래 기록 저장
                    trade_info = {
                        "type": "sell",
                        "ticker": ticker,
                        "price": current_price,
                        "amount": sell_amount,
                        "total": sell_amount * current_price,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "confidence": confidence,
                        "order_id": order.get("uuid")
                    }
                    
                    self.trade_history.append(trade_info)
                    self._log_trade(trade_info)
                    
                    trade_result = {
                        "status": "success",
                        "action": "sell",
                        "amount": sell_amount,
                        "price": current_price,
                        "message": f"{ticker} {sell_amount:.8f} BTC 매도 완료"
                    }
            
            return trade_result
        
        except Exception as e:
            error_msg = f"거래 실행 오류: {e}"
            print(error_msg)
            return {"status": "error", "message": error_msg}
    
    def _log_analysis(self, analysis_result):
        """
        분석 결과 로깅
        
        Args:
            analysis_result: 분석 결과 (dict)
        """
        try:
            # 로그 디렉토리 확인
            if not os.path.exists("logs"):
                os.makedirs("logs")
            
            # 로그 파일명 (일자별)
            log_date = datetime.now().strftime("%Y%m%d")
            log_file = f"logs/trading_log_{log_date}.json"
            
            # 기존 로그 파일 읽기
            log_data = []
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    try:
                        log_data = json.load(f)
                    except json.JSONDecodeError:
                        log_data = []
            
            # 로그 데이터 추가 - 결정 이유는 줄바꿈으로 포매팅
            if 'reasoning' in analysis_result and analysis_result['reasoning'] is not None:
                analysis_result['reasoning_lines'] = analysis_result['reasoning'].split('\n')
            
            log_data.append(analysis_result)
            
            # 로그 파일 쓰기
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print(f"로그 저장 오류: {e}")
    
    def _log_trade(self, trade_info):
        """
        거래 정보 로깅
        
        Args:
            trade_info: 거래 정보 (dict)
        """
        try:
            # 로그 디렉토리 확인
            if not os.path.exists("logs"):
                os.makedirs("logs")
            
            # 로그 파일명 (일자별)
            log_date = datetime.now().strftime("%Y%m%d")
            log_file = f"logs/trade_history_{log_date}.json"
            
            # 기존 로그 파일 읽기
            trade_log = []
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    try:
                        trade_log = json.load(f)
                    except json.JSONDecodeError:
                        trade_log = []
            
            # 로그 데이터 추가
            trade_log.append(trade_info)
            
            # 로그 파일 쓰기
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(trade_log, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print(f"거래 로그 저장 오류: {e}")
    
    def get_trading_stats(self):
        """
        트레이딩 통계 정보 조회
        
        Returns:
            dict: 트레이딩 통계
        """
        try:
            stats = {
                "total_trades": len(self.trade_history),
                "buy_count": 0,
                "sell_count": 0,
                "total_buy_amount": 0,
                "total_sell_amount": 0,
                "avg_buy_price": 0,
                "avg_sell_price": 0,
                "last_trade": None
            }
            
            # 거래 정보 분석
            for trade in self.trade_history:
                if trade["type"] == "buy":
                    stats["buy_count"] += 1
                    stats["total_buy_amount"] += trade["total"]
                elif trade["type"] == "sell":
                    stats["sell_count"] += 1
                    stats["total_sell_amount"] += trade["total"]
            
            # 평균 가격 계산
            if stats["buy_count"] > 0:
                stats["avg_buy_price"] = stats["total_buy_amount"] / stats["buy_count"]
            
            if stats["sell_count"] > 0:
                stats["avg_sell_price"] = stats["total_sell_amount"] / stats["sell_count"]
            
            # 마지막 거래 정보
            if self.trade_history:
                stats["last_trade"] = self.trade_history[-1]
            
            return stats
        
        except Exception as e:
            print(f"트레이딩 통계 계산 오류: {e}")
            return {"error": str(e)}
    
    def start_trading_loop(self, ticker="KRW-BTC", interval_minutes=None):
        """
        트레이딩 루프 시작
        
        Args:
            ticker: 티커 (예: KRW-BTC)
            interval_minutes: 트레이딩 간격 (분) (None이면 설정 파일에서 가져옴)
        
        Note:
            이 메서드는 일반적으로 별도의 스레드나 스케줄러에서 실행됩니다.
        """
        import time
        
        # 트레이딩 간격 설정
        if interval_minutes is None:
            interval_minutes = self.trading_settings.get("trading_interval", 60)
        
        interval_seconds = interval_minutes * 60
        
        print(f"트레이딩 루프 시작 (간격: {interval_minutes}분)")
        
        try:
            while True:
                # 현재 시간
                now = datetime.now()
                
                # 트레이딩 시간대 제한 확인
                trading_hours = self.trading_settings.get("trading_hours", {})
                trading_time_enabled = trading_hours.get("enabled", False)
                
                execute_trade = True
                
                if trading_time_enabled:
                    start_hour = trading_hours.get("start_hour", 9)
                    end_hour = trading_hours.get("end_hour", 23)
                    current_hour = now.hour
                    
                    # 설정된 시간대가 아니면 거래 실행 안 함
                    if current_hour < start_hour or current_hour > end_hour:
                        execute_trade = False
                        print(f"트레이딩 시간대 아님 (현재: {current_hour}시, 설정: {start_hour}-{end_hour}시)")
                
                if execute_trade:
                    try:
                        # 시장 분석
                        analysis_result = self.analyze_market(ticker)
                        
                        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 분석 결과: " + 
                              f"{analysis_result.get('decision')} " + 
                              f"(신뢰도: {analysis_result.get('confidence', 0):.2f})")
                        
                        # 실제 거래 실행
                        if self.enable_trade:
                            trade_result = self.execute_trade(analysis_result, ticker)
                            print(f"거래 결과: {trade_result}")
                    
                    except Exception as e:
                        print(f"트레이딩 루프 오류: {e}")
                
                # 다음 실행 시간까지 대기
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            print("트레이딩 루프 종료 (키보드 인터럽트)")
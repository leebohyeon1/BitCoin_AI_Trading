# -*- coding: utf-8 -*-
import os
import time
import schedule
import pandas as pd
from dotenv import load_dotenv

# 모듈 import
from api import UpbitAPI, ClaudeAPI
from indicators import TechnicalIndicators, MarketIndicators
from strategy import SignalAnalyzer, TradingEngine
from utils import Logger, load_config

def main():
    """
    메인 실행 함수
    """
    # 환경 변수 로드
    load_dotenv()
    
    # 로거 초기화
    logger = Logger()
    logger.log_app("비트코인 자동매매 프로그램 시작")

    try:
        # 설정 로드
        trading_config = load_config("config/trading_config.py")
        app_config = load_config("config/app_config.py")
        
        # API 클라이언트 초기화
        upbit_api = UpbitAPI(
            access_key=os.getenv("UPBIT_ACCESS_KEY"),
            secret_key=os.getenv("UPBIT_SECRET_KEY")
        )
        
        # Claude API 사용 여부 확인
        claude_api = None
        if trading_config.get("CLAUDE_SETTINGS", {}).get("use_claude", False):
            claude_api = ClaudeAPI(api_key=os.getenv("CLAUDE_API_KEY"))
        
        # 기본 티커 설정
        ticker = app_config.get("EXCHANGE_CONFIG", {}).get("default_market", "KRW-BTC")
        
        # OHLCV 데이터 조회
        interval = app_config.get("DATA_CONFIG", {}).get("default_interval", "minute60")
        count = app_config.get("DATA_CONFIG", {}).get("candle_count", 200)
        
        ohlcv = upbit_api.get_ohlcv(ticker, interval=interval, count=count)
        
        # 기술적 지표 계산기 초기화
        technical = TechnicalIndicators(ohlcv)
        
        # 시장 지표 계산기 초기화
        market = MarketIndicators(upbit_api)
        
        # 신호 분석기 초기화
        analyzer = SignalAnalyzer(trading_config, technical, market, claude_api)
        
        # 트레이딩 엔진 초기화
        trading_engine = TradingEngine(trading_config, upbit_api, analyzer)
        
        # 트레이딩 간격 설정
        interval_minutes = trading_config.get("TRADING_SETTINGS", {}).get("trading_interval", 60)
        
        # 스케줄 설정 (매 interval_minutes분마다 실행)
        def trading_job():
            try:
                # OHLCV 데이터 업데이트
                try:
                    ohlcv = upbit_api.get_ohlcv(ticker, interval=interval, count=count)
                    if ohlcv is not None and not ohlcv.empty:
                        technical.set_data(ohlcv)
                    else:
                        logger.log_error("OHLCV 데이터가 비어 있습니다.")
                        return
                except Exception as e:
                    logger.log_error(f"OHLCV 데이터 업데이트 오류: {e}")
                    return
                
                # 시장 분석
                try:
                    analysis_result = trading_engine.analyze_market(ticker)
                except Exception as e:
                    logger.log_error(f"시장 분석 오류: {e}")
                    return
                
                # 거래 실행 (enable_trade가 True일 때만)
                if os.getenv("ENABLE_TRADE", "false").lower() == "true":
                    try:
                        trade_result = trading_engine.execute_trade(analysis_result, ticker)
                        logger.log_trade(f"거래 결과: {trade_result}")
                    except Exception as e:
                        logger.log_error(f"거래 실행 오류: {e}")
                
                # 분석 결과 로깅
                logger.log_app(f"분석 결과: {analysis_result.get('decision', 'unknown')} (신뢰도: {analysis_result.get('confidence', 0):.2f})")
                
                current_price_info = "N/A"
                try:
                    if analysis_result.get('current_price') and analysis_result['current_price'][0]:
                        current_price_info = f"{analysis_result['current_price'][0].get('trade_price', 'N/A'):,}원"
                except:
                    pass
                
                logger.log_app(f"현재가: {current_price_info}")
            except Exception as e:
                logger.log_error(f"트레이딩 작업 오류: {e}")
                
        # 스케줄 등록
         # 스케줄러 대신 무한 루프 사용
        interval_minutes = trading_config.get("TRADING_SETTINGS", {}).get("trading_interval", 60)
        interval_seconds = interval_minutes * 60
        
        # 시작시 한 번 실행
        trading_job()
        
        # 스케줄러 실행
        logger.log_app(f"트레이딩 스케줄러 시작 (간격: {interval_minutes}분)")
        try:
            while True:
                time.sleep(interval_seconds)
                trading_job()
        except KeyboardInterrupt:
            logger.log_app("프로그램 종료 (키보드 인터럽트)")
        
    except Exception as e:
        logger.log_error(f"프로그램 실행 오류: {e}")
        raise

if __name__ == "__main__":
    main()
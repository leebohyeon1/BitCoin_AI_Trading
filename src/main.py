
def calculate_profit_info(upbit_api, ticker="KRW-BTC"):
    """
    현재 수익률 정보 계산
    
    Args:
        upbit_api: UpbitAPI 인스턴스
        ticker: 티커 (예: KRW-BTC)
        
    Returns:
        dict: 수익률 정보
    """
    try:
        if not upbit_api or not upbit_api.access_key or not upbit_api.secret_key:
            return None
            
        # 잔고 조회
        krw_balance = upbit_api.get_balance("KRW") or 0
        btc_balance = upbit_api.get_balance(ticker) or 0
        
        # 현재가 조회
        current_price = upbit_api.get_current_price(ticker) or 0
        
        # 평균 매수가 조회
        avg_buy_price = upbit_api.get_avg_buy_price(ticker) or 0
        
        # 총 투자금 추정 (평균 매수가 * 수량)
        total_investment = avg_buy_price * btc_balance if avg_buy_price > 0 and btc_balance > 0 else 0
        
        # 현재 가치
        current_value = btc_balance * current_price if current_price > 0 and btc_balance > 0 else 0
        
        # 수익금
        profit_amount = current_value - total_investment
        
        # 수익률
        profit_rate = (profit_amount / total_investment) * 100 if total_investment > 0 else 0
        
        return {
            'total_investment': total_investment,
            'current_value': current_value,
            'profit_amount': profit_amount,
            'profit_rate': profit_rate,
            'btc_balance': btc_balance,
            'krw_balance': krw_balance
        }
    except Exception as e:
        print(f"수익률 정보 계산 오류: {e}")
        return None

def generate_korean_reasoning(analysis_result):
    """
    분석 결과를 기반으로 자연스러운 한국어 설명 생성
    
    Args:
        analysis_result: 분석 결과 데이터
        
    Returns:
        str: 한국어 설명
    """
    decision = analysis_result.get('decision', 'hold')
    decision_kr = analysis_result.get('decision_kr', '홀드')
    confidence = analysis_result.get('confidence', 0.5)
    avg_signal_strength = analysis_result.get('avg_signal_strength', 0)
    signals = analysis_result.get('signals', [])
    signal_counts = analysis_result.get('signal_counts', {'buy': 0, 'sell': 0, 'hold': 0})
    current_price = None
    
    # 기본 하드코딩된 값들
    DECISION_THRESHOLDS = {'buy_threshold': 0.1, 'sell_threshold': -0.1}
    
    # 현재가 정보 추출
    try:
        if analysis_result.get('current_price') and len(analysis_result.get('current_price')) > 0:
            current_price = analysis_result.get('current_price')[0].get('trade_price')
    except:
        pass
    
    # 신호 분류
    buy_signals = [s for s in signals if s.get('signal') == 'buy']
    sell_signals = [s for s in signals if s.get('signal') == 'sell']
    hold_signals = [s for s in signals if s.get('signal') == 'hold']
    
    # 가장 강한 신호 추출 (가중치 적용)
    def get_weighted_strength(signal):
        source = signal.get('source', '').split('(')[0].strip()
        # 기본 가중치 설정
        weight = 1.0
        if source in ['RSI', 'MACD', 'FearGreed']:
            weight = 1.2
        elif source in ['Orderbook', 'Trades', 'KIMP']:
            weight = 0.8
        return signal.get('strength', 0) * weight
    
    # 각 신호 유형별 강도 정렬
    buy_signals_sorted = sorted(buy_signals, key=get_weighted_strength, reverse=True)
    sell_signals_sorted = sorted(sell_signals, key=get_weighted_strength, reverse=True)
    all_signals_sorted = sorted(signals, key=get_weighted_strength, reverse=True)
    
    # 상위 신호만 선택
    top_buy_signals = buy_signals_sorted[:2] if len(buy_signals_sorted) > 2 else buy_signals_sorted
    top_sell_signals = sell_signals_sorted[:2] if len(sell_signals_sorted) > 2 else sell_signals_sorted
    top_all_signals = all_signals_sorted[:3] if len(all_signals_sorted) > 3 else all_signals_sorted
    
    # 설명 생성
    explanation = []
    
    # 현재가 정보 추가
    if current_price:
        explanation.append(f"\n현재 비트코인 가격은 {current_price:,.0f}원입니다.")
    
    # 결정 유형에 따른 설명
    if decision == 'buy':
        explanation.append(f"\n현재 시장 상황을 분석한 결과 '매수' 결정을 내렸습니다. (신뢰도: {confidence:.1%})")
        explanation.append(f"\n전체 {len(signals)}개 지표 중 매수 신호가 {signal_counts.get('buy', 0)}개, 매도 신호가 {signal_counts.get('sell', 0)}개, 중립 신호가 {signal_counts.get('hold', 0)}개로 매수 신호가 우세합니다.")
        
        # 최상위 매수 신호 추가
        if top_buy_signals:
            explanation.append("\n특히 다음 지표들이 매수 결정에 큰 영향을 주었습니다:")
            for signal in top_buy_signals:
                explanation.append(f"- {signal.get('source')}: {signal.get('description')}")
    
    elif decision == 'sell':
        explanation.append(f"\n현재 시장 상황을 분석한 결과 '매도' 결정을 내렸습니다. (신뢰도: {confidence:.1%})")
        explanation.append(f"\n전체 {len(signals)}개 지표 중 매도 신호가 {signal_counts.get('sell', 0)}개, 매수 신호가 {signal_counts.get('buy', 0)}개, 중립 신호가 {signal_counts.get('hold', 0)}개로 매도 신호가 우세합니다.")
        
        # 최상위 매도 신호 추가
        if top_sell_signals:
            explanation.append("\n특히 다음 지표들이 매도 결정에 큰 영향을 주었습니다:")
            for signal in top_sell_signals:
                explanation.append(f"- {signal.get('source')}: {signal.get('description')}")
    
    else:  # 홀드
        explanation.append(f"\n현재 시장 상황을 분석한 결과 '{decision_kr}' 결정을 내렸습니다. (신뢰도: {confidence:.1%})")
        
        # 홀드 설명 - 더 자연스럽게
        if signal_counts.get('buy', 0) > signal_counts.get('sell', 0):
            explanation.append(f"\n매수 신호({signal_counts.get('buy', 0)}개)가 매도 신호({signal_counts.get('sell', 0)}개)보다 많지만, 강도가 충분히 높지 않습니다. (신호 강도 평균: {avg_signal_strength:.4f})")
        elif signal_counts.get('sell', 0) > signal_counts.get('buy', 0):
            explanation.append(f"\n매도 신호({signal_counts.get('sell', 0)}개)가 매수 신호({signal_counts.get('buy', 0)}개)보다 많지만, 강도가 충분히 높지 않습니다. (신호 강도 평균: {avg_signal_strength:.4f})")
        else:
            explanation.append(f"\n매수 신호와 매도 신호가 균형을 이루고 있습니다. (매수: {signal_counts.get('buy', 0)}개, 매도: {signal_counts.get('sell', 0)}개, 중립: {signal_counts.get('hold', 0)}개)")

        explanation.append(f"\n매수/매도 결정 임계값 범위({DECISION_THRESHOLDS['sell_threshold']:.1f}~{DECISION_THRESHOLDS['buy_threshold']:.1f}) 내에 신호 강도가 있어 포지션 변화를 제안하지 않습니다.")
        
        # 현재 주요 시장 지표 추가
        explanation.append("\n현재 주요 시장 지표:")
        for signal in top_all_signals:
            signal_type = ""
            if signal.get('signal') == 'buy':
                signal_type = "(매수 신호)"
            elif signal.get('signal') == 'sell':
                signal_type = "(매도 신호)"
            else:
                signal_type = "(중립)"
                
            explanation.append(f"- {signal.get('source')} {signal_type}: {signal.get('description')}")
    
    # 추가 설명 - 이곳에 필요한 경우 추가 설명 추가
    explanation.append("\n이 결정은 자동 분석 시스템에 의한 것으로, 최종 투자 결정은 심도있는 고려가 필요합니다.")
    
    return ''.join(explanation)# -*- coding: utf-8 -*-
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
        try:
            upbit_api = UpbitAPI(
                access_key=os.getenv("UPBIT_ACCESS_KEY"),
                secret_key=os.getenv("UPBIT_SECRET_KEY")
            )
            logger.log_app("UpbitAPI 초기화 성공")
        except Exception as e:
            logger.log_error(f"UpbitAPI 초기화 오류: {e}")
            raise
        
        # Claude API 사용 여부 확인
        claude_api = None
        if trading_config.get("CLAUDE_SETTINGS", {}).get("use_claude", False):
            claude_api = ClaudeAPI(api_key=os.getenv("CLAUDE_API_KEY"))
        
        # 기본 티커 설정
        ticker = app_config.get("EXCHANGE_CONFIG", {}).get("default_market", "KRW-BTC")
        
        # OHLCV 데이터 조회
        interval = app_config.get("DATA_CONFIG", {}).get("default_interval", "minute60")
        count = app_config.get("DATA_CONFIG", {}).get("candle_count", 200)
        
        try:
            ohlcv = upbit_api.get_ohlcv(ticker, interval=interval, count=count)
            if ohlcv is None or ohlcv.empty:
                logger.log_warning("OHLCV 데이터가 비어 있습니다. 더미 데이터를 사용합니다.")
                # 더미 데이터 생성
                import numpy as np
                import pandas as pd
                from datetime import datetime, timedelta
                
                # 샘플 데이터 생성
                dates = [(datetime.now() - timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S") for i in range(count, 0, -1)]
                prices = np.linspace(50000000, 52000000, count)  # 임의의 가격 범위
                
                ohlcv = pd.DataFrame({
                    'open': prices,
                    'high': prices * 1.01,
                    'low': prices * 0.99,
                    'close': prices,
                    'volume': np.random.rand(count) * 10
                }, index=pd.DatetimeIndex(dates))
            else:
                logger.log_app(f"OHLCV 데이터 크기: {len(ohlcv)}")
        except Exception as e:
            logger.log_error(f"OHLCV 데이터 조회 오류: {e}")
            raise
        
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
                    logger.log_app(f"{ticker} {interval} 데이터 조회 시도 중...")
                    ohlcv = upbit_api.get_ohlcv(ticker, interval=interval, count=count)
                    
                    if ohlcv is not None and not ohlcv.empty:
                        technical.set_data(ohlcv)
                        logger.log_app(f"데이터 업데이트 완료 (최신 가격: {ohlcv['close'].iloc[-1]:,.0f}원, 데이터 수: {len(ohlcv)})")
                    else:
                        logger.log_error("OHLCV 데이터를 가져올 수 없습니다. 현재가만 직접 조회합니다.")
                        # 현재가 직접 조회 시도
                        current_price = upbit_api.get_current_price(ticker)
                        logger.log_app(f"현재가 직접 조회 결과: {current_price}")
                        
                        # 기존 데이터가 있으면 그대로 유지하고, 현재가 정보 추가
                        if technical.df is not None and not technical.df.empty:
                            logger.log_app("기존 데이터 사용 + 현재가 정보 추가")
                            # 필요시 여기서 마지막 레코드의 종가 업데이트 가능
                            if current_price is not None:
                                logger.log_app(f"현재가 정보로 기존 데이터 업데이트: {current_price}원")
                        else:
                            if current_price is None:
                                logger.log_error("OHLCV 데이터도 없고 현재가도 가져올 수 없어 작업을 중단합니다.")
                                return
                            else:
                                logger.log_app(f"OHLCV 데이터는 없지만 현재가({current_price}원)는 확인되어 계속 진행합니다.")
                except Exception as e:
                    logger.log_error(f"OHLCV 데이터 업데이트 오류: {e}")
                    # 기존 데이터가 있으면 그대로 유지
                    if technical.df is not None and not technical.df.empty:
                        logger.log_app("오류 발생, 기존 데이터 사용 중...")
                    else:
                        # 현재가만이라도 가져와서 진행 시도
                        try:
                            current_price = upbit_api.get_current_price(ticker)
                            if current_price is not None:
                                logger.log_app(f"오류 발생했으나 현재가는 확인됨: {current_price}원")
                            else:
                                logger.log_error("OHLCV 데이터도 없고 현재가도 가져올 수 없어 작업을 중단합니다.")
                                return
                        except Exception as e2:
                            logger.log_error(f"현재가 조회도 실패: {e2}")
                            return
                
                # 시장 분석
                try:
                    analysis_result = trading_engine.analyze_market(ticker)
                except Exception as e:
                    logger.log_error(f"시장 분석 오류: {e}")
                    return
                
                # 거래 실행 (enable_trade가 True일 때만)
                if os.getenv("ENABLE_TRADE", "").lower() == "true":
                    try:
                        trade_result = trading_engine.execute_trade(analysis_result, ticker)
                        logger.log_trade(f"거래 결과: {trade_result}")
                    except Exception as e:
                        logger.log_error(f"거래 실행 오류: {e}")
                
                # 분석 결과 로깅
                decision = analysis_result.get('decision', 'unknown')
                confidence = analysis_result.get('confidence', 0)
                decision_kr = analysis_result.get('decision_kr', decision)
                
                # 자연스러운 한국어로 결정 이유 생성
                explanation = generate_korean_reasoning(analysis_result)
                
                # 한국어 설명 저장
                analysis_result['korean_reasoning'] = explanation
                
                # 수익률 정보 계산
                profit_info = None
                try:
                    if upbit_api.access_key and upbit_api.secret_key:
                        krw_balance = upbit_api.get_balance("KRW") or 0
                        btc_balance = upbit_api.get_balance(ticker) or 0
                        current_price = upbit_api.get_current_price(ticker) or 0
                        avg_buy_price = upbit_api.get_avg_buy_price(ticker) or 0
                        
                        # 총 투자금 추정 (평균 매수가 * 수량)
                        total_investment = avg_buy_price * btc_balance if avg_buy_price > 0 and btc_balance > 0 else 0
                        
                        # 현재 가치
                        current_value = btc_balance * current_price if current_price > 0 and btc_balance > 0 else 0
                        
                        # 수익금
                        profit_amount = current_value - total_investment
                        
                        # 수익률
                        profit_rate = (profit_amount / total_investment) * 100 if total_investment > 0 else 0
                        
                        profit_info = {
                            'total_investment': total_investment,
                            'current_value': current_value,
                            'profit_amount': profit_amount,
                            'profit_rate': profit_rate,
                            'btc_balance': btc_balance,
                            'krw_balance': krw_balance
                        }
                except Exception as e:
                    logger.log_warning(f"수익률 정보 계산 오류: {e}")
                
                # 새로운 로그 형식으로 출력
                logger.log_trade_analysis(analysis_result, profit_info)

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
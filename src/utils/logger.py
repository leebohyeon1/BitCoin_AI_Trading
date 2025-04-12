import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

class Logger:
    """
    로그 유틸리티 클래스
    application, trade, error 등 다양한 로그를 관리합니다.
    """
    
    def __init__(self, log_dir="logs", log_level=logging.INFO):
        """
        로거 초기화
        
        Args:
            log_dir: 로그 파일 디렉토리
            log_level: 로그 레벨 (logging.DEBUG, logging.INFO 등)
        """
        self.log_dir = log_dir
        self.log_level = log_level
        
        # 로그 디렉토리 생성
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 기본 로거 설정
        self.app_logger = self._setup_logger("app", f"{log_dir}/app.log")
        self.trade_logger = self._setup_logger("trade", f"{log_dir}/trade.log")
        self.error_logger = self._setup_logger("error", f"{log_dir}/error.log")
    
    def _setup_logger(self, name, log_file, level=None):
        """
        로거 설정
        
        Args:
            name: 로거 이름
            log_file: 로그 파일 경로
            level: 로그 레벨 (None이면 기본값 사용)
            
        Returns:
            logging.Logger: 설정된 로거
        """
        if level is None:
            level = self.log_level
        
        # 로거 생성
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 파일 핸들러 설정 (10MB 크기, 최대 5개 로그 유지)
        handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
        )
        
        # 포맷터 설정
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        
        # 핸들러 추가
        logger.addHandler(handler)
        
        # 콘솔 출력 핸들러 추가
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_app(self, message, level="info"):
        """
        애플리케이션 로그 출력
        
        Args:
            message: 로그 메시지
            level: 로그 레벨 (debug, info, warning, error, critical)
        """
        self._log(self.app_logger, message, level)
    
    def log_trade(self, message, level="info"):
        """
        트레이딩 로그 출력
        
        Args:
            message: 로그 메시지
            level: 로그 레벨 (debug, info, warning, error, critical)
        """
        self._log(self.trade_logger, message, level)
    
    def log_error(self, message, level="error"):
        """
        에러 로그 출력
        
        Args:
            message: 로그 메시지
            level: 로그 레벨 (debug, info, warning, error, critical)
        """
        self._log(self.error_logger, message, level)
        
    def log_warning(self, message):
        """
        경고 로그 출력 (에러 로그와 앱 로그 모두에 기록)
        
        Args:
            message: 로그 메시지
        """
        self._log(self.app_logger, message, "warning")
        self._log(self.error_logger, message, "warning")
    
    def _log(self, logger, message, level):
        """
        로그 출력 내부 메소드
        
        Args:
            logger: 로거 인스턴스
            message: 로그 메시지
            level: 로그 레벨
        """
        if level == "debug":
            logger.debug(message)
        elif level == "info":
            logger.info(message)
        elif level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)
        elif level == "critical":
            logger.critical(message)
        else:
            logger.info(message)
            
    def log_trade_analysis(self, analysis_result, profit_info=None):
        """
        트레이딩 분석 결과 로깅
        
        Args:
            analysis_result: 분석 결과 데이터
            profit_info: 현재 수익률 정보 (선택적)
        """
        if not analysis_result or not isinstance(analysis_result, dict):
            self.log_error("유효하지 않은 분석 결과 데이터")
            return
        
        # 기본 정보 추출
        decision = analysis_result.get('decision', 'unknown')
        decision_kr = analysis_result.get('decision_kr', decision)
        confidence = analysis_result.get('confidence', 0)
        reasoning = analysis_result.get('reasoning', '')
        signals = analysis_result.get('signals', [])
        current_price_data = analysis_result.get('current_price', [{}])
        current_price = current_price_data[0].get('trade_price', 'N/A') if current_price_data else 'N/A'
        price_change = analysis_result.get('price_change_24h', 'N/A')
        
        # 분석 데이터 요약
        signal_counts = analysis_result.get('signal_counts', {})
        buy_count = signal_counts.get('buy', 0)
        sell_count = signal_counts.get('sell', 0)
        hold_count = signal_counts.get('hold', 0)
        
        # 로그 메시지 구성
        log_lines = [
            "===== 비트코인 트레이딩 분석 결과 =====",
            f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "[분석 데이터]",
            f"현재가: {current_price:,}원" if isinstance(current_price, (int, float)) else f"현재가: {current_price}",
            f"가격변화(24h): {price_change}",
            f"신호 분포: 매수({buy_count}), 매도({sell_count}), 홀드({hold_count})",
            "",
            "[주요 지표]"
        ]
        
        # 주요 지표 추가 (상위 5개)
        sorted_signals = sorted(signals, key=lambda x: x.get('strength', 0), reverse=True)
        for i, signal in enumerate(sorted_signals[:5]):
            source = signal.get('source', '')
            signal_type = signal.get('signal', '')
            description = signal.get('description', '')
            strength = signal.get('strength', 0)
            log_lines.append(f"{i+1}. {source} - {signal_type.upper()} ({strength:.2f}): {description}")
        
        log_lines.extend([
            "",
            "[결정]",
            f"{decision_kr.upper()} (신뢰도: {confidence:.2%})",
            "",
            "[결정 이유]",
            reasoning,
            ""
        ])
        
        # 수익률 정보 추가 (있는 경우)
        if profit_info and isinstance(profit_info, dict):
            log_lines.extend([
                "[현재 수익률]",
                f"총 투자금: {profit_info.get('total_investment', 0):,}원",
                f"현재 가치: {profit_info.get('current_value', 0):,}원",
                f"수익금: {profit_info.get('profit_amount', 0):,}원",
                f"수익률: {profit_info.get('profit_rate', 0):.2f}%",
                f"보유 BTC: {profit_info.get('btc_balance', 0):.8f}"
            ])
        
        log_lines.append("========================================")
        
        # 로그 출력
        self.log_app("\n".join(log_lines))
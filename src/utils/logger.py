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
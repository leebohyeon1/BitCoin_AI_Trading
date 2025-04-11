import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

class Logger:
    """
    �α� ��ƿ��Ƽ Ŭ����
    application, trade, error �� �پ��� �α׸� �����մϴ�.
    """
    
    def __init__(self, log_dir="logs", log_level=logging.INFO):
        """
        �ΰ� �ʱ�ȭ
        
        Args:
            log_dir: �α� ���� ���丮
            log_level: �α� ���� (logging.DEBUG, logging.INFO ��)
        """
        self.log_dir = log_dir
        self.log_level = log_level
        
        # �α� ���丮 ����
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # �⺻ �ΰ� ����
        self.app_logger = self._setup_logger("app", f"{log_dir}/app.log")
        self.trade_logger = self._setup_logger("trade", f"{log_dir}/trade.log")
        self.error_logger = self._setup_logger("error", f"{log_dir}/error.log")
    
    def _setup_logger(self, name, log_file, level=None):
        """
        �ΰ� ����
        
        Args:
            name: �ΰ� �̸�
            log_file: �α� ���� ���
            level: �α� ���� (None�̸� �⺻�� ���)
            
        Returns:
            logging.Logger: ������ �ΰ�
        """
        if level is None:
            level = self.log_level
        
        # �ΰ� ����
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # ���� �ڵ鷯 ���� (10MB ũ��, �ִ� 5�� ��� ����)
        handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
        )
        
        # ������ ����
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        
        # �ڵ鷯 �߰�
        logger.addHandler(handler)
        
        # �ܼ� ��� �ڵ鷯 �߰�
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_app(self, message, level="info"):
        """
        ���ø����̼� �α� ���
        
        Args:
            message: �α� �޽���
            level: �α� ���� (debug, info, warning, error, critical)
        """
        self._log(self.app_logger, message, level)
    
    def log_trade(self, message, level="info"):
        """
        Ʈ���̵� �α� ���
        
        Args:
            message: �α� �޽���
            level: �α� ���� (debug, info, warning, error, critical)
        """
        self._log(self.trade_logger, message, level)
    
    def log_error(self, message, level="error"):
        """
        ���� �α� ���
        
        Args:
            message: �α� �޽���
            level: �α� ���� (debug, info, warning, error, critical)
        """
        self._log(self.error_logger, message, level)
    
    def _log(self, logger, message, level):
        """
        �α� ��� ���� �޼���
        
        Args:
            logger: �ΰ� �ν��Ͻ�
            message: �α� �޽���
            level: �α� ����
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
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from .market_analyzer import MarketAnalyzer
from .signal_analyzer_ai import SignalAnalyzer

# 로깅 설정
logger = logging.getLogger('analyzer')

def create_analyzer(config, technical_indicators=None, market_indicators=None, claude_api=None, use_ai=True):
    """분석기 생성 함수
    
    설정에 따라 적절한 분석기를 생성하고 반환합니다.
    
    Args:
        config: 설정 정보를 담은 딕셔너리
        technical_indicators: 기술적 지표 계산을 위한 객체
        market_indicators: 시장 지표 계산을 위한 객체
        claude_api: Claude API 객체 (AI 분석에 사용)
        use_ai: AI 분석기 사용 여부
        
    Returns:
        MarketAnalyzer 또는 SignalAnalyzer 객체
    """
    try:
        if use_ai and claude_api is not None:
            logger.info("AI 분석기 생성")
            return SignalAnalyzer(config, technical_indicators, market_indicators, claude_api)
        else:
            logger.info("기본 분석기 생성")
            return MarketAnalyzer()
    except Exception as e:
        logger.error(f"분석기 생성 오류: {e}")
        # 오류 발생 시 기본 분석기 반환
        return MarketAnalyzer()

class AnalysisResult:
    """분석 결과 클래스
    
    여러 분석 결과를 저장하고 집계하는 클래스입니다.
    """
    
    def __init__(self, timestamp=None):
        """초기화
        
        Args:
            timestamp: 분석 시간 (기본값: 현재 시간)
        """
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.decision = "hold"
        self.decision_kr = "홀드"
        self.confidence = 0.5
        self.reasoning = ""
        self.signals = []
        self.signal_counts = {"buy": 0, "sell": 0, "hold": 0}
        self.current_price = None
        self.price_change_24h = "N/A"
        self.avg_signal_strength = 0.0
        
        # AI 분석 결과 (있는 경우)
        self.claude_analysis = None
        self.claude_agrees = None
        self.claude_error = None
        
    def update_from_dict(self, result_dict):
        """분석 결과 딕셔너리로부터 업데이트
        
        Args:
            result_dict: 분석 결과를 담은 딕셔너리
            
        Returns:
            self: 업데이트된 자기 자신
        """
        if not result_dict:
            return self
            
        self.decision = result_dict.get("decision", self.decision)
        self.decision_kr = result_dict.get("decision_kr", self.decision_kr)
        self.confidence = result_dict.get("confidence", self.confidence)
        self.reasoning = result_dict.get("reasoning", self.reasoning)
        self.signals = result_dict.get("signals", self.signals)
        self.signal_counts = result_dict.get("signal_counts", self.signal_counts)
        self.current_price = result_dict.get("current_price", self.current_price)
        self.price_change_24h = result_dict.get("price_change_24h", self.price_change_24h)
        self.avg_signal_strength = result_dict.get("avg_signal_strength", self.avg_signal_strength)
        
        # AI 분석 관련 필드
        if "claude_analysis" in result_dict:
            self.claude_analysis = result_dict.get("claude_analysis")
        if "claude_agrees" in result_dict:
            self.claude_agrees = result_dict.get("claude_agrees")
        if "claude_error" in result_dict:
            self.claude_error = result_dict.get("claude_error")
            
        return self
        
    def to_dict(self):
        """딕셔너리로 변환
        
        Returns:
            dict: 분석 결과를 담은 딕셔너리
        """
        result = {
            "timestamp": self.timestamp,
            "decision": self.decision,
            "decision_kr": self.decision_kr,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "signals": self.signals,
            "signal_counts": self.signal_counts,
            "current_price": self.current_price,
            "price_change_24h": self.price_change_24h,
            "avg_signal_strength": self.avg_signal_strength
        }
        
        # AI 분석 결과가 있는 경우 추가
        if self.claude_analysis:
            result["claude_analysis"] = self.claude_analysis
        if self.claude_agrees is not None:
            result["claude_agrees"] = self.claude_agrees
        if self.claude_error:
            result["claude_error"] = self.claude_error
            
        return result
        
    def get_summary(self):
        """분석 결과 요약
        
        Returns:
            str: 분석 결과 요약 문자열
        """
        summary = []
        summary.append(f"[{self.timestamp}] 결정: {self.decision_kr} (신뢰도: {self.confidence:.2f})")
        summary.append(f"평균 신호 강도: {self.avg_signal_strength:.4f}")
        
        if self.current_price and isinstance(self.current_price, list) and len(self.current_price) > 0:
            price = self.current_price[0].get('trade_price', '알 수 없음')
            summary.append(f"현재가: {price:,}원 (24시간 변동: {self.price_change_24h})")
        
        signal_counts = f"매수 신호: {self.signal_counts.get('buy', 0)}개, " \
                       f"매도 신호: {self.signal_counts.get('sell', 0)}개, " \
                       f"홀드 신호: {self.signal_counts.get('hold', 0)}개"
        summary.append(signal_counts)
        
        if self.claude_analysis:
            ai_signal = self.claude_analysis.get('signal', '알 수 없음')
            ai_confidence = self.claude_analysis.get('confidence', 0)
            summary.append(f"AI 분석: {ai_signal} (신뢰도: {ai_confidence:.2f})")
            
            if self.claude_agrees is not None:
                agree_status = "일치" if self.claude_agrees else "불일치"
                summary.append(f"AI와 기술적 분석 결과: {agree_status}")
        
        if self.claude_error:
            summary.append(f"AI 분석 오류: {self.claude_error}")
            
        summary.append("\n결정 이유:")
        summary.append(self.reasoning)
        
        return "\n".join(summary)

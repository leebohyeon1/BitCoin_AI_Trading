#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from datetime import datetime

# 로깅 설정
logger = logging.getLogger('signal_generator')

class SignalGenerator:
    """신호 생성 및 분석 클래스"""
    
    def __init__(self, signal_strengths, indicator_weights, decision_thresholds):
        """초기화"""
        self.signal_strengths = signal_strengths
        self.indicator_weights = indicator_weights
        self.decision_thresholds = decision_thresholds
    
    def generate_final_decision(self, signals):
        """최종 매매 신호 결정"""
        # 신호 분류
        buy_signals = []
        sell_signals = []
        hold_signals = []
        
        # 신호 분류 및 가중치 적용
        total_weight = 0
        weighted_signal_sum = 0
        
        for signal in signals:
            source = signal["source"].split("(")[0].strip()
            weight = self.indicator_weights.get(source, 1.0)
            total_weight += weight
            
            if signal["signal"] == "buy":
                buy_signals.append(signal)
                weighted_signal_sum += signal["strength"] * weight
            elif signal["signal"] == "sell":
                sell_signals.append(signal)
                weighted_signal_sum -= signal["strength"] * weight
            else:  # hold
                hold_signals.append(signal)
        
        # 평균 신호 강도 계산 (-1 ~ 1 범위)
        avg_signal_strength = weighted_signal_sum / total_weight if total_weight > 0 else 0
        
        # 신호 카운트
        signal_counts = {
            "buy": len(buy_signals),
            "sell": len(sell_signals),
            "hold": len(hold_signals)
        }
        
        # 신뢰도 계산 (0.5 ~ 1.0 범위)
        confidence = 0.5 + abs(avg_signal_strength) / 2
        
        # 최종 결정 및 결정 이유
        reasoning = []
        if avg_signal_strength >= self.decision_thresholds["buy_threshold"]:
            decision = "buy"
            decision_kr = "매수" if avg_signal_strength >= 0.4 else "약한 매수"
            
            # 매수 결정 이유 추가
            buy_signals_list = [s for s in signals if s["signal"] == "buy"]
            # 가장 강한 매수 신호 최대 3개 추출
            top_buy_signals = sorted(buy_signals_list, key=lambda x: x["strength"] * self.indicator_weights.get(x["source"].split("(")[0].strip(), 1.0), reverse=True)
            top_buy_signals = top_buy_signals[:3] if len(top_buy_signals) > 3 else top_buy_signals
            
            reasoning.append(f"매수 신호 {len(buy_signals_list)}개, 매도 신호 {len(signals) - len(buy_signals_list) - len([s for s in signals if s['signal'] == 'hold'])}개")
            for signal in top_buy_signals:
                reasoning.append(f"{signal['source']}: {signal['description']}")
                
        elif avg_signal_strength <= self.decision_thresholds["sell_threshold"]:
            decision = "sell"
            decision_kr = "매도" if avg_signal_strength <= -0.4 else "약한 매도"
            
            # 매도 결정 이유 추가
            sell_signals_list = [s for s in signals if s["signal"] == "sell"]
            # 가장 강한 매도 신호 최대 3개 추출
            top_sell_signals = sorted(sell_signals_list, key=lambda x: x["strength"] * self.indicator_weights.get(x["source"].split("(")[0].strip(), 1.0), reverse=True)
            top_sell_signals = top_sell_signals[:3] if len(top_sell_signals) > 3 else top_sell_signals
            
            reasoning.append(f"매도 신호 {len(sell_signals_list)}개, 매수 신호 {len(signals) - len(sell_signals_list) - len([s for s in signals if s['signal'] == 'hold'])}개")
            for signal in top_sell_signals:
                reasoning.append(f"{signal['source']}: {signal['description']}")
                
        else:
            decision = "hold"
            decision_kr = "홀드" if abs(avg_signal_strength) < 0.05 else "약한 홀드"
            
            # 홀드 결정 이유 추가
            buy_count = len([s for s in signals if s["signal"] == "buy"])
            sell_count = len([s for s in signals if s["signal"] == "sell"])
            hold_count = len([s for s in signals if s["signal"] == "hold"])
            
            reasoning.append(f"매수 신호 {buy_count}개, 매도 신호 {sell_count}개, 홀드 신호 {hold_count}개")
            reasoning.append(f"평균 신호 강도: {avg_signal_strength:.4f} (결정 임계값: {self.decision_thresholds['buy_threshold']}/{self.decision_thresholds['sell_threshold']})")
            
            # 가장 강한 신호 몇 개 표시
            # 가장 강한 신호 최대 3개 추출
            top_signals = sorted(signals, key=lambda x: x["strength"] * self.indicator_weights.get(x["source"].split("(")[0].strip(), 1.0), reverse=True)
            top_signals = top_signals[:3] if len(top_signals) > 3 else top_signals
            for signal in top_signals:
                reasoning.append(f"{signal['source']} ({signal['signal']}): {signal['description']}")
        
        # 결정 이유를 문자열로 합치기
        reasoning_text = "\n".join(reasoning)
        
        # 결과 반환
        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "decision": decision,
            "decision_kr": decision_kr,
            "reasoning": reasoning_text,  # 결정 이유
            "confidence": confidence,
            "avg_signal_strength": avg_signal_strength,
            "signals": signals,
            "signal_counts": signal_counts
        }
        
        return result

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from .market_analyzer import MarketAnalyzer

# 로깅 설정
logger = logging.getLogger('signal_analyzer')

class SignalAnalyzer(MarketAnalyzer):
    """신호 분석 클래스 (MarketAnalyzer 상속)"""
    
    def __init__(self, config, technical_indicators=None, market_indicators=None, claude_api=None):
        """초기화"""
        super().__init__()
        self.config = config
        self.technical_indicators = technical_indicators
        self.market_indicators = market_indicators
        self.claude_api = claude_api
        
    def analyze(self, market_data, ticker="KRW-BTC"):
        """시장 분석 및 매매 신호 생성"""
        try:
            # 기존 MarketAnalyzer의 analyze 메서드 사용
            market_analysis = super().analyze(ticker)
            
            # market_analysis가 None이거나 비어있는 경우 기본값 설정
            if market_analysis is None or not isinstance(market_analysis, dict):
                logger.error("기본 분석 결과가 유효하지 않습니다. 기본값 사용")
                market_analysis = {
                    "decision": "hold",
                    "decision_kr": "홀드",
                    "confidence": 0.5,
                    "reasoning": "분석 오류로 인한 기본 홀드 상태",
                    "signals": [],
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "signal_counts": {"buy": 0, "sell": 0, "hold": 0},
                    "current_price": market_data.get("current_price"),
                    "price_change_24h": market_data.get("price_change_24h", "N/A")
                }
        
            # Claude AI 분석 통합 (설정된 경우)
            claude_settings = self.config.get("CLAUDE_SETTINGS", {})
            if claude_settings.get("use_claude", False) and self.claude_api is not None:
                try:
                    # 기술적 지표 데이터 준비
                    technical_data = {}
                    if self.technical_indicators is not None:
                        # 기술적 지표 데이터 구조화
                        try:
                            df = self.technical_indicators.df
                            if df is not None and len(df) > 0:
                                last_row = df.iloc[-1]
                                
                                technical_data = {
                                    "ma": {
                                        "ma5": float(self.technical_indicators.get_ma(period=5).iloc[-1]),
                                        "ma20": float(self.technical_indicators.get_ma(period=20).iloc[-1]),
                                        "ma60": float(self.technical_indicators.get_ma(period=60).iloc[-1]) if len(df) >= 60 else None
                                    },
                                    "rsi": float(self.technical_indicators.get_rsi().iloc[-1]),
                                    "macd": {
                                        "value": float(self.technical_indicators.get_macd()[0].iloc[-1]),
                                        "signal": float(self.technical_indicators.get_macd()[1].iloc[-1]),
                                        "histogram": float(self.technical_indicators.get_macd()[2].iloc[-1])
                                    },
                                    "bollingerBands": {
                                        "upper": float(self.technical_indicators.get_bollinger_bands()[0].iloc[-1]),
                                        "middle": float(self.technical_indicators.get_bollinger_bands()[1].iloc[-1]),
                                        "lower": float(self.technical_indicators.get_bollinger_bands()[2].iloc[-1])
                                    }
                                }
                        except Exception as e:
                            logger.warning(f"기술적 지표 데이터 구성 오류: {e}")
                    
                    # 시장 지표 데이터 준비
                    market_indicator_data = {}
                    if self.market_indicators is not None:
                        try:
                            market_signals = market_analysis.get("signals", [])
                            # 시장 신호 분류
                            orderbook_signals = [s for s in market_signals if '호가창' in s.get('source', '')]
                            trade_signals = [s for s in market_signals if '체결' in s.get('source', '')]
                            kimp_signals = [s for s in market_signals if '김프' in s.get('source', '')]
                            fear_greed_signals = [s for s in market_signals if '공포' in s.get('source', '') or '탐욕' in s.get('source', '')]
                            
                            market_indicator_data = {
                                "orderbook": orderbook_signals[0] if orderbook_signals else {},
                                "trades": trade_signals[0] if trade_signals else {},
                                "kimchiPremium": kimp_signals[0] if kimp_signals else {},
                                "fearGreedIndex": fear_greed_signals[0] if fear_greed_signals else {}
                            }
                        except Exception as e:
                            logger.warning(f"시장 지표 데이터 구성 오류: {e}")
                    
                    # 현재 시장 데이터
                    current_market_data = {
                        "currentPrice": market_analysis.get("current_price", [{}])[0].get("trade_price", 0),
                        "priceChange24h": market_analysis.get("price_change_24h", "0%"),
                        "timestamp": market_analysis.get("timestamp", "")
                    }
                    
                    # Claude API 호출
                    claude_analysis = self.claude_api.analyze_market(current_market_data, {
                        "technical": technical_data,
                        "market": market_indicator_data,
                        "signals": market_analysis.get("signals", [])
                    })
                    
                    # AI 우선 결정 여부 확인
                    ai_primary_decision = claude_settings.get("ai_primary_decision", False)
                    
                    if claude_analysis and "signal" in claude_analysis:
                        # AI 분석 결과 저장
                        market_analysis["claude_analysis"] = claude_analysis
                        
                        # AI 우선 결정 모드인 경우 Claude의 결정을 최종 결정으로 사용
                        if ai_primary_decision:
                            # 기존 결정 저장
                            market_analysis["original_decision"] = market_analysis["decision"]
                            market_analysis["original_confidence"] = market_analysis.get("confidence", 0.5)
                            
                            # Claude의 결정으로 대체
                            market_analysis["decision"] = claude_analysis["signal"]
                            
                            # 한국어 결정명 업데이트
                            decision_kr_map = {"buy": "매수", "sell": "매도", "hold": "홀드"}
                            market_analysis["decision_kr"] = decision_kr_map.get(claude_analysis["signal"], "홀드")
                            
                            # 신뢰도 업데이트 (Claude의 신뢰도 사용)
                            market_analysis["confidence"] = claude_analysis.get("confidence", 0.5)
                            
                            # 두 분석이 일치하면 신뢰도 강화
                            if claude_analysis["signal"] == market_analysis.get("original_decision"):
                                market_analysis["confidence"] = min(
                                    1.0,
                                    market_analysis["confidence"] + claude_settings.get("confidence_boost", 0.2)
                                )
                                market_analysis["claude_agrees"] = True
                            else:
                                market_analysis["claude_agrees"] = False
                                
                            # 로깅
                            logger.info(f"AI 우선 결정: {market_analysis['decision']} (원래 결정: {market_analysis.get('original_decision', '없음')})")
                        else:
                            # 기존 방식 유지 (Claude는 보조 역할)
                            if claude_analysis["signal"] == market_analysis["decision"]:
                                market_analysis["confidence"] = min(
                                    1.0, 
                                    market_analysis["confidence"] + claude_settings.get("confidence_boost", 0.1)
                                )
                                market_analysis["claude_agrees"] = True
                            else:
                                market_analysis["claude_agrees"] = False
                        
                        # Claude의 자연어 분석 이유를 기존 reasoning에 추가 혹은 대체
                        if "korean_analysis" in claude_analysis and claude_settings.get("override_reasoning", False):
                            # 기존 reasoning 저장
                            market_analysis["original_reasoning"] = market_analysis.get("reasoning", "")
                            
                            # 신뢰도와 신호 정보는 유지하면서 Claude의 분석을 사용
                            decision_summary = f"\n[AI 분석 결과] {market_analysis.get('decision_kr', '홀드')} (신뢰도: {market_analysis.get('confidence', 0.5):.1%})"
                            
                            # 신호 카운트
                            signal_counts = market_analysis.get('signal_counts', {})
                            counts_summary = f"\n전체 지표: 매수({signal_counts.get('buy', 0)}개), 매도({signal_counts.get('sell', 0)}개), 홀드({signal_counts.get('hold', 0)}개)"
                            
                            # AI 결정 모드인 경우 reasoning 강화
                            if ai_primary_decision:
                                # 원래 기술적 분석과 AI 분석의 차이점 설명
                                if market_analysis.get("original_decision") != market_analysis["decision"]:
                                    tech_vs_ai = f"\n\n※ AI 분석({market_analysis['decision_kr']})이 기술적 분석({decision_kr_map.get(market_analysis.get('original_decision'), '홀드')})과 다릅니다."
                                    tech_vs_ai += f" AI 분석 결과를 우선 적용합니다."
                                else:
                                    tech_vs_ai = f"\n\n※ AI 분석과 기술적 분석이 모두 '{market_analysis['decision_kr']}' 신호로 일치합니다."
                                
                                # Claude의 분석을 기본 reasoning으로 사용하고 비교 정보 추가
                                market_analysis["reasoning"] = decision_summary + counts_summary + tech_vs_ai + "\n\n" + claude_analysis["korean_analysis"]
                            else:
                                # 기존 방식 유지
                                market_analysis["reasoning"] = decision_summary + counts_summary + "\n\n" + claude_analysis["korean_analysis"]
                    else:
                        market_analysis["claude_error"] = "Claude 응답이 유효하지 않습니다."
                
                except Exception as e:
                    logger.error(f"Claude 분석 오류: {e}")
                    market_analysis["claude_error"] = str(e)
            
            return market_analysis
        
        except Exception as e:
            logger.error(f"시장 분석 오류: {e}")
            # 오류 발생 시 기본값 반환
            return {
                "decision": "hold",
                "decision_kr": "홀드",
                "confidence": 0.5,
                "reasoning": f"분석 오류: {str(e)}",
                "signals": [],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "signal_counts": {"buy": 0, "sell": 0, "hold": 0},
                "current_price": market_data.get("current_price") if market_data else None,
                "price_change_24h": market_data.get("price_change_24h", "N/A") if market_data else "N/A"
            }

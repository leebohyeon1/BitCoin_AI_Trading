#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import numpy as np
import pandas as pd
from datetime import datetime

# 로깅 설정
logger = logging.getLogger('technical_signals')

def analyze_moving_averages(df, signal_strengths):
    """이동평균선(MA) 분석"""
    signals = []
    last_row = df.iloc[-1]
    
    # 골든크로스/데드크로스 확인
    if last_row['MA5'] > last_row['MA20']:
        signals.append({
            "source": "이동평균선(MA)",
            "signal": "buy",
            "strength": signal_strengths.get("ma_crossover", 0.6),
            "description": "골든크로스 상태 (5일 이동평균선이 20일 이동평균선 위에 위치)"
        })
    else:
        signals.append({
            "source": "이동평균선(MA)",
            "signal": "sell",
            "strength": signal_strengths.get("ma_crossover", 0.6),
            "description": "데드크로스 상태 (5일 이동평균선이 20일 이동평균선 아래에 위치)"
        })
    
    # 장기 이동평균선(MA60) 분석
    if last_row['close'] > last_row['MA60']:
        signals.append({
            "source": "장기추세(MA60)",
            "signal": "buy",
            "strength": signal_strengths.get("ma_long_trend", 0.4),
            "description": "장기 상승 추세 (현재가가 60일 이동평균선 위에 위치)"
        })
    else:
        signals.append({
            "source": "장기추세(MA60)",
            "signal": "sell",
            "strength": signal_strengths.get("ma_long_trend", 0.4),
            "description": "장기 하락 추세 (현재가가 60일 이동평균선 아래에 위치)"
        })
    
    return signals

def analyze_bollinger_bands(df, signal_strengths):
    """볼린저 밴드(BB) 분석"""
    signals = []
    last_row = df.iloc[-1]
    
    # 밴드 내 위치 계산 (0~100%)
    band_width = last_row['BB_upper'] - last_row['BB_lower']
    if band_width > 0:
        position_pct = ((last_row['close'] - last_row['BB_lower']) / band_width) * 100
        
        if position_pct < 20:  # 하단 20% 이내
            signals.append({
                "source": "볼린저밴드(BB)",
                "signal": "buy",
                "strength": signal_strengths.get("bb_extreme", 0.7),
                "description": f"하단 돌파/접근 (밴드 내 위치: 하위 {position_pct:.0f}%)"
            })
        elif position_pct > 80:  # 상단 20% 이내
            signals.append({
                "source": "볼린저밴드(BB)",
                "signal": "sell",
                "strength": signal_strengths.get("bb_extreme", 0.7),
                "description": f"상단 돌파/접근 (밴드 내 위치: 상위 {position_pct:.0f}%)"
            })
        elif 20 <= position_pct < 40:  # 하단 20~40%
            signals.append({
                "source": "볼린저밴드(BB)",
                "signal": "buy",
                "strength": signal_strengths.get("bb_middle", 0.3),
                "description": f"하단 접근중 (밴드 내 위치: 하위 {position_pct:.0f}%)"
            })
        elif 60 < position_pct <= 80:  # 상단 60~80%
            signals.append({
                "source": "볼린저밴드(BB)",
                "signal": "sell",
                "strength": signal_strengths.get("bb_middle", 0.3),
                "description": f"상단 접근중 (밴드 내 위치: 상위 {position_pct:.0f}%)"
            })
        else:  # 중앙 40~60%
            signals.append({
                "source": "볼린저밴드(BB)",
                "signal": "hold",
                "strength": 0,
                "description": "밴드 중앙 부근 (중립적 위치)"
            })
    else:
        signals.append({
            "source": "볼린저밴드(BB)",
            "signal": "hold",
            "strength": 0,
            "description": "밴드 계산 오류 (중립적 위치)"
        })
    
    return signals

def analyze_rsi(df, signal_strengths):
    """RSI 분석"""
    signals = []
    last_row = df.iloc[-1]
    rsi = last_row['RSI']
    
    if rsi <= 30:  # 과매도 상태
        signals.append({
            "source": "RSI(상대강도지수)",
            "signal": "buy",
            "strength": signal_strengths.get("rsi_extreme", 0.8),
            "description": f"과매도 상태 (RSI: {rsi:.1f} < 30)"
        })
    elif rsi >= 70:  # 과매수 상태
        signals.append({
            "source": "RSI(상대강도지수)",
            "signal": "sell",
            "strength": signal_strengths.get("rsi_extreme", 0.8),
            "description": f"과매수 상태 (RSI: {rsi:.1f} > 70)"
        })
    elif 30 < rsi < 45:  # 매도세 우세
        signals.append({
            "source": "RSI(상대강도지수)",
            "signal": "buy",
            "strength": signal_strengths.get("rsi_middle", 0.2),
            "description": f"매도세 우세 (RSI: {rsi:.1f})"
        })
    elif 55 < rsi < 70:  # 매수세 우세
        signals.append({
            "source": "RSI(상대강도지수)",
            "signal": "sell",
            "strength": signal_strengths.get("rsi_middle", 0.2),
            "description": f"매수세 우세 (RSI: {rsi:.1f})"
        })
    else:  # 중립
        signals.append({
            "source": "RSI(상대강도지수)",
            "signal": "hold",
            "strength": 0,
            "description": f"중립적 (RSI: {rsi:.1f})"
        })
    
    return signals

def analyze_macd(df, signal_strengths):
    """MACD 분석"""
    signals = []
    last_row = df.iloc[-1]
    
    # MACD 골든크로스/데드크로스
    if last_row['MACD'] > last_row['MACD_signal']:
        if df['MACD'].iloc[-2] <= df['MACD_signal'].iloc[-2]:  # 교차 발생
            signals.append({
                "source": "MACD",
                "signal": "buy",
                "strength": signal_strengths.get("macd_crossover", 0.7),
                "description": "MACD 골든크로스 발생"
            })
        else:  # 유지
            signals.append({
                "source": "MACD",
                "signal": "buy",
                "strength": signal_strengths.get("macd_trend", 0.3),
                "description": "MACD 상승 추세 유지중"
            })
    elif last_row['MACD'] < last_row['MACD_signal']:
        if df['MACD'].iloc[-2] >= df['MACD_signal'].iloc[-2]:  # 교차 발생
            signals.append({
                "source": "MACD",
                "signal": "sell",
                "strength": signal_strengths.get("macd_crossover", 0.7),
                "description": "MACD 데드크로스 발생"
            })
        else:  # 유지
            signals.append({
                "source": "MACD",
                "signal": "sell",
                "strength": signal_strengths.get("macd_trend", 0.3),
                "description": "MACD 하락 추세 유지중"
            })
    else:  # MACD와 시그널 라인이 같은 경우 (드물지만)
        signals.append({
            "source": "MACD",
            "signal": "hold",
            "strength": 0,
            "description": "MACD 중립적 상태"
        })
    
    return signals

def analyze_stochastic(df, signal_strengths):
    """스토캐스틱 분석"""
    signals = []
    last_row = df.iloc[-1]
    k = last_row['STOCH_K']
    d = last_row['STOCH_D']
    
    # 과매수/과매도 영역 확인
    if k <= 20 and d <= 20:  # 과매도 영역
        if k > d:  # K가 D를 상향돌파 (반등 신호)
            signals.append({
                "source": "스토캐스틱",
                "signal": "buy",
                "strength": signal_strengths.get("stoch_extreme", 0.6),
                "description": f"과매도 반등 신호 (K: {k:.1f}, D: {d:.1f})"
            })
        else:
            signals.append({
                "source": "스토캐스틱",
                "signal": "buy",
                "strength": signal_strengths.get("stoch_middle", 0.3),
                "description": f"과매도 영역 (K: {k:.1f}, D: {d:.1f})"
            })
    elif k >= 80 and d >= 80:  # 과매수 영역
        if k < d:  # K가 D를 하향돌파 (하락 반전 신호)
            signals.append({
                "source": "스토캐스틱",
                "signal": "sell",
                "strength": signal_strengths.get("stoch_extreme", 0.6),
                "description": f"과매수 반전 신호 (K: {k:.1f}, D: {d:.1f})"
            })
        else:
            signals.append({
                "source": "스토캐스틱",
                "signal": "sell",
                "strength": signal_strengths.get("stoch_middle", 0.3),
                "description": f"과매수 영역 (K: {k:.1f}, D: {d:.1f})"
            })
    elif k > d:  # K가 D보다 위 (상승 모멘텀)
        signals.append({
            "source": "스토캐스틱",
            "signal": "buy",
            "strength": signal_strengths.get("stoch_middle", 0.3),
            "description": f"상승 모멘텀 (K: {k:.1f} > D: {d:.1f})"
        })
    elif k < d:  # K가 D보다 아래 (하락 모멘텀)
        signals.append({
            "source": "스토캐스틱",
            "signal": "sell",
            "strength": signal_strengths.get("stoch_middle", 0.3),
            "description": f"하락 모멘텀 (K: {k:.1f} < D: {d:.1f})"
        })
    else:  # K와 D가 같은 경우
        signals.append({
            "source": "스토캐스틱",
            "signal": "hold",
            "strength": 0,
            "description": f"중립적 (K: {k:.1f}, D: {d:.1f})"
        })
    
    return signals

def analyze_orderbook_data(orderbook_ratio, signal_strengths):
    """호가창 분석"""
    signals = []
    
    if orderbook_ratio > 1.2:  # 매수세가 강함
        strength = min(0.6, (orderbook_ratio - 1) / 2)  # 최대 0.6
        signals.append({
            "source": "호가창(매수/매도비율)",
            "signal": "buy",
            "strength": strength,
            "description": f"매수세 강함 (매수/매도 비율: {orderbook_ratio:.2f})"
        })
    elif orderbook_ratio < 0.8:  # 매도세가 강함
        strength = min(0.6, (1 - orderbook_ratio) / 2)  # 최대 0.6
        signals.append({
            "source": "호가창(매수/매도비율)",
            "signal": "sell",
            "strength": strength,
            "description": f"매도세 강함 (매수/매도 비율: {orderbook_ratio:.2f})"
        })
    else:  # 중립적
        signals.append({
            "source": "호가창(매수/매도비율)",
            "signal": "hold",
            "strength": 0,
            "description": f"중립적 호가창 (매수/매도 비율: {orderbook_ratio:.2f})"
        })
    
    return signals

def analyze_trade_data(trade_signal, signal_strengths):
    """체결 데이터 분석"""
    signals = []
    
    if trade_signal > 0.3:  # 매수세 우세
        signals.append({
            "source": "체결데이터",
            "signal": "buy",
            "strength": signal_strengths.get("trade_data", 0.5) * min(1, trade_signal),
            "description": f"매수 체결 우세 (신호 강도: {trade_signal:.2f})"
        })
    elif trade_signal < -0.3:  # 매도세 우세
        signals.append({
            "source": "체결데이터",
            "signal": "sell",
            "strength": signal_strengths.get("trade_data", 0.5) * min(1, abs(trade_signal)),
            "description": f"매도 체결 우세 (신호 강도: {trade_signal:.2f})"
        })
    else:  # 중립적
        signals.append({
            "source": "체결데이터",
            "signal": "hold",
            "strength": 0,
            "description": f"중립적 체결 (신호 강도: {trade_signal:.2f})"
        })
    
    return signals

def analyze_kimchi_premium(kimchi_premium, signal_strengths):
    """김프(한국 프리미엄) 분석"""
    signals = []
    
    if kimchi_premium < -1.0:  # 역프리미엄 1% 이상 (한국 가격이 저평가)
        strength = min(0.5, abs(kimchi_premium) / 10)  # 최대 0.5
        signals.append({
            "source": "김프(한국 프리미엄)",
            "signal": "buy",
            "strength": strength,
            "description": f"역프리미엄 발생 (김프: {kimchi_premium:.2f}%)"
        })
    elif kimchi_premium > 4.0:  # 프리미엄 4% 이상 (한국 가격이 고평가)
        strength = min(0.5, kimchi_premium / 10)  # 최대 0.5
        signals.append({
            "source": "김프(한국 프리미엄)",
            "signal": "sell",
            "strength": strength,
            "description": f"높은 프리미엄 (김프: {kimchi_premium:.2f}%)"
        })
    else:  # 적정 수준의 프리미엄
        signals.append({
            "source": "김프(한국 프리미엄)",
            "signal": "hold",
            "strength": 0,
            "description": f"적정 프리미엄 수준 (김프: {kimchi_premium:.2f}%)"
        })
    
    return signals

def analyze_fear_greed_index(fear_greed_value, signal_strengths):
    """공포 & 탐욕 지수 분석"""
    signals = []
    
    if fear_greed_value <= 25:  # 극도의 공포 (0-25)
        signals.append({
            "source": "시장심리(공포&탐욕지수)",
            "signal": "buy",
            "strength": signal_strengths.get("fear_greed_extreme", 0.7),
            "description": f"극도의 공포 상태 (Fear & Greed: {fear_greed_value}, Extreme Fear)"
        })
    elif fear_greed_value <= 40:  # 공포 (26-40)
        signals.append({
            "source": "시장심리(공포&탐욕지수)",
            "signal": "buy",
            "strength": signal_strengths.get("fear_greed_middle", 0.4),
            "description": f"공포 우세 상태 (Fear & Greed: {fear_greed_value}, Fear)"
        })
    elif fear_greed_value >= 75:  # 극도의 탐욕 (75-100)
        signals.append({
            "source": "시장심리(공포&탐욕지수)",
            "signal": "sell",
            "strength": signal_strengths.get("fear_greed_extreme", 0.7),
            "description": f"극도의 탐욕 상태 (Fear & Greed: {fear_greed_value}, Extreme Greed)"
        })
    elif fear_greed_value >= 60:  # 탐욕 (60-74)
        signals.append({
            "source": "시장심리(공포&탐욕지수)",
            "signal": "sell",
            "strength": signal_strengths.get("fear_greed_middle", 0.4),
            "description": f"탐욕 우세 상태 (Fear & Greed: {fear_greed_value}, Greed)"
        })
    else:  # 중립 (41-59)
        signals.append({
            "source": "시장심리(공포&탐욕지수)",
            "signal": "hold",
            "strength": 0,
            "description": f"중립적 시장 심리 (Fear & Greed: {fear_greed_value}, Neutral)"
        })
    
    return signals

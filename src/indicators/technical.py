import numpy as np
import pandas as pd

class TechnicalIndicators:
    """
    기술적 지표 계산 클래스
    이동평균선, RSI, MACD, 볼린저 밴드 등 다양한 기술적 지표를 계산합니다.
    """
    
    def __init__(self, df=None):
        """
        기술적 지표 계산기 초기화
        
        Args:
            df: OHLCV 데이터프레임 (없으면 나중에 set_data로 설정)
        """
        self.df = df
    
    def set_data(self, df):
        """
        데이터 설정
        
        Args:
            df: OHLCV 데이터프레임
        """
        self.df = df
    
    def get_ma(self, period=20, column='close'):
        """
        이동평균선 계산
        
        Args:
            period: 기간 (일)
            column: 사용할 가격 컬럼 (기본: close)
            
        Returns:
            pandas.Series: 이동평균선
        """
        if self.df is None:
            raise ValueError("데이터가 설정되지 않았습니다.")
        
        return self.df[column].rolling(window=period).mean()
    
    def get_ema(self, period=20, column='close'):
        """
        지수이동평균선 계산
        
        Args:
            period: 기간 (일)
            column: 사용할 가격 컬럼 (기본: close)
            
        Returns:
            pandas.Series: 지수이동평균선
        """
        if self.df is None:
            raise ValueError("데이터가 설정되지 않았습니다.")
        
        return self.df[column].ewm(span=period, adjust=False).mean()
    
    def get_rsi(self, period=14, column='close'):
        """
        RSI(상대강도지수) 계산
        
        Args:
            period: 기간 (일)
            column: 사용할 가격 컬럼 (기본: close)
            
        Returns:
            pandas.Series: RSI 값
        """
        if self.df is None:
            raise ValueError("데이터가 설정되지 않았습니다.")
        
        delta = self.df[column].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        
        ma_up = up.rolling(window=period).mean()
        ma_down = down.rolling(window=period).mean()
        
        rsi = 100 - (100 / (1 + ma_up / ma_down))
        return rsi
    
    def get_macd(self, fast=12, slow=26, signal=9, column='close'):
        """
        MACD(이동평균수렴확산) 계산
        
        Args:
            fast: 단기 이동평균 기간
            slow: 장기 이동평균 기간
            signal: 시그널 기간
            column: 사용할 가격 컬럼 (기본: close)
            
        Returns:
            tuple: (MACD, Signal, Histogram)
        """
        if self.df is None:
            raise ValueError("데이터가 설정되지 않았습니다.")
        
        ema_fast = self.df[column].ewm(span=fast, adjust=False).mean()
        ema_slow = self.df[column].ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal
        
        return macd, signal, histogram
    
    def get_bollinger_bands(self, period=20, std_dev=2, column='close'):
        """
        볼린저 밴드 계산
        
        Args:
            period: 이동평균 기간
            std_dev: 표준편차 배수
            column: 사용할 가격 컬럼 (기본: close)
            
        Returns:
            tuple: (상단, 중앙, 하단)
        """
        if self.df is None:
            raise ValueError("데이터가 설정되지 않았습니다.")
        
        ma = self.df[column].rolling(window=period).mean()
        std = self.df[column].rolling(window=period).std()
        
        upper = ma + (std * std_dev)
        lower = ma - (std * std_dev)
        
        return upper, ma, lower
    
    def get_stochastic(self, period_k=14, period_d=3, column='close'):
        """
        스토캐스틱 오실레이터 계산
        
        Args:
            period_k: K 기간
            period_d: D 기간
            column: 사용할 가격 컬럼 (기본: close)
            
        Returns:
            tuple: (%K, %D)
        """
        if self.df is None:
            raise ValueError("데이터가 설정되지 않았습니다.")
        
        low_min = self.df['low'].rolling(window=period_k).min()
        high_max = self.df['high'].rolling(window=period_k).max()
        
        k = 100 * ((self.df[column] - low_min) / (high_max - low_min))
        d = k.rolling(window=period_d).mean()
        
        return k, d
    
    def get_atr(self, period=14):
        """
        ATR(평균 실제 범위) 계산
        
        Args:
            period: 기간 (일)
            
        Returns:
            pandas.Series: ATR 값
        """
        if self.df is None:
            raise ValueError("데이터가 설정되지 않았습니다.")
        
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        # 전일 종가
        prev_close = close.shift(1)
        
        # 실제 범위 (TR)
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        
        tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
        
        # ATR
        atr = tr.rolling(window=period).mean()
        return atr
    
    def get_price_change(self, period=1, column='close'):
        """
        가격 변화율 계산
        
        Args:
            period: 기간 (일)
            column: 사용할 가격 컬럼 (기본: close)
            
        Returns:
            pandas.Series: 가격 변화율 (%)
        """
        if self.df is None:
            raise ValueError("데이터가 설정되지 않았습니다.")
        
        return self.df[column].pct_change(periods=period) * 100
    
    def get_ma_crossover_signal(self, fast_period=5, slow_period=20, column='close'):
        """
        이동평균선 골든크로스/데드크로스 신호 계산
        
        Args:
            fast_period: 단기 이동평균 기간
            slow_period: 장기 이동평균 기간
            column: 사용할 가격 컬럼 (기본: close)
            
        Returns:
            int: 1 (골든크로스), -1 (데드크로스), 0 (무신호)
        """
        if self.df is None:
            raise ValueError("데이터가 설정되지 않았습니다.")
        
        fast_ma = self.get_ma(period=fast_period, column=column)
        slow_ma = self.get_ma(period=slow_period, column=column)
        
        # 현재 상태
        current_cross = 1 if fast_ma.iloc[-1] > slow_ma.iloc[-1] else -1
        
        # 이전 상태
        prev_cross = 1 if fast_ma.iloc[-2] > slow_ma.iloc[-2] else -1
        
        # 크로스 신호
        if current_cross == 1 and prev_cross == -1:
            return 1  # 골든크로스
        elif current_cross == -1 and prev_cross == 1:
            return -1  # 데드크로스
        else:
            return 0  # 무신호
    
    def get_rsi_signal(self, period=14, oversold=30, overbought=70, column='close'):
        """
        RSI 매수/매도 신호 계산
        
        Args:
            period: RSI 계산 기간
            oversold: 과매도 기준
            overbought: 과매수 기준
            column: 사용할 가격 컬럼 (기본: close)
            
        Returns:
            int: 1 (매수 신호), -1 (매도 신호), 0 (무신호)
        """
        if self.df is None:
            raise ValueError("데이터가 설정되지 않았습니다.")
        
        rsi = self.get_rsi(period=period, column=column)
        
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2]
        
        if current_rsi < oversold and prev_rsi < oversold:
            return 1  # 과매도 -> 매수 신호
        elif current_rsi > overbought and prev_rsi > overbought:
            return -1  # 과매수 -> 매도 신호
        else:
            return 0  # 무신호
    
    def get_macd_signal(self, fast=12, slow=26, signal=9, column='close'):
        """
        MACD 매수/매도 신호 계산
        
        Args:
            fast: 단기 이동평균 기간
            slow: 장기 이동평균 기간
            signal: 시그널 기간
            column: 사용할 가격 컬럼 (기본: close)
            
        Returns:
            int: 1 (매수 신호), -1 (매도 신호), 0 (무신호)
        """
        if self.df is None:
            raise ValueError("데이터가 설정되지 않았습니다.")
        
        macd, signal, histogram = self.get_macd(fast=fast, slow=slow, signal=signal, column=column)
        
        # 현재 히스토그램
        current_hist = histogram.iloc[-1]
        prev_hist = histogram.iloc[-2]
        
        # MACD 골든크로스: 히스토그램이 음수에서 양수로 전환
        if current_hist > 0 and prev_hist < 0:
            return 1  # 매수 신호
        # MACD 데드크로스: 히스토그램이 양수에서 음수로 전환
        elif current_hist < 0 and prev_hist > 0:
            return -1  # 매도 신호
        else:
            return 0  # 무신호
    
    def get_bollinger_signal(self, period=20, std_dev=2, column='close'):
        """
        볼린저 밴드 매수/매도 신호 계산
        
        Args:
            period: 이동평균 기간
            std_dev: 표준편차 배수
            column: 사용할 가격 컬럼 (기본: close)
            
        Returns:
            int: 1 (매수 신호), -1 (매도 신호), 0 (무신호)
        """
        if self.df is None:
            raise ValueError("데이터가 설정되지 않았습니다.")
        
        upper, middle, lower = self.get_bollinger_bands(period=period, std_dev=std_dev, column=column)
        
        current_price = self.df[column].iloc[-1]
        
        # 볼린저 밴드 하단 돌파: 매수 신호
        if current_price < lower.iloc[-1]:
            return 1
        # 볼린저 밴드 상단 돌파: 매도 신호
        elif current_price > upper.iloc[-1]:
            return -1
        else:
            return 0
    
    def get_stochastic_signal(self, period_k=14, period_d=3, column='close'):
        """
        스토캐스틱 매수/매도 신호 계산
        
        Args:
            period_k: K 기간
            period_d: D 기간
            column: 사용할 가격 컬럼 (기본: close)
            
        Returns:
            int: 1 (매수 신호), -1 (매도 신호), 0 (무신호)
        """
        if self.df is None:
            raise ValueError("데이터가 설정되지 않았습니다.")
        
        k, d = self.get_stochastic(period_k=period_k, period_d=period_d, column=column)
        
        # 현재 K, D 값
        current_k = k.iloc[-1]
        current_d = d.iloc[-1]
        
        # 이전 K, D 값
        prev_k = k.iloc[-2]
        prev_d = d.iloc[-2]
        
        # 과매도 영역에서 K가 D를 상향 돌파: 매수 신호
        if current_k < 20 and current_d < 20 and current_k > current_d and prev_k < prev_d:
            return 1
        # 과매수 영역에서 K가 D를 하향 돌파: 매도 신호
        elif current_k > 80 and current_d > 80 and current_k < current_d and prev_k > prev_d:
            return -1
        else:
            return 0
    
    def get_all_signals(self, include_strength=True):
        """
        모든 기술적 지표 신호 계산
        
        Args:
            include_strength: 신호 강도 포함 여부
            
        Returns:
            dict: 지표별 신호
        """
        if self.df is None:
            raise ValueError("데이터가 설정되지 않았습니다.")
        
        signals = {}
        
        # 이동평균선 신호
        ma_signal = self.get_ma_crossover_signal(5, 20)
        signals["MA"] = {
            "signal": "buy" if ma_signal == 1 else "sell" if ma_signal == -1 else "hold",
            "value": ma_signal
        }
        
        if include_strength:
            if ma_signal == 1:
                signals["MA"]["strength"] = 0.6  # 골든크로스 강도
                signals["MA"]["description"] = "골든크로스 상태 (5일 이동평균선이 20일 이동평균선 위에 위치)"
            elif ma_signal == -1:
                signals["MA"]["strength"] = 0.6  # 데드크로스 강도
                signals["MA"]["description"] = "데드크로스 상태 (5일 이동평균선이 20일 이동평균선 아래에 위치)"
            else:
                signals["MA"]["strength"] = 0.0
                signals["MA"]["description"] = "뚜렷한 추세 없음"
        
        # RSI 신호
        rsi_value = self.get_rsi().iloc[-1]
        rsi_signal = self.get_rsi_signal()
        signals["RSI"] = {
            "signal": "buy" if rsi_signal == 1 else "sell" if rsi_signal == -1 else "hold",
            "value": rsi_value
        }
        
        if include_strength:
            if rsi_value < 30:
                signals["RSI"]["strength"] = 0.8  # 과매도 강도
                signals["RSI"]["description"] = f"과매도 상태 (RSI: {rsi_value:.1f} < 30)"
            elif rsi_value > 70:
                signals["RSI"]["strength"] = 0.8  # 과매수 강도
                signals["RSI"]["description"] = f"과매수 상태 (RSI: {rsi_value:.1f} > 70)"
            elif rsi_value < 45:
                signals["RSI"]["strength"] = 0.2  # 약한 매수 신호
                signals["RSI"]["description"] = f"매도세 우세 (RSI: {rsi_value:.1f})"
            elif rsi_value > 55:
                signals["RSI"]["strength"] = 0.2  # 약한 매도 신호
                signals["RSI"]["description"] = f"매수세 우세 (RSI: {rsi_value:.1f})"
            else:
                signals["RSI"]["strength"] = 0.0
                signals["RSI"]["description"] = f"중립적 (RSI: {rsi_value:.1f})"
        
        # MACD 신호
        macd_signal = self.get_macd_signal()
        macd, signal, histogram = self.get_macd()
        signals["MACD"] = {
            "signal": "buy" if macd_signal == 1 else "sell" if macd_signal == -1 else "hold",
            "value": histogram.iloc[-1]
        }
        
        if include_strength:
            if macd_signal == 1:
                signals["MACD"]["strength"] = 0.7  # 골든크로스 강도
                signals["MACD"]["description"] = "MACD 골든크로스 발생"
            elif macd_signal == -1:
                signals["MACD"]["strength"] = 0.7  # 데드크로스 강도
                signals["MACD"]["description"] = "MACD 데드크로스 발생"
            elif histogram.iloc[-1] > 0 and histogram.iloc[-2] > 0:
                signals["MACD"]["strength"] = 0.3
                signals["MACD"]["description"] = "MACD 상승 추세 유지중"
            elif histogram.iloc[-1] < 0 and histogram.iloc[-2] < 0:
                signals["MACD"]["strength"] = 0.3
                signals["MACD"]["description"] = "MACD 하락 추세 유지중"
            else:
                signals["MACD"]["strength"] = 0.0
                signals["MACD"]["description"] = "MACD 중립적 상태"
        
        # 볼린저 밴드 신호
        bb_signal = self.get_bollinger_signal()
        upper, middle, lower = self.get_bollinger_bands()
        current_price = self.df['close'].iloc[-1]
        
        # 현재 가격의 밴드 내 위치 (%)
        bb_position = (current_price - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1]) * 100
        
        signals["BB"] = {
            "signal": "buy" if bb_signal == 1 else "sell" if bb_signal == -1 else "hold",
            "value": bb_position
        }
        
        if include_strength:
            if bb_signal == 1:
                signals["BB"]["strength"] = 0.7  # 하단 돌파 강도
                signals["BB"]["description"] = "볼린저 밴드 하단 돌파 (초과매도)"
            elif bb_signal == -1:
                signals["BB"]["strength"] = 0.7  # 상단 돌파 강도
                signals["BB"]["description"] = "볼린저 밴드 상단 돌파 (초과매수)"
            elif bb_position < 30:
                signals["BB"]["strength"] = 0.3
                signals["BB"]["description"] = f"하단 접근중 (밴드 내 위치: 하위 {bb_position:.0f}%)"
            elif bb_position > 70:
                signals["BB"]["strength"] = 0.3
                signals["BB"]["description"] = f"상단 접근중 (밴드 내 위치: 상위 {bb_position:.0f}%)"
            else:
                signals["BB"]["strength"] = 0.0
                signals["BB"]["description"] = "밴드 중앙 부근 (중립적 위치)"
        
        # 스토캐스틱 신호
        stoch_signal = self.get_stochastic_signal()
        k, d = self.get_stochastic()
        
        signals["Stochastic"] = {
            "signal": "buy" if stoch_signal == 1 else "sell" if stoch_signal == -1 else "hold",
            "value": k.iloc[-1]
        }
        
        if include_strength:
            if stoch_signal == 1:
                signals["Stochastic"]["strength"] = 0.6
                signals["Stochastic"]["description"] = f"과매도 반전 신호 (K: {k.iloc[-1]:.1f}, D: {d.iloc[-1]:.1f})"
            elif stoch_signal == -1:
                signals["Stochastic"]["strength"] = 0.6
                signals["Stochastic"]["description"] = f"과매수 반전 신호 (K: {k.iloc[-1]:.1f}, D: {d.iloc[-1]:.1f})"
            elif k.iloc[-1] > d.iloc[-1]:
                signals["Stochastic"]["strength"] = 0.3
                signals["Stochastic"]["description"] = f"상승 반전 신호 (K > D, K: {k.iloc[-1]:.1f}, D: {d.iloc[-1]:.1f})"
            elif k.iloc[-1] < d.iloc[-1]:
                signals["Stochastic"]["strength"] = 0.3
                signals["Stochastic"]["description"] = f"하락 반전 신호 (K < D, K: {k.iloc[-1]:.1f}, D: {d.iloc[-1]:.1f})"
            else:
                signals["Stochastic"]["strength"] = 0.0
                signals["Stochastic"]["description"] = f"중립적 (K: {k.iloc[-1]:.1f}, D: {d.iloc[-1]:.1f})"
        
        return signals
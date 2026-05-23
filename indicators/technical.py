"""
FinancialProof - Technische Indikatoren
Berechnung von SMA, EMA, RSI, Bollinger Bänder, MACD, etc.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class IndicatorType(str, Enum):
    """Typen von technischen Indikatoren"""
    # Trend-Indikatoren
    SMA = "sma"
    EMA = "ema"
    MACD = "macd"

    # Momentum-Indikatoren
    RSI = "rsi"
    STOCHASTIC = "stochastic"
    ROC = "roc"  # Rate of Change

    # Volatilitäts-Indikatoren
    BOLLINGER = "bollinger"
    ATR = "atr"  # Average True Range

    # Volumen-Indikatoren
    OBV = "obv"  # On-Balance Volume
    VWAP = "vwap"  # Volume Weighted Average Price


@dataclass
class IndicatorConfig:
    """Konfiguration für einen Indikator"""
    name: str
    display_name: str
    indicator_type: IndicatorType
    default_params: Dict
    description: str
    overlay: bool  # True = wird über den Kurs gelegt, False = separater Chart


# Vorkonfigurierte Indikatoren
INDICATOR_CONFIGS = {
    "sma_20": IndicatorConfig(
        name="sma_20",
        display_name="SMA 20",
        indicator_type=IndicatorType.SMA,
        default_params={"period": 20},
        description="Einfacher gleitender Durchschnitt (20 Tage)",
        overlay=True
    ),
    "sma_50": IndicatorConfig(
        name="sma_50",
        display_name="SMA 50",
        indicator_type=IndicatorType.SMA,
        default_params={"period": 50},
        description="Einfacher gleitender Durchschnitt (50 Tage)",
        overlay=True
    ),
    "sma_200": IndicatorConfig(
        name="sma_200",
        display_name="SMA 200",
        indicator_type=IndicatorType.SMA,
        default_params={"period": 200},
        description="Einfacher gleitender Durchschnitt (200 Tage)",
        overlay=True
    ),
    "ema_12": IndicatorConfig(
        name="ema_12",
        display_name="EMA 12",
        indicator_type=IndicatorType.EMA,
        default_params={"period": 12},
        description="Exponentieller gleitender Durchschnitt (12 Tage)",
        overlay=True
    ),
    "ema_26": IndicatorConfig(
        name="ema_26",
        display_name="EMA 26",
        indicator_type=IndicatorType.EMA,
        default_params={"period": 26},
        description="Exponentieller gleitender Durchschnitt (26 Tage)",
        overlay=True
    ),
    "rsi": IndicatorConfig(
        name="rsi",
        display_name="RSI (14)",
        indicator_type=IndicatorType.RSI,
        default_params={"period": 14},
        description="Relative Strength Index - misst überkaufte/überverkaufte Zustände",
        overlay=False
    ),
    "bollinger": IndicatorConfig(
        name="bollinger",
        display_name="Bollinger Bänder",
        indicator_type=IndicatorType.BOLLINGER,
        default_params={"period": 20, "std_dev": 2.0},
        description="Volatilitätsbänder um den gleitenden Durchschnitt",
        overlay=True
    ),
    "macd": IndicatorConfig(
        name="macd",
        display_name="MACD",
        indicator_type=IndicatorType.MACD,
        default_params={"fast": 12, "slow": 26, "signal": 9},
        description="Moving Average Convergence Divergence",
        overlay=False
    ),
    "stochastic": IndicatorConfig(
        name="stochastic",
        display_name="Stochastic",
        indicator_type=IndicatorType.STOCHASTIC,
        default_params={"k_period": 14, "d_period": 3},
        description="Stochastic Oscillator - Momentum-Indikator",
        overlay=False
    ),
    "atr": IndicatorConfig(
        name="atr",
        display_name="ATR (14)",
        indicator_type=IndicatorType.ATR,
        default_params={"period": 14},
        description="Average True Range - Volatilitätsmaß",
        overlay=False
    )
}


class TechnicalIndicators:
    """Berechnet technische Indikatoren"""

    # ===== TREND-INDIKATOREN =====

    @staticmethod
    def sma(data: pd.Series, period: int = 20) -> pd.Series:
        """
        Einfacher gleitender Durchschnitt (Simple Moving Average)

        Args:
            data: Kursdaten (typisch: Close)
            period: Anzahl der Perioden

        Returns:
            Series mit SMA-Werten
        """
        return data.rolling(window=period, min_periods=1).mean()

    @staticmethod
    def ema(data: pd.Series, period: int = 12) -> pd.Series:
        """
        Exponentieller gleitender Durchschnitt (Exponential Moving Average)

        Args:
            data: Kursdaten
            period: Anzahl der Perioden

        Returns:
            Series mit EMA-Werten
        """
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def macd(
        data: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, pd.Series]:
        """
        Moving Average Convergence Divergence

        Args:
            data: Kursdaten (Close)
            fast: Schnelle EMA-Periode
            slow: Langsame EMA-Periode
            signal: Signal-Linie Periode

        Returns:
            Dict mit 'macd', 'signal', 'histogram'
        """
        ema_fast = TechnicalIndicators.ema(data, fast)
        ema_slow = TechnicalIndicators.ema(data, slow)

        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line

        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    # ===== MOMENTUM-INDIKATOREN =====

    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index

        Args:
            data: Kursdaten (Close)
            period: Berechnungsperiode (Standard: 14)

        Returns:
            Series mit RSI-Werten (0-100)
        """
        delta = data.diff()

        gain = delta.where(delta > 0, 0.0)
        loss = (-delta.where(delta < 0, 0.0))

        # Erste Berechnung mit SMA
        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()

        # Division durch 0 sauber behandeln:
        # - nur Gewinne -> RSI 100
        # - nur Verluste -> RSI 0
        # - weder Gewinne noch Verluste -> neutral 50
        rsi = pd.Series(50.0, index=data.index, dtype=float)
        bullish = (avg_loss == 0) & (avg_gain > 0)
        bearish = (avg_gain == 0) & (avg_loss > 0)
        neutral = (avg_gain == 0) & (avg_loss == 0)
        normal = ~(bullish | bearish | neutral)

        if normal.any():
            rs = avg_gain.loc[normal] / avg_loss.loc[normal]
            rsi.loc[normal] = 100 - (100 / (1 + rs))

        rsi.loc[bullish] = 100.0
        rsi.loc[bearish] = 0.0
        rsi.loc[neutral] = 50.0

        return rsi.fillna(50)

    @staticmethod
    def stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3
    ) -> Dict[str, pd.Series]:
        """
        Stochastic Oscillator

        Args:
            high: Höchstkurse
            low: Tiefstkurse
            close: Schlusskurse
            k_period: %K Periode
            d_period: %D Periode (Glättung)

        Returns:
            Dict mit 'k' und 'd' Werten
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        k = 100 * (close - lowest_low) / (highest_high - lowest_low + 0.0001)
        d = k.rolling(window=d_period).mean()

        return {'k': k, 'd': d}

    @staticmethod
    def roc(data: pd.Series, period: int = 10) -> pd.Series:
        """
        Rate of Change - prozentuale Änderung über n Perioden

        Args:
            data: Kursdaten
            period: Berechnungsperiode

        Returns:
            Series mit ROC-Werten in Prozent
        """
        return ((data - data.shift(period)) / data.shift(period)) * 100

    # ===== VOLATILITÄTS-INDIKATOREN =====

    @staticmethod
    def bollinger_bands(
        data: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        Bollinger Bänder

        Args:
            data: Kursdaten (Close)
            period: SMA-Periode
            std_dev: Anzahl der Standardabweichungen

        Returns:
            Dict mit 'middle', 'upper', 'lower', 'width', 'pct_b'
        """
        middle = TechnicalIndicators.sma(data, period)
        std = data.rolling(window=period).std()

        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)

        # Bandbreite (für Squeeze-Erkennung)
        width = (upper - lower) / middle * 100

        # %B - Position des Kurses innerhalb der Bänder (0-1)
        pct_b = (data - lower) / (upper - lower + 0.0001)

        return {
            'middle': middle,
            'upper': upper,
            'lower': lower,
            'width': width,
            'pct_b': pct_b
        }

    @staticmethod
    def atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Average True Range - Volatilitätsmaß

        Args:
            high: Höchstkurse
            low: Tiefstkurse
            close: Schlusskurse
            period: Berechnungsperiode

        Returns:
            Series mit ATR-Werten
        """
        prev_close = close.shift(1)

        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        return true_range.rolling(window=period).mean()

    # ===== VOLUMEN-INDIKATOREN =====

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        On-Balance Volume

        Args:
            close: Schlusskurse
            volume: Volumen

        Returns:
            Series mit OBV-Werten
        """
        direction = np.where(close > close.shift(1), 1,
                            np.where(close < close.shift(1), -1, 0))
        return (direction * volume).cumsum()

    @staticmethod
    def vwap(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series
    ) -> pd.Series:
        """
        Volume Weighted Average Price

        Args:
            high: Höchstkurse
            low: Tiefstkurse
            close: Schlusskurse
            volume: Volumen

        Returns:
            Series mit VWAP-Werten
        """
        typical_price = (high + low + close) / 3
        return (typical_price * volume).cumsum() / volume.cumsum()

    # ===== KOMBINIERTE BERECHNUNGEN =====

    @staticmethod
    def calculate_all(
        df: pd.DataFrame,
        indicators: List[str] = None
    ) -> pd.DataFrame:
        """
        Berechnet mehrere Indikatoren auf einmal.

        Args:
            df: DataFrame mit OHLCV-Daten
            indicators: Liste der gewünschten Indikatoren (Keys aus INDICATOR_CONFIGS)
                       None = alle Standard-Indikatoren

        Returns:
            DataFrame mit zusätzlichen Indikator-Spalten
        """
        result = df.copy()
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']

        if indicators is None:
            indicators = ['sma_20', 'sma_50', 'rsi', 'bollinger', 'macd']

        for ind_name in indicators:
            config = INDICATOR_CONFIGS.get(ind_name)
            if not config:
                continue

            params = config.default_params

            if config.indicator_type == IndicatorType.SMA:
                result[ind_name] = TechnicalIndicators.sma(close, params['period'])

            elif config.indicator_type == IndicatorType.EMA:
                result[ind_name] = TechnicalIndicators.ema(close, params['period'])

            elif config.indicator_type == IndicatorType.RSI:
                result['rsi'] = TechnicalIndicators.rsi(close, params['period'])

            elif config.indicator_type == IndicatorType.BOLLINGER:
                bb = TechnicalIndicators.bollinger_bands(
                    close, params['period'], params['std_dev']
                )
                result['bb_upper'] = bb['upper']
                result['bb_middle'] = bb['middle']
                result['bb_lower'] = bb['lower']
                result['bb_width'] = bb['width']
                result['bb_pct_b'] = bb['pct_b']

            elif config.indicator_type == IndicatorType.MACD:
                macd_data = TechnicalIndicators.macd(
                    close, params['fast'], params['slow'], params['signal']
                )
                result['macd'] = macd_data['macd']
                result['macd_signal'] = macd_data['signal']
                result['macd_histogram'] = macd_data['histogram']

            elif config.indicator_type == IndicatorType.STOCHASTIC:
                stoch = TechnicalIndicators.stochastic(
                    high, low, close, params['k_period'], params['d_period']
                )
                result['stoch_k'] = stoch['k']
                result['stoch_d'] = stoch['d']

            elif config.indicator_type == IndicatorType.ATR:
                result['atr'] = TechnicalIndicators.atr(
                    high, low, close, params['period']
                )

        return result

    # ===== HILFSFUNKTIONEN =====

    @staticmethod
    def get_trend_direction(data: pd.Series, period: int = 20) -> str:
        """
        Bestimmt die Trendrichtung basierend auf SMA.

        Returns:
            'bullish', 'bearish' oder 'neutral'
        """
        sma = TechnicalIndicators.sma(data, period)
        current = data.iloc[-1]
        sma_current = sma.iloc[-1]

        if current > sma_current * 1.02:
            return 'bullish'
        elif current < sma_current * 0.98:
            return 'bearish'
        return 'neutral'

    @staticmethod
    def get_volatility_state(df: pd.DataFrame) -> str:
        """
        Bestimmt den Volatilitätszustand basierend auf Bollinger Bandbreite.

        Returns:
            'high', 'normal' oder 'low' (Squeeze)
        """
        bb = TechnicalIndicators.bollinger_bands(df['Close'])
        width = bb['width'].iloc[-1]

        # Vergleich mit historischer Bandbreite
        avg_width = bb['width'].mean()

        if width > avg_width * 1.5:
            return 'high'
        elif width < avg_width * 0.5:
            return 'low'  # Squeeze - oft vor größeren Bewegungen
        return 'normal'

    @staticmethod
    def get_momentum_state(df: pd.DataFrame) -> Tuple[str, float]:
        """
        Bestimmt den Momentum-Zustand basierend auf RSI.

        Returns:
            Tuple (Zustand, RSI-Wert)
            Zustand: 'overbought', 'oversold', 'neutral'
        """
        rsi = TechnicalIndicators.rsi(df['Close'])
        current_rsi = rsi.iloc[-1]

        if current_rsi >= 70:
            return ('overbought', current_rsi)
        elif current_rsi <= 30:
            return ('oversold', current_rsi)
        return ('neutral', current_rsi)

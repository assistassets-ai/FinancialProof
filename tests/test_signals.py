"""
Tests fuer Signal-Generierung
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd
import numpy as np
from indicators.signals import (
    SignalGenerator, SignalType, SignalStrength, Signal, format_signal_for_display
)
from indicators.technical import TechnicalIndicators


@pytest.fixture
def sample_ohlcv():
    """Erzeugt einen OHLCV-DataFrame mit 200 Tagen Testdaten"""
    np.random.seed(123)
    n = 200
    dates = pd.date_range("2025-01-01", periods=n, freq="B")
    close = 100 + np.cumsum(np.random.randn(n) * 1.0)
    high = close + np.abs(np.random.randn(n) * 0.5)
    low = close - np.abs(np.random.randn(n) * 0.5)
    open_ = close + np.random.randn(n) * 0.3
    volume = np.random.randint(1_000_000, 10_000_000, size=n).astype(float)

    return pd.DataFrame({
        "Open": open_,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": volume
    }, index=dates)


@pytest.fixture
def df_with_indicators(sample_ohlcv):
    """OHLCV mit berechneten Indikatoren"""
    return TechnicalIndicators.calculate_all(
        sample_ohlcv,
        ["sma_20", "sma_50", "rsi", "bollinger", "macd"]
    )


class TestSignalGenerator:
    def test_generate_returns_list(self, df_with_indicators):
        gen = SignalGenerator()
        signals = gen.generate_all_signals(df_with_indicators)
        assert isinstance(signals, list)

    def test_signals_are_signal_objects(self, df_with_indicators):
        gen = SignalGenerator()
        signals = gen.generate_all_signals(df_with_indicators)
        for s in signals:
            assert isinstance(s, Signal)

    def test_signals_sorted_by_date_desc(self, df_with_indicators):
        gen = SignalGenerator()
        signals = gen.generate_all_signals(df_with_indicators)
        if len(signals) > 1:
            for i in range(len(signals) - 1):
                assert signals[i].date >= signals[i + 1].date

    def test_signal_types_valid(self, df_with_indicators):
        gen = SignalGenerator()
        signals = gen.generate_all_signals(df_with_indicators)
        for s in signals:
            assert s.signal_type in (SignalType.BUY, SignalType.SELL, SignalType.HOLD)

    def test_signal_confidence_range(self, df_with_indicators):
        gen = SignalGenerator()
        signals = gen.generate_all_signals(df_with_indicators)
        for s in signals:
            assert 0 <= s.confidence <= 1


class TestSignalSummary:
    def test_summary_keys(self, df_with_indicators):
        gen = SignalGenerator()
        summary = gen.get_signal_summary(df_with_indicators)
        assert "overall_signal" in summary
        assert "buy_count" in summary
        assert "sell_count" in summary
        assert "recent_signals" in summary

    def test_summary_overall_is_signal_type(self, df_with_indicators):
        gen = SignalGenerator()
        summary = gen.get_signal_summary(df_with_indicators)
        assert summary["overall_signal"] in (SignalType.BUY, SignalType.SELL, SignalType.HOLD)


class TestFormatSignal:
    def test_format_buy_signal(self):
        signal = Signal(
            date=pd.Timestamp("2025-06-01"),
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            indicator="RSI",
            description="Test signal",
            price=150.50,
            confidence=0.8
        )
        result = format_signal_for_display(signal)
        # Neutrales Label statt "Kaufen" (Rechtsaudit § 32 KWG)
        assert result["type"] == "Bullisches Muster"
        assert result["strength"] == "Stark"
        assert result["confidence"] == "80%"
        assert result["price"] == "150.50"

    def test_format_sell_signal(self):
        signal = Signal(
            date=pd.Timestamp("2025-06-01"),
            signal_type=SignalType.SELL,
            strength=SignalStrength.MODERATE,
            indicator="MACD",
            description="Test sell",
            price=99.99,
            confidence=0.65
        )
        result = format_signal_for_display(signal)
        # Neutrales Label statt "Verkaufen" (Rechtsaudit § 32 KWG)
        assert result["type"] == "Bärisches Muster"
        assert result["strength"] == "Mittel"

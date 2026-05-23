"""
Tests fuer technische Indikatoren
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd
import numpy as np
from indicators.technical import TechnicalIndicators, INDICATOR_CONFIGS


@pytest.fixture
def sample_ohlcv():
    """Erzeugt einen OHLCV-DataFrame mit 100 Tagen Testdaten"""
    np.random.seed(42)
    n = 100
    dates = pd.date_range("2025-01-01", periods=n, freq="B")
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)
    open_ = close + np.random.randn(n) * 0.2
    volume = np.random.randint(1_000_000, 10_000_000, size=n).astype(float)

    return pd.DataFrame({
        "Open": open_,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": volume
    }, index=dates)


class TestSMA:
    def test_sma_length(self, sample_ohlcv):
        result = TechnicalIndicators.sma(sample_ohlcv["Close"], 20)
        assert len(result) == len(sample_ohlcv)

    def test_sma_values_after_warmup(self, sample_ohlcv):
        period = 20
        result = TechnicalIndicators.sma(sample_ohlcv["Close"], period)
        expected = sample_ohlcv["Close"].iloc[:period].mean()
        assert abs(result.iloc[period - 1] - expected) < 0.01


class TestEMA:
    def test_ema_length(self, sample_ohlcv):
        result = TechnicalIndicators.ema(sample_ohlcv["Close"], 12)
        assert len(result) == len(sample_ohlcv)

    def test_ema_first_value(self, sample_ohlcv):
        result = TechnicalIndicators.ema(sample_ohlcv["Close"], 12)
        assert not np.isnan(result.iloc[0])


class TestRSI:
    def test_rsi_range(self, sample_ohlcv):
        result = TechnicalIndicators.rsi(sample_ohlcv["Close"], 14)
        assert result.min() >= 0
        assert result.max() <= 100

    def test_rsi_length(self, sample_ohlcv):
        result = TechnicalIndicators.rsi(sample_ohlcv["Close"], 14)
        assert len(result) == len(sample_ohlcv)

    @pytest.mark.parametrize(
        "close, expected_last",
        [
            (pd.Series(np.arange(1.0, 21.0)), 100.0),
            (pd.Series(np.arange(20.0, 0.0, -1.0)), 0.0),
            (pd.Series([5.0] * 20), 50.0),
        ],
    )
    def test_rsi_extremes_handle_trend_and_flat_series(self, close, expected_last):
        result = TechnicalIndicators.rsi(close, 14)
        assert result.iloc[-1] == pytest.approx(expected_last)


class TestBollingerBands:
    def test_bollinger_keys(self, sample_ohlcv):
        result = TechnicalIndicators.bollinger_bands(sample_ohlcv["Close"])
        assert "upper" in result
        assert "middle" in result
        assert "lower" in result
        assert "width" in result
        assert "pct_b" in result

    def test_bollinger_order(self, sample_ohlcv):
        result = TechnicalIndicators.bollinger_bands(sample_ohlcv["Close"])
        # Nach Warmup: upper > middle > lower
        idx = 25
        assert result["upper"].iloc[idx] > result["middle"].iloc[idx]
        assert result["middle"].iloc[idx] > result["lower"].iloc[idx]


class TestMACD:
    def test_macd_keys(self, sample_ohlcv):
        result = TechnicalIndicators.macd(sample_ohlcv["Close"])
        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result

    def test_macd_histogram_equals_diff(self, sample_ohlcv):
        result = TechnicalIndicators.macd(sample_ohlcv["Close"])
        diff = result["macd"] - result["signal"]
        np.testing.assert_allclose(result["histogram"].values, diff.values, atol=1e-10)


class TestATR:
    def test_atr_positive(self, sample_ohlcv):
        result = TechnicalIndicators.atr(
            sample_ohlcv["High"],
            sample_ohlcv["Low"],
            sample_ohlcv["Close"]
        )
        # Nach Warmup sollte ATR positiv sein
        assert result.dropna().min() >= 0


class TestCalculateAll:
    def test_calculate_all_adds_columns(self, sample_ohlcv):
        result = TechnicalIndicators.calculate_all(
            sample_ohlcv,
            ["sma_20", "rsi", "bollinger"]
        )
        assert "sma_20" in result.columns
        assert "rsi" in result.columns
        assert "bb_upper" in result.columns
        assert "bb_lower" in result.columns

    def test_calculate_all_preserves_original(self, sample_ohlcv):
        result = TechnicalIndicators.calculate_all(sample_ohlcv, ["sma_20"])
        assert "Close" in result.columns
        assert "Volume" in result.columns


class TestIndicatorConfigs:
    def test_all_configs_have_required_fields(self):
        for name, cfg in INDICATOR_CONFIGS.items():
            assert cfg.name == name
            assert cfg.display_name
            assert cfg.description
            assert isinstance(cfg.overlay, bool)

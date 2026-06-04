"""
Tests fuer MeanReversionAnalyzer.

Regression: chart_data-Konstruktion schlug fehl wenn len(prices) < lookback,
weil [value] * lookback laengere Listen erzeugte als prices.iloc[-lookback:].
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest

from analysis.statistical.mean_reversion import MeanReversionAnalyzer


@pytest.fixture
def analyzer():
    return MeanReversionAnalyzer()


@pytest.fixture
def short_price_series():
    """55 Datenpunkte — weniger als der Standard-Lookback von 60."""
    rng = np.random.default_rng(7)
    prices = 100 + np.cumsum(rng.normal(0, 1, 55))
    return pd.Series(prices, name="Close")


@pytest.fixture
def full_price_series():
    """120 Datenpunkte — mehr als Standard-Lookback."""
    rng = np.random.default_rng(7)
    prices = 100 + np.cumsum(rng.normal(0, 1, 120))
    return pd.Series(prices, name="Close")


class TestChartDataConstruction:
    """chart_data wird korrekt gebaut, auch wenn len(prices) < lookback."""

    def test_short_series_does_not_raise(self, analyzer, short_price_series):
        """Keine ValueError wenn Datenpunkte < lookback (Regression)."""
        lookback = 60
        metrics = analyzer._calculate_metrics(short_price_series, lookback)
        result = analyzer._build_result(
            symbol="TEST",
            prices=short_price_series,
            metrics=metrics,
            is_stationary=False,
            adf_pvalue=0.5,
            half_life=30.0,
            z_threshold=2.0,
            lookback=lookback,
        )
        assert result.chart_data is not None

    def test_chart_data_length_matches_available_data(self, analyzer, short_price_series):
        """chart_data hat so viele Zeilen wie tatsaechlich verfuegbare Datenpunkte."""
        lookback = 60
        metrics = analyzer._calculate_metrics(short_price_series, lookback)
        result = analyzer._build_result(
            symbol="TEST",
            prices=short_price_series,
            metrics=metrics,
            is_stationary=False,
            adf_pvalue=0.5,
            half_life=30.0,
            z_threshold=2.0,
            lookback=lookback,
        )
        expected_len = min(lookback, len(short_price_series))
        assert len(result.chart_data) == expected_len

    def test_chart_data_columns_equal_length(self, analyzer, short_price_series):
        """Alle chart_data-Spalten haben dieselbe Laenge."""
        lookback = 60
        metrics = analyzer._calculate_metrics(short_price_series, lookback)
        result = analyzer._build_result(
            symbol="TEST",
            prices=short_price_series,
            metrics=metrics,
            is_stationary=False,
            adf_pvalue=0.5,
            half_life=30.0,
            z_threshold=2.0,
            lookback=lookback,
        )
        lengths = [len(result.chart_data[c]) for c in result.chart_data.columns]
        assert len(set(lengths)) == 1, f"Ungleiche Spaltenlängen: {lengths}"

    def test_full_series_still_works(self, analyzer, full_price_series):
        """Normalbetrieb (len > lookback) funktioniert weiterhin."""
        lookback = 60
        metrics = analyzer._calculate_metrics(full_price_series, lookback)
        result = analyzer._build_result(
            symbol="TEST",
            prices=full_price_series,
            metrics=metrics,
            is_stationary=True,
            adf_pvalue=0.02,
            half_life=20.0,
            z_threshold=2.0,
            lookback=lookback,
        )
        assert len(result.chart_data) == lookback

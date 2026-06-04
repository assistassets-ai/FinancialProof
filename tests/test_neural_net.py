"""
Tests fuer NeuralNetAnalyzer._simple_pattern_analysis (Fallback ohne TensorFlow).
"""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))


def _make_df(prices):
    """Hilfsfunktion: DataFrame aus einer Preisliste bauen."""
    n = len(prices)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "Open":   prices,
        "High":   [p + 1.0 for p in prices],
        "Low":    [p - 1.0 for p in prices],
        "Close":  prices,
        "Volume": [1000] * n,
    }, index=dates)


class TestSimplePatternAnalysis:
    def _analyzer(self):
        from analysis.ml.neural_net import NeuralNetAnalyzer
        return NeuralNetAnalyzer()

    def test_flat_series_no_division_by_zero(self):
        """Komplett flache Preisserie darf KEINEN ZeroDivisionError ausloesen."""
        analyzer = self._analyzer()
        flat_prices = [100.0] * 40
        df = _make_df(flat_prices)
        # recent_high == recent_low -> frueherer Bug: ZeroDivisionError
        prediction, confidence, metrics = analyzer._simple_pattern_analysis(df, lookback=20)
        assert prediction in (0, 1)
        assert 0.0 <= confidence <= 1.0

    def test_trending_up_returns_bullish_prediction(self):
        """Klarer Aufwaertstrend soll Vorhersage 1 (bullish) liefern."""
        analyzer = self._analyzer()
        prices = [float(i) for i in range(60, 100)]
        df = _make_df(prices)
        prediction, confidence, metrics = analyzer._simple_pattern_analysis(df, lookback=20)
        assert prediction == 1

    def test_trending_down_returns_bearish_prediction(self):
        """Klarer Abwaertstrend soll Vorhersage 0 (bearish) liefern."""
        analyzer = self._analyzer()
        prices = [float(i) for i in range(100, 60, -1)]
        df = _make_df(prices)
        prediction, confidence, metrics = analyzer._simple_pattern_analysis(df, lookback=20)
        assert prediction == 0

    def test_confidence_capped_at_75_percent(self):
        """Konfidenz darf ohne echtes ML nicht ueber 75 % steigen."""
        analyzer = self._analyzer()
        prices = [float(i) * 10 for i in range(40)]
        df = _make_df(prices)
        _, confidence, _ = analyzer._simple_pattern_analysis(df, lookback=20)
        assert confidence <= 0.75

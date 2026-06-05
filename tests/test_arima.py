"""
Tests fuer ARIMAAnalyzer — insbesondere confidence_interval-Weitergabe.

Regression: confidence_interval hatte keinen Effekt, weil alpha an
get_forecast() uebergeben wurde (dort ignoriert) statt an conf_int(alpha=...).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest

from analysis.statistical.arima import ARIMAAnalyzer


@pytest.fixture
def price_series():
    """Synthetische Preiszeitreihe fuer ARIMA-Tests."""
    rng = np.random.default_rng(42)
    n = 120
    prices = 100 + np.cumsum(rng.normal(0, 1, n))
    return pd.Series(prices, name="Close")


class TestZFromAlpha:
    """_z_from_alpha gibt plausible z-Werte zurueck."""

    def test_standard_alpha_95(self):
        z = ARIMAAnalyzer._z_from_alpha(0.05)
        assert abs(z - 1.96) < 0.01

    def test_wider_ci_has_larger_z(self):
        z_99 = ARIMAAnalyzer._z_from_alpha(0.01)
        z_90 = ARIMAAnalyzer._z_from_alpha(0.10)
        assert z_99 > z_90

    def test_returns_positive_value(self):
        for alpha in (0.01, 0.05, 0.10, 0.20):
            assert ARIMAAnalyzer._z_from_alpha(alpha) > 0


class TestSimpleForecastAlpha:
    """SimpleForecast respektiert den alpha-Parameter (Regression-Test)."""

    def test_wider_alpha_produces_narrower_ci(self, price_series):
        model = ARIMAAnalyzer()._simple_forecast_model(price_series)
        result_narrow = model.get_forecast(steps=10, alpha=0.01)  # 99% CI — breit
        result_wide = model.get_forecast(steps=10, alpha=0.20)    # 80% CI — schmal

        ci_narrow = result_narrow.conf_int()
        ci_wide = result_wide.conf_int()

        spread_narrow = ci_narrow[:, 1] - ci_narrow[:, 0]
        spread_wide = ci_wide[:, 1] - ci_wide[:, 0]

        # 99%-CI muss breiter sein als 80%-CI
        assert np.all(spread_narrow > spread_wide), (
            "99%-CI (alpha=0.01) muss breiter sein als 80%-CI (alpha=0.20); "
            f"99%-CI spread mean={spread_narrow.mean():.2f}, "
            f"80%-CI spread mean={spread_wide.mean():.2f}"
        )

    def test_default_alpha_matches_95_percent(self, price_series):
        model = ARIMAAnalyzer()._simple_forecast_model(price_series)
        result_default = model.get_forecast(steps=5)          # alpha=0.05
        result_explicit = model.get_forecast(steps=5, alpha=0.05)

        ci_default = result_default.conf_int()
        ci_explicit = result_explicit.conf_int()

        np.testing.assert_array_almost_equal(ci_default, ci_explicit)

    def test_forecast_shape_correct(self, price_series):
        model = ARIMAAnalyzer()._simple_forecast_model(price_series)
        steps = 7
        result = model.get_forecast(steps=steps, alpha=0.05)
        ci = result.conf_int()
        assert len(result.predicted_mean) == steps
        assert ci.shape == (steps, 2)

    def test_conf_int_accepts_alpha_keyword_argument(self, price_series):
        """Regression: conf_int war lambda: conf und warf TypeError bei conf_int(alpha=...)."""
        model = ARIMAAnalyzer()._simple_forecast_model(price_series)
        result = model.get_forecast(steps=5)
        # Muss ohne TypeError aufrufbar sein (so wie _forecast es aufruft)
        ci = result.conf_int(alpha=0.05)
        assert ci.shape == (5, 2)

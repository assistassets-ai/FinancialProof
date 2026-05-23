"""
Regressionstests fuer protokollierte Analyse-Fehlerpfade.
"""
import asyncio
import importlib
import logging

import numpy as np
import pandas as pd
import pytest

from analysis.base import AnalysisParameters, AnalysisTimeframe


@pytest.fixture
def long_ohlcv_data():
    """Erstellt ausreichend lange OHLCV-Daten fuer alle Analyzer."""
    periods = 240
    close = np.linspace(100.0, 150.0, periods)
    return pd.DataFrame(
        {
            "Open": close - 0.5,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": np.linspace(1_000_000.0, 1_500_000.0, periods),
        }
    )


@pytest.mark.parametrize(
    ("module_name", "class_name", "failing_method", "expected_log"),
    [
        (
            "analysis.ml.random_forest",
            "RandomForestAnalyzer",
            "_prepare_features",
            "Random-Forest-Analyse fuer AAPL fehlgeschlagen",
        ),
        (
            "analysis.ml.neural_net",
            "NeuralNetAnalyzer",
            "_prepare_sequences",
            "Neural-Network-Analyse fuer AAPL fehlgeschlagen",
        ),
        (
            "analysis.statistical.monte_carlo",
            "MonteCarloAnalyzer",
            "_run_simulation",
            "Monte-Carlo-Analyse fuer AAPL fehlgeschlagen",
        ),
        (
            "analysis.statistical.mean_reversion",
            "MeanReversionAnalyzer",
            "_calculate_metrics",
            "Mean-Reversion-Analyse fuer AAPL fehlgeschlagen",
        ),
        (
            "analysis.statistical.arima",
            "ARIMAAnalyzer",
            "_fit_arima",
            "ARIMA-Analyse fuer AAPL fehlgeschlagen",
        ),
    ],
)
def test_analyzer_failures_are_logged(
    module_name,
    class_name,
    failing_method,
    expected_log,
    long_ohlcv_data,
    monkeypatch,
    caplog,
):
    """Interne Analyzer-Fehler liefern ein Fehlerresultat und werden geloggt."""
    module = importlib.import_module(module_name)
    analyzer_cls = getattr(module, class_name)

    def fail(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(analyzer_cls, failing_method, fail)
    caplog.set_level(logging.ERROR, logger=module_name)

    analyzer = analyzer_cls()
    result = asyncio.run(
        analyzer.analyze(
            AnalysisParameters(
                symbol="AAPL",
                data=long_ohlcv_data,
                timeframe=AnalysisTimeframe.MEDIUM,
            )
        )
    )

    assert result.error == "boom"
    assert expected_log in caplog.text


def test_arima_analysis_uses_descriptive_signal_types(long_ohlcv_data, monkeypatch):
    """ARIMA signalisiert nur deskriptive Mustertypen statt Kauf-/Verkaufstermini."""
    module = importlib.import_module("analysis.statistical.arima")
    analyzer = module.ARIMAAnalyzer()

    class DummyForecastModel:
        _best_order = (1, 0, 1)

    def fake_fit_arima(data):
        return DummyForecastModel()

    def fake_forecast(_model, steps, confidence):
        return (
            np.array([200.0, 210.0]),
            np.array([[170.0, 230.0], [175.0, 235.0]]),
        )

    monkeypatch.setattr(analyzer, "_fit_arima", fake_fit_arima)
    monkeypatch.setattr(analyzer, "_forecast", fake_forecast)

    result = asyncio.run(
        analyzer.analyze(
            AnalysisParameters(
                symbol="AAPL",
                data=long_ohlcv_data,
                timeframe=AnalysisTimeframe.MEDIUM,
            )
        )
    )

    assert result.error is None
    assert result.recommendation == "bullish"
    assert result.signals
    assert all(signal["type"] == "bullish" for signal in result.signals)
    assert "buy" not in str(result.signals)


def test_monte_carlo_analysis_handles_range_index_data(long_ohlcv_data, monkeypatch):
    """Monte-Carlo erzeugt Forecast-Daten auch ohne DatetimeIndex."""
    module = importlib.import_module("analysis.statistical.monte_carlo")
    analyzer = module.MonteCarloAnalyzer()

    def fake_run_simulation(start_price, mu, sigma, days, num_simulations):
        paths = np.tile(
            np.linspace(start_price, start_price * 1.02, days),
            (num_simulations, 1),
        )
        final_prices = paths[:, -1]
        return module.SimulationResult(
            final_prices=final_prices,
            paths=paths,
            var_95=-0.05,
            var_99=-0.08,
            cvar_95=-0.06,
            expected_return=0.01,
            probability_profit=0.6,
        )

    monkeypatch.setattr(analyzer, "_run_simulation", fake_run_simulation)

    result = asyncio.run(
        analyzer.analyze(
            AnalysisParameters(
                symbol="AAPL",
                data=long_ohlcv_data,
                timeframe=AnalysisTimeframe.MEDIUM,
                custom_params={"num_simulations": 12},
            )
        )
    )

    assert result.error is None
    assert result.chart_data is not None
    assert len(result.predictions["dates"]) == analyzer.DEFAULT_DAYS[AnalysisTimeframe.MEDIUM]

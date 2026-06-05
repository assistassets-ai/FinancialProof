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


def test_random_forest_prepare_features_returns_current_row_for_prediction():
    """_prepare_features gibt X_predict als letzten (aktuellsten) Datenpunkt zurück."""
    module = importlib.import_module("analysis.ml.random_forest")
    analyzer = module.RandomForestAnalyzer()

    periods = 200
    close = np.linspace(100.0, 150.0, periods)
    df = pd.DataFrame(
        {
            "Open": close - 0.5,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": np.linspace(1_000_000.0, 1_500_000.0, periods),
        }
    )

    X, y, feature_names, X_predict = analyzer._prepare_features(df, prediction_days=1)

    # X_predict darf nicht dieselbe letzte Zeile wie X haben
    assert X_predict.shape[0] == 1
    assert not np.array_equal(X_predict, X[-1:]), (
        "X_predict muss die aktuellste Zeile sein, nicht die letzte Trainingszeile"
    )


def test_mean_reversion_uses_descriptive_signal_types(long_ohlcv_data):
    """MeanReversionAnalyzer signalisiert nur deskriptive Mustertypen statt Kauf-/Verkaufstermini."""
    module = importlib.import_module("analysis.statistical.mean_reversion")
    analyzer = module.MeanReversionAnalyzer()

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
    assert result.recommendation in {"bullish", "bearish", "neutral"}
    assert result.signals
    assert all(signal["type"] in {"bullish", "bearish", "neutral"} for signal in result.signals)
    assert "buy" not in str(result.signals)
    assert "sell" not in str(result.signals)


@pytest.mark.parametrize("module_name,class_name", [
    ("analysis.ml.random_forest", "RandomForestAnalyzer"),
    ("analysis.ml.neural_net", "NeuralNetAnalyzer"),
])
def test_ml_analyzer_uses_descriptive_signal_types(module_name, class_name, long_ohlcv_data):
    """ML-Analyzer signalisieren nur deskriptive Mustertypen statt Kauf-/Verkaufstermini."""
    module = importlib.import_module(module_name)
    analyzer = getattr(module, class_name)()

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
    assert result.recommendation in {"bullish", "bearish", "neutral"}
    assert result.signals
    assert all(signal["type"] in {"bullish", "bearish", "neutral"} for signal in result.signals)
    assert "buy" not in str(result.signals)
    assert "sell" not in str(result.signals)


def test_arima_build_result_handles_zero_current_price(monkeypatch):
    """_build_result darf bei current_price==0 keinen ZeroDivisionError werfen."""
    module = importlib.import_module("analysis.statistical.arima")
    analyzer = module.ARIMAAnalyzer()

    prices = pd.Series(np.zeros(100))
    forecast = np.array([1.0, 2.0, 3.0])
    conf_int = np.array([[0.5, 1.5], [1.5, 2.5], [2.5, 3.5]])

    class DummyModel:
        _best_order = (1, 0, 1)

    result = analyzer._build_result(
        "TEST", prices, forecast, conf_int,
        DummyModel(), AnalysisTimeframe.SHORT
    )
    assert result.data["change_percent"] == 0.0


@pytest.mark.parametrize("module_name,class_name", [
    ("analysis.nlp.sentiment", "SentimentAnalyzer"),
    ("analysis.statistical.monte_carlo", "MonteCarloAnalyzer"),
])
def test_analyzer_build_result_uses_descriptive_recommendation(module_name, class_name):
    """Sentiment- und Monte-Carlo-Analyzer verwenden neutrale Muster-Polaritaeten."""
    module = importlib.import_module(module_name)
    analyzer = getattr(module, class_name)()

    ALLOWED = {"bullish", "bearish", "neutral"}

    if class_name == "SentimentAnalyzer":
        articles = [{"title": "Stock surges on strong earnings", "publisher": "Reuters",
                     "link": "", "published": 0, "type": "news",
                     "sentiment_score": 0.8, "sentiment_label": "positiv"}]
        metrics = {"average": 0.8, "median": 0.8, "std": 0.1,
                   "positive_count": 1, "negative_count": 0, "neutral_count": 0,
                   "positive_pct": 100.0, "negative_pct": 0.0, "neutral_pct": 0.0,
                   "total_articles": 1}
        result = analyzer._build_result("AAPL", articles, metrics)
    else:
        SimulationResult = importlib.import_module(module_name).SimulationResult
        sim = SimulationResult(
            final_prices=np.array([110.0, 115.0]),
            paths=np.ones((2, 10)) * 110.0,
            var_95=-0.03,
            var_99=-0.05,
            cvar_95=-0.04,
            expected_return=0.05,
            probability_profit=0.7,
        )
        result = analyzer._build_result(
            "AAPL",
            pd.Series(np.linspace(100.0, 105.0, 50)),
            sim,
            10000.0,
            10,
            AnalysisTimeframe.MEDIUM,
        )

    assert result.recommendation in ALLOWED
    assert all(s["type"] in ALLOWED for s in result.signals)
    assert "buy" not in str(result.signals)
    assert "sell" not in str(result.signals)

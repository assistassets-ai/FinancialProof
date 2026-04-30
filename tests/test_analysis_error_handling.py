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

"""
Tests fuer Analyse-Basislogik und Registry.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from analysis.base import (
    AnalysisCategory,
    AnalysisParameters,
    AnalysisResult,
    AnalysisTimeframe,
    BaseAnalyzer,
    MethodSelector,
)
import analysis.registry as registry_module
from analysis.registry import AnalysisRegistry, get_analyzer_for_ui


class DummyAnalyzer(BaseAnalyzer):
    """Kleiner Analyzer fuer Registry- und Basis-Tests."""

    name = "dummy"
    display_name = "Dummy Analyzer"
    category = AnalysisCategory.STATISTICAL
    description = "Dummy test analyzer"

    async def analyze(self, params: AnalysisParameters) -> AnalysisResult:
        return self.create_empty_result(self.name, params.symbol, "not implemented")


class MomentumAnalyzer(DummyAnalyzer):
    """Zweiter Analyzer fuer UI-Gruppierung."""

    name = "momentum"
    display_name = "Momentum Analyzer"
    category = AnalysisCategory.ML
    description = "Momentum test analyzer"


@pytest.fixture(autouse=True)
def clear_registry_state():
    """Stellt pro Test ein sauberes Registry-Setup sicher."""
    AnalysisRegistry.clear()
    old_initialized = registry_module._initialized
    registry_module._initialized = False
    yield
    AnalysisRegistry.clear()
    registry_module._initialized = old_initialized


@pytest.fixture
def valid_ohlcv():
    """Erstellt einen gueltigen OHLCV-DataFrame fuer Analyzer-Tests."""
    periods = 60
    close = np.linspace(100.0, 140.0, periods)
    return pd.DataFrame(
        {
            "Open": close - 1.0,
            "High": close + 1.0,
            "Low": close - 2.0,
            "Close": close,
            "Volume": np.linspace(1_000.0, 2_000.0, periods),
        }
    )


class TestBaseAnalyzer:
    def test_validate_data_reports_missing_columns_and_short_length(self):
        analyzer = DummyAnalyzer()
        incomplete = pd.DataFrame(
            {
                "Open": [100.0, 101.0],
                "High": [102.0, 103.0],
                "Low": [99.0, 100.0],
                "Close": [101.0, 102.0],
            }
        )

        errors = analyzer.validate_data(incomplete)

        assert any("Fehlende Spalten" in error for error in errors)
        assert any("Zu wenig Datenpunkte" in error for error in errors)

    def test_validate_data_reports_missing_close_without_key_error(self):
        analyzer = DummyAnalyzer()
        incomplete = pd.DataFrame(
            {
                "Open": [100.0, 101.0],
                "High": [102.0, 103.0],
                "Low": [99.0, 100.0],
                "Volume": [1_000.0, 1_100.0],
            }
        )

        errors = analyzer.validate_data(incomplete)

        assert any("Fehlende Spalten: Close" in error for error in errors)
        assert any("Zu wenig Datenpunkte" in error for error in errors)

    def test_validate_data_reports_many_missing_close_values(self, valid_ohlcv):
        analyzer = DummyAnalyzer()
        valid_ohlcv.loc[:9, "Close"] = np.nan

        errors = analyzer.validate_data(valid_ohlcv)

        assert "Zu viele fehlende Werte in den Kursdaten" in errors

    def test_create_empty_result_sets_error_payload(self):
        result = DummyAnalyzer.create_empty_result("dummy", "AAPL", "network error")

        assert result.analysis_type == "dummy"
        assert result.symbol == "AAPL"
        assert result.error == "network error"
        assert result.confidence == 0.0
        assert result.summary == "Analyse konnte nicht durchgeführt werden"
        assert isinstance(result.timestamp, datetime)


class TestMethodSelector:
    def test_select_methods_uses_ml_model_when_available(self, valid_ohlcv):
        selector = MethodSelector()

        class StubModel:
            def predict(self, data, methods):
                return ["stubbed"]

        selector.set_ml_model(StubModel())

        result = selector.select_methods(valid_ohlcv, ["sentiment", "arima"])

        assert result == ["stubbed"]

    def test_select_methods_picks_trend_and_ml_methods(self):
        close = pd.Series(np.linspace(100.0, 220.0, 260))
        data = pd.DataFrame({"Close": close})
        selector = MethodSelector()

        result = selector.select_methods(
            data,
            ["sentiment", "arima", "neural_network", "correlation"],
        )

        assert "sentiment" in result
        assert "arima" in result
        assert "neural_network" in result
        assert "correlation" in result

    def test_select_methods_detects_sideways_market(self):
        close = pd.Series(100.0 + np.sin(np.linspace(0, 8 * np.pi, 120)))
        data = pd.DataFrame({"Close": close})
        selector = MethodSelector()

        result = selector.select_methods(data, ["mean_reversion"])

        assert result == ["mean_reversion"]

    def test_select_methods_falls_back_to_first_available(self):
        close = pd.Series([100.0] * 40)
        data = pd.DataFrame({"Close": close})
        selector = MethodSelector()

        result = selector.select_methods(data, ["custom_method"])

        assert result == ["custom_method"]

    def test_select_methods_handles_empty_data_without_crash(self):
        data = pd.DataFrame()
        selector = MethodSelector()

        result = selector.select_methods(data, ["sentiment", "arima"])

        assert result == ["sentiment"]

    def test_select_methods_handles_missing_close_column(self):
        data = pd.DataFrame({"Open": [1, 2, 3], "CloseLike": [1, 2, 3]})
        selector = MethodSelector()

        result = selector.select_methods(data, ["sentiment", "arima"])

        assert result == ["sentiment"]


class TestAnalysisRegistry:
    def test_register_duplicate_name_raises_value_error(self):
        AnalysisRegistry.register(DummyAnalyzer)

        with pytest.raises(ValueError, match="bereits registriert"):
            AnalysisRegistry.register(DummyAnalyzer)

    def test_get_returns_singleton_instance_and_resets_state(self):
        AnalysisRegistry.register(DummyAnalyzer)

        first = AnalysisRegistry.get("dummy")
        first.set_progress(80)
        first.request_cancel()

        second = AnalysisRegistry.get("dummy")

        assert first is second
        assert second.get_progress() == 0
        assert not second.is_cancel_requested()

    def test_ensure_initialized_runs_registration_only_once(self, monkeypatch):
        calls = {"count": 0}

        def fake_register_all():
            calls["count"] += 1

        monkeypatch.setattr(registry_module, "_register_all_analyzers", fake_register_all)
        registry_module._initialized = False

        registry_module.ensure_initialized()
        registry_module.ensure_initialized()

        assert calls["count"] == 1

    def test_get_analyzer_for_ui_groups_only_present_categories(self, monkeypatch):
        AnalysisRegistry.register(DummyAnalyzer)
        AnalysisRegistry.register(MomentumAnalyzer)
        monkeypatch.setattr(registry_module, "_initialized", True)

        grouped = get_analyzer_for_ui()

        assert set(grouped.keys()) == {"statistical", "ml"}
        assert grouped["statistical"]["analyzers"][0]["name"] == "dummy"
        assert grouped["ml"]["analyzers"][0]["name"] == "momentum"

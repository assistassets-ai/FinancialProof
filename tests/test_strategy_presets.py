"""
Tests fuer Analyse-Presets und die deskriptive Regel-Engine.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from config import Config


@pytest.fixture
def strategy_context():
    """Erstellt eine temporaere Preset-/Strategie-Testumgebung."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Config.__new__(Config)
        cfg.BASE_DIR = Path(tmpdir)
        cfg.DATA_DIR = Path(tmpdir) / "data"
        cfg.DB_PATH = cfg.DATA_DIR / "test.db"
        cfg.SECRETS_PATH = cfg.DATA_DIR / ".secrets"
        cfg.DATA_DIR.mkdir(exist_ok=True)

        with patch("core.database.config", cfg):
            from core.database import DatabaseManager
            from core.strategy import StrategyEngine
            from core.strategy_manager import StrategyManager, StrategyRuleError

            database = DatabaseManager()
            manager = StrategyManager(database)
            engine = StrategyEngine(manager)
            yield {
                "db": database,
                "manager": manager,
                "engine": engine,
                "rule_error": StrategyRuleError,
            }


def test_strategy_schema_tables_exist(strategy_context):
    database = strategy_context["db"]

    with database.get_connection() as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert "strategies" in tables
    assert "analysis_runs" in tables


def test_strategy_manager_saves_and_activates_asset_specific_presets(strategy_context):
    manager = strategy_context["manager"]

    stock_aggressive = manager.save_preset(
        name="Stock Aggressiv",
        asset_type="stock",
        rules={"min_confidence": 0.9, "required_signals": ["bullish"]},
        is_active=True,
    )
    stock_defensive = manager.save_preset(
        name="Stock Defensiv",
        asset_type="stock",
        rules={"min_confidence": 0.6},
        is_active=False,
    )
    crypto_active = manager.save_preset(
        name="Krypto Aktiv",
        asset_type="crypto",
        rules={"min_confidence": 0.7},
        is_active=True,
    )

    active_stock = manager.get_active_preset("STOCK")
    active_crypto = manager.get_active_preset("CRYPTO")
    all_stock_presets = manager.list_presets(asset_type="STOCK")

    assert stock_aggressive.id is not None
    assert stock_defensive.id is not None
    assert crypto_active.id is not None
    assert active_stock.name == "Stock Aggressiv"
    assert active_crypto.name == "Krypto Aktiv"
    assert [preset.name for preset in all_stock_presets] == [
        "Stock Aggressiv",
        "Stock Defensiv",
    ]

    reactivated = manager.activate_preset(stock_defensive.id)
    assert reactivated is not None
    assert reactivated.name == "Stock Defensiv"
    assert manager.get_active_preset("stock").name == "Stock Defensiv"


def test_strategy_manager_parses_flat_and_json_rules(strategy_context):
    manager = strategy_context["manager"]

    flat_rules = manager.parse_rules(
        {
            "min_confidence": 0.85,
            "required_signals": ["bullish", "bullish"],
            "min_volume_ratio": 1.25,
        }
    )
    json_rules = manager.parse_rules(
        json.dumps(
            {
                "pattern_rules": {"max_rsi": 55},
                "risk_notes": {"volatility_warning_percent": 7.5},
            }
        )
    )

    assert flat_rules["pattern_rules"]["min_confidence"] == pytest.approx(0.85)
    assert flat_rules["pattern_rules"]["required_signals"] == ["bullish"]
    assert flat_rules["pattern_rules"]["min_volume_ratio"] == pytest.approx(1.25)
    assert json_rules["pattern_rules"]["max_rsi"] == pytest.approx(55.0)
    assert json_rules["risk_notes"]["volatility_warning_percent"] == pytest.approx(7.5)


def test_strategy_manager_rejects_invalid_rule_values(strategy_context):
    manager = strategy_context["manager"]
    rule_error = strategy_context["rule_error"]

    with pytest.raises(rule_error):
        manager.parse_rules({"min_confidence": 1.2})

    with pytest.raises(rule_error):
        manager.save_preset(
            name="",
            asset_type="stock",
            rules={"min_confidence": 0.5},
        )


def test_strategy_engine_evaluates_and_persists_analysis_runs(strategy_context):
    manager = strategy_context["manager"]
    engine = strategy_context["engine"]
    database = strategy_context["db"]

    preset = manager.save_preset(
        name="Momentum",
        asset_type="stock",
        rules={
            "pattern_rules": {
                "min_confidence": 0.7,
                "max_rsi": 65,
                "required_signals": ["bullish"],
                "min_volume_ratio": 1.1,
            }
        },
        is_active=True,
    )

    market_data = pd.DataFrame(
        {
            "RSI": [48.0, 55.0, 60.0],
            "Volume": [100.0, 110.0, 180.0],
        }
    )
    analysis_result = {
        "job_id": 42,
        "confidence": 0.83,
        "signals": [{"signal": "bullish"}],
    }

    result = engine.evaluate(analysis_result, market_data, "AAPL")
    runs = database.get_analysis_runs(symbol="AAPL")

    assert preset.id is not None
    assert result["passed"] is True
    assert result["pattern_class"] == "bullish"
    assert result["reason"] == "Historisches Muster erfüllt"
    assert len(runs) == 1
    assert runs[0].strategy_id == preset.id
    assert runs[0].job_id == 42


def test_strategy_engine_marks_failed_rules_as_neutral(strategy_context):
    manager = strategy_context["manager"]
    engine = strategy_context["engine"]

    preset = manager.save_preset(
        name="Vorsichtig",
        asset_type="stock",
        rules={
            "min_confidence": 0.8,
            "required_signals": ["bullish"],
            "max_rsi": 50,
        },
        is_active=True,
    )

    market_data = pd.DataFrame(
        {
            "RSI": [45.0, 58.0],
            "Volume": [120.0, 118.0],
        }
    )

    result = engine.evaluate(
        {"confidence": 0.6, "signals": [{"signal": "bearish"}]},
        market_data,
        "AAPL",
        strategy=preset,
        persist=False,
    )

    assert result["passed"] is False
    assert result["pattern_class"] == "neutral"
    assert "Unsicher" in result["reason"]
    assert "RSI zu hoch" in result["reason"]

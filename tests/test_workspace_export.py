from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from config import Config, config


def _build_temp_config(tmpdir: str) -> Config:
    cfg = Config.__new__(Config)
    cfg.BASE_DIR = Path(tmpdir)
    cfg.DATA_DIR = Path(tmpdir) / "data"
    cfg.DB_PATH = cfg.DATA_DIR / "financial.db"
    cfg.SECRETS_PATH = cfg.DATA_DIR / ".secrets"
    cfg.LOG_FILE = cfg.DATA_DIR / "financialproof.log"
    cfg.APP_NAME = config.APP_NAME
    cfg.APP_VERSION = config.APP_VERSION
    cfg.DEFAULT_TICKER = config.DEFAULT_TICKER
    cfg.DEFAULT_PERIOD = config.DEFAULT_PERIOD
    cfg.DATA_DIR.mkdir(exist_ok=True)
    return cfg


def test_build_workspace_export_collects_watchlist_presets_and_snapshots():
    with TemporaryDirectory() as tmpdir:
        cfg = _build_temp_config(tmpdir)

        with patch("core.database.config", cfg):
            from core.database import (
                AnalysisResult,
                DatabaseManager,
                Job,
                JobStatus,
                StrategyPreset,
                WatchlistItem,
            )
            from core.workspace_export import build_workspace_export

            database = DatabaseManager()
            database.add_to_watchlist(
                WatchlistItem(
                    symbol="aapl",
                    name="Apple Inc.",
                    asset_type="stock",
                    notes="Überwachen",
                )
            )
            database.save_strategy(
                StrategyPreset(
                    name="ETF defensiv",
                    asset_type="ETF",
                    rules={
                        "pattern_rules": {"min_confidence": 0.7},
                        "risk_notes": {"volatility_warning_percent": 4.5},
                    },
                    is_active=True,
                )
            )

            job_id = database.create_job(
                Job(
                    symbol="AAPL",
                    analysis_type="arima",
                    parameters={"timeframe": "6mo"},
                    status=JobStatus.PENDING,
                )
            )
            database.update_job_status(job_id, JobStatus.COMPLETED, progress=100)
            database.save_result(
                AnalysisResult(
                    job_id=job_id,
                    summary="Historische Musteranalyse",
                    data={
                        "RSI": 58.4,
                        "volatility_percent": 7.6,
                    },
                    signals=[{"type": "bullish"}],
                    confidence=0.78,
                )
            )

            payload = build_workspace_export(
                database=database,
                exported_at=datetime(2026, 6, 1, 10, 30, tzinfo=timezone.utc),
                app_version="test-build",
                disclaimer_meta={
                    "disclaimer_hash": "hash-123",
                    "disclaimer_version": "1.0",
                    "not_financial_advice": True,
                    "warnings": ["Keine Anlageberatung; nur historische Auswertung."],
                },
            )

    assert payload["schema"] == "financialproof-workspace-v1"
    assert payload["app"]["version"] == "test-build"
    assert payload["legal"]["disclaimer_hash"] == "hash-123"
    assert payload["watchlist"][0]["symbol"] == "AAPL"
    assert payload["watchlist"][0]["notes"] == "Überwachen"
    assert payload["analysis_presets"][0]["name"] == "ETF defensiv"
    assert payload["analysis_snapshots"][0]["timeframe"] == "6mo"
    assert payload["analysis_snapshots"][0]["pattern_class"] == "bullish"
    assert payload["analysis_snapshots"][0]["indicators"]["rsi"] == 58.4
    assert "Erhöhte Volatilität im Snapshot." in payload["analysis_snapshots"][0]["warnings"]


def test_build_workspace_export_json_preserves_umlauts_and_default_timeframe():
    with TemporaryDirectory() as tmpdir:
        cfg = _build_temp_config(tmpdir)

        with patch("core.database.config", cfg):
            from core.database import AnalysisResult, DatabaseManager, Job, JobStatus, WatchlistItem
            from core.workspace_export import build_workspace_export_json

            database = DatabaseManager()
            database.add_to_watchlist(
                WatchlistItem(
                    symbol="msci",
                    name="MSCI World ETF",
                    asset_type="etf",
                    notes="Für später prüfen",
                )
            )

            job_id = database.create_job(
                Job(
                    symbol="MSCI",
                    analysis_type="mean_reversion",
                    status=JobStatus.PENDING,
                )
            )
            database.update_job_status(job_id, JobStatus.COMPLETED, progress=100)
            database.save_result(
                AnalysisResult(
                    job_id=job_id,
                    summary="Neutrales Muster",
                    data={},
                    signals=[],
                    confidence=0.42,
                )
            )

            payload_json = build_workspace_export_json(
                database=database,
                disclaimer_meta={
                    "disclaimer_hash": "hash-456",
                    "disclaimer_version": "1.0",
                    "not_financial_advice": True,
                    "warnings": [],
                },
            )

    assert "Für später prüfen" in payload_json
    assert "financialproof-workspace-v1" in payload_json
    assert f'"timeframe": "{config.DEFAULT_PERIOD}"' in payload_json

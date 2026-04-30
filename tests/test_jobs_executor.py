"""
Tests fuer Job-Management und Job-Ausfuehrung.
"""
import asyncio
import importlib
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.base import AnalysisResult, AnalysisTimeframe


@pytest.fixture
def temp_config(tmp_path):
    """Erstellt eine temporaere Konfiguration fuer die Test-Datenbank."""
    from config import Config

    cfg = Config.__new__(Config)
    cfg.BASE_DIR = tmp_path
    cfg.DATA_DIR = tmp_path / "data"
    cfg.DB_PATH = cfg.DATA_DIR / "financial.db"
    cfg.SECRETS_PATH = cfg.DATA_DIR / ".secrets"
    cfg.DATA_DIR.mkdir(parents=True, exist_ok=True)
    return cfg


@pytest.fixture
def database_module(temp_config, monkeypatch):
    """Laedt core.database mit isoliertem DB-Pfad neu."""
    import config as config_module

    monkeypatch.setattr(config_module, "config", temp_config)
    module = importlib.import_module("core.database")
    return importlib.reload(module)


@pytest.fixture
def manager_module(database_module):
    """Laedt jobs.manager gegen die temporaere Datenbank."""
    module = importlib.import_module("jobs.manager")
    return importlib.reload(module)


@pytest.fixture
def executor_module(database_module, manager_module, monkeypatch):
    """Laedt jobs.executor ohne Analyzer-Heavy-Init neu."""
    import analysis.registry as registry_module

    monkeypatch.setattr(registry_module, "ensure_initialized", lambda: None)
    module = importlib.import_module("jobs.executor")
    return importlib.reload(module)


@pytest.fixture
def sample_market_data():
    """Erstellt einen kleinen gueltigen Marktdaten-DataFrame."""
    closes = [100.0, 101.5, 102.0, 103.2, 104.8, 105.5]
    return pd.DataFrame(
        {
            "Open": [value - 0.4 for value in closes],
            "High": [value + 0.6 for value in closes],
            "Low": [value - 0.8 for value in closes],
            "Close": closes,
            "Volume": [1_000_000, 1_100_000, 900_000, 950_000, 1_050_000, 1_200_000],
        }
    )


def _make_analysis_result(symbol: str, analysis_type: str = "dummy") -> AnalysisResult:
    """Erstellt ein kleines Analyse-Ergebnis fuer Tests."""
    return AnalysisResult(
        analysis_type=analysis_type,
        symbol=symbol,
        timestamp=datetime.now(),
        summary=f"{analysis_type} ready",
        confidence=0.82,
        data={"score": 7},
        signals=[{"kind": "info"}],
        predictions={"trend": "up"},
    )


class TestJobManager:
    def test_create_job_normalizes_symbol_and_defaults_to_pending(self, manager_module):
        job_id = manager_module.JobManager.create_job(
            "msft",
            "dummy",
            parameters={"timeframe": "short", "window": 12},
        )

        job = manager_module.JobManager.get_job(job_id)

        assert job.symbol == "MSFT"
        assert job.analysis_type == "dummy"
        assert job.status == manager_module.JobStatus.PENDING
        assert job.parameters == {"timeframe": "short", "window": 12}

    def test_cancel_job_only_pending_jobs_can_be_cancelled(self, manager_module):
        pending_id = manager_module.JobManager.create_job("AAPL", "dummy")
        running_id = manager_module.JobManager.create_job("TSLA", "dummy")
        manager_module.JobManager.start_job(running_id)

        assert manager_module.JobManager.cancel_job(pending_id) is True
        assert manager_module.JobManager.cancel_job(running_id) is False
        assert manager_module.JobManager.get_job(pending_id).status == manager_module.JobStatus.CANCELLED
        assert manager_module.JobManager.get_job(running_id).status == manager_module.JobStatus.RUNNING

    def test_save_result_serializes_predictions_and_object_signals(self, manager_module):
        job_id = manager_module.JobManager.create_job("NFLX", "dummy")
        result = AnalysisResult(
            analysis_type="dummy",
            symbol="NFLX",
            timestamp=datetime.now(),
            summary="finished",
            confidence=0.66,
            data={"metric": 1},
            signals=[SimpleNamespace(kind="alert", strength=0.5)],
            predictions={"target": 123.45},
        )

        manager_module.JobManager.save_result(job_id, result)
        stored = manager_module.JobManager.get_results_for_job(job_id)

        assert len(stored) == 1
        assert stored[0].summary == "finished"
        assert stored[0].details == "{'target': 123.45}"
        assert stored[0].signals == [{"kind": "alert", "strength": 0.5}]


class TestJobQueue:
    def test_recover_stale_jobs_marks_running_jobs_failed(self, manager_module):
        job_id = manager_module.JobManager.create_job("SAP", "dummy")
        manager_module.JobManager.start_job(job_id)

        manager_module.JobQueue()
        recovered = manager_module.JobManager.get_job(job_id)

        assert recovered.status == manager_module.JobStatus.FAILED
        assert "Crash-Recovery" in recovered.error_message

    def test_dequeue_marks_job_running_and_caches_job(self, manager_module):
        job_id = manager_module.JobManager.create_job("AMD", "dummy")
        queue = manager_module.JobQueue()

        job = queue.dequeue()

        assert job.id == job_id
        assert queue.is_job_running(job_id) is True
        assert manager_module.JobManager.get_job(job_id).status == manager_module.JobStatus.RUNNING

    def test_mark_complete_persists_result_and_clears_running_cache(self, manager_module):
        job_id = manager_module.JobManager.create_job("NVDA", "dummy")
        queue = manager_module.JobQueue()
        queue.dequeue()

        queue.mark_complete(job_id, _make_analysis_result("NVDA"))

        stored_results = manager_module.JobManager.get_results_for_job(job_id)
        assert len(stored_results) == 1
        assert manager_module.JobManager.get_job(job_id).status == manager_module.JobStatus.COMPLETED
        assert queue.is_job_running(job_id) is False

    def test_mark_failed_persists_error_and_clears_running_cache(self, manager_module):
        job_id = manager_module.JobManager.create_job("ORCL", "dummy")
        queue = manager_module.JobQueue()
        queue.dequeue()

        queue.mark_failed(job_id, "network timeout")
        failed_job = manager_module.JobManager.get_job(job_id)

        assert failed_job.status == manager_module.JobStatus.FAILED
        assert failed_job.error_message == "network timeout"
        assert queue.is_job_running(job_id) is False


class TestJobExecutor:
    def test_execute_job_completes_successfully_with_valid_timeframe(
        self,
        executor_module,
        manager_module,
        sample_market_data,
        monkeypatch,
    ):
        job_id = manager_module.JobManager.create_job(
            "aapl",
            "dummy",
            parameters={"timeframe": "long", "alpha": 2},
        )
        captured = {}

        class FakeAnalyzer:
            async def analyze(self, params):
                captured["symbol"] = params.symbol
                captured["timeframe"] = params.timeframe
                captured["custom_params"] = params.custom_params
                return _make_analysis_result(params.symbol)

        monkeypatch.setattr(
            executor_module.DataProvider,
            "get_market_data",
            staticmethod(lambda symbol, period="1y": sample_market_data),
        )
        monkeypatch.setattr(executor_module, "get_analyzer", lambda name: FakeAnalyzer())

        executor = executor_module.JobExecutor()
        success = asyncio.run(executor.execute_job(job_id))
        stored_results = manager_module.JobManager.get_results_for_job(job_id)
        job = manager_module.JobManager.get_job(job_id)

        assert success is True
        assert captured["symbol"] == "AAPL"
        assert captured["timeframe"] == AnalysisTimeframe.LONG
        assert captured["custom_params"] == {"timeframe": "long", "alpha": 2}
        assert job.status == manager_module.JobStatus.COMPLETED
        assert job.progress == 100
        assert len(stored_results) == 1

    def test_execute_job_falls_back_to_medium_for_invalid_timeframe(
        self,
        executor_module,
        manager_module,
        sample_market_data,
        monkeypatch,
    ):
        job_id = manager_module.JobManager.create_job(
            "meta",
            "dummy",
            parameters={"timeframe": "invalid-value"},
        )
        captured = {}

        class FakeAnalyzer:
            async def analyze(self, params):
                captured["timeframe"] = params.timeframe
                return _make_analysis_result(params.symbol)

        monkeypatch.setattr(
            executor_module.DataProvider,
            "get_market_data",
            staticmethod(lambda symbol, period="1y": sample_market_data),
        )
        monkeypatch.setattr(executor_module, "get_analyzer", lambda name: FakeAnalyzer())

        executor = executor_module.JobExecutor()
        success = asyncio.run(executor.execute_job(job_id))

        assert success is True
        assert captured["timeframe"] == AnalysisTimeframe.MEDIUM

    def test_execute_job_fails_when_market_data_missing(self, executor_module, manager_module, monkeypatch):
        job_id = manager_module.JobManager.create_job("BABA", "dummy")

        monkeypatch.setattr(
            executor_module.DataProvider,
            "get_market_data",
            staticmethod(lambda symbol, period="1y": pd.DataFrame()),
        )

        executor = executor_module.JobExecutor()
        success = asyncio.run(executor.execute_job(job_id))
        job = manager_module.JobManager.get_job(job_id)

        assert success is False
        assert job.status == manager_module.JobStatus.FAILED
        assert job.error_message == "Keine Marktdaten verfügbar"

    def test_execute_job_fails_when_analyzer_missing(
        self,
        executor_module,
        manager_module,
        sample_market_data,
        monkeypatch,
    ):
        job_id = manager_module.JobManager.create_job("IBM", "unknown")

        monkeypatch.setattr(
            executor_module.DataProvider,
            "get_market_data",
            staticmethod(lambda symbol, period="1y": sample_market_data),
        )
        monkeypatch.setattr(executor_module, "get_analyzer", lambda name: None)

        executor = executor_module.JobExecutor()
        success = asyncio.run(executor.execute_job(job_id))
        job = manager_module.JobManager.get_job(job_id)

        assert success is False
        assert job.status == manager_module.JobStatus.FAILED
        assert job.error_message == "Analyzer 'unknown' nicht gefunden"

    def test_execute_all_pending_counts_successes_and_failures(self, executor_module, manager_module):
        job_ids = [
            manager_module.JobManager.create_job("AAPL", "dummy"),
            manager_module.JobManager.create_job("MSFT", "dummy"),
            manager_module.JobManager.create_job("TSLA", "dummy"),
        ]
        seen = []

        async def fake_execute(job_id):
            seen.append(job_id)
            return job_id != job_ids[-1]

        executor = executor_module.JobExecutor()
        executor.execute_job = fake_execute

        summary = asyncio.run(executor.execute_all_pending(max_jobs=5))

        assert seen == job_ids
        assert summary == {"completed": 2, "failed": 1, "total": 3}

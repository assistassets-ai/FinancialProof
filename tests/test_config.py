"""
Tests fuer Konfigurationsmodul
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from config import APIKeyManager, Config, UIText


class TestConfig:
    def test_default_values(self):
        cfg = Config()
        assert cfg.APP_NAME == "FinancialProof"
        assert cfg.DEFAULT_TICKER == "AAPL"
        assert cfg.DEFAULT_PERIOD == "1y"
        assert cfg.CHART_HEIGHT == 600

    def test_paths_initialized(self):
        cfg = Config()
        assert cfg.DATA_DIR == cfg.BASE_DIR / "data"
        assert cfg.DB_PATH == cfg.DATA_DIR / "financial.db"
        assert cfg.LOG_FILE == cfg.DATA_DIR / "financialproof.log"

    def test_cache_ttl_values(self):
        cfg = Config()
        assert cfg.CACHE_TTL_MARKET_DATA == 3600
        assert cfg.CACHE_TTL_TICKER_INFO == 86400
        assert cfg.CACHE_TTL_NEWS == 1800

    def test_default_sma_periods(self):
        cfg = Config()
        assert cfg.DEFAULT_SMA_PERIODS == [20, 50, 200]

    def test_log_level_can_be_overridden_by_environment(self, monkeypatch):
        monkeypatch.setenv("FINANCIALPROOF_LOG_LEVEL", "warning")

        cfg = Config()

        assert cfg.LOG_LEVEL == "WARNING"

    def test_corrupted_secrets_file_is_ignored(self, tmp_path):
        cfg = Config(BASE_DIR=tmp_path)
        manager = APIKeyManager(cfg)
        cfg.SECRETS_PATH.write_text("{broken json", encoding="utf-8")

        assert manager.get_api_key("twitter") is None

    def test_save_api_key_recovers_from_corrupted_secrets_file(self, tmp_path):
        cfg = Config(BASE_DIR=tmp_path)
        manager = APIKeyManager(cfg)
        cfg.SECRETS_PATH.write_text("[]", encoding="utf-8")

        manager.save_api_key("twitter", "token-123")

        assert manager.get_api_key("twitter") == "token-123"
        assert json.loads(cfg.SECRETS_PATH.read_text(encoding="utf-8"))["twitter"]

    def test_save_secrets_writes_utf8(self, tmp_path):
        cfg = Config(BASE_DIR=tmp_path)
        manager = APIKeyManager(cfg)

        # Service-Name mit Nicht-ASCII prüft UTF-8-Schreibkonsistenz
        manager.save_api_key("test_service", "wert-äöü")

        raw = cfg.SECRETS_PATH.read_bytes()
        assert b"\xe4" not in raw  # kein CP1252-Byte für 'ä'
        text = cfg.SECRETS_PATH.read_text(encoding="utf-8")
        assert json.loads(text)  # valides JSON in UTF-8


class TestUIText:
    def test_periods_mapping(self):
        texts = UIText()
        assert "1y" in texts.PERIODS
        assert "1mo" in texts.PERIODS
        assert texts.PERIODS["1y"] == "1 Jahr"

    def test_required_text_attributes(self):
        texts = UIText()
        assert texts.APP_TITLE
        assert texts.MSG_NO_DATA
        assert texts.MSG_LOADING

    def test_job_status_texts(self):
        texts = UIText()
        assert texts.JOB_PENDING == "Wartend"
        assert texts.JOB_COMPLETED == "Abgeschlossen"
        assert texts.JOB_FAILED == "Fehlgeschlagen"

    def test_job_status_texts_accessible_via_getattr_not_instance_dict(self):
        """Klassenattribute von UIText liegen NICHT in __dict__ — getattr verwenden."""
        texts = UIText()
        assert texts.__dict__.get("JOB_PENDING") is None
        assert getattr(texts, "JOB_PENDING", None) == "Wartend"
        assert getattr(texts, "JOB_COMPLETED", None) == "Abgeschlossen"
        assert getattr(texts, "JOB_FAILED", None) == "Fehlgeschlagen"

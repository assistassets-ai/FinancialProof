"""
Tests fuer zentrales Logging.
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logging_utils import configure_logging, reset_logging


class TestLoggingUtils:
    def teardown_method(self):
        reset_logging()

    def test_configure_logging_writes_to_file(self, tmp_path):
        """configure_logging schreibt Meldungen in die konfigurierte Log-Datei."""
        log_file = tmp_path / "financialproof.log"

        root_logger = configure_logging(log_file=log_file, level="INFO", force=True)
        logging.getLogger("tests.logging").info("logging smoke test")

        for handler in root_logger.handlers:
            if hasattr(handler, "flush"):
                handler.flush()

        assert log_file.exists()
        assert "logging smoke test" in log_file.read_text(encoding="utf-8")

    def test_configure_logging_is_idempotent(self, tmp_path):
        """Mehrfaches Konfigurieren darf keine doppelten FinancialProof-Handler erzeugen."""
        log_file = tmp_path / "financialproof.log"

        root_logger = configure_logging(log_file=log_file, level="INFO", force=True)
        configure_logging(log_file=log_file, level="DEBUG")

        handler_names = [
            getattr(handler, "name", "")
            for handler in root_logger.handlers
            if getattr(handler, "name", "") in {"financialproof_console", "financialproof_file"}
        ]

        assert handler_names.count("financialproof_console") == 1
        assert handler_names.count("financialproof_file") == 1

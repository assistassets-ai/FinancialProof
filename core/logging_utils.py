"""
FinancialProof - Logging-Hilfsfunktionen
Zentrale Initialisierung fuer Datei- und Konsolen-Logging.
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union


CONSOLE_HANDLER_NAME = "financialproof_console"
FILE_HANDLER_NAME = "financialproof_file"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def _resolve_log_level(level_name: Optional[str]) -> int:
    """Mappt einen Level-Namen auf die passende logging-Konstante."""
    if not level_name:
        return logging.INFO

    normalized = str(level_name).upper()
    return getattr(logging, normalized, logging.INFO)


def reset_logging() -> None:
    """Entfernt von FinancialProof registrierte Logging-Handler."""
    root_logger = logging.getLogger()

    for handler in list(root_logger.handlers):
        if getattr(handler, "name", "") in {CONSOLE_HANDLER_NAME, FILE_HANDLER_NAME}:
            root_logger.removeHandler(handler)
            handler.close()


def configure_logging(
    log_file: Optional[Union[str, Path]] = None,
    level: Optional[str] = None,
    *,
    force: bool = False,
) -> logging.Logger:
    """Initialisiert das zentrale Application-Logging.

    Args:
        log_file: Optionaler Zielpfad fuer die Log-Datei.
        level: Optionaler Logging-Level als Name.
        force: Entfernt bestehende FinancialProof-Handler vor der Neuinitialisierung.

    Returns:
        Der konfigurierte Root-Logger.
    """
    from config import config

    root_logger = logging.getLogger()
    resolved_level = _resolve_log_level(level or config.LOG_LEVEL)
    resolved_log_file = Path(log_file or config.LOG_FILE)
    resolved_log_file.parent.mkdir(parents=True, exist_ok=True)

    if force:
        reset_logging()

    root_logger.setLevel(resolved_level)
    formatter = logging.Formatter(LOG_FORMAT)

    has_console_handler = any(
        getattr(handler, "name", "") == CONSOLE_HANDLER_NAME
        for handler in root_logger.handlers
    )

    has_file_handler = any(
        getattr(handler, "name", "") == FILE_HANDLER_NAME
        and Path(getattr(handler, "baseFilename", "")).resolve() == resolved_log_file.resolve()
        for handler in root_logger.handlers
    )

    if not has_console_handler:
        console_handler = logging.StreamHandler()
        console_handler.set_name(CONSOLE_HANDLER_NAME)
        console_handler.setLevel(resolved_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    if not has_file_handler:
        file_handler = RotatingFileHandler(
            resolved_log_file,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.set_name(FILE_HANDLER_NAME)
        file_handler.setLevel(resolved_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger

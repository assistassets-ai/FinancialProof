"""
FinancialProof - redigierter Workspace-Export fuer den PWA-Companion.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any, Optional

from config import config
from core.database import AnalysisResult, DatabaseManager, Job, JobStatus, db
from ui.disclaimer_widget import get_current_disclaimer_metadata


SCHEMA_NAME = "financialproof-workspace-v1"
DEFAULT_SNAPSHOT_WARNING = "Keine Anlageberatung; nur historische Auswertung."


def build_workspace_export(
    database: Optional[DatabaseManager] = None,
    *,
    source: str = "desktop",
    exported_at: Optional[datetime] = None,
    app_version: Optional[str] = None,
    disclaimer_meta: Optional[dict[str, Any]] = None,
    job_limit: int = 20,
) -> dict[str, Any]:
    """Baut den redigierten Workspace-Export fuer den lokalen Companion."""
    database = database or db
    exported_at = exported_at or datetime.now(timezone.utc)
    disclaimer_meta = disclaimer_meta or get_current_disclaimer_metadata()

    completed_jobs = database.get_jobs(status=JobStatus.COMPLETED, limit=job_limit)
    snapshots = []

    for job in completed_jobs:
        results = database.get_results_for_job(job.id)
        if not results:
            continue
        snapshot = _build_snapshot(job, results[0])
        if snapshot is not None:
            snapshots.append(snapshot)

    snapshots.sort(key=lambda item: item["created_at"], reverse=True)

    return {
        "schema": SCHEMA_NAME,
        "app": {
            "name": config.APP_NAME,
            "version": app_version or config.APP_VERSION,
            "exported_at": _to_iso_timestamp(exported_at),
            "source": source,
        },
        "legal": {
            "disclaimer_hash": str(disclaimer_meta.get("disclaimer_hash", "unbekannt")),
            "disclaimer_version": str(
                disclaimer_meta.get("disclaimer_version", "unbekannt")
            ),
            "not_financial_advice": disclaimer_meta.get("not_financial_advice", True)
            is not False,
            "warnings": _normalize_warnings(
                disclaimer_meta.get("warnings"),
                fallback=DEFAULT_SNAPSHOT_WARNING,
            ),
        },
        "watchlist": [
            {
                "symbol": item.symbol.upper(),
                "asset_type": (item.asset_type or "stock").lower(),
                "display_name": item.name or item.symbol.upper(),
                "notes": item.notes or "",
                "created_at": _to_iso_timestamp(item.added_at),
            }
            for item in database.get_watchlist()
        ],
        "analysis_presets": [
            {
                "name": preset.name,
                "asset_type": preset.asset_type,
                "is_active": bool(preset.is_active),
                "rules": preset.rules or {},
            }
            for preset in database.list_strategies()
        ],
        "analysis_snapshots": snapshots,
    }


def build_workspace_export_json(
    database: Optional[DatabaseManager] = None,
    **kwargs: Any,
) -> str:
    """Serialisiert den Companion-Export als UTF-8-JSON."""
    payload = build_workspace_export(database=database, **kwargs)
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _build_snapshot(job: Job, result: AnalysisResult) -> Optional[dict[str, Any]]:
    symbol = (job.symbol or "").upper().strip()
    if not symbol:
        return None

    return {
        "symbol": symbol,
        "timeframe": _extract_timeframe(job),
        "created_at": _to_iso_timestamp(result.created_at or job.completed_at or job.created_at),
        "summary": result.summary or "Historische Analyse ohne Zusammenfassung",
        "pattern_class": _infer_pattern_class(result),
        "confidence": _safe_float(result.confidence),
        "indicators": _extract_indicator_values(result.data),
        "warnings": _collect_snapshot_warnings(result.data),
    }


def _extract_timeframe(job: Job) -> str:
    if isinstance(job.parameters, dict):
        timeframe = job.parameters.get("timeframe")
        if timeframe:
            return str(timeframe)
    return config.DEFAULT_PERIOD


def _infer_pattern_class(result: AnalysisResult) -> str:
    if isinstance(result.data, dict):
        raw_pattern = result.data.get("pattern_class")
        if raw_pattern:
            return str(raw_pattern).strip().lower()

    signal_names: list[str] = []
    for signal in result.signals or []:
        if isinstance(signal, dict):
            value = signal.get("signal") or signal.get("type") or signal.get("label")
        else:
            value = signal
        normalized = str(value).strip().lower() if value is not None else ""
        if normalized:
            signal_names.append(normalized)

    has_bullish = any(name in {"buy", "bullish"} for name in signal_names)
    has_bearish = any(name in {"sell", "bearish"} for name in signal_names)

    if has_bullish and not has_bearish:
        return "bullish"
    if has_bearish and not has_bullish:
        return "bearish"
    return "neutral"


def _extract_indicator_values(data: Optional[dict[str, Any]]) -> dict[str, float]:
    if not isinstance(data, dict):
        return {}

    interesting_tokens = (
        "rsi",
        "macd",
        "sma",
        "ema",
        "atr",
        "stochastic",
        "bollinger",
        "volatility",
        "sharpe",
        "drawdown",
        "var",
    )
    indicators: dict[str, float] = {}
    stack: list[tuple[str, Any, int]] = [("", data, 0)]

    while stack and len(indicators) < 8:
        prefix, current, depth = stack.pop()
        if depth > 2 or not isinstance(current, dict):
            continue

        for key, value in current.items():
            normalized_key = str(key).strip().lower()
            compound_key = f"{prefix}_{normalized_key}".strip("_")

            if isinstance(value, dict):
                stack.append((compound_key, value, depth + 1))
                continue

            numeric_value = _safe_float(value)
            if numeric_value is None:
                continue

            if any(token in compound_key for token in interesting_tokens):
                indicators[compound_key] = numeric_value

    return indicators


def _collect_snapshot_warnings(data: Optional[dict[str, Any]]) -> list[str]:
    warnings = [DEFAULT_SNAPSHOT_WARNING]
    if isinstance(data, dict):
        warnings.extend(_normalize_warnings(data.get("warnings")))

        volatility = None
        for key in ("volatility_percent", "volatility", "annualized_volatility"):
            if key in data:
                volatility = _safe_float(data.get(key))
                break

        if volatility is not None and volatility >= 5:
            warnings.append("Erhöhte Volatilität im Snapshot.")

    return list(dict.fromkeys(warnings))


def _normalize_warnings(raw_warnings: Any, fallback: Optional[str] = None) -> list[str]:
    warnings = []
    if isinstance(raw_warnings, list):
        for warning in raw_warnings:
            text = str(warning).strip()
            if text:
                warnings.append(text)

    if not warnings and fallback:
        warnings.append(fallback)

    return list(dict.fromkeys(warnings))


def _safe_float(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None
    return number


def _to_iso_timestamp(value: Any) -> str:
    if value in (None, ""):
        return ""

    if isinstance(value, datetime):
        dt_value = value
    else:
        text = str(value).strip()
        if not text:
            return ""
        try:
            dt_value = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return text

    if dt_value.tzinfo is None:
        return dt_value.isoformat(timespec="seconds")
    return dt_value.astimezone(timezone.utc).isoformat(timespec="seconds")

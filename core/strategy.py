"""
Deskriptive Regel-Engine fuer historische Analyse-Presets.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

import pandas as pd

from core.database import StrategyPreset
from core.strategy_manager import StrategyManager


class StrategyEngine:
    """Bewertet Analyse-Ergebnisse gegen ein gespeichertes Preset."""

    def __init__(self, manager: Optional[StrategyManager] = None):
        self.manager = manager or StrategyManager()

    def evaluate(
        self,
        analysis_result: Dict[str, Any],
        market_data: pd.DataFrame,
        symbol: str,
        *,
        strategy: Optional[StrategyPreset] = None,
        persist: bool = True,
    ) -> Dict[str, Any]:
        """Wendet Preset-Regeln deskriptiv auf ein Analyse-Ergebnis an."""
        preset = strategy or self.manager.get_active_preset(
            self.manager.infer_asset_type(symbol)
        )
        pattern_rules = (preset.rules or {}).get("pattern_rules", {})
        risk_notes = (preset.rules or {}).get("risk_notes", {})

        signal_names = self._extract_signal_names(analysis_result.get("signals"))
        confidence = self._safe_float(analysis_result.get("confidence"), default=0.0)
        current_rsi = self._extract_current_rsi(market_data)
        volume_ratio = self._extract_volume_ratio(
            analysis_result=analysis_result,
            market_data=market_data,
        )

        required_signals = pattern_rules.get("required_signals", [])
        min_confidence = self._safe_float(
            pattern_rules.get("min_confidence"),
            default=0.0,
        )
        max_rsi = self._safe_float(pattern_rules.get("max_rsi"), default=100.0)
        min_volume_ratio = self._safe_float(
            pattern_rules.get("min_volume_ratio"),
            default=0.0,
        )

        reasons: list[str] = []
        passed = True

        if confidence < min_confidence:
            passed = False
            reasons.append(f"Unsicher ({confidence:.2f} < {min_confidence:.2f})")

        if current_rsi > max_rsi:
            passed = False
            reasons.append(f"RSI zu hoch ({current_rsi:.1f} > {max_rsi:.1f})")

        if volume_ratio < min_volume_ratio:
            passed = False
            reasons.append(
                f"Volumenverhältnis zu niedrig ({volume_ratio:.2f} < {min_volume_ratio:.2f})"
            )

        missing_signals = [
            signal for signal in required_signals if signal not in signal_names
        ]
        if missing_signals:
            passed = False
            reasons.append(f"Signale fehlen: {', '.join(missing_signals)}")

        pattern_class = self._determine_pattern_class(signal_names, passed)
        summary = "Historisches Muster erfüllt" if passed else ", ".join(reasons)

        result = {
            "strategy_name": preset.name,
            "asset_type": preset.asset_type,
            "pattern_class": pattern_class,
            "passed": passed,
            "reason": summary,
            "reasons": reasons,
            "signals": signal_names,
            "metrics": {
                "confidence": confidence,
                "current_rsi": current_rsi,
                "volume_ratio": volume_ratio,
            },
            "risk_notes": risk_notes,
        }

        if persist and preset.id is not None:
            self.manager.record_analysis_run(
                symbol=symbol,
                strategy_id=preset.id,
                pattern_class=pattern_class,
                notes=summary,
                job_id=analysis_result.get("job_id"),
            )

        return result

    @staticmethod
    def _extract_signal_names(raw_signals: Any) -> list[str]:
        if raw_signals is None:
            return []

        if isinstance(raw_signals, dict):
            iterable: Iterable[Any] = raw_signals.values()
        elif isinstance(raw_signals, Iterable) and not isinstance(raw_signals, (str, bytes)):
            iterable = raw_signals
        else:
            iterable = [raw_signals]

        signal_names = []
        for entry in iterable:
            if isinstance(entry, dict):
                value = entry.get("signal") or entry.get("type") or entry.get("label")
            else:
                value = entry
            normalized = str(value).strip().lower() if value is not None else ""
            if normalized:
                signal_names.append(normalized)
        return sorted(set(signal_names))

    @staticmethod
    def _extract_current_rsi(market_data: pd.DataFrame) -> float:
        if "RSI" not in market_data or market_data["RSI"].empty:
            return 50.0

        value = market_data["RSI"].iloc[-1]
        if pd.isna(value):
            return 50.0
        return float(value)

    @staticmethod
    def _extract_volume_ratio(
        *,
        analysis_result: Dict[str, Any],
        market_data: pd.DataFrame,
    ) -> float:
        if "volume_ratio" in analysis_result:
            return StrategyEngine._safe_float(analysis_result.get("volume_ratio"), default=0.0)

        if "Volume" not in market_data or market_data["Volume"].empty:
            return 0.0

        series = market_data["Volume"].dropna()
        if len(series) < 2:
            return 0.0

        current_volume = float(series.iloc[-1])
        baseline = float(series.iloc[:-1].tail(20).mean())
        if baseline <= 0:
            return 0.0
        return current_volume / baseline

    @staticmethod
    def _determine_pattern_class(signal_names: list[str], passed: bool) -> str:
        if not passed:
            return "neutral"
        if "bearish" in signal_names and "bullish" not in signal_names:
            return "bearish"
        if "bullish" in signal_names:
            return "bullish"
        return "neutral"

    @staticmethod
    def _safe_float(value: Any, *, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

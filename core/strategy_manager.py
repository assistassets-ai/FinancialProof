"""
Verwaltung und Validierung von Analyse-Presets fuer historische Musterbewertungen.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Optional

from core.database import AnalysisRun, DatabaseManager, StrategyPreset, db


DEFAULT_RULES: Dict[str, Dict[str, Any]] = {
    "pattern_rules": {
        "min_confidence": 0.8,
        "max_rsi": 70.0,
        "required_signals": [],
        "min_volume_ratio": 0.0,
    },
    "risk_notes": {
        "max_rsi_warning": 70.0,
        "volatility_warning_percent": 5.0,
    },
}

ALLOWED_ASSET_TYPES = {"STOCK", "ETF", "FUND", "CRYPTO", "FOREX", "INDEX"}


class StrategyRuleError(ValueError):
    """Ungueltige oder nicht parsebare Preset-Regeln."""


class StrategyManager:
    """CRUD- und Parser-Helfer fuer Analyse-Presets."""

    def __init__(self, database: Optional[DatabaseManager] = None):
        self.db = database or db

    @staticmethod
    def normalize_asset_type(asset_type: str) -> str:
        """Normalisiert und validiert den Asset-Typ."""
        normalized = (asset_type or "STOCK").strip().upper()
        if normalized not in ALLOWED_ASSET_TYPES:
            raise StrategyRuleError(f"Unbekannter Asset-Typ: {asset_type}")
        return normalized

    @staticmethod
    def infer_asset_type(symbol: str) -> str:
        """Leitet den Asset-Typ heuristisch aus einem Symbol ab."""
        upper = (symbol or "").upper()
        if "-" in upper:
            return "CRYPTO"
        if upper.startswith("^"):
            return "INDEX"
        if "=" in upper:
            return "FOREX"
        return "STOCK"

    def parse_rules(self, raw_rules: Any) -> Dict[str, Dict[str, Any]]:
        """Parst und normalisiert flache oder verschachtelte Regeldefinitionen."""
        if raw_rules is None:
            payload: Dict[str, Any] = {}
        elif isinstance(raw_rules, str):
            try:
                payload = json.loads(raw_rules)
            except json.JSONDecodeError as exc:
                raise StrategyRuleError("Ungültiges Regel-JSON") from exc
        elif isinstance(raw_rules, dict):
            payload = dict(raw_rules)
        else:
            raise StrategyRuleError("Regeln müssen als Dict oder JSON-String vorliegen")

        pattern_source = payload.get("pattern_rules")
        if not isinstance(pattern_source, dict):
            pattern_source = payload

        risk_source = payload.get("risk_notes")
        if not isinstance(risk_source, dict):
            risk_source = {}

        pattern_rules = {
            "min_confidence": self._bounded_float(
                pattern_source.get("min_confidence", DEFAULT_RULES["pattern_rules"]["min_confidence"]),
                minimum=0.0,
                maximum=1.0,
                field_name="min_confidence",
            ),
            "max_rsi": self._bounded_float(
                pattern_source.get("max_rsi", DEFAULT_RULES["pattern_rules"]["max_rsi"]),
                minimum=0.0,
                maximum=100.0,
                field_name="max_rsi",
            ),
            "required_signals": self._normalize_signals(
                pattern_source.get("required_signals", DEFAULT_RULES["pattern_rules"]["required_signals"])
            ),
            "min_volume_ratio": self._bounded_float(
                pattern_source.get(
                    "min_volume_ratio",
                    DEFAULT_RULES["pattern_rules"]["min_volume_ratio"],
                ),
                minimum=0.0,
                maximum=None,
                field_name="min_volume_ratio",
            ),
        }

        risk_notes = {
            "max_rsi_warning": self._bounded_float(
                risk_source.get(
                    "max_rsi_warning",
                    pattern_rules["max_rsi"],
                ),
                minimum=0.0,
                maximum=100.0,
                field_name="max_rsi_warning",
            ),
            "volatility_warning_percent": self._bounded_float(
                risk_source.get(
                    "volatility_warning_percent",
                    DEFAULT_RULES["risk_notes"]["volatility_warning_percent"],
                ),
                minimum=0.0,
                maximum=None,
                field_name="volatility_warning_percent",
            ),
        }

        return {
            "pattern_rules": pattern_rules,
            "risk_notes": risk_notes,
        }

    def build_preset(
        self,
        name: str,
        asset_type: str,
        rules: Any,
        is_active: bool = False,
        preset_id: Optional[int] = None,
    ) -> StrategyPreset:
        """Erzeugt ein normalisiertes Analyse-Preset."""
        cleaned_name = (name or "").strip()
        if not cleaned_name:
            raise StrategyRuleError("Preset-Name darf nicht leer sein")

        return StrategyPreset(
            id=preset_id,
            name=cleaned_name,
            asset_type=self.normalize_asset_type(asset_type),
            rules=self.parse_rules(rules),
            is_active=is_active,
        )

    def save_preset(
        self,
        name: str,
        asset_type: str,
        rules: Any,
        is_active: bool = False,
        preset_id: Optional[int] = None,
    ) -> StrategyPreset:
        """Speichert ein Analyse-Preset und liefert die persistierte Version zurueck."""
        preset = self.build_preset(
            name=name,
            asset_type=asset_type,
            rules=rules,
            is_active=is_active,
            preset_id=preset_id,
        )
        strategy_id = self.db.save_strategy(preset)
        return self.db.get_strategy(strategy_id)

    def list_presets(
        self,
        asset_type: Optional[str] = None,
        active_only: bool = False,
    ) -> list[StrategyPreset]:
        """Listet Analyse-Presets."""
        normalized_asset_type = self.normalize_asset_type(asset_type) if asset_type else None
        return self.db.list_strategies(
            asset_type=normalized_asset_type,
            active_only=active_only,
        )

    def get_preset(self, strategy_id: int) -> Optional[StrategyPreset]:
        """Holt ein Preset anhand der ID."""
        return self.db.get_strategy(strategy_id)

    def get_active_preset(self, asset_type: str) -> StrategyPreset:
        """Holt das aktive Preset oder liefert ein deskriptives Fallback."""
        normalized_asset_type = self.normalize_asset_type(asset_type)
        preset = self.db.get_active_strategy(normalized_asset_type)
        if preset is not None:
            return preset

        return StrategyPreset(
            name=f"{normalized_asset_type.title()} Standard",
            asset_type=normalized_asset_type,
            rules=self.parse_rules(None),
            is_active=False,
        )

    def activate_preset(self, strategy_id: int) -> Optional[StrategyPreset]:
        """Markiert ein Preset als aktiv."""
        return self.db.set_active_strategy(strategy_id)

    def delete_preset(self, strategy_id: int):
        """Loescht ein Preset."""
        self.db.delete_strategy(strategy_id)

    def record_analysis_run(
        self,
        symbol: str,
        strategy_id: Optional[int],
        pattern_class: str,
        notes: Optional[str] = None,
        job_id: Optional[int] = None,
    ) -> int:
        """Protokolliert die Auswertung eines Analyse-Presets."""
        run = AnalysisRun(
            symbol=symbol,
            strategy_id=strategy_id,
            job_id=job_id,
            pattern_class=pattern_class,
            notes=notes,
        )
        return self.db.save_analysis_run(run)

    @staticmethod
    def _bounded_float(
        value: Any,
        *,
        minimum: float,
        maximum: Optional[float],
        field_name: str,
    ) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise StrategyRuleError(f"Ungültiger Zahlenwert für {field_name}") from exc

        if number < minimum:
            raise StrategyRuleError(f"{field_name} muss mindestens {minimum} sein")
        if maximum is not None and number > maximum:
            raise StrategyRuleError(f"{field_name} darf höchstens {maximum} sein")
        return number

    @staticmethod
    def _normalize_signals(raw_signals: Any) -> list[str]:
        if raw_signals is None:
            return []
        if isinstance(raw_signals, str):
            signals: Iterable[Any] = [raw_signals]
        elif isinstance(raw_signals, Iterable):
            signals = raw_signals
        else:
            raise StrategyRuleError("required_signals muss eine Liste oder ein String sein")

        normalized = []
        for signal in signals:
            value = str(signal).strip().lower()
            if value:
                normalized.append(value)
        return sorted(set(normalized))

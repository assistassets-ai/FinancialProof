"""
FinancialProof - Analyse-Registry
Zentrales Register für alle verfügbaren Analyse-Algorithmen
"""
import logging
import threading
from typing import Dict, List, Type, Optional, Any
from analysis.base import BaseAnalyzer, AnalysisCategory

logger = logging.getLogger(__name__)


class AnalysisRegistry:
    """
    Zentrales Register für alle Analyse-Algorithmen.

    Ermöglicht dynamische Registrierung und Abfrage von Analyzern.
    """

    _analyzers: Dict[str, Type[BaseAnalyzer]] = {}
    _instances: Dict[str, BaseAnalyzer] = {}
    _instances_lock: threading.Lock = threading.Lock()

    @classmethod
    def register(cls, analyzer_class: Type[BaseAnalyzer]) -> Type[BaseAnalyzer]:
        """
        Registriert einen Analyzer.

        Kann als Decorator verwendet werden:

            @AnalysisRegistry.register
            class MyAnalyzer(BaseAnalyzer):
                ...

        Args:
            analyzer_class: Die Analyzer-Klasse

        Returns:
            Die gleiche Klasse (für Decorator-Verwendung)
        """
        name = analyzer_class.name
        if name in cls._analyzers:
            raise ValueError(f"Analyzer '{name}' ist bereits registriert")

        cls._analyzers[name] = analyzer_class
        return analyzer_class

    @classmethod
    def unregister(cls, name: str):
        """Entfernt einen Analyzer aus dem Register"""
        if name in cls._analyzers:
            del cls._analyzers[name]
        if name in cls._instances:
            del cls._instances[name]

    @classmethod
    def get(cls, name: str) -> Optional[BaseAnalyzer]:
        """
        Gibt eine Analyzer-Instanz zurück.

        Erstellt eine neue Instanz wenn nötig (Singleton-Pattern).

        Args:
            name: Name des Analyzers

        Returns:
            Analyzer-Instanz oder None
        """
        if name not in cls._analyzers:
            return None

        with cls._instances_lock:
            if name not in cls._instances:
                cls._instances[name] = cls._analyzers[name]()
            instance = cls._instances[name]

        # Reset vor Verwendung
        instance.reset()
        return instance

    @classmethod
    def get_class(cls, name: str) -> Optional[Type[BaseAnalyzer]]:
        """Gibt die Analyzer-Klasse zurück"""
        return cls._analyzers.get(name)

    @classmethod
    def list_all(cls) -> List[Dict[str, Any]]:
        """
        Gibt Informationen über alle registrierten Analyzer zurück.

        Returns:
            Liste von Info-Dicts für jeden Analyzer
        """
        return [
            analyzer_class.get_info()
            for analyzer_class in cls._analyzers.values()
        ]

    @classmethod
    def list_by_category(cls, category: AnalysisCategory) -> List[Dict[str, Any]]:
        """
        Gibt Analyzer einer bestimmten Kategorie zurück.

        Args:
            category: Die gewünschte Kategorie

        Returns:
            Liste von Info-Dicts
        """
        return [
            analyzer_class.get_info()
            for analyzer_class in cls._analyzers.values()
            if analyzer_class.category == category
        ]

    @classmethod
    def list_names(cls) -> List[str]:
        """Gibt alle registrierten Analyzer-Namen zurück"""
        return list(cls._analyzers.keys())

    @classmethod
    def exists(cls, name: str) -> bool:
        """Prüft ob ein Analyzer existiert"""
        return name in cls._analyzers

    @classmethod
    def get_categories(cls) -> Dict[str, List[str]]:
        """
        Gruppiert Analyzer nach Kategorie.

        Returns:
            Dict {category_name: [analyzer_names]}
        """
        categories: Dict[str, List[str]] = {}

        for name, analyzer_class in cls._analyzers.items():
            cat = analyzer_class.category.value
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(name)

        return categories

    @classmethod
    def clear(cls):
        """Löscht alle Registrierungen (für Tests)"""
        cls._analyzers.clear()
        cls._instances.clear()


# ===== INITIALISIERUNG =====
# Importiere und registriere alle Analyzer beim Laden des Moduls

def _register_all_analyzers():
    """
    Importiert und registriert alle verfügbaren Analyzer.

    Wird beim Laden des Moduls aufgerufen.
    """
    # Die Imports müssen hier sein um zirkuläre Imports zu vermeiden
    analyzers_to_import = [
        ("analysis.statistical.arima", "ARIMAAnalyzer"),
        ("analysis.statistical.monte_carlo", "MonteCarloAnalyzer"),
        ("analysis.statistical.mean_reversion", "MeanReversionAnalyzer"),
        ("analysis.correlation.cointegration", "CorrelationAnalyzer"),
        ("analysis.ml.random_forest", "RandomForestAnalyzer"),
        ("analysis.ml.neural_net", "NeuralNetAnalyzer"),
        ("analysis.nlp.sentiment", "SentimentAnalyzer"),
        ("analysis.nlp.research_agent", "ResearchAgent"),
    ]

    for module_path, class_name in analyzers_to_import:
        try:
            __import__(module_path, fromlist=[class_name])
        except ImportError as e:
            logger.debug(f"Analyzer {class_name} nicht verfuegbar: {e}")


# Registrierung wird verzögert, damit die Analyzer-Module Zeit haben zu laden
# Dies geschieht beim ersten Zugriff auf das Registry

_initialized = False
_init_lock = threading.Lock()


def ensure_initialized():
    """Stellt sicher, dass alle Analyzer registriert sind"""
    global _initialized
    if not _initialized:
        with _init_lock:
            if not _initialized:
                _register_all_analyzers()
                _initialized = True


# ===== HILFSFUNKTIONEN =====

def get_analyzer(name: str) -> Optional[BaseAnalyzer]:
    """
    Komfort-Funktion um einen Analyzer zu holen.

    Args:
        name: Name des Analyzers

    Returns:
        Analyzer-Instanz oder None
    """
    ensure_initialized()
    return AnalysisRegistry.get(name)


def list_analyzers() -> List[Dict[str, Any]]:
    """
    Komfort-Funktion um alle Analyzer aufzulisten.

    Returns:
        Liste von Analyzer-Informationen
    """
    ensure_initialized()
    return AnalysisRegistry.list_all()


def get_analyzer_for_ui() -> Dict[str, List[Dict]]:
    """
    Gibt Analyzer gruppiert nach Kategorie für die UI zurück.

    Returns:
        Dict mit Kategorien und ihren Analyzern
    """
    ensure_initialized()

    categories = {
        AnalysisCategory.STATISTICAL.value: {
            "name": "Statistische Analysen",
            "icon": "📊",
            "analyzers": []
        },
        AnalysisCategory.CORRELATION.value: {
            "name": "Korrelation & Kointegration",
            "icon": "🔗",
            "analyzers": []
        },
        AnalysisCategory.ML.value: {
            "name": "Machine Learning",
            "icon": "🤖",
            "analyzers": []
        },
        AnalysisCategory.NLP.value: {
            "name": "Sentiment & NLP",
            "icon": "📰",
            "analyzers": []
        },
        AnalysisCategory.RESEARCH.value: {
            "name": "Web-Recherche",
            "icon": "🔍",
            "analyzers": []
        }
    }

    for info in AnalysisRegistry.list_all():
        cat = info.get("category", "statistical")
        if cat in categories:
            categories[cat]["analyzers"].append(info)

    # Nur Kategorien mit Analyzern zurückgeben
    return {k: v for k, v in categories.items() if v["analyzers"]}

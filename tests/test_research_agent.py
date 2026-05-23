"""
Regressionstests fuer den Web-Recherche-Agenten.
"""
import asyncio
import logging

import pandas as pd

from analysis.base import AnalysisParameters, AnalysisTimeframe
from analysis.nlp.research_agent import ResearchAgent


def test_research_agent_result_uses_descriptive_pattern_language():
    """Research-Ergebnisse duerfen keine App-eigene Kauf-/Verkaufsempfehlung ausgeben."""
    analyzer = ResearchAgent()
    result = analyzer._build_result(
        "AAPL",
        {
            "fundamentals": {
                "company_name": "Apple Inc.",
                "sector": "Technology",
                "market_cap_formatted": "3.00T",
                "pe_ratio": 10,
                "current_price": 100.0,
                "target_price": 125.0,
            },
            "recommendations": {
                "available": True,
                "consensus": "buy",
            },
            "news": {},
            "dividends": {},
        },
        [],
    )

    assert result.recommendation == "bullish"
    assert result.signals[0]["type"] == "bullish"
    assert "Historische Musterlage" in result.summary
    assert "Gesamteinsch" not in result.summary
    assert "BUY" not in result.summary
    assert "SELL" not in result.summary
    assert all(
        signal["signal"] not in {"buy", "sell"}
        for signal in result.data["signals_found"]
    )


def test_research_agent_analyze_logs_unexpected_failure(monkeypatch, caplog):
    """Unerwartete Analysefehler werden als Fehlerresultat und Log sichtbar."""
    analyzer = ResearchAgent()

    def fail(_ticker):
        raise RuntimeError("fundamental boom")

    monkeypatch.setattr(analyzer, "_get_fundamentals", fail)

    with caplog.at_level(logging.ERROR, logger="analysis.nlp.research_agent"):
        result = asyncio.run(
            analyzer.analyze(
                AnalysisParameters(
                    symbol="AAPL",
                    data=pd.DataFrame(),
                    timeframe=AnalysisTimeframe.SHORT,
                    custom_params={
                        "include_fundamentals": True,
                        "include_recommendations": False,
                        "include_news": False,
                    },
                )
            )
        )

    assert result.error == "fundamental boom"
    assert "Research-Agent-Analyse fuer AAPL fehlgeschlagen" in caplog.text


def test_research_agent_fundamental_fallback_is_logged(caplog):
    """Helper-Fallbacks duerfen nicht still bleiben."""

    class BrokenTicker:
        @property
        def info(self):
            raise RuntimeError("info boom")

    analyzer = ResearchAgent()

    with caplog.at_level(logging.WARNING, logger="analysis.nlp.research_agent"):
        result = analyzer._get_fundamentals(BrokenTicker())

    assert result == {"error": "info boom"}
    assert "Fundamentaldaten konnten nicht geladen werden" in caplog.text

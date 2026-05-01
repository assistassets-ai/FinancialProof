"""
Regressionstests fuer den Web-Recherche-Agenten.
"""

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

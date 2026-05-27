# Exportformat - FinancialProof Workspace

Stand: 2026-05-27

Dieses Dokument beschreibt das geplante Austauschformat
`financialproof-workspace-v1.json`. Es ist noch nicht implementiert und dient
als stabile Vorgabe für Export/Import und den späteren PWA-Companion.

## Ziel

Das Format soll lokale Arbeitsstände zwischen Desktop-Vollversion und
PWA-Companion übertragen, ohne Secrets oder regulierungsrelevante
Broker-/Orderdaten mitzunehmen.

## Sicherheitsregeln

- Keine API-Keys, Tokens, `.env`, `.secrets` oder lokalen Schlüssel exportieren.
- Keine SQLite-Datei direkt exportieren.
- Keine Broker-Konten, Orders, Depotdaten oder Trading-Automation aufnehmen.
- Analyse-Texte müssen als historische, deskriptive Auswertung markiert sein.
- Import muss unbekannte Felder tolerieren, aber unbekannte Schema-Versionen
  sichtbar ablehnen.

## Schema-Skizze

```json
{
  "schema": "financialproof-workspace-v1",
  "app": {
    "name": "FinancialProof",
    "version": "1.1-dev",
    "exported_at": "2026-05-27T00:00:00+02:00",
    "source": "desktop"
  },
  "legal": {
    "disclaimer_hash": "sha256-of-current-disclaimer",
    "not_financial_advice": true
  },
  "watchlist": [
    {
      "symbol": "AAPL",
      "asset_type": "stock",
      "display_name": "Apple Inc.",
      "notes": "",
      "created_at": "2026-05-27T00:00:00+02:00"
    }
  ],
  "analysis_presets": [
    {
      "name": "ETF defensiv",
      "asset_type": "ETF",
      "is_active": true,
      "rules": {
        "pattern_rules": {
          "min_confidence": 0.75,
          "max_rsi": 70
        },
        "risk_notes": {
          "volatility_warning_percent": 5.0
        }
      }
    }
  ],
  "analysis_snapshots": [
    {
      "symbol": "AAPL",
      "timeframe": "1y",
      "created_at": "2026-05-27T00:00:00+02:00",
      "summary": "Historische Musteranalyse",
      "pattern_class": "neutral",
      "confidence": 0.62,
      "indicators": {
        "rsi": 54.2,
        "macd": 1.4
      },
      "charts": [],
      "warnings": [
        "Keine Anlageberatung; nur historische Auswertung."
      ]
    }
  ]
}
```

## PWA-Importumfang

Der Companion soll zunächst nur lesen:

- Watchlist
- Analyse-Presets als Anzeige
- Analyse-Snapshots
- Disclaimer-/Warnhinweise

Die PWA soll im ersten Schritt keine neuen Marktdaten laden und keine
Analysejobs starten.

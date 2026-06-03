# Exportformat - FinancialProof Workspace

Stand: 2026-06-01

Dieses Dokument beschreibt das umgesetzte Austauschformat
`financialproof-workspace-v1.json`. Es dient als stabiler Vertrag zwischen der
lokalen Streamlit-Vollversion und dem read-only Web/PWA-Companion.

## Ziel

Das Format soll lokale Arbeitsstände zwischen Desktop-Vollversion und
PWA-Companion übertragen, ohne Secrets oder regulierungsrelevante
Broker-/Orderdaten mitzunehmen.

Aktueller Exportpfad in der App:

- `Einstellungen -> Companion-Export -> Workspace exportieren (JSON)`

## Sicherheitsregeln

- Keine API-Keys, Tokens, `.env`, `.secrets` oder lokalen Schlüssel exportieren.
- Keine SQLite-Datei direkt exportieren.
- Keine Broker-Konten, Orders, Depotdaten oder Trading-Automation aufnehmen.
- Analyse-Texte müssen als historische, deskriptive Auswertung markiert sein.
- Import muss unbekannte Felder tolerieren, aber unbekannte Schema-Versionen
  sichtbar ablehnen.
- Pflichtsammlungen (`watchlist`, `analysis_presets`, `analysis_snapshots`) müssen
  als Arrays vorliegen; Pflichtschlüssel wie `symbol` und `name` dürfen nicht leer
  sein. Snapshot-`confidence` muss eine endliche Zahl bleiben.

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
    "disclaimer_version": "1.0",
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

## Umsetzungsstand

- Exportiert werden aktuell:
  - `watchlist`
  - `analysis_presets`
  - `analysis_snapshots` aus abgeschlossenen Jobs
  - `legal` mit Disclaimer-Hash/-Version und Companion-Warnhinweisen
- Der Web/PWA-Companion validiert beim Import jetzt zusätzlich:
  - Schema-Version
  - Top-Level-Typen der Pflichtsammlungen
  - leere `symbol`-/`name`-Pflichtfelder
  - `legal.not_financial_advice !== false`
  - endliche `confidence`-Werte pro Snapshot
- Nicht exportiert werden:
  - API-Keys, `.secrets`, `.env`, Datenbankdatei, Logs
  - Broker-/Orderdaten
  - Live-Marktdatenfeeds oder aktive Job-Warteschlangen
- Unbekannte Zusatzfelder bleiben zulässig, damit spätere Exporterweiterungen
  den read-only Companion nicht unnötig brechen.

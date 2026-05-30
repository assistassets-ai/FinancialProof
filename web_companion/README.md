# FinancialProof Web/PWA Companion

Stand: 2026-05-30

Der Companion ist jetzt als statischer Offline-Reader umgesetzt. Er liest
lokale `financialproof-workspace-v1.json`-Dateien direkt im Browser, speichert
den zuletzt geladenen Workspace für Offline-Starts in `localStorage` und hält
den rechtlichen Rahmen sichtbar im UI.

## Enthaltene Funktionen

- Datei-Import für `financialproof-workspace-v1.json`
- Text/Paste-Import für lokale JSON-Snapshots
- Demo-Workspace über Button oder `?demo=1`
- Übersicht für Watchlist, Analyse-Presets und Analyse-Snapshots
- Suche sowie Filter nach Asset-Typ und Musterklasse
- Sichtbare Warn- und Disclaimer-Box
- Service Worker für lokale Offline-Smokes

## Grenzen

- Keine Server-Uploads
- Keine API-Keys
- Keine Live-Marktdaten im ersten Schritt
- Keine Broker-/Orderfunktionen
- Keine Anlageempfehlungen oder Prognoseclaims
- Kein Desktop-Roundtrip zurück in die Streamlit-App

## Lokaler Start

Ein einfacher statischer Server reicht:

```bash
python -m http.server 8766
```

Dann `http://127.0.0.1:8766/web_companion/?demo=1` im Browser öffnen.

## Tests

```bash
node --test web_companion/tests/workspace.test.mjs
node --check web_companion/app.mjs
node --check web_companion/library.mjs
```

## Offener nächster Schritt

Der Desktop-Export aus `EXPORTFORMAT.md` ist weiterhin offen. Erst damit kann
die Vollversion echte lokale Arbeitsstände ohne Demo-Daten an den Companion
übergeben.

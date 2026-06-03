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
- Sichtbare Importvalidierung für Schema-Version, Pflichtlisten, Pflichtfelder,
  Legal-Flags und endliche Confidence-Werte
- Service Worker für lokale Offline-Smokes

## Grenzen

- Keine Server-Uploads
- Keine API-Keys
- Keine Live-Marktdaten im ersten Schritt
- Keine Broker-/Orderfunktionen
- Keine Anlageempfehlungen oder Prognoseclaims
- Kein Desktop-Roundtrip zurück in die Streamlit-App
- Unbekannte Zusatzfelder in gültigen Exporten bleiben bewusst erlaubt, damit
  spätere Desktop-Erweiterungen den Reader nicht unnötig brechen.

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

## Nächster Schritt

Der Desktop-Export ist seit 2026-06-01 umgesetzt. Die Vollversion kann jetzt
über `Einstellungen -> Companion-Export -> Workspace exportieren (JSON)` echte
lokale Arbeitsstände als `financialproof-workspace-v1.json` an den Companion
übergeben.

Als nächste Schritte bleiben vor allem mobile Android-/iOS-Smokes für den
bestehenden PWA-Pfad offen.

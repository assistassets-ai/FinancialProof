# FinancialProof Web/PWA Companion

Stand: 2026-05-27

Dieser Ordner ist der Platzhalter für einen späteren statischen
Web/PWA-Companion. Noch gibt es keine implementierte PWA.

## Zweck

Der Companion soll mobile Nutzung ermöglichen, ohne die Desktop-Vollanalyse
auf Android oder iOS zu klonen:

- `financialproof-workspace-v1.json` lokal im Browser importieren
- Watchlist und Analyse-Snapshots mobil lesen
- Warn- und Disclaimer-Texte sichtbar halten
- Offline-Ansicht nach Import unterstützen

## Grenzen

- Keine Server-Uploads
- Keine API-Keys
- Keine Live-Marktdaten im ersten Schritt
- Keine Broker-/Orderfunktionen
- Keine Anlageempfehlungen oder Prognoseclaims

## Nächster Umsetzungsschritt

Vor UI-Arbeit muss der Desktop-Export aus `EXPORTFORMAT.md` implementiert und
mit Tests abgesichert werden.

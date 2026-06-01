# Portierungsplan - FinancialProof

Stand: 2026-05-30

## Kurzentscheidung

FinancialProof ist bereits eine browserbasierte Streamlit-Anwendung und damit
technisch näher an einer lokalen Web-App als an einer klassischen Desktop-App.
Die Vollversion bleibt deshalb eine lokale `localhost`-Anwendung mit Python,
SQLite, yfinance und optionalen NLP-/ML-Abhängigkeiten. Plattformübergreifende
Nutzung wird zuerst über macOS-/Linux-Smokes und ein secret-freies
Austauschformat vorbereitet; Android, iOS und Web bekommen keinen nativen
Klon, sondern einen späteren PWA-Companion für Watchlists und Analyse-Snapshots.

Keine Linie darf Brokerage, Orderrouting, Trading-Automation oder
Anlageempfehlungen einführen. Alle Plattformen müssen das bestehende
Disclaimer- und Nicht-Anlageberatungs-Framing beibehalten.

## Warum Portierung sinnvoll ist

- Finanzanalyse wird häufig mobil geprüft: Watchlists, historische Muster und
  Analyseprotokolle sind typische Unterwegs-Use-Cases.
- Die aktuelle Streamlit-App ist für Desktop-Nutzung gut geeignet, aber
  Smartphone-Bedienung, Offline-Lesen und Import/Export sind noch nicht
  sauber getrennt.
- macOS und Linux sind für Open-Source-Nutzer naheliegend, weil FinancialProof
  als Python-/Streamlit-Projekt ohne Windows-only-Kernlogik läuft.
- Eine öffentliche Upload-Webapp wäre riskant, weil Finanzdaten, API-Keys,
  yfinance-Limits und regulatorisches Framing sauber kontrolliert werden
  müssen. Deshalb bleibt die Vollanalyse lokal.

## Plattformbewertung

| Option | Entscheidung | Begründung |
|---|---|---|
| Windows Store Release | Später nur als lokaler Launcher prüfen | Store-Vertrieb ist möglich, aber wegen Finanz-Kontext, GPL-3.0, Disclaimer-Pflicht, externen Datenquellen und Streamlit-Laufzeit nicht der nächste Schritt. GitHub bleibt primärer Kanal. |
| Android Version oder Clone | Kein nativer Clone | Mobile Nutzer brauchen eher Watchlist-/Report-Lesen als lokale ML-/NLP-Vollanalyse. PWA-Companion ist günstiger und regulatorisch klarer. |
| Webapp | Ja, aber als lokaler/PWA-Companion | Keine öffentliche SaaS-Uploadplattform. Sinnvoll ist ein statischer Companion, der exportierte Snapshots importiert und offline lesbar macht. |
| iOS Version | Kein nativer Clone | Wie Android: PWA-first, später optional App-Store-Hülle nur bei belegter Nachfrage. |
| Mac App | Source-/Smoke-Ziel | Streamlit sollte auf macOS laufen; Verpackung erst nach erfolgreichem Smoke, ggf. `.zip`/`.dmg` über GitHub. |
| Linux Version | Source-/Smoke-Ziel | Linux ist für Python-Tools naheliegend; zunächst Install-/Start-Smoke, später optional AppImage oder Tarball. |

## Zielarchitektur

### Desktop-Vollversion

- Autoritative Anwendung bleibt `python -m streamlit run app.py`.
- Lokale Datenbank, Secrets und Disclaimer-Bestätigung bleiben ausschließlich
  lokal.
- Windows-Launcher bleibt Komfortpfad, nicht fachliche Hauptarchitektur.
- macOS/Linux werden mit derselben Codebasis getestet, ohne separaten Fork.

### Austauschformat

- Geplantes Schema: `financialproof-workspace-v1.json`.
- Umgesetzt am 2026-06-01: redigierter Desktop-Export über
  `Einstellungen -> Companion-Export -> Workspace exportieren (JSON)`.
- Enthält Watchlist, Analyse-Presets, Analyse-Snapshots, Disclaimer-Version
  und Export-Metadaten.
- Enthält keine API-Keys, keine `.secrets`, keine lokalen Datenbankdateien,
  keine personenbezogenen Kontodaten und keine Order-/Broker-Informationen.
- Details stehen in `EXPORTFORMAT.md`.

### PWA-Companion

- Ordner: `web_companion/`.
- Fokus: Import von `financialproof-workspace-v1.json`, mobile Lesbarkeit,
  Offline-Ansicht und Teilen von Analyseprotokollen.
- Kein Abruf von Marktdaten, keine Server-Persistenz, keine Konto- oder
  Broker-Funktionen im ersten Schritt.

## Phasenplan

### P0 - Portierungsbasis

- `PORTIERUNGSPLAN.md` und `EXPORTFORMAT.md` pflegen.
- macOS-/Linux-Smoke-Testplan ergänzen.
- Sicherstellen, dass README und TODO die Plattformstrategie klar führen.

### P1 - Export/Import der lokalen Arbeitsfläche

- Exportfunktion für `financialproof-workspace-v1.json` implementieren. (erledigt 2026-06-01)
- Importfunktion defensiv validieren und alte/ungültige Schemas sauber melden.
- Tests für secret-freien Export, Schema-Version und Roundtrip ergänzen.

### P2 - PWA-Companion

- Statische PWA unter `web_companion/` aufbauen. (erledigt 2026-05-30)
- JSON-Datei lokal im Browser importieren, ohne Upload zu einem Server. (erledigt 2026-05-30)
- Watchlist, historische Analyse-Snapshots und Disclaimer sichtbar machen. (erledigt 2026-05-30)
- Mobile Smokes für Android Chrome und iOS Safari dokumentieren. (offen)

### P3 - Desktop-Plattform-Smokes

- macOS: frisches Python-Setup, Streamlit-Start, Datenabruf mit yfinance,
  Disclaimer-Flow und Chart-Renderpfad testen.
- Linux: analoger Smoke auf sauberer Umgebung.
- Erst danach über `.dmg`, AppImage oder Tarball entscheiden.

## Nicht-Ziele

- Kein Brokerage, keine Orders, keine Trading-Automation.
- Keine öffentliche Finanzdaten-Uploadplattform.
- Keine native Android-/iOS-Codebasis ohne vorher belegte Nachfrage.
- Kein Windows-Store-Paket, bevor Disclaimer, Datenschutz-/Support-URL,
  GPL-Source-Verweis und yfinance-Nutzungsgrenzen geprüft sind.

## Offene nächste Schritte

Die aktiven Aufgaben stehen in `TODO.md` unter "Phase 13: Plattform und
Portierung".

## Umgesetzt am 2026-05-30

`web_companion/` ist jetzt ein statischer Offline-Reader für
`financialproof-workspace-v1.json`:

- Datei- und Text-Import für lokale JSON-Snapshots
- Demo-Modus via Button oder `?demo=1`
- Übersicht für Watchlist, Analyse-Presets und Analyse-Snapshots
- Suche und Filter nach Asset-Typ bzw. Musterklasse
- sichtbarer Disclaimer-/Warnblock
- Service Worker und lokale Wiederherstellung des zuletzt geladenen Workspaces

Der Companion bleibt read-only. Der Desktop-Export aus `EXPORTFORMAT.md` ist
jetzt der produktive Anschluss, damit echte App-Daten ohne Demo oder manuell
erzeugte JSON-Dateien genutzt werden können. Offen bleibt als nächster
Web/PWA-nahe Schritt die Importvalidierung für alte oder beschädigte
Workspace-Dateien.

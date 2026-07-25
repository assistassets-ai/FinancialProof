# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Hinzugefügt / Added
- Documentation & Discoverability (2026-07-25): `pyproject.toml` um PEP 621 Standard-Metadaten (`keywords`, `project.urls`) und Pytest `pythonpath = ["."]` ergänzt. `llms.txt` Header auf `Last-checked: 2026-07-25` und 355 verifizierte Unit- & Companion-Tests (204 Python + 151 Web Companion) aktualisiert. Shields.io-Badges (Pytest, Web Companion, Local-First, LLM-Context) und KI/LLM-Integrationshinweise (`> [!NOTE]`) in [`README.md`](README.md) und [`README_de.md`](README_de.md) eingebunden.
- Documentation & Discoverability: Deutsche Startseite [`README_de.md`](README_de.md) erstellt, Sprachwahl-Navigation (`[English](README.md) | [Deutsch](README_de.md)`) oben im README integriert, Mermaid-Architekturdiagramm für Datenfluss & PWA-Offline-Companion ergänzt, Disambiguation gegen Namenskollisionen mit Bankauszugs-/Krediteinreichungs-Generatoren in README/README_de/llms.txt geschärft, `llms.txt` `Last-checked` Datum auf `2026-07-21` aktualisiert.
- `web_companion/`: Gefilterter Export (CSV/JSON) — drei neue Buttons unterhalb des Filter-Panels; Watchlist als CSV, Snapshots als CSV, gefilterte Daten als re-importierbares Workspace-JSON (2026-06-28).
  - `library.mjs`: `watchlistToCsv`, `snapshotsToCsv`, `filteredToJson` (Pure Logic, DOM-frei).
  - CSV: Semikolon-Delimiter (Excel-DE), UTF-8-BOM im Download-Blob, CSV-Injection-Schutz (Tab-Präfix für Formeln).
  - JSON: schema-valider Companion-Export (`source: "companion-export"`), direkt per `parseWorkspace()` re-importierbar.
  - `i18n.mjs`: 7 neue `export.*`-Schlüssel in DE und EN.
  - `index.html`: Export-Sektion mit `aria-live="polite"` Feedback.
  - `sw.js`: CACHE_NAME v4 → v5.
  - `tests/export.test.mjs`: 32 neue Tests — CSV-Spalten, Injection-Schutz, Escaping, Roundtrip, I18N-Parität.
  - `package.json`: Test-Script auf alle 5 Test-Dateien (inkl. bisher fehlendem `i18n.test.mjs`) erweitert.
  - Gesamttestzahl: 100/100 grün.
- `web_companion/`: PWA-Härtung — Offline-Fix (Service-Worker-Registrierung robuster), Manifest-Icons und Installierbarkeit verbessert (`0798d06`).
- `web_companion/`: iOS-Installierbarkeit — `apple-touch-icon-180`, `viewport-fit=cover`, Safe-Area-CSS, 44px Touch-Targets, Service-Worker CACHE_NAME v3 (`4d1420b`).

### Behoben / Fixed
- `analysis/nlp/research_agent.py`: None-Multiplikations-Crash für `profitMargins`, `revenueGrowth`, `earningsGrowth` behoben — `is not None`-Prüfung statt Truthiness-Check (`info.get(x, 0) * 100` schluckte lautlos echte Nullwerte).
- `app.py`: Veraltetes `delta_color`-Argument aus `st.metric()` entfernt (deprecated in neueren Streamlit-Versionen).
- `web_companion/app.mjs`: XSS-Schutz — `escHtml()`-Funktion ergänzt, alle `innerHTML`-Zuweisungen mit Nutzerdaten escapen Symbol, Name, Notizen, Preset-Felder und Summary-Cards.
- `web_companion/library.mjs`: `Date.parse(x || 0)` → `Date.parse(x) || 0` — null/undefined-Timestamps werden korrekt auf 0 Fallback gesetzt statt `Date.parse` mit Zahl aufzurufen.

### Dependencies
- requests auf `>=2.33.1,<3.0.0` angehoben; OSV meldete für `2.31.0`
  drei Advisories, für `2.33.1` keine Treffer.
- scikit-learn auf `>=1.4.0,<1.10.0` angehoben (Dependabot PR #23; `659b6ee`).

### Tests
- Neue Regressionstests für `research_agent.py` (None-Check-Pfade) in `tests/test_research_agent.py`.
- Neue UI-Integrationstests in `tests/test_ui_interactions.py`.
- Neue Web-Companion-Tests in `web_companion/tests/workspace.test.mjs`.
- Aktuelle Testzahl: 211/211 (`python -m pytest tests -q`).

### Build / Release
- EXE neu gebaut 2026-06-01 (PyInstaller --onefile, Launcher); 163/163 Tests grün, Smoke OK. EXE war 2026-05-01; Anlass: core/strategy.py + database.py 2026-05-22.

### Qualität und Repository-Hygiene
- Discoverability-Refresh: README um eine Start-Here-Tabelle und
  Such-/Abgrenzungskontext für local-first Streamlit-Finanzanalyse,
  historische technische Indikatoren, yfinance, SQLite-Watchlists und
  No-Trading-Scope ergänzt; `llms.txt` auf denselben öffentlichen
  Projektkontext und den verifizierten 208-Teststand synchronisiert.
- Interne Steuerdateien `PORTIERUNGSPLAN.md` und `TODO.md` aus dem Git-Tracking
  entfernt; sie bleiben lokal durch `.gitignore` geschützt.
- README-Plattformstrategie ohne Link auf interne Portierungsnotizen formuliert.
- Web/PWA-Brücke für echte App-Daten geschlossen: neuer redigierter
  Workspace-Export `financialproof-workspace-v1.json` sammelt Watchlist,
  Analyse-Presets, abgeschlossene Analyse-Snapshots und Disclaimer-Metadaten
  ohne API-Keys, `.secrets`, SQLite-Datei oder Brokerdaten.
- Sidebar-Einstellungen enthalten jetzt unter `Companion-Export` einen direkten
  JSON-Download für den lokalen Web/PWA-Companion.
- Neue Regressionstests `tests/test_workspace_export.py`; Gesamtsuite jetzt
  165/165 Tests grün (`python -m pytest tests -q`).
- Discoverability- und Repo-Metadatenpflege: README-Einstieg auf
  local-first Streamlit, historische Musteranalyse, No-advice-Scope und
  passende Suchbegriffe geschärft; neues `llms.txt` als maschinenlesbarer
  Projektkontext ergänzt; TESTLOG auf den aktuellen 165-Teststand gebracht.
- Portierungsplanung ergänzt: `PORTIERUNGSPLAN.md` legt Desktop/localhost als
  Vollversion fest, macOS/Linux als Smoke-Ziele und Mobile/Web als späteren
  PWA-Companion ohne Brokerage, Orders oder öffentliche Uploadplattform.
- Geplantes Austauschformat `financialproof-workspace-v1.json` in
  `EXPORTFORMAT.md` dokumentiert; `web_companion/README.md` beschreibt den
  späteren PWA-Companion als read-only Importansicht für Watchlists und
  Analyse-Snapshots.
- Analyse-Preset-Kern ergänzt: SQLite-Schema für `strategies` und
  `analysis_runs`, `core.strategy_manager` für Parser/CRUD/Aktivierung pro
  Asset-Typ sowie `core.strategy` für deskriptive Musterbewertungen.
- Regressionstests für Preset-Schema, Parser, Asset-Typ-Fallbacks,
  Aktivierungslogik und Analyse-Run-Protokoll ergänzt; lokaler Stand jetzt
  165/165 Tests grün (`python -m pytest tests -q`).
- OHLCV-Validierung gehärtet: fehlende `Close`-Spalte wird als
  Validierungsfehler gemeldet statt einen `KeyError` auszulösen.
- Regressionstest für unvollständige OHLCV-Daten ergänzt; lokale Test-Suite
  jetzt 106/106 Tests grün (`python -m pytest tests -q`).
- Roadmap und TODO geschärft: ausgesetzte Trading-/Broker-Funktionen klar von
  aktiven Analyse- und Hardening-Aufgaben getrennt.
- Zentrales Logging mit Console- und Rotating-File-Handler ergänzt.
- Fehlerpfade in DataProvider, ARIMA und Sentiment-Analyse von `print()`
  auf Logger umgestellt.
- Fehlerpfade in Random Forest, Neural Network, Monte Carlo und Mean Reversion
  protokolliert und mit Regressionstests abgesichert.
- Verbleibende stille Fallbacks in `core.data_provider` und
  `analysis.nlp.research_agent` protokolliert; kompatible leere
  Rückgaben bleiben erhalten, sind aber jetzt diagnostisch sichtbar.
- Community-Dateien aktualisiert: Code of Conduct ohne öffentliche
  E-Mail-Adresse und Test-Template mit neutraler Terminologie.
- CI-Workflow wieder versionierbar gemacht und auf `master`/`main`-Branches
  sowie echte Testfehler ausgerichtet.
- TESTLOG und interne Indikator-Kommentare auf neutrale Muster-/Indikator-
  Terminologie aktualisiert.
- Testabdeckung für Analyse-Kernlogik, Job-Executor, Logging und UI-Helfer
  erweitert.
- `env.example`, README-Konfiguration und Screenshot-Pfade auf die aktuelle
  Repository-Struktur gebracht.
- README mit operativen Anleitungen erweitert: Streamlit-/Launcher-Startwege,
  Log- und Wartungsanweisungen, Rate-Limit-Telemetrie-Troubleshooting.
- `.gitignore` um lokale Secret-Dateien, Test-Locks, Release-Artefakte und
  interne Steuerdateien erweitert.
- Windows-Launcher ergänzt: `build_exe.bat` baut eine schlanke
  `FinancialProof.exe`, die die lokale Python-/Streamlit-Installation nutzt
  und fehlende Runtime-Abhängigkeiten vor dem Start meldet.
- README, `START.bat` und Build-Hinweise auf Python 3.10+ und lokale,
  ignorierte Launcher-Artefakte abgestimmt.
- CI-Matrix und `scikit-learn`-Version auf die aktuelle Python-3.10+ Runtime
  abgestimmt, damit Dependency-Installation reproduzierbar bleibt.
- Token-Bucket-Rate-Limiter für yfinance-Aufrufe ergänzt und in
  DataProvider, Sentiment-Analyse und Research-Agent eingebunden.
- Rate-Limit-Telemetrie ergänzt: Token-Buckets zählen Anfragen, verzögerte
  Bezüge, Timeouts, Token-Knappheit und Wartezeiten; die Sidebar zeigt den
  yfinance-Status mit Reset-Funktion.
- README und `env.example` um Rate-Limit-Konfiguration
  (`FINANCIALPROOF_RL_YF_*`) sowie den aktuellen Teststand 143/143 ergänzt.
- Rate-Limit-Sidebar generalisiert: Telemetrie wird über
  `RateLimiter.get_all_stats()` für alle aktiven Buckets angezeigt
  (zukunftssicher für weitere API-Quellen wie Twitter/Reddit-Sentiment),
  Reset-Knopf setzt jetzt alle Bucket-Statistiken global zurück.
  Lokaler Stand: 145/145 Tests grün (`python -m pytest tests -q`).
- Rate-Limit-Sidebar in der Streamlit-Laufumgebung geprüft und aktualisiert:
  Settings werden nach den datenbezogenen yfinance-Aufrufen gerendert, sodass
  der `yfinance`-Bucket direkt im selben App-Run sichtbar ist. Regressionstest
  ergänzt; lokaler Stand: 149/149 Tests grün (`python -m pytest tests -q`).
- Streamlit-UI auf die aktuelle Breiten-API umgestellt:
  `use_container_width=True` wurde durch `width="stretch"` ersetzt.
- `APIKeyManager` ignoriert beschädigte oder nicht objektförmige
  `data/.secrets`-Dateien jetzt robust und kann sie beim nächsten Speichern
  sauber neu schreiben.
- ARIMA- und Monte-Carlo-Chartdaten funktionieren auch mit `RangeIndex`-
  Test- oder Importdaten; Forecast-Startdaten werden zentral indexrobust
  bestimmt.
- ARIMA-Ergebnisse verwenden nur noch deskriptive Musterlabels
  (`bullish`/`bearish`/`neutral`) statt Kauf-/Verkaufsterminologie.
- RSI behandelt reine Aufwärts-, Abwärts- und Flat-Serien korrekt als
  Extrem- beziehungsweise Neutralwerte.
- Repository-Hygiene ergänzt: `.gitattributes` fixiert Text- und
  Binärdatei-Behandlung für konsistente Checkouts.

### Rechtliche Korrekturen (Rechtsaudit Stufe 2, § 32 KWG / § 2 Abs. 9 WpHG)
- **Terminologie neutralisiert:** UI-Labels "Kauf-/Verkaufssignal" durch
  "bullisches/bärisches Muster" ersetzt. Interne Code-Identifier
  (`SignalType.BUY/SELL`, `SignalGenerator`) bleiben aus
  Rückwärtskompatibilitätsgründen erhalten. Docstrings klargestellt:
  rein deskriptive historische Muster, keine Anlageberatung.
- **README:** Prominentes "Keine Anlageberatung / No Financial Advice"-Banner
  direkt unter dem Titel. Marketing-Sprache ("AI-powered deep analyses",
  "automatic buy/sell signals") durch neutrale Formulierungen ersetzt
  ("Statistical pattern analyses", "Indicator calculation",
  "historical pattern recognition"). Hinweis auf die Terminologie-Änderung.
- **Erststart-Acknowledgement:** Neues Streamlit-Modul
  `ui/disclaimer_widget.py` blockiert die Haupt-UI bis der Nutzer vier
  Pflicht-Checkboxen bestätigt hat: keine Anlageberatung, historische
  Muster, Eigenverantwortung, eigenes Risiko (§ 521 BGB). Persistenz
  per SHA-256-Hash des Disclaimer-Texts (`data/.disclaimer_acceptance.json`)
  — bei Textänderung wird erneut bestätigt. `st.stop()` bei Ablehnung.
- Tests entsprechend angepasst (keine Funktionsänderung der
  Analyse-Logik).

### Geplant
- Automatisierte Trading-Anbindung: **out of scope**, bis regulatorische
  Einordnung unter KWG/WpHG/MiFID II geklärt ist.
- Strategy Engine mit Regelwerk
- Backtesting-Engine
- Multi-User Support

---

## [1.0.0] - 2026-01-20

### Hinzugefügt

#### Core
- Streamlit-basierte Web-Anwendung
- SQLite-Datenbank für Persistenz
- yfinance-Integration für Marktdaten
- Caching-System für API-Anfragen

#### Technische Indikatoren
- Simple Moving Average (SMA) - 20, 50, 200 Perioden
- Exponential Moving Average (EMA) - 12, 26 Perioden
- Relative Strength Index (RSI) - 14 Perioden
- Bollinger Bands - 20 Perioden, 2 Standardabweichungen
- MACD - 12/26/9 Konfiguration
- Stochastic Oscillator - 14/3/3 Konfiguration
- Average True Range (ATR) - 14 Perioden

#### Signal-Generierung
- Golden Cross / Death Cross (SMA 50/200)
- RSI Überkauft/Überverkauft Signale
- Bollinger Band Breakouts
- MACD Signal-Kreuzungen
- Candlestick-Muster (Hammer, Engulfing, Doji)

#### Analyse-Module
- **ARIMA**: Historischer Zeitreihen-Fit mit statsmodels
- **Monte Carlo**: Value at Risk Simulation
- **Mean Reversion**: Rückkehr-zum-Mittelwert Analyse
- **Random Forest**: ML-basierte historische Trendklassifikation
- **Neural Network**: Deep Learning Pattern Recognition
- **Sentiment**: News-Stimmungsanalyse mit NLP
- **Research Agent**: Web-Recherche Agent

#### Job-System
- Asynchrone Job-Ausführung
- Job-Queue mit Status-Tracking (pending, running, completed, failed)
- SQLite-Persistenz für Jobs und Ergebnisse
- Automatische Methodenauswahl basierend auf Marktbedingungen

#### Benutzeroberfläche
- Responsive Sidebar mit Watchlist
- Interaktive Candlestick-Charts (Plotly)
- Indikator-Overlays
- Tab-basierte Navigation (Chart, Analyse, Jobs)
- Deutsche Benutzeroberfläche

### Technische Details
- Python 3.9+ Kompatibilität
- Modulare Architektur mit Registry-Pattern
- Abstrakte Basisklassen für Erweiterbarkeit
- Error Handling mit Fallback-Mechanismen

---

## Versionshistorie

| Version | Datum | Beschreibung |
|---------|-------|--------------|
| 1.0.0 | 2026-01-20 | Initiale Release mit allen Basis-Features |

---

## Upgrade-Hinweise

### Von 0.x auf 1.0.0
Dies ist die erste stabile Version. Keine Migration erforderlich.

### Zukünftige Upgrades
Bei Datenbank-Schema-Änderungen wird ein Migrations-Skript bereitgestellt.

---

## Links

- [Roadmap](ROADMAP.md)
- [Contributing](CONTRIBUTING.md)
- [GitHub Issues](https://github.com/assistassets-ai/FinancialProof/issues)

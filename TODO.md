# TODO - FinancialProof

Aufgabenliste im [TODO.md Format](https://github.com/todomd/todo.md) - kompatibel mit Kanban-Visualisierung.

---

## Backlog

> Hinweis: Trading- und Broker-Anbindungen sind regulatorisch ausgesetzt,
> bis KWG/WpHG/MiFID-II-Einordnung geklärt ist. Bis dahin bleibt
> FinancialProof ein reines Analysewerkzeug.

### Ausgesetzt: Trading- und Broker-Anbindung

Diese Aufgaben sind absichtlich nicht im aktiven Backlog. Keine Broker-API,
Order-Funktion, Auto-Trade-Logik oder Secret-Konfiguration implementieren, bis
die regulatorische Einordnung unter KWG/WpHG/MiFID II geklärt ist.

### Phase 8: Analyse-Regelwerk
- [ ] Datenbank-Schema für Analyse-Presets erweitern ~1d #database
- [ ] Regel-Engine für historische Musterklassen ~2d #core
- [ ] Preset-Manager CRUD ~1d #core
- [ ] Regel-JSON Parser ~1d #core
- [ ] Analyse-Konfigurator UI ~2d #ui
- [ ] Asset-Typ spezifische Analyse-Presets ~1d #feature

### Phase 10: Erweiterte Analysen
- [ ] Korrelationsmatrix für Watchlist ~2d #analysis
- [ ] Kointegration für Pairs Trading ~2d #analysis
- [ ] Reinforcement Learning Agent ~5d #ml
- [ ] Twitter/X Sentiment Integration ~2d #nlp
- [ ] Reddit Sentiment (PRAW) ~2d #nlp
- [ ] YouTube Video-Analyse ~2d #nlp

### Phase 11: Performance & Skalierung
- [ ] Redis Cache Integration ~2d #performance
- [ ] Inkrementelle Daten-Updates ~2d #performance
- [ ] Benutzer-Authentifizierung ~3d #feature
- [ ] Multi-User Support ~3d #feature
- [ ] Docker Container ~1d #devops
- [ ] Streamlit Cloud Deployment ~1d #devops

### Phase 12: Historische Simulation & Reporting
- [ ] Backtesting Engine ~5d #feature
- [ ] Performance-Metriken (Sharpe, Drawdown) ~2d #analysis
- [ ] Analyse-Protokoll Export (CSV/PDF) ~1d #feature
- [ ] Täglicher Analyse-Report ~2d #feature
- [ ] Steuer-Übersicht ~2d #feature

---

## In Progress

- [ ] App testen und Bugs fixen #testing

---

## Review

_Keine Aufgaben in Review_

---

## Done ✓

### v1.0.0 - Basis-Features
- [x] Streamlit Web-App Grundgerüst #core
- [x] SQLite Datenbank Setup #database
- [x] yfinance Integration #data
- [x] Technische Indikatoren (SMA, EMA, RSI, BB, MACD) #indicators
- [x] Historische Mustererkennung #indicators
- [x] ARIMA Analyse-Modul #analysis
- [x] Monte Carlo Simulation #analysis
- [x] Mean Reversion Analyse #analysis
- [x] Random Forest Trendklassifikation #ml
- [x] Neural Network Pattern Recognition #ml
- [x] Sentiment-Analyse (News) #nlp
- [x] Research Agent #nlp
- [x] Job-Queue System #core
- [x] Automatische Methodenauswahl #core
- [x] Sidebar mit Watchlist #ui
- [x] Chart-View mit Overlays #ui
- [x] Analyse-Tab #ui
- [x] Job-Queue-Ansicht #ui
- [x] Deutsche Benutzeroberfläche #ui

### Dokumentation
- [x] README.md erstellen #docs
- [x] CHANGELOG.md erstellen #docs
- [x] CONTRIBUTING.md erstellen #docs
- [x] ROADMAP.md erstellen #docs
- [x] LICENSE hinzufügen #docs
- [x] .gitignore konfigurieren #devops
- [x] env.example erstellen #devops

### Qualität & Tests
- [x] Analyse-Kernlogik (Base/Registry/MethodSelector) mit Unit-Tests abgesichert #testing
- [x] Job-/Executor-Logik (Manager, Queue, Executor) mit Unit-Tests abgesichert #testing
- [x] Test-Suite von optionalen Abhängigkeiten entkoppelt (yfinance/cryptography) #testing
- [x] Disclaimer-Persistenz und UI-Helfer (Formatierung, Cleanup-Retention) mit Unit-Tests abgesichert #testing
- [x] Streamlit-Interaktionspfade für Sidebar, Chart-View und Analyse-Trigger mit Tests abgesichert #testing
- [x] OHLCV-Validierung gegen fehlende `Close`-Spalte abgesichert #testing

---

## Technische Schulden

- [x] Interaktions-/E2E-Tests für verbleibende Streamlit-Views und Integrationspfade schreiben ~3d #testing
- [x] Analyzer-Fehlerlogging für Random Forest, Neural Network, Monte Carlo und Mean Reversion mit Regressionstests absichern ~1d #quality
- [ ] Error Handling verbessern ~2d #quality
- [x] Logging-System einführen ~1d #quality
- [ ] API Rate Limiting implementieren ~1d #quality
- [x] Docstrings vervollständigen ~2d #docs
- [ ] Type Hints überall hinzufügen ~2d #quality

---

## Bugs

_Keine bekannten Bugs_

---

## Legende

**Tags:**
- `#feature` - Neue Funktionalität
- `#core` - Kern-Komponente
- `#ui` - Benutzeroberfläche
- `#analysis` - Analyse-Modul
- `#ml` - Machine Learning
- `#nlp` - Natural Language Processing
- `#database` - Datenbank
- `#security` - Sicherheit
- `#performance` - Performance
- `#devops` - DevOps/Deployment
- `#testing` - Tests
- `#quality` - Code-Qualität
- `#docs` - Dokumentation

**Zeitschätzungen:**
- `~1d` - 1 Tag
- `~2d` - 2 Tage
- `~3d` - 3 Tage
- `~5d` - 5 Tage (1 Woche)

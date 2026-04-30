# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Qualität und Repository-Hygiene
- Zentrales Logging mit Console- und Rotating-File-Handler ergänzt.
- Fehlerpfade in DataProvider, ARIMA und Sentiment-Analyse von `print()`
  auf Logger umgestellt.
- Fehlerpfade in Random Forest, Neural Network, Monte Carlo und Mean Reversion
  protokolliert und mit Regressionstests abgesichert.
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
- `.gitignore` um lokale Secret-Dateien, Test-Locks, Release-Artefakte und
  interne Steuerdateien erweitert.

### Rechtliche Korrekturen (Rechtsaudit Stufe 2, § 32 KWG / § 2 Abs. 9 WpHG)
- **Terminologie neutralisiert:** UI-Labels „Kauf-/Verkaufssignal" durch
  „bullisches/bärisches Muster" ersetzt. Interne Code-Identifier
  (`SignalType.BUY/SELL`, `SignalGenerator`) bleiben aus
  Rückwärtskompatibilitätsgründen erhalten. Docstrings klargestellt:
  rein deskriptive historische Muster, keine Anlageberatung.
- **README:** Prominentes „Keine Anlageberatung / No Financial Advice"-Banner
  direkt unter dem Titel. Marketing-Sprache („AI-powered deep analyses",
  „automatic buy/sell signals") durch neutrale Formulierungen ersetzt
  („Statistical pattern analyses", „Indicator calculation",
  „historical pattern recognition"). Hinweis auf die Terminologie-Änderung.
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

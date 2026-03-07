# FinancialProof

Eine browserbasierte Finanz-Analyse Web-App mit KI-gestützten Tiefenanalysen.

## Features

- **Technische Indikatoren**: SMA, EMA, RSI, Bollinger Bands, MACD, Stochastic, ATR
- **Automatische Signale**: Kauf-/Verkaufssignale basierend auf technischen Mustern
- **KI-Analysen**:
  - ARIMA Zeitreihenprognose
  - Monte Carlo Simulation (VaR)
  - Mean Reversion Analyse
  - Random Forest Trendvorhersage
  - Neural Network Pattern Recognition
  - Sentiment-Analyse (News)
  - Web Research Agent
- **Job-Queue System**: Asynchrone Analyse-Aufträge mit SQLite-Persistenz
- **Watchlist**: Portfolio-Übersicht mit mehreren Assets
- **Deutsche Benutzeroberfläche**

## Screenshots

```
┌─────────────────────────────────────────────────────────────┐
│  📊 Chart    │  🧠 Tiefen-Analyse    │  📋 Aufträge         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Candlestick Chart mit Indikatoren]                       │
│                                                             │
│  ────────────────────────────────────────────────────────  │
│  RSI: 45.2  │  Signal: NEUTRAL  │  Trend: Seitwärts        │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Voraussetzungen

- Python 3.9+
- pip

### Setup

1. **Repository klonen**
   ```bash
   git clone https://github.com/username/FinancialProof.git
   cd FinancialProof
   ```

2. **Virtuelle Umgebung erstellen** (empfohlen)
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Dependencies installieren**
   ```bash
   pip install -r requirements.txt
   ```

4. **Umgebungsvariablen konfigurieren** (optional)
   ```bash
   cp .env.example .env
   # .env Datei bearbeiten und API-Keys eintragen
   ```

5. **App starten**
   ```bash
   streamlit run app.py
   ```

6. **Browser öffnen**
   ```
   http://localhost:8501
   ```

## Projektstruktur

```
FinancialProof/
├── app.py                  # Hauptanwendung
├── config.py               # Konfiguration
├── requirements.txt        # Dependencies
│
├── core/
│   ├── database.py         # SQLite Datenbank
│   └── data_provider.py    # yfinance Wrapper
│
├── indicators/
│   ├── technical.py        # Technische Indikatoren
│   └── signals.py          # Signal-Generierung
│
├── analysis/
│   ├── base.py             # Abstrakte Basisklasse
│   ├── registry.py         # Analyse-Registry
│   ├── statistical/        # ARIMA, Monte Carlo, Mean Reversion
│   ├── ml/                 # Random Forest, Neural Network
│   └── nlp/                # Sentiment, Research Agent
│
├── jobs/
│   ├── manager.py          # Job-Verwaltung
│   └── executor.py         # Job-Ausführung
│
├── ui/
│   ├── sidebar.py          # Sidebar-Komponente
│   ├── chart_view.py       # Chart-Ansicht
│   ├── analysis_view.py    # Analyse-Tab
│   └── job_queue.py        # Job-Queue-Ansicht
│
└── data/
    └── financial.db        # SQLite Datenbank
```

## Verwendung

### Symbol eingeben

Gib ein Ticker-Symbol in der Sidebar ein:
- Aktien: `AAPL`, `MSFT`, `GOOGL`
- ETFs: `SPY`, `QQQ`, `VOO`
- Krypto: `BTC-USD`, `ETH-USD`
- Indizes: `^GSPC`, `^DJI`

### Analyse starten

1. Wähle einen Zeitraum (1M - 5J)
2. Aktiviere gewünschte Indikatoren
3. Wechsle zum Tab "Tiefen-Analyse"
4. Wähle eine Analysemethode und starte den Auftrag

### Ergebnisse ansehen

- Tab "Aufträge" zeigt alle laufenden und abgeschlossenen Jobs
- Klicke auf einen Job für Details und Empfehlungen

## Konfiguration

### Umgebungsvariablen

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `OPENAI_API_KEY` | OpenAI API Key für Research Agent | - |
| `TWITTER_BEARER_TOKEN` | Twitter API für Sentiment | - |
| `YOUTUBE_API_KEY` | YouTube API für Video-Analyse | - |

### Einstellungen in `config.py`

```python
DEFAULT_TICKER = "AAPL"      # Standard-Symbol
CACHE_TTL_MARKET_DATA = 3600 # Cache-Dauer (Sekunden)
```

## Analyse-Module

| Modul | Kategorie | Beschreibung |
|-------|-----------|--------------|
| ARIMA | Statistik | Zeitreihen-Prognose |
| Monte Carlo | Statistik | Value at Risk Simulation |
| Mean Reversion | Statistik | Rückkehr-zum-Mittelwert Analyse |
| Random Forest | ML | Trend-Klassifikation |
| Neural Network | ML | Muster-Erkennung |
| Sentiment | NLP | News-Stimmungsanalyse |
| Research Agent | NLP | Web-Recherche |

## Technologie-Stack

- **Frontend**: Streamlit
- **Charts**: Plotly
- **Daten**: yfinance, pandas, numpy
- **ML**: scikit-learn, TensorFlow (optional)
- **NLP**: transformers, TextBlob
- **Datenbank**: SQLite

## Roadmap

Siehe [ROADMAP.md](ROADMAP.md) für geplante Features:

- [ ] Phase 7: Trading-Anbindung (Alpaca, CCXT)
- [ ] Phase 8: Strategy Engine
- [ ] Phase 9: Automatisiertes Trading
- [ ] Phase 10: Erweiterte Analysen
- [ ] Phase 11: Performance & Skalierung
- [ ] Phase 12: Backtesting & Reporting

## Mitwirken

Beiträge sind willkommen! Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

## Lizenz

GPL v3 - Siehe [LICENSE](LICENSE)

## Haftungsausschluss

**Dieses Tool dient nur zu Informationszwecken und stellt keine Anlageberatung dar.**

Die bereitgestellten Analysen und Signale sind keine Empfehlung zum Kauf oder Verkauf von Wertpapieren. Investitionen in Finanzmärkte sind mit Risiken verbunden. Vergangene Performance ist kein Indikator für zukünftige Ergebnisse.

## Changelog

Siehe [CHANGELOG.md](CHANGELOG.md) für alle Änderungen.

---

## English

A browser-based financial analysis web app with technical indicators, AI analysis, and job queue.

### Features

- Technical indicators (RSI, MACD, etc.)
- AI-powered market analysis
- Background job queue
- Interactive charts

### Installation

```bash
git clone https://github.com/lukisch/REL-PUB_FinancialProof.git
cd REL-PUB_FinancialProof
pip install -r requirements.txt
python "app.py"
```

### License

See [LICENSE](LICENSE) for details.

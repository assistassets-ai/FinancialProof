# FinancialProof

A browser-based financial analysis web app with AI-powered deep analyses.

## Features

- **Technical Indicators**: SMA, EMA, RSI, Bollinger Bands, MACD, Stochastic, ATR
- **Automatic Signals**: Buy/sell signals based on technical patterns
- **AI Analyses**:
  - ARIMA time series forecasting
  - Monte Carlo simulation (VaR)
  - Mean Reversion analysis
  - Random Forest trend prediction
  - Neural Network pattern recognition
  - Sentiment analysis (News)
  - Web Research Agent
- **Job Queue System**: Asynchronous analysis tasks with SQLite persistence
- **Watchlist**: Portfolio overview with multiple assets
- **German User Interface**

## Screenshots

**Light Theme:**

<img src="screenshot_light.jpg" alt="FinancialProof Light Theme" width="700">

**Dark Theme:**

<img src="screenshot_dark.jpg" alt="FinancialProof Dark Theme" width="700">

## Installation

### Prerequisites

- Python 3.9+
- pip

### Setup

1. **Clone repository**
   ```bash
   git clone https://github.com/assistassets-ai/FinancialProof.git
   cd FinancialProof
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (optional)
   ```bash
   cp .env.example .env
   # Edit .env file and add API keys
   ```

5. **Launch app**
   ```bash
   streamlit run app.py
   ```

6. **Open browser**
   ```
   http://localhost:8501
   ```

## Project Structure

```
FinancialProof/
├── app.py                   # Main application
├── config.py                # Configuration
├── requirements.txt         # Dependencies
│
├── core/
│   ├── database.py          # SQLite database
│   └── data_provider.py     # yfinance wrapper
│
├── indicators/
│   ├── technical.py         # Technical indicators
│   └── signals.py           # Signal generation
│
├── analysis/
│   ├── base.py              # Abstract base class
│   ├── registry.py          # Analysis registry
│   ├── statistical/         # ARIMA, Monte Carlo, Mean Reversion
│   ├── ml/                  # Random Forest, Neural Network
│   └── nlp/                 # Sentiment, Research Agent
│
├── jobs/
│   ├── manager.py           # Job management
│   └── executor.py          # Job execution
│
├── ui/
│   ├── sidebar.py           # Sidebar component
│   ├── chart_view.py        # Chart view
│   ├── analysis_view.py     # Analysis tab
│   └── job_queue.py         # Job queue view
│
└── data/
    └── financial.db         # SQLite database
```

## Usage

### Enter Symbol

Enter a ticker symbol in the sidebar:
- Stocks: `AAPL`, `MSFT`, `GOOGL`
- ETFs: `SPY`, `QQQ`, `VOO`
- Crypto: `BTC-USD`, `ETH-USD`
- Indices: `^GSPC`, `^DJI`

### Start Analysis

1. Select a time period (1M - 5Y)
2. Activate desired indicators
3. Switch to the "Deep Analysis" tab
4. Select an analysis method and start the job

### View Results

- The "Jobs" tab shows all running and completed jobs
- Click on a job for details and recommendations

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for Research Agent | - |
| `TWITTER_BEARER_TOKEN` | Twitter API for Sentiment | - |
| `YOUTUBE_API_KEY` | YouTube API for video analysis | - |

### Settings in `config.py`

```python
DEFAULT_TICKER = "AAPL"      # Default symbol
CACHE_TTL_MARKET_DATA = 3600 # Cache duration (seconds)
```

## Analysis Modules

| Module | Category | Description |
|--------|----------|-------------|
| ARIMA | Statistics | Time series forecasting |
| Monte Carlo | Statistics | Value at Risk simulation |
| Mean Reversion | Statistics | Mean-reversion analysis |
| Random Forest | ML | Trend classification |
| Neural Network | ML | Pattern recognition |
| Sentiment | NLP | News sentiment analysis |
| Research Agent | NLP | Web research |

## Technology Stack

- **Frontend**: Streamlit
- **Charts**: Plotly
- **Data**: yfinance, pandas, numpy
- **ML**: scikit-learn, TensorFlow (optional)
- **NLP**: transformers, TextBlob
- **Database**: SQLite

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features:

- [ ] Phase 7: Trading integration (Alpaca, CCXT)
- [ ] Phase 8: Strategy Engine
- [ ] Phase 9: Automated Trading
- [ ] Phase 10: Extended Analyses
- [ ] Phase 11: Performance & Scaling
- [ ] Phase 12: Backtesting & Reporting

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

GPL v3 - See [LICENSE](LICENSE)

## Disclaimer

**This tool is for informational purposes only and does not constitute investment advice.**

The analyses and signals provided are not recommendations to buy or sell securities. Investments in financial markets involve risks. Past performance is not an indicator of future results.

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

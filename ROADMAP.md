# FinancialProof - Entwicklungs-Roadmap

> **Rechtlicher Hinweis:** FinancialProof ist ein technisches Werkzeug
> zur statistischen Mustererkennung, **keine Anlageberatung** (§ 32 KWG
> / § 2 Abs. 9 WpHG). Die unten skizzierten Trading-Phasen sind
> **ausgesetzt**, bis die regulatorische Einordnung unter KWG / WpHG /
> MiFID II geklärt ist. Siehe README.

## Aktueller Stand (v1.0) ✅

Die Basis-Anwendung ist vollständig implementiert:

- ✅ Browserbasierte Streamlit Web-App
- ✅ Watchlist mit Portfolio-Übersicht
- ✅ Technische Indikatoren (SMA, EMA, RSI, Bollinger, MACD)
- ✅ Automatische Erkennung bullischer/bärischer Muster (historisch, deskriptiv)
- ✅ 7 Analyse-Module (ARIMA, Monte Carlo, Mean Reversion, Random Forest, Neural Network, Sentiment, Research Agent)
- ✅ Job-Queue System mit SQLite-Persistenz
- ✅ Regelbasierte automatische Methodenauswahl
- ✅ Deutsche Benutzeroberfläche
- ✅ Erststart-Acknowledgement (§ 32 KWG / § 2 Abs. 9 WpHG)

---

## Phase 7: Trading-Anbindung ⏸️ AUSGESETZT (regulatorisch)

### 7.0 Konfiguration erweitern
Keine aktiven Broker- oder Trading-API-Konfigurationen im Repository
pflegen. Solche Variablen bleiben ausgesetzt, bis die regulatorische
Einordnung geklärt ist.

### 7.1 Broker-Integration
**Ziel:** Verbindung zu echten Trading-Konten herstellen

#### Unterstützte Broker (geplant):
| Broker | Region | Asset-Typen | API |
|--------|--------|-------------|-----|
| **Alpaca** | USA | Aktien, ETFs | REST + WebSocket |
| **Interactive Brokers** | Global | Alle | TWS API |
| **CCXT** | Global | Krypto | Universal |
| **Trade Republic** | EU | Aktien, ETFs, Krypto | (Inoffiziell) |

#### Neue Dateien:
```
core/
├── trader.py           # Trading-Bot Hauptklasse
├── broker_alpaca.py    # Alpaca-spezifische Implementation
├── broker_ccxt.py      # Krypto-Börsen via CCXT
└── broker_base.py      # Abstrakte Broker-Klasse
```

#### Code-Beispiel: `core/trader.py`
```python
import alpaca_trade_api as tradeapi
from config import Config

class TradingBot:
    def __init__(self):
        self.api = tradeapi.REST(
            Config.API_KEY,
            Config.API_SECRET,
            Config.API_BASE_URL,
            api_version='v2'
        )

    def get_account_summary(self):
        """Holt Kontostand und Buying Power"""
        account = self.api.get_account()
        return {
            "cash": float(account.cash),
            "equity": float(account.equity),
            "buying_power": float(account.buying_power),
            "status": account.status
        }

    def get_positions(self):
        """Holt alle offenen Aktien-Positionen"""
        positions = self.api.list_positions()
        return [
            {
                "symbol": p.symbol,
                "qty": float(p.qty),
                "current_price": float(p.current_price),
                "profit_usd": float(p.unrealized_pl),
                "profit_pct": float(p.unrealized_plpc) * 100
            }
            for p in positions
        ]

    def place_order(self, symbol, qty, side="buy", type="market"):
        """Platziert einen Trade (Market Order)"""
        order = self.api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=type,
            time_in_force='gtc'
        )
        return {"status": "success", "order_id": order.id}
```

#### Funktionen:
- [ ] Konto-Übersicht (Cash, Equity, Buying Power)
- [ ] Offene Positionen anzeigen
- [ ] Market Orders platzieren
- [ ] Limit Orders platzieren
- [ ] Stop-Loss Orders
- [ ] Order-Historie

#### Sicherheitsmaßnahmen:
- [ ] Paper Trading Modus (Spielgeld) als Standard
- [ ] Bestätigungs-Dialog vor echten Trades
- [ ] Maximale Order-Größe konfigurierbar
- [ ] Tägliches Trading-Limit
- [ ] Keine Leerverkäufe ohne explizite Aktivierung

---

### 7.2 Trading-Dashboard (UI)
**Neue Datei:** `ui/trading_view.py`

#### Code-Beispiel: `ui/trading_view.py`
```python
import streamlit as st
from core.trader import TradingBot
import pandas as pd

def render_trading_dashboard():
    st.header("Live Trading Portfolio (Paper Account)")

    bot = TradingBot()
    account = bot.get_account_summary()

    if "error" in account:
        st.error(f"Verbindung fehlgeschlagen: {account['error']}")
        return

    # Konto-Übersicht
    c1, c2, c3 = st.columns(3)
    c1.metric("Cash", f"${account['cash']:,.2f}")
    c2.metric("Portfolio Wert", f"${account['equity']:,.2f}")
    c3.metric("Buying Power", f"${account['buying_power']:,.2f}")

    st.divider()

    # Offene Positionen
    st.subheader("Offene Positionen")
    positions = bot.get_positions()

    if positions:
        df_pos = pd.DataFrame(positions)
        st.dataframe(df_pos)
    else:
        st.info("Keine offenen Positionen.")

    st.divider()

    # Schnelle Order
    st.subheader("Schnelle Order")
    symbol = st.text_input("Symbol", "AAPL").upper()
    qty = st.number_input("Menge", min_value=1, value=1)
    action = st.radio("Aktion", ["Kaufen", "Verkaufen"])

    if st.button("Order ausführen"):
        side = "buy" if action == "Kaufen" else "sell"
        res = bot.place_order(symbol, qty, side)
        if res['status'] == 'success':
            st.success(f"Order platziert!")
            st.rerun()
        else:
            st.error(res.get('message', 'Fehler'))
```

#### Komponenten:
```
┌─────────────────────────────────────────────────────────┐
│  🏦 Live Trading Portfolio (Paper Account)              │
├─────────────────────────────────────────────────────────┤
│  Cash: $10,000  │  Equity: $12,500  │  Buying: $8,000   │
├─────────────────────────────────────────────────────────┤
│  📦 Offene Positionen                                   │
│  ┌───────┬───────┬──────────┬──────────┬───────────┐   │
│  │Symbol │ Menge │ Akt.Kurs │ Gewinn $ │ Gewinn %  │   │
│  ├───────┼───────┼──────────┼──────────┼───────────┤   │
│  │ AAPL  │  10   │  $175.50 │  +$125   │  +7.7%    │   │
│  │ MSFT  │   5   │  $380.20 │  -$45    │  -2.3%    │   │
│  └───────┴───────┴──────────┴──────────┴───────────┘   │
├─────────────────────────────────────────────────────────┤
│  ⚡ Schnelle Order          │  🧠 KI-Empfehlungen       │
│  Symbol: [AAPL    ]         │  Job #12: 🟢 BUY MSFT    │
│  Menge:  [1       ]         │  Konfidenz: 88%          │
│  (●) Kaufen  ( ) Verkaufen  │  [Jetzt Handeln]         │
│  [Order ausführen]          │                          │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 8: Strategy Engine (Regelwerk) 🔜

### 8.1 Datenbank-Schema Erweiterung

```sql
-- Strategien & Regeln
CREATE TABLE strategies (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    asset_type TEXT,              -- 'STOCK', 'CRYPTO', 'FOREX', 'ETF'
    rules_json TEXT,              -- Regeln als JSON
    is_active INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trading-Historie
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    side TEXT,                    -- 'buy', 'sell'
    quantity REAL,
    price REAL,
    strategy_id INTEGER,
    job_id INTEGER,               -- Welche Analyse hat den Trade ausgelöst?
    status TEXT,                  -- 'pending', 'filled', 'cancelled'
    broker_order_id TEXT,
    executed_at TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```

### 8.2 Strategy Manager
**Neue Dateien:**
```
core/
├── strategy.py         # Strategy Engine (Regelauswertung)
└── strategy_manager.py # CRUD für Strategien
```

#### Code-Beispiel: `core/strategy.py`
```python
from core.strategy_manager import StrategyManager

class StrategyEngine:
    def evaluate(self, analysis_result, market_data, symbol):
        # 1. Asset Typ bestimmen
        asset_type = "CRYPTO" if "-" in symbol or "BTC" in symbol else "STOCK"

        # 2. Strategie aus DB laden
        strategy_data = StrategyManager.get_active_strategy(asset_type)
        rules = strategy_data["rules"]

        # 3. Daten extrahieren
        summary = analysis_result.get("summary", "")
        confidence = float(analysis_result.get("confidence", 0))
        current_rsi = market_data['RSI'].iloc[-1] if 'RSI' in market_data else 50

        reasons = []
        passed = True

        # Regel: Min Confidence
        min_conf = rules.get("min_confidence", 0.5)
        if confidence < min_conf:
            passed = False
            reasons.append(f"Unsicher ({confidence:.2f} < {min_conf})")

        # Regel: Max RSI
        max_rsi = rules.get("max_rsi", 100)
        if current_rsi > max_rsi:
            passed = False
            reasons.append(f"RSI zu hoch ({current_rsi:.0f} > {max_rsi})")

        return {
            "strategy_name": strategy_data["name"],
            "action": "BUY" if passed else "HOLD",
            "reason": "Regeln erfüllt" if passed else ", ".join(reasons)
        }
```

#### Code-Beispiel: `core/strategy_manager.py`
```python
import json
from core.database import db

class StrategyManager:
    @staticmethod
    def get_active_strategy(asset_type="STOCK"):
        """Holt die aktive Strategie für einen Asset-Typ"""
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, rules_json FROM strategies
            WHERE asset_type = ? AND is_active = 1
            LIMIT 1
        """, (asset_type,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {"name": row[0], "rules": json.loads(row[1])}
        else:
            return {
                "name": "Fallback",
                "rules": {"min_confidence": 0.80, "max_rsi": 70}
            }

    @staticmethod
    def save_strategy(name, asset_type, rules_dict):
        """Speichert oder aktualisiert eine Strategie"""
        conn = db.get_connection()
        cursor = conn.cursor()
        rules_json = json.dumps(rules_dict)

        cursor.execute("""
            INSERT INTO strategies (name, asset_type, rules_json, is_active)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(name) DO UPDATE SET
                rules_json = excluded.rules_json,
                asset_type = excluded.asset_type
        """, (name, asset_type, rules_json))
        conn.commit()
        conn.close()
        return True
```

#### Regel-Struktur (JSON):
```json
{
  "name": "Krypto Aggressiv",
  "asset_type": "CRYPTO",
  "buy_rules": {
    "min_confidence": 0.85,
    "max_rsi": 40,
    "required_signals": ["bullish"],
    "min_volume_ratio": 1.5
  },
  "sell_rules": {
    "min_confidence": 0.80,
    "min_rsi": 70,
    "stop_loss_percent": -5,
    "take_profit_percent": 15
  },
  "position_sizing": {
    "max_position_percent": 10,
    "max_positions": 5
  }
}
```

### 8.3 Strategie-Konfigurator (UI)
**Neue Datei:** `ui/settings_view.py`

#### Code-Beispiel: `ui/settings_view.py`
```python
import streamlit as st
from core.strategy_manager import StrategyManager

def render_settings_view():
    st.header("Strategie-Konfigurator")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Neue Strategie anlegen")

        strat_name = st.text_input("Name der Strategie", "Krypto Aggressiv")
        asset_type = st.selectbox("Anwenden auf:", ["STOCK", "CRYPTO", "FOREX"])

        st.markdown("---")
        st.write("**Regelwerk definieren:**")

        min_conf = st.slider("Mindest-Sicherheit (KI)", 0.5, 0.99, 0.80)
        max_rsi = st.number_input("Maximaler RSI (Kauf-Limit)", 30, 90, 70)

        if st.button("Strategie speichern"):
            rules = {"min_confidence": min_conf, "max_rsi": max_rsi}
            if StrategyManager.save_strategy(strat_name, asset_type, rules):
                st.success(f"Strategie '{strat_name}' gespeichert!")

    with col2:
        st.subheader("Aktive Regelwerke")
        # Hier Strategien aus DB anzeigen
```

#### Funktionen:
- [ ] Strategie erstellen/bearbeiten/löschen
- [ ] Regeln per Slider/Input definieren
- [ ] Asset-Typ zuweisen (Aktien, Krypto, etc.)
- [ ] Strategie aktivieren/deaktivieren
- [ ] Backtesting der Strategie (historische Simulation)

---

## Phase 9: Automatisiertes Trading 🔜

### 9.1 Auto-Trading Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Analyse    │────▶│  Strategy   │────▶│  Trading    │
│  (KI/Stats) │     │  Engine     │     │  Bot        │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
 "AAPL: Bullish"    "Regeln erfüllt:    "Order gesendet:
  Konfidenz: 88%     BUY Signal"         BUY 5x AAPL"
```

#### Code-Beispiel: Auto-Trade Integration in `jobs/manager.py`
```python
from core.strategy import StrategyEngine
from core.trader import TradingBot

class JobManager:
    @staticmethod
    def auto_trade_based_on_result(job_id, symbol, result_data, market_data):
        """
        Entscheidet basierend auf KI-Ergebnis und Strategie, ob gehandelt wird.
        """
        engine = StrategyEngine()
        decision = engine.evaluate(result_data, market_data, symbol)

        if decision["action"] == "BUY":
            bot = TradingBot()
            trade_res = bot.place_order(symbol=symbol, qty=1, side="buy")
            return f"Auto-Trade: {trade_res['message']}"

        return f"Kein Trade: {decision['reason']}"
```

### 9.2 Automatisierungs-Level

| Level | Name | Beschreibung |
|-------|------|--------------|
| 0 | **Manuell** | Alle Trades von Hand |
| 1 | **Empfehlungen** | KI zeigt Signale, User entscheidet |
| 2 | **Semi-Auto** | KI fragt vor jedem Trade nach Bestätigung |
| 3 | **Auto (Paper)** | Automatisch auf Paper-Konto |
| 4 | **Auto (Live)** | Automatisch auf echtem Konto (⚠️ Risiko!) |

### 9.3 Sicherheits-Features

- [ ] **Kill Switch**: Sofortiger Stopp aller Auto-Trades
- [ ] **Tägliches Limit**: Max. Verlust pro Tag (z.B. -3%)
- [ ] **Positionslimit**: Max. % des Portfolios pro Trade
- [ ] **Zeitfenster**: Trading nur zu bestimmten Uhrzeiten
- [ ] **Benachrichtigungen**: Email/Push bei Trades

---

## Phase 10: Erweiterte Analysen 🔮

### 10.1 Korrelationsanalyse
**Neue Datei:** `analysis/correlation/cointegration.py`

- [ ] Korrelationsmatrix für Watchlist
- [ ] Kointegration für Pairs Trading
- [ ] Diversifikations-Score

### 10.2 Reinforcement Learning
**Neue Datei:** `analysis/ml/reinforcement.py`

- [ ] Multi-Timeframe Trend-Erkennung (kurz/mittel/lang)
- [ ] RL-Agent der aus historischen Daten lernt
- [ ] Adaptive Strategie-Optimierung

### 10.3 Erweiterte Sentiment-Quellen

| Quelle | API | Status |
|--------|-----|--------|
| yfinance News | Built-in | ✅ Implementiert |
| Twitter/X | Tweepy | 🔜 Geplant |
| YouTube | Google API | 🔜 Geplant |
| Reddit | PRAW | 🔜 Geplant |
| StockTwits | REST API | 🔜 Geplant |

---

## Phase 11: Performance & Skalierung 🔮

### 11.1 Caching & Performance
- [ ] Redis Cache für häufige Abfragen
- [ ] Inkrementelle Daten-Updates statt Voll-Refresh
- [ ] Background-Worker für lange Analysen

### 11.2 Multi-User Support
- [ ] Benutzer-Authentifizierung
- [ ] Separate Watchlists/Strategien pro User
- [ ] Admin-Dashboard

### 11.3 Deployment
- [ ] Docker-Container
- [ ] Streamlit Cloud Deployment
- [ ] Mobile-optimierte Ansicht

---

## Phase 12: Backtesting & Reporting 🔮

### 12.1 Backtesting-Engine
**Neue Dateien:**
```
backtesting/
├── engine.py           # Backtesting-Logik
├── metrics.py          # Performance-Metriken
└── visualizer.py       # Chart-Generierung
```

#### Metriken:
- [ ] Gesamtrendite
- [ ] Sharpe Ratio
- [ ] Maximum Drawdown
- [ ] Win Rate
- [ ] Profit Factor

### 12.2 Reporting
- [ ] Täglicher Performance-Report
- [ ] Trade-Protokoll Export (CSV/PDF)
- [ ] Steuer-Übersicht

---

## Priorisierte Nächste Schritte

### Kurzfristig (Nächste Version)
1. **Error Handling härten** - verbleibende Module auf klare Fehlerpfade und Logging prüfen
2. **API Rate Limiting** - externe Datenquellen kontrolliert und nachvollziehbar abfragen
3. **Dokumentation ergänzen** - API-/CLI-nahe Beispiele und Betriebshinweise ausbauen
4. **Trading-/Broker-Funktionen ausgesetzt lassen** - erst nach regulatorischer Klärung

### Mittelfristig
5. **Twitter/YouTube Sentiment** - Mehr Datenquellen ohne Anlageempfehlungs-Framing
6. **Backtesting als reine historische Auswertung** - keine Live-Order-Funktion
7. **Barrierefreiheit und Mehrsprachigkeit** - UI-Texte und README weiter schärfen

### Langfristig
8. **Multi-User & Cloud** - Für mehrere Nutzer
9. **Mobile App** - React Native oder Flutter

---

## Technische Schulden & Verbesserungen

- [x] Analyse-, Job-, Logging- und UI-Helfer-Tests erweitert
- [ ] Error Handling verbessern
- [x] Logging-System einführen
- [ ] API Rate Limiting
- [ ] Dokumentation (Docstrings, README)

---

## Ressourcen & Links

### APIs
- [Alpaca Markets](https://alpaca.markets/) - nur als ausgesetzte Referenz, keine aktuelle Integration
- [CCXT](https://github.com/ccxt/ccxt) - nur als ausgesetzte Referenz, keine aktuelle Integration
- [yfinance](https://github.com/ranaroussi/yfinance) - Marktdaten

### Bibliotheken für Backtesting
- [Backtrader](https://www.backtrader.com/)
- [Zipline](https://github.com/quantopian/zipline)
- [VectorBT](https://github.com/polakowo/vectorbt)

---

## Changelog

### v1.0.0 (Aktuell)
- Initiale Version mit allen Basis-Features
- 7 Analyse-Module implementiert
- Job-Queue mit Persistenz
- Deutsche UI

### v1.1.0 (Geplant)
- Hardening, Logging und Dokumentationsausbau
- API Rate Limiting
- Erweiterte historische Auswertungen ohne Broker-Integration

### v1.2.0 (Geplant)
- Backtesting als reine historische Simulation
- Twitter/YouTube Sentiment
- Mehrsprachige Dokumentation

---

*Letzte Aktualisierung: April 2026*

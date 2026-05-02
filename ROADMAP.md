# FinancialProof - Entwicklungs-Roadmap

> **Rechtlicher Hinweis:** FinancialProof ist ein technisches Werkzeug
> zur statistischen Mustererkennung, **keine Anlageberatung** (§ 32 KWG
> / § 2 Abs. 9 WpHG). Die unten skizzierten Trading-Phasen sind
> **ausgesetzt**, bis die regulatorische Einordnung unter KWG / WpHG /
> MiFID II geklärt ist. Siehe README.

## Aktueller Stand (v1.1-dev) ✅

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
- ✅ Logging-Hardening und 134 automatisierte Tests
- ✅ OHLCV-Validierung meldet fehlende Pflichtspalten ohne `KeyError`
- ✅ Rate Limiting (Token-Bucket) für yfinance-Aufrufe in DataProvider, Sentiment- und Research-Agent
- ✅ Rate-Limit-Telemetrie für alle Buckets (Sidebar-Anzeige, automatisch erweiterbar für künftige API-Quellen)

---

## Phase 7: Trading-Anbindung ⏸️ AUSGESETZT (regulatorisch)

Dieser Abschnitt ist ein historischer Konzeptentwurf, **kein aktiver
Implementierungsplan**. Keine Broker-API, Order-Funktion, Auto-Trade-Logik
oder Secret-Konfiguration implementieren, bis die regulatorische Einordnung
unter KWG/WpHG/MiFID II geklärt ist.

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

#### Nicht im aktiven Scope

Keine `trader.py`, Broker-Adapter, Order-API oder Broker-Credential-Konfiguration
anlegen. Historische Recherche zu Broker-APIs bleibt außerhalb des
Repository-Codes und darf keine Secrets, Beispiel-Keys oder ausführbaren
Order-Flow enthalten.

#### Gesperrte Funktionen:
- [ ] Keine Konto-Übersicht
- [ ] Keine Positionsanzeige
- [ ] Keine Order-Erfassung
- [ ] Keine Order-Historie
- [ ] Keine Broker-Zugangsdaten

#### Sicherheitsmaßnahmen:
- [ ] Broker-/Order-Code bleibt aus dem Repository entfernt
- [ ] Dokumentation enthält keine ausführbaren Order-Beispiele
- [ ] Tests und Templates enthalten keine Beispiel-Secrets

---

### 7.2 Broker-UI (gesperrt)

Kein UI für Konten, Positionen oder Orders anlegen. Zulässig bleiben nur
deskriptive Analyseansichten für historische Daten, Charts, Jobs und lokale
Diagnostik.

---

## Phase 8: Analyse-Regelwerk 🔜

Ziel ist ein Regelwerk für **historische Analyse-Presets**, nicht für
Order-Entscheidungen. Alle Ergebnisse bleiben deskriptiv und dürfen nicht als
Kauf-/Verkaufsempfehlung formuliert werden.

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

-- Historische Analyse-Auswertung
CREATE TABLE analysis_runs (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    strategy_id INTEGER,
    job_id INTEGER,               -- Welche Analyse wurde ausgewertet?
    pattern_class TEXT,           -- 'bullish', 'bearish', 'neutral'
    notes TEXT,
    evaluated_at TIMESTAMP,
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
            "pattern_class": "bullish" if passed else "neutral",
            "reason": "Historisches Muster erfüllt" if passed else ", ".join(reasons)
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
  "pattern_rules": {
    "min_confidence": 0.85,
    "max_rsi": 40,
    "required_signals": ["bullish"],
    "min_volume_ratio": 1.5
  },
  "risk_notes": {
    "max_rsi_warning": 70,
    "volatility_warning_percent": 5
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
        st.subheader("Neues Analyse-Preset anlegen")

        strat_name = st.text_input("Name des Presets", "Krypto Volatilität")
        asset_type = st.selectbox("Anwenden auf:", ["STOCK", "CRYPTO", "FOREX"])

        st.markdown("---")
        st.write("**Regelwerk definieren:**")

        min_conf = st.slider("Mindest-Sicherheit (KI)", 0.5, 0.99, 0.80)
        max_rsi = st.number_input("RSI-Warnschwelle", 30, 90, 70)

        if st.button("Strategie speichern"):
            rules = {"min_confidence": min_conf, "max_rsi": max_rsi}
            if StrategyManager.save_strategy(strat_name, asset_type, rules):
                st.success(f"Analyse-Preset '{strat_name}' gespeichert!")

    with col2:
        st.subheader("Aktive Analyse-Presets")
        # Hier Presets aus DB anzeigen
```

#### Funktionen:
- [ ] Analyse-Preset erstellen/bearbeiten/löschen
- [ ] Regeln per Slider/Input definieren
- [ ] Asset-Typ zuweisen (Aktien, Krypto, etc.)
- [ ] Preset aktivieren/deaktivieren
- [ ] Backtesting der Strategie (historische Simulation)

---

## Phase 9: Automatisiertes Trading ⏸️ AUSGESETZT (regulatorisch)

Nicht implementieren, bis KWG/WpHG/MiFID-II-Fragen geklärt sind. Diese Phase
bleibt als abgelegter Ideenspeicher erhalten und ist kein aktiver Scope für
FinancialProof.

### 9.1 Auto-Trading Workflow

Kein Workflow, kein Code-Beispiel und keine Job-Integration im aktiven Scope.
Analyse-Jobs dürfen historische Muster klassifizieren und protokollieren, aber
keine Handlungsaufforderung und keine Order auslösen.

### 9.2 Automatisierungs-Level

| Level | Name | Beschreibung |
|-------|------|--------------|
| 0 | **Analyse** | Historische Daten anzeigen und Muster beschreiben |
| 1 | **Reporting** | Analyse-Ergebnisse exportieren |
| 2-4 | **Nicht freigegeben** | Keine Broker-, Order- oder Automationsfunktion |

### 9.3 Sicherheits-Features

- [ ] Keine Broker-Abhängigkeiten in `requirements.txt`
- [ ] Keine Order-Funktionen oder Broker-Adapter im Code
- [ ] Keine Trading-Secrets in Templates, Tests oder Dokumentation
- [ ] Deskriptive Sprache in UI, README und Changelog beibehalten

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
2. ✅ **API Rate Limiting** - Token-Bucket-Limiter (`core/rate_limiter.py`) drosselt yfinance-Aufrufe in DataProvider, Sentiment- und Research-Agent (2026-05-01)
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
- [x] API Rate Limiting (Token-Bucket, konfigurierbar via `config.py` und `FINANCIALPROOF_RL_*`-ENV-Variablen)
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

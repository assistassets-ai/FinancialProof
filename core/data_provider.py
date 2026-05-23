"""
FinancialProof - Data Provider Modul
Wrapper für yfinance mit Caching und Fehlerbehandlung

Migriert von Streamlit: 2026-01-25
- @st.cache_data durch TTL-aware Cache-Decorator ersetzt
- Keine GUI-Abhängigkeiten mehr
"""
import logging
import sys
import time
from functools import wraps
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple, Callable

import yfinance as yf
import pandas as pd
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config
from core.rate_limiter import init_from_config, rate_limited_call

logger = logging.getLogger(__name__)

# Rate-Limiter mit Werten aus der Config initialisieren (kann von Tests
# durch RateLimiter.configure_bucket(...) ueberschrieben werden).
init_from_config(config)

_RL_BUCKET = "yfinance"
_RL_TIMEOUT = float(getattr(config, "API_RATE_LIMIT_YFINANCE_TIMEOUT", 30.0))


def _rl_call(func, *args, **kwargs):
    """Hilfsfunktion: yfinance-Aufruf mit Rate-Limiter throtteln."""
    return rate_limited_call(
        _RL_BUCKET, func, *args, timeout=_RL_TIMEOUT, **kwargs
    )


def ttl_cache(ttl_seconds: int = 300, maxsize: int = 128):
    """
    Time-to-live Cache Decorator (Ersatz für @st.cache_data)

    Args:
        ttl_seconds: Cache-Lebenszeit in Sekunden
        maxsize: Maximale Cache-Größe
    """
    import threading

    def decorator(func: Callable):
        """Apply TTL caching to a callable.

        Args:
            func: The function to wrap with caching behaviour.

        Returns:
            Wrapped function with cache_clear and cache_info attributes.
        """
        cache = {}
        timestamps = {}
        lock = threading.Lock()

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Call func, returning a cached result if still within the TTL."""
            # Cache-Key aus Argumenten erstellen
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()

            with lock:
                # Prüfen ob im Cache und noch gültig
                if key in cache and key in timestamps:
                    if current_time - timestamps[key] < ttl_seconds:
                        return cache[key]

                # Alten Cache aufräumen wenn zu groß
                if len(cache) >= maxsize:
                    # Älteste Einträge entfernen
                    oldest_keys = sorted(timestamps.keys(), key=lambda k: timestamps[k])[:maxsize//4]
                    for old_key in oldest_keys:
                        cache.pop(old_key, None)
                        timestamps.pop(old_key, None)

            # Neuen Wert außerhalb des Locks berechnen (vermeidet langen Lock-Hold)
            result = func(*args, **kwargs)

            with lock:
                cache[key] = result
                timestamps[key] = current_time
            return result

        # Cache-Kontrollfunktionen
        def cache_clear():
            """Clear all cached entries and timestamps."""
            with lock:
                cache.clear()
                timestamps.clear()

        wrapper.cache_clear = cache_clear
        wrapper.cache_info = lambda: {"size": len(cache), "maxsize": maxsize, "ttl": ttl_seconds}

        return wrapper
    return decorator


class DataProvider:
    """Zentraler Daten-Provider für Marktdaten"""

    # Asset-Typen mit typischen Suffixen
    ASSET_TYPES = {
        "stock": "",
        "etf": "",
        "fund": "",
        "crypto": "-USD",
        "forex": "=X",
        "index": "^"
    }

    # Bekannte Indizes
    KNOWN_INDICES = {
        "DAX": "^GDAXI",
        "DOW": "^DJI",
        "S&P500": "^GSPC",
        "NASDAQ": "^IXIC",
        "FTSE": "^FTSE",
        "NIKKEI": "^N225"
    }

    @staticmethod
    @ttl_cache(ttl_seconds=config.CACHE_TTL_MARKET_DATA)
    def get_market_data(
        ticker: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Lädt OHLCV-Marktdaten für ein Symbol.

        Args:
            ticker: Das Symbol (z.B. "AAPL", "BTC-USD", "^GDAXI")
            period: Zeitraum ("1mo", "3mo", "6mo", "1y", "2y", "5y", "max")
            interval: Intervall ("1m", "5m", "15m", "1h", "1d", "1wk", "1mo")

        Returns:
            DataFrame mit Open, High, Low, Close, Volume oder None
        """
        try:
            df = _rl_call(
                yf.download,
                ticker,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=True,
            )

            if df is None or df.empty:
                return None

            # Spaltennamen normalisieren (für Multi-Ticker Fälle)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Sicherstellen dass alle benötigten Spalten da sind
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_cols:
                if col not in df.columns:
                    return None

            # NaN-Werte am Anfang/Ende entfernen
            df = df.dropna()

            return df

        except Exception as e:
            logger.warning("Fehler beim Laden der Daten fuer %s: %s", ticker, e)
            return None

    @staticmethod
    @ttl_cache(ttl_seconds=config.CACHE_TTL_TICKER_INFO)
    def get_ticker_info(ticker: str) -> Dict[str, Any]:
        """
        Lädt Metadaten für ein Symbol (Name, Sektor, etc.)

        Args:
            ticker: Das Symbol

        Returns:
            Dictionary mit Ticker-Informationen
        """
        try:
            t = yf.Ticker(ticker)
            info = _rl_call(lambda: t.info)
            return info if info else {}
        except Exception as e:
            logger.warning("Ticker-Info fuer %s konnte nicht geladen werden: %s", ticker, e)
            return {}

    @staticmethod
    @ttl_cache(ttl_seconds=config.CACHE_TTL_NEWS)
    def get_news(ticker: str, limit: int = 10) -> List[Dict]:
        """
        Lädt News für ein Symbol von yfinance.

        Args:
            ticker: Das Symbol
            limit: Maximale Anzahl News

        Returns:
            Liste von News-Dictionaries
        """
        try:
            t = yf.Ticker(ticker)
            news = _rl_call(lambda: t.news)
            if news:
                return news[:limit]
            return []
        except Exception as e:
            logger.warning("News fuer %s konnten nicht geladen werden: %s", ticker, e)
            return []

    @staticmethod
    def get_current_price(ticker: str) -> Optional[Tuple[float, float, float]]:
        """
        Holt den aktuellen Preis und Änderung.

        Args:
            ticker: Das Symbol

        Returns:
            Tuple (aktueller_preis, änderung, änderung_prozent) oder None
        """
        try:
            t = yf.Ticker(ticker)
            hist = _rl_call(t.history, period="2d")
            if hist is None:
                return None
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                previous = hist['Close'].iloc[-2]
                change = current - previous
                change_pct = (change / previous) * 100 if previous != 0 else 0.0
                return (current, change, change_pct)
            elif len(hist) == 1:
                return (hist['Close'].iloc[-1], 0, 0)
            return None
        except Exception as e:
            logger.warning("Aktueller Preis fuer %s konnte nicht geladen werden: %s", ticker, e)
            return None

    @staticmethod
    @ttl_cache(ttl_seconds=config.CACHE_TTL_MARKET_DATA)
    def get_multiple_tickers(
        tickers: List[str],
        period: str = "1y",
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        Lädt Daten für mehrere Ticker gleichzeitig.

        Args:
            tickers: Liste von Symbolen
            period: Zeitraum
            interval: Intervall

        Returns:
        Dictionary {ticker: DataFrame}
        """
        result = {}
        try:
            if not tickers:
                return result

            data = _rl_call(
                yf.download,
                tickers,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=True,
                group_by='ticker',
            )

            if data is None:
                return result

            if isinstance(data.columns, pd.MultiIndex):
                for ticker in tickers:
                    if ticker in data.columns.get_level_values(0):
                        df = data[ticker].dropna()
                        if not df.empty:
                            result[ticker] = df
            else:
                # Nur ein Ticker, keine MultiIndex
                if not data.empty:
                    result[tickers[0]] = data.dropna()

        except Exception as e:
            logger.warning("Fehler beim Laden mehrerer Ticker %s: %s", tickers, e)

        return result

    @staticmethod
    def search_ticker(query: str, limit: int = 10) -> List[Dict]:
        """
        Sucht nach Symbolen basierend auf einem Suchbegriff.

        Args:
            query: Suchbegriff (Name oder Symbol)
            limit: Maximale Anzahl Ergebnisse

        Returns:
            Liste von {symbol, name, type} Dictionaries
        """
        try:
            # yfinance hat keine native Suchfunktion,
            # daher verwenden wir die Ticker-Info als Workaround
            t = yf.Ticker(query.upper())
            info = _rl_call(lambda: t.info)

            if info and 'symbol' in info:
                return [{
                    'symbol': info.get('symbol', query.upper()),
                    'name': info.get('longName', info.get('shortName', query)),
                    'type': info.get('quoteType', 'EQUITY').lower(),
                    'exchange': info.get('exchange', 'Unknown')
                }]
            return []
        except Exception as e:
            logger.warning("Ticker-Suche fuer %s fehlgeschlagen: %s", query, e)
            return []

    @staticmethod
    def validate_ticker(ticker: str) -> bool:
        """
        Prüft ob ein Ticker gültig ist.

        Args:
            ticker: Das zu prüfende Symbol

        Returns:
            True wenn gültig, False sonst
        """
        try:
            data = _rl_call(yf.download, ticker, period="5d", progress=False)
            if data is None:
                return False
            return not data.empty
        except Exception as e:
            logger.warning("Ticker-Validierung fuer %s fehlgeschlagen: %s", ticker, e)
            return False

    @staticmethod
    def get_asset_type(ticker: str) -> str:
        """
        Ermittelt den Asset-Typ basierend auf dem Symbol.

        Args:
            ticker: Das Symbol

        Returns:
            Asset-Typ ('stock', 'etf', 'crypto', 'index', etc.)
        """
        ticker = ticker.upper()

        # Indizes
        if ticker.startswith('^'):
            return 'index'

        # Krypto
        if ticker.endswith('-USD') or ticker.endswith('-EUR'):
            return 'crypto'

        # Forex
        if ticker.endswith('=X'):
            return 'forex'

        # Versuche Info abzurufen
        try:
            info = DataProvider.get_ticker_info(ticker)
            quote_type = info.get('quoteType', '').upper()
            if quote_type == 'ETF':
                return 'etf'
            elif quote_type == 'MUTUALFUND':
                return 'fund'
            elif quote_type == 'CRYPTOCURRENCY':
                return 'crypto'
            elif quote_type == 'INDEX':
                return 'index'
        except Exception as e:
            logger.debug(
                "Asset-Typ fuer %s konnte nicht ueber Ticker-Info ermittelt werden: %s",
                ticker,
                e,
            )

        return 'stock'

    @staticmethod
    def get_financials(ticker: str) -> Dict[str, pd.DataFrame]:
        """
        Lädt Finanzberichte für eine Aktie.

        Args:
            ticker: Das Symbol

        Returns:
            Dictionary mit 'income', 'balance', 'cashflow' DataFrames
        """
        try:
            t = yf.Ticker(ticker)
            income = _rl_call(lambda: t.income_stmt)
            balance = _rl_call(lambda: t.balance_sheet)
            cashflow = _rl_call(lambda: t.cashflow)
            return {
                'income': income,
                'balance': balance,
                'cashflow': cashflow,
            }
        except Exception as e:
            logger.warning("Finanzberichte fuer %s konnten nicht geladen werden: %s", ticker, e)
            return {}

    @staticmethod
    def get_dividends(ticker: str) -> pd.Series:
        """
        Lädt Dividenden-Historie.

        Args:
            ticker: Das Symbol

        Returns:
            Series mit Dividenden-Daten
        """
        try:
            t = yf.Ticker(ticker)
            dividends = _rl_call(lambda: t.dividends)
            if dividends is None:
                return pd.Series()
            return dividends
        except Exception as e:
            logger.warning("Dividenden fuer %s konnten nicht geladen werden: %s", ticker, e)
            return pd.Series()

    @staticmethod
    def get_recommendations(ticker: str) -> pd.DataFrame:
        """
        Lädt Analysten-Empfehlungen.

        Args:
            ticker: Das Symbol

        Returns:
            DataFrame mit Empfehlungen
        """
        try:
            t = yf.Ticker(ticker)
            rec = _rl_call(lambda: t.recommendations)
            return rec if rec is not None else pd.DataFrame()
        except Exception as e:
            logger.warning("Analysten-Empfehlungen fuer %s konnten nicht geladen werden: %s", ticker, e)
            return pd.DataFrame()


class MarketOverview:
    """Gibt einen Überblick über wichtige Marktindizes"""

    MAIN_INDICES = [
        ("^GDAXI", "DAX", "Frankfurt"),
        ("^GSPC", "S&P 500", "New York"),
        ("^DJI", "Dow Jones", "New York"),
        ("^IXIC", "NASDAQ", "New York"),
        ("^FTSE", "FTSE 100", "London"),
        ("^N225", "Nikkei 225", "Tokyo")
    ]

    @staticmethod
    @ttl_cache(ttl_seconds=300)  # 5 Minuten Cache
    def get_indices_overview() -> List[Dict]:
        """
        Holt aktuelle Daten für die Hauptindizes.

        Returns:
            Liste von Dicts mit Index-Daten
        """
        results = []
        for symbol, name, exchange in MarketOverview.MAIN_INDICES:
            try:
                price_data = DataProvider.get_current_price(symbol)
                if price_data:
                    current, change, change_pct = price_data
                    results.append({
                        'symbol': symbol,
                        'name': name,
                        'exchange': exchange,
                        'price': current,
                        'change': change,
                        'change_pct': change_pct
                    })
            except Exception as e:
                logger.warning("Index-Ueberblick fuer %s konnte nicht geladen werden: %s", symbol, e)
                continue
        return results

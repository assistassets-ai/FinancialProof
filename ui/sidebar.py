"""
FinancialProof - Sidebar UI Komponente
Watchlist, Asset-Auswahl und Einstellungen
"""
import streamlit as st
from datetime import datetime
from typing import Any, Dict, Tuple
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config, texts, api_keys
from core.database import db, WatchlistItem
from core.data_provider import DataProvider
from core.rate_limiter import RateLimiter


def render_sidebar() -> Tuple[str, str, dict]:
    """
    Rendert die Sidebar.

    Returns:
        Tuple (ausgewähltes_symbol, zeitraum, indikator_einstellungen)
    """
    st.sidebar.title(texts.APP_TITLE)

    # Asset-Auswahl
    symbol, period = _render_asset_selection()

    # Watchlist
    _render_watchlist(symbol)

    st.sidebar.markdown("---")

    # Indikator-Einstellungen
    indicators = _render_indicator_settings()

    return symbol, period, indicators


def render_sidebar_settings() -> None:
    """Rendert die Sidebar-Einstellungen nach datenbezogenen API-Aufrufen."""
    st.sidebar.markdown("---")
    _render_settings()


def _render_asset_selection() -> Tuple[str, str]:
    """Rendert die Asset-Auswahl"""
    st.sidebar.header(texts.SIDEBAR_TITLE)

    # Symbol-Eingabe
    symbol = st.sidebar.text_input(
        texts.SIDEBAR_SYMBOL,
        value=st.session_state.get('selected_symbol', config.DEFAULT_TICKER),
        help="z.B. AAPL, MSFT, BTC-USD, ^GDAXI"
    ).upper().strip()

    # Speichere ausgewähltes Symbol
    if symbol:
        st.session_state['selected_symbol'] = symbol

    # Zeitraum-Auswahl
    period_options = list(texts.PERIODS.keys())
    period_labels = list(texts.PERIODS.values())

    selected_idx = st.sidebar.selectbox(
        texts.SIDEBAR_PERIOD,
        range(len(period_options)),
        format_func=lambda x: period_labels[x],
        index=period_options.index(config.DEFAULT_PERIOD) if config.DEFAULT_PERIOD in period_options else 3
    )

    period = period_options[selected_idx]

    return symbol, period


def _render_watchlist(current_symbol: str):
    """Rendert die Watchlist"""
    st.sidebar.subheader(texts.SIDEBAR_WATCHLIST)

    watchlist = db.get_watchlist()

    if watchlist:
        for item in watchlist:
            col1, col2 = st.sidebar.columns([3, 1])

            with col1:
                # Aktuellen Preis holen (gecached)
                price_data = DataProvider.get_current_price(item.symbol)
                if price_data:
                    price, change, change_pct = price_data
                    color = "🟢" if change >= 0 else "🔴"
                    label = f"{item.symbol} {color} {change_pct:+.1f}%"
                else:
                    label = f"{item.symbol}"

                if st.button(label, key=f"wl_{item.symbol}", width="stretch"):
                    st.session_state['selected_symbol'] = item.symbol
                    st.rerun()

            with col2:
                if st.button("❌", key=f"rm_{item.symbol}"):
                    db.remove_from_watchlist(item.symbol)
                    st.rerun()
    else:
        st.sidebar.caption("Keine Assets in der Watchlist")

    # Hinzufügen-Button
    if current_symbol and not db.is_in_watchlist(current_symbol):
        if st.sidebar.button(f"➕ {current_symbol} hinzufügen", width="stretch"):
            info = DataProvider.get_ticker_info(current_symbol)
            item = WatchlistItem(
                symbol=current_symbol,
                name=info.get('longName', current_symbol),
                asset_type=DataProvider.get_asset_type(current_symbol)
            )
            db.add_to_watchlist(item)
            st.rerun()


def _render_indicator_settings() -> dict:
    """Rendert die Indikator-Einstellungen"""
    st.sidebar.subheader(texts.SIDEBAR_INDICATORS)

    indicators = {}

    # Moving Averages
    indicators['sma_20'] = st.sidebar.checkbox("SMA 20", value=True)
    indicators['sma_50'] = st.sidebar.checkbox("SMA 50", value=True)
    indicators['sma_200'] = st.sidebar.checkbox("SMA 200", value=False)

    # Bollinger Bänder
    indicators['bollinger'] = st.sidebar.checkbox(texts.IND_BOLLINGER, value=False)

    # RSI
    indicators['rsi'] = st.sidebar.checkbox(texts.IND_RSI, value=True)

    # MACD
    indicators['macd'] = st.sidebar.checkbox(texts.IND_MACD, value=False)

    return indicators


def _render_settings():
    """Rendert den Einstellungen-Bereich"""
    with st.sidebar.expander(texts.SIDEBAR_SETTINGS):
        st.caption("**Theme:** Wechsel via Menu (⋮ oben rechts) → Settings → Theme")
        st.markdown("---")
        st.caption("API-Keys für erweiterte Funktionen")

        # Twitter API Key
        twitter_key = st.text_input(
            texts.API_TWITTER,
            type="password",
            value="" if not api_keys.has_api_key("twitter") else "***gespeichert***"
        )

        if twitter_key and twitter_key != "***gespeichert***":
            if st.button("Twitter-Key speichern"):
                api_keys.save_api_key("twitter", twitter_key)
                st.success("Gespeichert!")

        # YouTube API Key
        youtube_key = st.text_input(
            texts.API_YOUTUBE,
            type="password",
            value="" if not api_keys.has_api_key("youtube") else "***gespeichert***"
        )

        if youtube_key and youtube_key != "***gespeichert***":
            if st.button("YouTube-Key speichern"):
                api_keys.save_api_key("youtube", youtube_key)
                st.success("Gespeichert!")

        # API-Rate-Limit-Telemetrie
        st.markdown("---")
        _render_rate_limit_status()

        # Datenbank-Reset
        st.markdown("---")
        if st.button("🗑️ Datenbank zurücksetzen", type="secondary"):
            if st.checkbox("Bestätigen"):
                # Alle Jobs und Ergebnisse löschen
                import os
                db_path = config.DB_PATH
                if os.path.exists(db_path):
                    try:
                        os.remove(db_path)
                        st.success("Datenbank wurde zurückgesetzt")
                        st.rerun()
                    except PermissionError:
                        st.error("Datenbank ist gesperrt (OneDrive-Sync oder anderer Prozess). Bitte später erneut versuchen.")


def _render_rate_limit_status():
    """Zeigt Telemetrie aller aktiven Rate-Limit-Buckets in der Sidebar.

    Liest die Statistiken via ``RateLimiter.get_all_stats`` und blendet jeden
    Bucket als kompakten Block ein. Dadurch werden zukuenftige Buckets
    (z.B. Twitter/Reddit-Sentiment laut ROADMAP) automatisch sichtbar, ohne
    dass die UI nachgezogen werden muss.
    """
    all_stats = RateLimiter.get_all_stats()
    st.caption("**API-Rate-Limits**")
    if not all_stats:
        st.caption("Noch keine API-Aufrufe protokolliert.")
        return

    for stats in all_stats:
        _render_bucket_stats(stats)

    if st.button("Rate-Limit-Statistik zurücksetzen"):
        RateLimiter.reset_stats()
        st.success("Rate-Limit-Statistik zurückgesetzt")


def _render_bucket_stats(stats: Dict[str, Any]) -> None:
    """Rendert einen einzelnen Bucket-Telemetrie-Block."""
    name = stats.get("name", "?")
    st.caption(f"_{name}_")
    st.caption(
        "Anfragen: {requests} | verzögert: {delayed} | Timeouts: {timeouts}".format(
            requests=stats.get("requests", 0),
            delayed=stats.get("delayed_acquired", 0),
            timeouts=stats.get("timeouts", 0),
        )
    )
    st.caption(
        "Token knapp: {events} | verfügbar: {tokens:.1f}/{capacity:.1f}".format(
            events=stats.get("low_token_events", 0),
            tokens=stats.get("available_tokens", 0.0),
            capacity=stats.get("capacity", 0.0),
        )
    )
    if stats.get("last_low_tokens_at") is not None:
        st.caption(
            "Letzte Knappheit: "
            f"{_format_rate_limit_timestamp(stats['last_low_tokens_at'])}"
        )
    if stats.get("last_timeout_at") is not None:
        st.caption(
            "Letzter Timeout: "
            f"{_format_rate_limit_timestamp(stats['last_timeout_at'])}"
        )


def _format_rate_limit_timestamp(timestamp: float) -> str:
    """Formatiert Unix-Zeitstempel fuer die kompakte Sidebar-Anzeige."""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

"""
FinancialProof - Sidebar UI Komponente
Watchlist, Asset-Auswahl und Einstellungen
"""
import streamlit as st
from typing import Tuple
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config, texts, api_keys
from core.database import db, WatchlistItem
from core.data_provider import DataProvider


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

    st.sidebar.markdown("---")

    # Einstellungen
    _render_settings()

    return symbol, period, indicators


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

                if st.button(label, key=f"wl_{item.symbol}", use_container_width=True):
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
        if st.sidebar.button(f"➕ {current_symbol} hinzufügen", use_container_width=True):
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

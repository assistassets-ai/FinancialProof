"""
FinancialProof - Hauptanwendung
Browserbasierte Finanz-Analyse Web-App
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Pfad für lokale Imports setzen
sys.path.insert(0, str(Path(__file__).parent))

from config import texts
from core.data_provider import DataProvider
from ui.sidebar import render_sidebar
from ui.chart_view import render_chart_view
from ui.analysis_view import render_analysis_view
from ui.job_queue import render_job_queue
from ui.disclaimer_widget import ensure_acknowledged


# ===== PAGE CONFIGURATION =====
# Muss VOR jedem anderen Streamlit-Aufruf erfolgen.
st.set_page_config(
    page_title=texts.APP_TITLE,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== ERSTSTART-ACKNOWLEDGEMENT (§ 32 KWG / § 2 Abs. 9 WpHG) =====
# Blockiert die App, bis der Nutzer vier Pflicht-Checkboxen bestätigt hat.
# Persistiert via SHA-256-Hash des Disclaimer-Texts. Bei Textänderung wird
# erneut bestätigt. Ruft intern st.stop(), wenn nicht akzeptiert.
ensure_acknowledged()


# ===== CUSTOM CSS =====
st.markdown("""
<style>
    /* Button Styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }

    /* Metric Styling */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Hauptfunktion der Anwendung"""

    # Sidebar rendern und Auswahl erhalten
    symbol, period, indicators = render_sidebar()

    # Hauptbereich
    if not symbol:
        st.title(texts.APP_TITLE)
        st.info("Bitte gib ein Symbol in der Sidebar ein (z.B. AAPL, MSFT, BTC-USD)")
        return

    # Daten laden
    with st.spinner(texts.MSG_LOADING):
        data = DataProvider.get_market_data(symbol, period=period)
        info = DataProvider.get_ticker_info(symbol)

    if data is None or data.empty:
        st.error(texts.MSG_NO_DATA)
        st.info(f"Versuche ein anderes Symbol. Eingabe: {symbol}")
        return

    # Header mit Asset-Info
    _render_header(symbol, info, data)

    # Tabs für verschiedene Ansichten
    tab_chart, tab_analysis, tab_jobs = st.tabs([
        f"📊 {texts.TAB_CHART}",
        f"🧠 {texts.TAB_ANALYSIS}",
        f"📋 {texts.TAB_JOBS}"
    ])

    with tab_chart:
        render_chart_view(data, symbol, indicators)

    with tab_analysis:
        render_analysis_view(symbol, data)

    with tab_jobs:
        render_job_queue()


def _render_header(symbol: str, info: dict, data):
    """Rendert den Header mit Asset-Informationen"""
    name = info.get('longName', info.get('shortName', symbol))
    sector = info.get('sector', 'N/A')
    industry = info.get('industry', 'N/A')

    # Aktuelle Preisdaten
    current_price = data['Close'].iloc[-1]
    prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
    if pd.isna(current_price) or pd.isna(prev_price):
        current_price = current_price if not pd.isna(current_price) else 0
        prev_price = prev_price if not pd.isna(prev_price) else current_price
    change = current_price - prev_price
    change_pct = (change / prev_price) * 100 if prev_price > 0 else 0

    # Header-Zeile
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.title(f"{name}")
        st.caption(f"{symbol} | {sector} | {industry}")

    with col2:
        delta_color = "normal" if change >= 0 else "inverse"
        st.metric(
            label="Aktueller Kurs",
            value=f"{current_price:.2f}",
            delta=f"{change:+.2f} ({change_pct:+.2f}%)",
            delta_color=delta_color
        )

    with col3:
        # Marktkapitalisierung
        market_cap = info.get('marketCap', 0)
        if market_cap:
            if market_cap >= 1e12:
                cap_str = f"{market_cap/1e12:.2f}T"
            elif market_cap >= 1e9:
                cap_str = f"{market_cap/1e9:.2f}B"
            elif market_cap >= 1e6:
                cap_str = f"{market_cap/1e6:.2f}M"
            else:
                cap_str = f"{market_cap:,.0f}"
            st.metric("Marktkapitalisierung", cap_str)
        else:
            st.metric("Volumen", f"{data['Volume'].iloc[-1]:,.0f}")


if __name__ == "__main__":
    main()

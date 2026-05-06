"""
FinancialProof - Chart View UI Komponente
Kursverlauf mit technischen Indikatoren und erkannten Mustern
(keine Anlageempfehlung; siehe Disclaimer in der App)
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config, texts
from indicators.technical import TechnicalIndicators, INDICATOR_CONFIGS
from indicators.signals import SignalGenerator, format_signal_for_display


def render_chart_view(df: pd.DataFrame, symbol: str, indicators: dict):
    """
    Rendert den Chart-Bereich.

    Args:
        df: DataFrame mit OHLCV-Daten
        symbol: Das Symbol
        indicators: Dict mit aktiven Indikatoren
    """
    if df is None or df.empty:
        st.error(texts.MSG_NO_DATA)
        return

    # Indikatoren berechnen
    active_indicators = [k for k, v in indicators.items() if v]
    df_with_indicators = TechnicalIndicators.calculate_all(df, active_indicators)

    # Signale generieren
    signal_gen = SignalGenerator()
    signals = signal_gen.generate_all_signals(df_with_indicators)
    signal_summary = signal_gen.get_signal_summary(df_with_indicators)

    # Header mit Preis-Info
    _render_price_header(df, symbol, signal_summary)

    # Hauptchart mit Subplots
    _render_main_chart(df_with_indicators, symbol, indicators, signals)

    # Signal-Übersicht
    _render_signal_summary(signal_summary)


def _render_price_header(df: pd.DataFrame, symbol: str, signals: dict):
    """Rendert den Preis-Header"""
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    current_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
    if pd.isna(current_price) or pd.isna(prev_price):
        current_price = current_price if not pd.isna(current_price) else 0
        prev_price = prev_price if not pd.isna(prev_price) else current_price
    change = current_price - prev_price
    change_pct = (change / prev_price) * 100 if prev_price > 0 else 0

    with col1:
        st.subheader(f"{symbol}")

    with col2:
        st.metric(
            "Kurs",
            f"{current_price:.2f}",
            f"{change:+.2f} ({change_pct:+.2f}%)"
        )

    with col3:
        # Höchst/Tiefst
        high = df['High'].max()
        low = df['Low'].min()
        st.metric("52W Hoch", f"{high:.2f}")

    with col4:
        st.metric("52W Tief", f"{low:.2f}")


def _render_main_chart(
    df: pd.DataFrame,
    symbol: str,
    indicators: dict,
    signals: List
):
    """Rendert den Hauptchart"""
    # Bestimme Anzahl der Subplots
    has_rsi = indicators.get('rsi', False)
    has_macd = indicators.get('macd', False)

    num_rows = 1 + int(has_rsi) + int(has_macd)
    row_heights = [0.6]
    if has_rsi:
        row_heights.append(0.2)
    if has_macd:
        row_heights.append(0.2)

    # Subplots erstellen
    fig = make_subplots(
        rows=num_rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights
    )

    # 1. Candlestick Chart
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Kurs',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ),
        row=1, col=1
    )

    # 2. Moving Averages
    colors = {'sma_20': '#FFA726', 'sma_50': '#42A5F5', 'sma_200': '#AB47BC'}

    for ma_name, color in colors.items():
        if indicators.get(ma_name) and ma_name in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[ma_name],
                    name=ma_name.upper().replace('_', ' '),
                    line=dict(color=color, width=1),
                    opacity=0.8
                ),
                row=1, col=1
            )

    # 3. Bollinger Bänder
    if indicators.get('bollinger') and 'bb_upper' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['bb_upper'],
                name='BB Upper',
                line=dict(color='gray', width=1, dash='dot'),
                opacity=0.5
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['bb_lower'],
                name='BB Lower',
                line=dict(color='gray', width=1, dash='dot'),
                fill='tonexty',
                fillcolor='rgba(128,128,128,0.1)',
                opacity=0.5
            ),
            row=1, col=1
        )

    # 4. Signale als Marker
    buy_signals = [s for s in signals if s.signal_type.value == 'buy']
    sell_signals = [s for s in signals if s.signal_type.value == 'sell']

    # Nur letzte 20 Signale anzeigen
    for signal in buy_signals[-10:]:
        if signal.date in df.index:
            fig.add_trace(
                go.Scatter(
                    x=[signal.date],
                    y=[signal.price * 0.98],  # Leicht unter dem Preis
                    mode='markers',
                    marker=dict(
                        symbol='triangle-up',
                        size=12,
                        color='#26a69a'
                    ),
                    name='Bullisches Muster',
                    hovertext=signal.description,
                    showlegend=False
                ),
                row=1, col=1
            )

    for signal in sell_signals[-10:]:
        if signal.date in df.index:
            fig.add_trace(
                go.Scatter(
                    x=[signal.date],
                    y=[signal.price * 1.02],  # Leicht über dem Preis
                    mode='markers',
                    marker=dict(
                        symbol='triangle-down',
                        size=12,
                        color='#ef5350'
                    ),
                    name='Bärisches Muster',
                    hovertext=signal.description,
                    showlegend=False
                ),
                row=1, col=1
            )

    # 5. RSI Subplot
    current_row = 2
    if has_rsi and 'rsi' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['rsi'],
                name='RSI',
                line=dict(color='#9C27B0', width=1)
            ),
            row=current_row, col=1
        )

        # Überkauft/Überverkauft Linien
        fig.add_hline(y=70, line_dash="dash", line_color="red",
                      opacity=0.5, row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green",
                      opacity=0.5, row=current_row, col=1)

        fig.update_yaxes(title_text="RSI", row=current_row, col=1)
        current_row += 1

    # 6. MACD Subplot
    if has_macd and 'macd' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['macd'],
                name='MACD',
                line=dict(color='#2196F3', width=1)
            ),
            row=current_row, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['macd_signal'],
                name='Signal',
                line=dict(color='#FF9800', width=1)
            ),
            row=current_row, col=1
        )

        # MACD Histogram
        colors = ['#26a69a' if v >= 0 else '#ef5350'
                  for v in df['macd_histogram']]

        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['macd_histogram'],
                name='Histogram',
                marker_color=colors,
                opacity=0.5
            ),
            row=current_row, col=1
        )

        fig.update_yaxes(title_text="MACD", row=current_row, col=1)

    # Layout
    fig.update_layout(
        title=f"{symbol} - Kursverlauf",
        template=config.CHART_THEME,
        height=config.CHART_HEIGHT + (100 * (num_rows - 1)),
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=50, b=50)
    )

    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # Wochenenden ausblenden
        ]
    )

    st.plotly_chart(fig, width="stretch")


def _render_signal_summary(signal_summary: dict):
    """Rendert die Muster-Übersicht (deskriptiv, keine Empfehlung)."""
    st.subheader("Muster-Übersicht")
    st.caption(
        "Rein deskriptive Zusammenfassung historischer Muster — "
        "keine Kauf-/Verkaufsempfehlung, keine Prognose."
    )

    col1, col2, col3 = st.columns(3)

    overall = signal_summary.get('overall_signal')
    if overall:
        if overall.value == 'buy':
            col1.success("🟢 Tendenz: überwiegend bullische Muster")
        elif overall.value == 'sell':
            col1.error("🔴 Tendenz: überwiegend bärische Muster")
        else:
            col1.info("🟡 Tendenz: gemischt / neutral")

    col2.metric("Bullische Muster", signal_summary.get('buy_count', 0))
    col3.metric("Bärische Muster", signal_summary.get('sell_count', 0))

    # Letzte erkannte Muster anzeigen
    recent = signal_summary.get('recent_signals', [])
    if recent:
        with st.expander("Zuletzt erkannte Muster", expanded=False):
            for signal in recent[:5]:
                formatted = format_signal_for_display(signal)
                st.markdown(
                    f"{formatted['emoji']} **{formatted['indicator']}** - "
                    f"{formatted['description']} "
                    f"({formatted['date']}, Konfidenz: {formatted['confidence']})"
                )

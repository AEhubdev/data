import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# CSS for custom metrics and signal containers
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricLabel"] { color: #808495 !important; }
    [data-testid="stMetricValue"] { color: white !important; }
    .signal-container {
        background-color: #1E222D;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #363A45;
        margin-bottom: 10px;
    }
    /* Custom Large White Header Style */
    .custom-header {
        color: white;
        font-family: 'Arial Black', sans-serif;
        font-size: 28px;
        text-align: center;
        margin-bottom: 20px;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)


# HELPER: Custom metric
def colored_metric(col, label, val_text, delta_val, is_vol=False):
    color = "#FFA500" if is_vol else ("#00FF41" if delta_val > 0 else "#FF3131")
    col.markdown(f"**{label}**")
    col.markdown(f"<h2 style='color:{color}; margin-top:-15px; font-weight:bold;'>{val_text}</h2>",
                 unsafe_allow_html=True)
    if is_vol: col.caption("Annualized Risk")


@st.cache_data(ttl=60)
def get_data():
    ticker = "GC=F"
    df = yf.download(ticker, start="2024-09-01")
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # Indicators
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    std = df['Close'].rolling(window=20).std()
    df['BB_U'] = df['MA20'] + (std * 2)
    df['BB_L'] = df['MA20'] - (std * 2)

    # RSI, MACD, Stoch
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['STOCH_K'] = (df['Close'] - df['Low'].rolling(14).min()) * 100 / (
                df['High'].rolling(14).max() - df['Low'].rolling(14).min())

    return df[df.index >= "2025-01-01"], float(df['Close'].iloc[-1])


data, price = get_data()

# --- 1. MARKET OVERVIEW ---
st.title("🏆 Gold Market Overview")
st.divider()

# --- 2. CHART & SIGNAL LAYOUT ---
col_charts, col_signals = st.columns([0.72, 0.28])

with col_charts:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.15,
        row_heights=[0.7, 0.3],
        subplot_titles=("MARKET TREND & INDICATORS", "TRADING VOLUME")
    )

    # Price Data
    fig.add_trace(
        go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                       name="Price"), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA 20", line=dict(color='#FFEB3B', width=1.5)), row=1,
                  col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], name="MA 50", line=dict(color='#E91E63', width=1.5)), row=1,
                  col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_U'], name="BB Upper",
                             line=dict(color='rgba(173, 216, 230, 0.5)', dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_L'], name="BB Lower",
                             line=dict(color='rgba(173, 216, 230, 0.5)', dash='dash'), fill='tonexty',
                             fillcolor='rgba(173, 216, 230, 0.05)'), row=1, col=1)

    # Volume Data
    v_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(data['Close'], data['Open'])]
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=v_colors, name="Volume", opacity=0.8), row=2,
                  col=1)

    # Styling Chart Headers (Centered & White)
    fig.update_annotations(font=dict(size=26, color="white", family="Arial Black"))
    fig.layout.annotations[0].update(x=0.5, xanchor='center', y=1.08)
    fig.layout.annotations[1].update(x=0.5, xanchor='center', y=0.28)

    fig.update_layout(
        template="plotly_dark", xaxis_rangeslider_visible=False, height=900,
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=1.04, xanchor="center", x=0.5),
        margin=dict(t=120, b=40, l=40, r=40)
    )
    st.plotly_chart(fig, use_container_width=True)

with col_signals:
    # --- LARGE WHITE TRADING INDICATORS HEADER ---
    st.markdown('<p class="custom-header">TRADING INDICATORS</p>', unsafe_allow_html=True)

    latest = data.iloc[-1]


    def display_signal(label, value, status, color):
        st.markdown(f"""<div class="signal-container"><small style='color:#808495'>{label}</small><br>
            <span style='font-size: 20px; font-weight: bold;'>{value}</span>
            <span style='color:{color}; float: right; font-weight: bold; margin-top: 5px;'>{status}</span></div>""",
                    unsafe_allow_html=True)


    display_signal("RSI (14)", f"{latest['RSI']:.1f}", "Neutral", "#808495")
    display_signal("MACD", f"{latest['MACD']:.2f}", "Bullish" if latest['MACD'] > latest['MACD_Signal'] else "Bearish",
                   "#00FF41")
    display_signal("Stoch (%K)", f"{latest['STOCH_K']:.1f}%", "Active", "#FFA500")
    display_signal("Trend", "Bullish" if latest['Close'] > latest['MA20'] else "Bearish", "LIVE", "#00FF41")
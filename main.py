import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# Enhanced CSS for Terminal Aesthetic
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricLabel"] { color: #808495 !important; font-size: 14px !important; }
    [data-testid="stMetricValue"] { color: white !important; font-weight: bold !important; }
    .sidebar-header {
        color: white !important;
        font-size: 24px !important;
        font-weight: bold !important;
        font-family: 'Arial Black', sans-serif;
        margin-bottom: 20px;
        text-align: center;
        border-bottom: 2px solid #363A45;
    }
    .signal-container {
        background-color: #1E222D;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #363A45;
        margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=60)
def get_gold_data():
    df = yf.download("GC=F", start="2024-09-01")
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # Indicator Calculations
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    std = df['Close'].rolling(window=20).std()
    df['BB_U'] = df['MA20'] + (std * 2)
    df['BB_L'] = df['MA20'] - (std * 2)

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    return df[df.index >= "2025-01-01"], float(df['Close'].iloc[-1]), df


data, price, df_full = get_gold_data()

# --- 1. TOP MARKET OVERVIEW ---
st.title("🏆 GOLD MARKET TERMINAL")
m1, m2, m3, m4, m5 = st.columns(5)

# Metrics calculation
y_start = df_full[df_full.index >= "2025-01-01"]['Close'].iloc[0]
ytd_change = ((price - y_start) / y_start) * 100
vol = np.log(df_full['Close'] / df_full['Close'].shift(1)).std() * np.sqrt(252) * 100

m1.metric("Live Gold Price", f"${price:,.2f}")
m2.metric("YTD Performance", f"{ytd_change:+.2f}%", f"{ytd_change:+.2f}%")
m3.metric("RSI (14-Day)", f"{data['RSI'].iloc[-1]:.1f}")
m4.metric("Volatility (Ann.)", f"{vol:.1f}%")
m5.metric("Trend Status", "Bullish" if price > data['MA20'].iloc[-1] else "Bearish")
st.divider()

# --- 2. MULTI-HISTORY CHARTS ---
col_left, col_right = st.columns([0.78, 0.22])

with col_left:
    # Set shared_xaxes to True to align history across all charts
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,  # Pushes grids apart to make room for headers
        row_heights=[0.4, 0.15, 0.2, 0.25],
        subplot_titles=(
            "<b>PRICE & TREND HISTORY</b>",
            "<b>VOLUME HISTORY</b>",
            "<b>RELATIVE STRENGTH (RSI) HISTORY</b>",
            "<b>MACD MOMENTUM HISTORY</b>"
        )
    )

    # Subplot 1: Price History
    fig.add_trace(
        go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                       name="Gold"), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA 20", line=dict(color='#FFD700')), row=1, col=1)
    fig.add_trace(
        go.Scatter(x=data.index, y=data['BB_U'], name="BB Upper", line=dict(color='rgba(255,255,255,0.2)', dash='dot')),
        row=1, col=1)
    fig.add_trace(
        go.Scatter(x=data.index, y=data['BB_L'], name="BB Lower", line=dict(color='rgba(255,255,255,0.2)', dash='dot'),
                   fill='tonexty'), row=1, col=1)

    # Subplot 2: Volume History
    v_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(data['Close'], data['Open'])]
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=v_colors, name="Vol"), row=2, col=1)

    # Subplot 3: RSI History
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name="RSI", line=dict(color='#BB86FC')), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#ef5350", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#26a69a", row=3, col=1)

    # Subplot 4: MACD History
    fig.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], name="Hist",
                         marker_color=['#26a69a' if x > 0 else '#ef5350' for x in data['MACD_Hist']]), row=4, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name="MACD", line=dict(color='#03DAC6')), row=4, col=1)

    # --- HEADER POSITIONING FIX ---
    # We update the y-coordinates of subplot annotations so they sit above the charts
    fig.update_annotations(font=dict(size=18, color="white"))
    fig.layout.annotations[0].update(y=1.03)  # Price Title
    fig.layout.annotations[1].update(y=0.56)  # Volume Title
    fig.layout.annotations[2].update(y=0.38)  # RSI Title
    fig.layout.annotations[3].update(y=0.15)  # MACD Title

    fig.update_layout(
        template="plotly_dark", height=1400, showlegend=False,
        xaxis_rangeslider_visible=False,
        margin=dict(t=80, b=40, l=50, r=50)
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown('<div class="sidebar-header">SIGNAL ANALYSIS</div>', unsafe_allow_html=True)
    latest = data.iloc[-1]


    # Strong Buy/Sell Logic for Signals
    def get_signal(label, value, logic_type):
        if logic_type == "RSI":
            status = "STRONG SELL" if value >= 70 else ("STRONG BUY" if value <= 30 else "NEUTRAL")
            color = "#ef5350" if value >= 70 else ("#26a69a" if value <= 30 else "#808495")
        else:  # MACD
            status = "STRONG BUY" if value > 0 else "STRONG SELL"
            color = "#26a69a" if value > 0 else "#ef5350"

        st.markdown(f"""
            <div class="signal-container">
                <small style="color:#808495">{label}</small><br>
                <span style="font-size:20px; font-weight:bold;">{value:.2f}</span>
                <div style="float:right; background:{color}; color:black; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:12px;">{status}</div>
            </div>""", unsafe_allow_html=True)


    get_signal("RSI MOMENTUM", latest['RSI'], "RSI")
    get_signal("MACD TREND", latest['MACD_Hist'], "MACD")

    st.info(
        "**Strategy Note:** Strong Buy triggers when RSI is under 30 (Oversold) or MACD Histogram is positive (Bullish Momentum).")
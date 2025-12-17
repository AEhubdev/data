import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# CSS for Window Styling
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .chart-window {
        background-color: #161A25;
        border: 1px solid #363A45;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 25px;
    }
    .window-header {
        color: #FFFFFF;
        font-family: 'Arial Black', sans-serif;
        font-size: 20px;
        margin-bottom: 10px;
        border-left: 5px solid #FFD700;
        padding-left: 10px;
    }
    [data-testid="stMetricValue"] { color: white !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=60)
def get_data():
    ticker = "GC=F"
    df = yf.download(ticker, start="2024-09-01")
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # Technical Indicators
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    std = df['Close'].rolling(20).std()
    df['BB_U'], df['BB_L'] = df['MA20'] + (std * 2), df['MA20'] - (std * 2)

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    ema12, ema26 = df['Close'].ewm(span=12).mean(), df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_S'] = df['MACD'].ewm(span=9).mean()
    df['MACD_H'] = df['MACD'] - df['MACD_S']

    return df[df.index >= "2025-01-01"], float(df['Close'].iloc[-1]), df


data, price, df_full = get_data()

# --- 1. OVERVIEW TAB ---
st.title("🏆 GOLD MARKET OVERVIEW")
m1, m2, m3, m4, m5 = st.columns(5)
y_start = df_full[df_full.index >= "2025-01-01"]['Close'].iloc[0]
ytd = ((price - y_start) / y_start) * 100
vol = np.log(df_full['Close'] / df_full['Close'].shift(1)).std() * np.sqrt(252) * 100

m1.metric("Current Price", f"${price:,.2f}")
m2.metric("YTD Change", f"{ytd:+.2f}%")
m3.metric("RSI Level", f"{data['RSI'].iloc[-1]:.1f}")
m4.metric("Volatility", f"{vol:.1f}%")
m5.metric("Trend", "BULLISH" if price > data['MA20'].iloc[-1] else "BEARISH")
st.divider()

# --- 2. MULTI-WINDOW CHARTS ---
col_main, col_side = st.columns([0.75, 0.25])

with col_main:
    # --- WINDOW 1: PRICE HISTORY ---
    st.markdown('<div class="window-header">PRICE & TREND HISTORY</div>', unsafe_allow_html=True)
    fig1 = go.Figure()
    fig1.add_trace(
        go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                       name="Price"))
    fig1.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA20", line=dict(color='#FFEB3B')))
    fig1.update_layout(template="plotly_dark", height=450, margin=dict(t=0, b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig1, use_container_width=True)

    # --- WINDOW 2: VOLUME HISTORY ---
    st.markdown('<div class="window-header">TRADING VOLUME HISTORY</div>', unsafe_allow_html=True)
    v_cols = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(data['Close'], data['Open'])]
    fig2 = go.Figure(go.Bar(x=data.index, y=data['Volume'], marker_color=v_cols))
    fig2.update_layout(template="plotly_dark", height=250, margin=dict(t=0, b=0))
    st.plotly_chart(fig2, use_container_width=True)

    # --- WINDOW 3: RSI HISTORY ---
    st.markdown('<div class="window-header">RELATIVE STRENGTH INDEX (RSI) HISTORY</div>', unsafe_allow_html=True)
    fig3 = go.Figure(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='#BB86FC')))
    fig3.add_hline(y=70, line_dash="dash", line_color="#FF3131")
    fig3.add_hline(y=30, line_dash="dash", line_color="#00FF41")
    fig3.update_layout(template="plotly_dark", height=250, margin=dict(t=0, b=0))
    st.plotly_chart(fig3, use_container_width=True)

    # --- WINDOW 4: MACD HISTORY ---
    st.markdown('<div class="window-header">MACD MOMENTUM HISTORY</div>', unsafe_allow_html=True)
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(x=data.index, y=data['MACD_H'],
                          marker_color=['#00FF41' if x > 0 else '#FF3131' for x in data['MACD_H']]))
    fig4.add_trace(go.Scatter(x=data.index, y=data['MACD'], line=dict(color='#00E5FF')))
    fig4.update_layout(template="plotly_dark", height=300, margin=dict(t=0, b=0))
    st.plotly_chart(fig4, use_container_width=True)

with col_side:
    st.markdown('<h3 style="color:white; text-align:center;">SIGNAL ANALYSIS</h3>', unsafe_allow_html=True)
    latest = data.iloc[-1]

    # RSI SIGNAL
    rsi = latest['RSI']
    r_stat = "STRONG SELL" if rsi > 70 else ("STRONG BUY" if rsi < 30 else "NEUTRAL")
    st.info(f"**RSI (14):** {rsi:.1f} ({r_stat})")

    # MACD SIGNAL
    macd_h = latest['MACD_H']
    m_stat = "STRONG BUY" if macd_h > 0 else "STRONG SELL"
    st.success(f"**MACD Trend:** {m_stat}") if macd_h > 0 else st.error(f"**MACD Trend:** {m_stat}")
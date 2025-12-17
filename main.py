import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# FIX: Removed the line forcing all values to #00D4FF blue.
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricLabel"] { color: #808495 !important; }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=60)
def get_advanced_data():
    ticker = "GC=F"
    df = yf.download(ticker, start="2024-11-01")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Technical Indicators
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['MA20'] + (std * 2)
    df['BB_Lower'] = df['MA20'] - (std * 2)

    # Performance Calculations
    current_p = float(df['Close'].iloc[-1])
    w_p = float(df['Close'].iloc[-5]);
    w_c = ((current_p - w_p) / w_p) * 100
    m_p = float(df['Close'].iloc[-21]);
    m_c = ((current_p - m_p) / m_p) * 100
    ytd_start = df[df.index >= "2025-01-01"]['Close'].iloc[0]
    ytd_c = ((current_p - ytd_start) / ytd_start) * 100
    vol = df['Close'].pct_change().std() * np.sqrt(252) * 100

    chart_df = df[df.index >= "2025-01-01"].copy()
    return chart_df, current_p, w_c, m_c, ytd_c, vol


data, price, week_c, month_c, ytd_c, vol = get_advanced_data()

# --- 1. MARKET OVERVIEW (FIXED COLORS) ---
st.title("🏆 Gold Market Overview")
c1, c2, c3, c4, c5 = st.columns(5)


# Helper function to get the color string
def get_col(val):
    if val > 0: return "green"
    if val < 0: return "red"
    return "white"


c1.metric("Current Price", f"${price:,.2f}", f"{week_c:+.2f}%")

# The :color[] syntax works because we removed the blue CSS override
c2.metric("Weekly Change", f":{get_col(week_c)}[{week_c:+.2f}%]", delta=f"{week_c:+.2f}%")
c3.metric("Monthly Change", f":{get_col(month_c)}[{month_c:+.2f}%]", delta=f"{month_c:+.2f}%")
c4.metric("YTD Change", f":{get_col(ytd_c)}[{ytd_c:+.2f}%]", delta=f"{ytd_c:+.2f}%")
c5.metric("Volatility", f"{vol:.2f}%", "Annualized")

st.divider()

# --- 2. CHART SECTION WITH VOLUME ---
col_chart, col_pulse = st.columns([3, 1])

with col_chart:
    chart_type = st.toggle("Switch to Line Chart", value=False)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.8, 0.2])

    if chart_type:
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Price", line=dict(color='#00D4FF', width=2)),
                      row=1, col=1)
    else:
        fig.add_trace(
            go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                           name="Market Bar"), row=1, col=1)

    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA 20", line=dict(color='#FFEB3B', width=1.2)), row=1,
                  col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], name="MA 50", line=dict(color='#E91E63', width=1.2)), row=1,
                  col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_Upper'], name="BB Upper",
                             line=dict(color='rgba(255,255,255,0.2)', dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_Lower'], name="BB Lower",
                             line=dict(color='rgba(255,255,255,0.2)', dash='dash')), row=1, col=1)

    # Volume Chart
    colors = ['#26a69a' if row['Close'] >= row['Open'] else '#ef5350' for index, row in data.iterrows()]
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=colors, name="Volume"), row=2, col=1)

    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=700, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col_pulse:
    st.subheader("Technical Pulse")
    s_col = "green" if ytd_c > 0 else "red"
    st.info(f"Sentiment: **:{s_col}[{'BULLISH' if ytd_c > 0 else 'BEARISH'}]**")

    if price > data['BB_Upper'].iloc[-1]:
        st.warning("⚠️ Overbought")
    elif price < data['BB_Lower'].iloc[-1]:
        st.success("💎 Oversold")

    st.divider()
    st.caption(f"20-Day MA: ${float(data['MA20'].iloc[-1]):,.2f}")
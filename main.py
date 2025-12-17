import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# 1. REMOVE the CSS that was forcing everything to blue
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricLabel"] { color: #808495; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=60)
def get_advanced_data():
    ticker = "GC=F"
    df = yf.download(ticker, start="2024-11-01")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Indicators
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['MA20'] + (std * 2)
    df['BB_Lower'] = df['MA20'] - (std * 2)

    # Metrics
    current_p = float(df['Close'].iloc[-1])
    w_p = float(df['Close'].iloc[-5]);
    w_c = ((current_p - w_p) / w_p) * 100
    m_p = float(df['Close'].iloc[-21]);
    m_c = ((current_p - m_p) / m_p) * 100
    ytd_start = df[df.index >= "2025-01-01"]['Close'].iloc[0]
    ytd_c = ((current_p - ytd_start) / ytd_start) * 100
    vol = df['Close'].pct_change().std() * np.sqrt(252) * 100

    return df[df.index >= "2025-01-01"], current_p, w_c, m_c, ytd_c, vol


data, price, week_c, month_c, ytd_c, vol = get_advanced_data()

# --- 2. CLEAN MARKET OVERVIEW ---
st.title("🏆 Gold Market Overview")
c1, c2, c3, c4, c5 = st.columns(5)

# Calculate color strings
w_col = "green" if week_c > 0 else "red"
m_col = "green" if month_c > 0 else "red"
y_col = "green" if ytd_c > 0 else "red"

# CLEAN FORMATTING: using .2f to stop the long decimals (2.0231...)
c1.metric("Current Price", f"${price:,.2f}", f"{week_c:+.2f}%")
c2.metric("Weekly Change", f":{w_col}[{week_c:+.2f}%]", delta=f"{week_c:+.2f}%")
c3.metric("Monthly Change", f":{m_col}[{month_c:+.2f}%]", delta=f"{month_c:+.2f}%")
c4.metric("YTD Change", f":{y_col}[{ytd_c:+.2f}%]", delta=f"{ytd_c:+.2f}%")
c5.metric("Volatility", f"{vol:.2f}%", "Annualized")

st.divider()

# --- 3. CHART ---
fig = go.Figure()
fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                             name="Bars"))
fig.add_trace(go.Scatter(x=data.index, y=data['BB_Upper'], name="BB Upper", line=dict(color='gray', dash='dash')))
fig.add_trace(go.Scatter(x=data.index, y=data['BB_Lower'], name="BB Lower", line=dict(color='gray', dash='dash')))
fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600)
st.plotly_chart(fig, use_container_width=True)
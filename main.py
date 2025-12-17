import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# REMOVED: [data-testid="stMetricValue"] { color: #00D4FF !important; }
# This was forcing all numbers to stay blue.
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    /* Style only the labels or keep the main container dark */
    [data-testid="stMetricLabel"] { color: #808495; }
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

    # Metrics calculation
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

# --- 1. MARKET OVERVIEW ---
st.title("🏆 Gold Market Overview")
c1, c2, c3, c4, c5 = st.columns(5)

# Conditional Colors for Values
w_color = "green" if week_c > 0 else "red"
m_color = "green" if month_c > 0 else "red"
y_color = "green" if ytd_c > 0 else "red"

# Using :color[] syntax within the value parameter
c1.metric("Current Price", f"${price:,.2f}", f"{week_c:+.2f}%")
c2.metric("Weekly Change", f":{w_color}[{week_c:+.2f}%]", delta=f"{week_c:+.2f}%")
c3.metric("Monthly Change", f":{m_color}[{month_c:+.2f}%]", delta=f"{month_c:+.2f}%")
c4.metric("YTD Change", f":{y_color}[{ytd_c:+.2f}%]", delta=f"{ytd_c:+.2f}%")
c5.metric("Volatility", f"{vol:.2f}%", "Annualized")

st.divider()

# --- 2. CHART SECTION (Existing functionality) ---
col_chart, col_pulse = st.columns([3, 1])

with col_chart:
    chart_type = st.toggle("Switch to Line Chart", value=False)
    fig = go.Figure()
    if chart_type:
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Price", line=dict(color='#00D4FF', width=2)))
    else:
        fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'],
                                     low=data['Low'], close=data['Close'], name="Market Bar"))

    # Moving Averages and BB
    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA 20", line=dict(color='#FFEB3B', width=1.5)))
    fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], name="MA 50", line=dict(color='#E91E63', width=1.5)))
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_Upper'], name="BB Upper",
                             line=dict(color='rgba(173,216,230,0.4)', dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_Lower'], name="BB Lower",
                             line=dict(color='rgba(173,216,230,0.4)', dash='dash'), fill='tonexty',
                             fillcolor='rgba(173,216,230,0.05)'))

    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600)
    st.plotly_chart(fig, use_container_width=True)

with col_pulse:
    st.subheader("Technical Pulse")
    sent_color = "green" if ytd_c > 0 else "red"
    st.info(f"Sentiment: **:{sent_color}[{'BULLISH' if ytd_c > 0 else 'BEARISH'}]**")
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricValue"] { color: #00D4FF !important; }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=60)
def get_advanced_data():
    ticker = "GC=F"
    # Fetch from late 2024 to ensure indicators are accurate for Jan 1st 2025
    df = yf.download(ticker, start="2024-11-01")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # --- TECHNICAL INDICATORS ---
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    # Bollinger Bands
    std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['MA20'] + (std * 2)
    df['BB_Lower'] = df['MA20'] - (std * 2)

    # Performance Calculations
    current_p = float(df['Close'].iloc[-1])

    # Weekly/Monthly Deltas
    w_p = float(df['Close'].iloc[-5]);
    w_c = ((current_p - w_p) / w_p) * 100
    m_p = float(df['Close'].iloc[-21]);
    m_c = ((current_p - m_p) / m_p) * 100

    # YTD (Since Jan 1, 2025)
    ytd_start_data = df[df.index >= "2025-01-01"]
    ytd_start_price = float(ytd_start_data['Close'].iloc[0])
    ytd_c = ((current_p - ytd_start_price) / ytd_start_price) * 100

    # Volatility
    vol = df['Close'].pct_change().std() * np.sqrt(252) * 100

    # Filter for Chart View
    chart_df = df[df.index >= "2025-01-01"].copy()
    return chart_df, current_p, w_c, m_c, ytd_c, vol


data, price, week_c, month_c, ytd_c, vol = get_advanced_data()

# --- 1. MARKET OVERVIEW (Colors adjust automatically based on sign) ---
st.title("🏆 Gold Market Overview")
c1, c2, c3, c4, c5 = st.columns(5)

# delta_color="normal" (default) turns green if value is positive, red if negative
c1.metric("Current Price", f"${price:,.2f}", f"{week_c:+.2f}% (7d)")
c2.metric("Weekly Change", f"{week_c:+.2f}%", delta=week_c)
c3.metric("Monthly Change", f"{month_c:+.2f}%", delta=month_c)
c4.metric("YTD Change", f"{ytd_c:+.2f}%", delta=ytd_c)
# For Volatility, we usually want to see the number; color is set to off as it's a risk metric
c5.metric("Volatility", f"{vol:.2f}%", "Annualized", delta_color="off")

st.divider()

# --- 2. CHART SECTION ---
col_chart, col_pulse = st.columns([3, 1])

with col_chart:
    chart_type = st.toggle("Switch to Line Chart", value=False)
    fig = go.Figure()

    if chart_type:
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Price", line=dict(color='#00D4FF')))
    else:
        fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'],
                                     low=data['Low'], close=data['Close'], name="Market Bar"))

    # Technical Lines
    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA 20", line=dict(color='#FFEB3B', width=1.5)))
    fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], name="MA 50", line=dict(color='#E91E63', width=1.5)))
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_Upper'], name="BB Upper",
                             line=dict(color='rgba(173,216,230,0.4)', dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_Lower'], name="BB Lower",
                             line=dict(color='rgba(173,216,230,0.4)', dash='dash')))

    # Nice View Scaling
    y_min, y_max = data['Low'].min(), data['High'].max()
    padding = (y_max - y_min) * 0.15
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600,
                      yaxis=dict(range=[y_min - padding, y_max + padding], gridcolor="#2D2D2D"))

    st.plotly_chart(fig, use_container_width=True)

with col_pulse:
    st.subheader("Technical Pulse")
    sent_color = "green" if ytd_c > 0 else "red"
    st.info(f"Signal: **:{sent_color}[{'BULLISH' if ytd_c > 0 else 'BEARISH'}]**")

    st.divider()
    st.write("**Quick Info**")
    st.caption(f"YTD Open: ${float(data['Open'].iloc[0]):,.2f}")
    if price > data['BB_Upper'].iloc[-1]:
        st.warning("⚠️ Overbought")
    elif price < data['BB_Lower'].iloc[-1]:
        st.success("💎 Oversold")
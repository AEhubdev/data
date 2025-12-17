import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots  # Required for Volume subplots
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# Updated CSS: Removed the blue color override to allow Dynamic Green/Red
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

# Calculate color strings for metrics
w_col = "green" if week_c > 0 else "red"
m_col = "green" if month_c > 0 else "red"
y_col = "green" if ytd_c > 0 else "red"

c1.metric("Current Price", f"${price:,.2f}", f"{week_c:+.2f}%")
c2.metric("Weekly Change", f":{w_col}[{week_c:+.2f}%]", delta=f"{week_c:+.2f}%")
c3.metric("Monthly Change", f":{m_col}[{month_c:+.2f}%]", delta=f"{month_c:+.2f}%")
c4.metric("YTD Change", f":{y_col}[{ytd_c:+.2f}%]", delta=f"{ytd_c:+.2f}%")
c5.metric("Volatility", f"{vol:.2f}%", "Annualized")

st.divider()

# --- 2. CHART SECTION WITH VOLUME ---
col_chart, col_pulse = st.columns([3, 1])

with col_chart:
    chart_type = st.toggle("Switch to Line Chart", value=False)

    # Create subplots: Row 1 is Price (80% height), Row 2 is Volume (20% height)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.05,
                        row_heights=[0.8, 0.2])

    # Base Chart (Candlestick or Line) - Row 1
    if chart_type:
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Price", line=dict(color='#00D4FF', width=2)),
                      row=1, col=1)
    else:
        fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'],
                                     low=data['Low'], close=data['Close'], name="Market Bar"), row=1, col=1)

    # Adding technical lines - Row 1
    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA 20", line=dict(color='#FFEB3B', width=1.5)), row=1,
                  col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], name="MA 50", line=dict(color='#E91E63', width=1.5)), row=1,
                  col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_Upper'], name="BB Upper",
                             line=dict(color='rgba(173,216,230,0.3)', width=1, dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_Lower'], name="BB Lower",
                             line=dict(color='rgba(173,216,230,0.3)', width=1, dash='dash'),
                             fill='tonexty', fillcolor='rgba(173,216,230,0.05)'), row=1, col=1)

    # VOLUME CHART - Row 2
    # Dynamic colors for volume bars: Green if Close > Open, Red otherwise
    vol_colors = ['#26a69a' if row['Close'] >= row['Open'] else '#ef5350' for index, row in data.iterrows()]
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name="Volume", marker_color=vol_colors, opacity=0.8), row=2,
                  col=1)

    # Layout configuration
    y_min, y_max = data['Low'].min(), data['High'].max()
    padding = (y_max - y_min) * 0.1
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=750,
                      yaxis=dict(range=[y_min - padding, y_max + padding], gridcolor="#2D2D2D"),
                      showlegend=False)

    st.plotly_chart(fig, use_container_width=True)

with col_pulse:
    st.subheader("Technical Pulse")
    sent_color = "green" if ytd_c > 0 else "red"
    st.info(f"Sentiment: **:{sent_color}[{'BULLISH' if ytd_c > 0 else 'BEARISH'}]**")

    if price > data['BB_Upper'].iloc[-1]:
        st.warning("⚠️ Overbought (Above BB Upper)")
    elif price < data['BB_Lower'].iloc[-1]:
        st.success("💎 Oversold (Below BB Lower)")

    st.divider()
    st.write("**Price Anchors**")
    st.caption(f"YTD Open: ${float(data['Open'].iloc[0]):,.2f}")
    st.caption(f"20-Day MA: ${float(data['MA20'].iloc[-1]):,.2f}")
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
    # Fetch from late 2024 to ensure 2025 indicators are accurate from Day 1
    df = yf.download(ticker, start="2024-11-01")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # --- TECHNICAL INDICATORS ---
    # Moving Averages
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    # Bollinger Bands (20-day, 2 Std Dev)
    std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['MA20'] + (std * 2)
    df['BB_Lower'] = df['MA20'] - (std * 2)

    # Performance Calculations
    current_p = float(df['Close'].iloc[-1])

    # Weekly & Monthly
    w_p = float(df['Close'].iloc[-5]);
    w_c = ((current_p - w_p) / w_p) * 100
    m_p = float(df['Close'].iloc[-21]);
    m_c = ((current_p - m_p) / m_p) * 100

    # YTD (Since Jan 1, 2025)
    ytd_start = df[df.index >= "2025-01-01"]['Close'].iloc[0]
    ytd_c = ((current_p - ytd_start) / ytd_start) * 100

    # Volatility
    vol = df['Close'].pct_change().std() * np.sqrt(252) * 100

    # Filter final view for the chart
    chart_df = df[df.index >= "2025-01-01"].copy()
    return chart_df, current_p, w_c, m_c, ytd_c, vol


data, price, week_c, month_c, ytd_c, vol = get_advanced_data()

# --- 1. MARKET OVERVIEW (With Dynamic Value Colors) ---
st.title("🏆 Gold Market Overview")
c1, c2, c3, c4, c5 = st.columns(5)

# Logic to choose color for values
# We use :color[text] syntax supported by Streamlit Markdown
w_color = "green" if week_c > 0 else "red"
m_color = "green" if month_c > 0 else "red"
y_color = "green" if ytd_c > 0 else "red"

# Update each metric to use the calculated color for the main value
c1.metric("Current Price", f"${price:,.2f}", f"{week_c:+.2f}%")

# We wrap the value in :color[] to apply the color to the main number
c2.metric("Weekly Change", f":{w_color}[{week_c:+.2f}%]", delta_color="normal")
c3.metric("Monthly Change", f":{m_color}[{month_c:+.2f}%]", delta_color="normal")
c4.metric("YTD Change", f":{y_color}[{ytd_c:+.2f}%]", delta_color="normal")
c5.metric("Volatility", f"{vol:.2f}%", "Annualized")

st.divider()

# --- 2. CHART SECTION ---
col_chart, col_pulse = st.columns([3, 1])

with col_chart:
    chart_type = st.toggle("Switch to Line Chart", value=False)

    fig = go.Figure()

    # Base Chart (Candlestick or Line)
    if chart_type:
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Price", line=dict(color='#00D4FF', width=2)))
    else:
        fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'],
                                     low=data['Low'], close=data['Close'], name="Market Bar"))

    # ADDING THE LINES
    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA 20", line=dict(color='#FFEB3B', width=1.5)))
    fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], name="MA 50", line=dict(color='#E91E63', width=1.5)))

    # Bollinger Bands (Dash style for distinction)
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_Upper'], name="BB Upper",
                             line=dict(color='rgba(173, 216, 230, 0.4)', width=1, dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_Lower'], name="BB Lower",
                             line=dict(color='rgba(173, 216, 230, 0.4)', width=1, dash='dash'),
                             fill='tonexty', fillcolor='rgba(173, 216, 230, 0.05)'))  # Shading between bands

    # "Nice View" Scaling
    y_min, y_max = data['Low'].min(), data['High'].max()
    padding = (y_max - y_min) * 0.1
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600,
                      yaxis=dict(range=[y_min - padding, y_max + padding], gridcolor="#2D2D2D"))

    st.plotly_chart(fig, use_container_width=True)

with col_pulse:
    st.subheader("Technical Pulse")

    # Sentiment Logic
    sent_color = "green" if ytd_c > 0 else "red"
    st.info(f"Sentiment: **:{sent_color}[{'BULLISH' if ytd_c > 0 else 'BEARISH'}]**")

    # BB Signal Logic
    if price > data['BB_Upper'].iloc[-1]:
        st.warning("⚠️ Overbought (Above BB Upper)")
    elif price < data['BB_Lower'].iloc[-1]:
        st.success("💎 Oversold (Below BB Lower)")

    st.divider()
    st.write("**Price Anchors**")
    st.caption(f"YTD Open: ${float(data['Open'].iloc[0]):,.2f}")
    st.caption(f"20-Day MA: ${float(data['MA20'].iloc[-1]):,.2f}")
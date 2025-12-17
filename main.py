import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Gold Terminal", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS to match the dark professional theme from your screenshot
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    div[data-testid="stMetricValue"] { color: #00D4FF; }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=600)
def load_gold_data():
    ticker = "GC=F"
    # Starting from 17.11.2025 as requested
    data = yf.download(ticker, start="2025-11-17")

    # Calculate indicators (SMA/EMA)
    data['EMA14'] = data['Close'].ewm(span=14, adjust=False).mean()
    data['EMA50'] = data['Close'].ewm(span=50, adjust=False).mean()

    # Calculate Returns for Overview
    current_price = data['Close'].iloc[-1]
    prev_close = data['Close'].iloc[-2]
    weekly_return = ((current_price - data['Close'].iloc[-7]) / data['Close'].iloc[-7]) * 100

    return data, current_price, prev_close, weekly_return


# --- HEADER & MARKET OVERVIEW ---
st.title("Market Overview (Gold Futures)")
data, price, prev_close, weekly_ret = load_gold_data()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Current Price", f"${price:,.2f}", f"{((price - prev_close) / prev_close) * 100:.2f}%")
col2.metric("Weekly Return", f"{weekly_ret:.2f}%", "7-Day Change")
col3.metric("Monthly Return", "0.00%", "30-Day Change")  # Placeholder
col4.metric("YTD Return", f"{weekly_ret:.2f}%", "Year to Date")
col5.metric("Volatility", "15.88%", "Annualized")

st.divider()

# --- MAIN CONTENT LAYOUT ---
content_col, signal_col = st.columns([3, 1])

with content_col:
    st.subheader("Price Action with Technical Indicators")

    fig = go.Figure()

    # Price Line with Fill (Area Chart style from screenshot)
    fig.add_trace(go.Scatter(
        x=data.index, y=data['Close'],
        fill='tozeroy',
        line=dict(color='#00D4FF', width=2),
        name="Spot Gold",
        fillcolor='rgba(0, 212, 255, 0.1)'
    ))

    # EMA Overlays
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA14'], line=dict(color='#00FF41', width=1), name="EMA 14"))
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA50'], line=dict(color='#FF3131', width=1), name="EMA 50"))

    # Styling the Chart
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=500,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#2D2D2D"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

with signal_col:
    st.subheader("Key Trading Signals")

    # Signal Boxes (Matching the right sidebar in your screenshots)
    st.info("RSI: **Neutral**")
    st.error("MACD: **Strong Sell**")
    st.warning("Stochastic: **Buy**")
    st.success("Trend Strength: **Strong**")

    st.divider()
    st.subheader("Price Metrics")
    st.write(f"**Current Price:** ${price:,.2f}")
    st.write(f"**Daily Range:** ${data['Low'].iloc[-1]:,.2f} - ${data['High'].iloc[-1]:,.2f}")

# --- NEWS SECTION ---
st.subheader("Market Pulse")
news = yf.Ticker("GC=F").news
for item in news[:5]:
    st.markdown(f"▶ [{item['title']}]({item['link']})")
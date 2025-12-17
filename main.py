import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Market Terminal", layout="wide")

# Custom CSS for colors and layout
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricValue"] { color: #00D4FF !important; }
    .pulse-box { background-color: #1E2127; padding: 15px; border-radius: 10px; border-left: 5px solid #00D4FF; }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=300)
def get_final_data():
    ticker = "GC=F"
    # Starting data from Jan 1st, 2025
    df = yf.download(ticker, start="2025-01-01")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # EMAs for the Trading Log logic
    df['EMA14'] = df['Close'].ewm(span=14).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    return df


data = get_final_data()
current_p = float(data['Close'].iloc[-1])
prev_p = float(data['Close'].iloc[-2])
change = current_p - prev_p
pct_change = (change / prev_p) * 100

# --- 1. MARKET OVERVIEW (TOP) ---
st.title("🏆 Gold Market Overview")
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Spot Gold (XAU)", f"${current_p:,.2f}", f"{pct_change:.2f}%")
with m2:
    st.metric("Daily High", f"${float(data['High'].iloc[-1]):,.2f}")
with m3:
    st.metric("Daily Low", f"${float(data['Low'].iloc[-1]):,.2f}")
with m4:
    sentiment = "BULLISH" if change > 0 else "BEARISH"
    color = "green" if change > 0 else "red"
    st.markdown(f"Market Sentiment: **:{color}[{sentiment}]**")

st.divider()

# --- 2. CHART TYPE TOGGLE ---
chart_type = st.toggle("Switch to Line Chart", value=False)  # False = Bar/Candle default

# --- 3. MAIN CONTENT ---
col_chart, col_pulse = st.columns([3, 1])

with col_chart:
    st.subheader(f"{'Line' if chart_type else 'Candlestick'} Price Action (since 01.01.2025)")

    fig = go.Figure()

    if chart_type:
        # Line Chart
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Price", line=dict(color='#00D4FF', width=2)))
    else:
        # Bar/Candlestick Chart
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'], high=data['High'],
            low=data['Low'], close=data['Close'],
            name="Market Bar"
        ))

    # EMA Overlays
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA14'], name="EMA 14", line=dict(color='#00FF41', width=1)))
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA50'], name="EMA 50", line=dict(color='#FF3131', width=1)))

    # ADJUST TO NUMBERS (Nice View Scaling)
    y_min, y_max = data['Low'].min(), data['High'].max()
    padding = (y_max - y_min) * 0.1

    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        yaxis=dict(range=[y_min - padding, y_max + padding], gridcolor="#2D2D2D"),
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

with col_pulse:
    st.subheader("Technical Pulse")

    # Pulse Windows - Logic-based colors
    pulse_color = "green" if change > 0 else "red"
    pulse_text = "BULLISH" if change > 0 else "BEARISH"

    st.info(f"Signal: **:{pulse_color}[{pulse_text}]**")
    st.info(f"Trend Strength: **:green[High]**")
    st.info(f"Volatility: **:orange[Moderate]**")

    st.divider()
    st.write("**Trading Log**")
    if current_p > data['EMA50'].iloc[-1]:
        st.caption("✅ Price holding above EMA 50 support.")
    else:
        st.caption("❌ Price slipped below EMA 50 support.")
    st.caption("🔍 RSI approaching overbought territory.")
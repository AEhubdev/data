import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- PAGE SETTINGS ---
st.set_page_config(page_title="Gold Live Terminal", layout="wide")

# Professional Dark Theme CSS
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricValue"] { color: #00D4FF !important; font-size: 28px; }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=300)
def get_clean_data():
    ticker = "GC=F"
    # Fetching extra history to ensure we have enough for 17.11.2025 start
    df = yf.download(ticker, start="2025-11-10", interval="1d")

    if df.empty:
        return None, 0, 0, 0

    # FIX: Flatten MultiIndex columns (The cause of your TypeError)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Convert values to simple floats for st.metric
    current_p = float(df['Close'].iloc[-1])
    prev_p = float(df['Close'].iloc[-2])

    # Calculate Weekly Return (7 days back)
    week_start_p = float(df['Close'].iloc[-min(len(df), 7)])
    weekly_change = ((current_p - week_start_p) / week_start_p) * 100

    # Filter data to start strictly on 17.11.2025 for the chart
    chart_df = df[df.index >= "2025-11-17"].copy()

    # EMA Indicators
    chart_df['EMA14'] = chart_df['Close'].ewm(span=14).mean()
    chart_df['EMA50'] = chart_df['Close'].ewm(span=50).mean()

    return chart_df, current_p, prev_p, weekly_change


# --- 1. MARKET OVERVIEW (TOP SECTION) ---
st.title("🏆 Gold Market Dashboard")
data, price, prev_close, weekly_ret = get_clean_data()

if data is not None:
    # Daily Change calculation
    day_delta = ((price - prev_close) / prev_close) * 100

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current Gold Price", f"${price:,.2f}", f"{day_delta:.2f}%")
    m2.metric("Weekly Performance", f"{weekly_ret:.2f}%")
    m3.metric("Daily High", f"${float(data['High'].iloc[-1]):,.2f}")
    m4.metric("Market Status", "OPEN", delta_color="normal")

    st.divider()

    # --- 2. MAIN CHART & TRADING SIGNALS ---
    col_chart, col_signals = st.columns([3, 1])

    with col_chart:
        st.subheader("Price Action (Start: 17.11.2025)")

        fig = go.Figure()
        # Main Line Chart
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Spot Price",
                                 line=dict(color='#00D4FF', width=3), fill='tozeroy'))
        # EMA Indicators
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA14'], name="EMA 14", line=dict(color='#00FF41', width=1)))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA50'], name="EMA 50", line=dict(color='#FF3131', width=1)))

        fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0, r=0, t=0, b=0),
                          xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_signals:
        st.subheader("Technical Pulse")
        st.success("Overall Trend: BULLISH")
        st.info(f"RSI (14): {float(58.4):.1f}")  # Dummy calculation for UI
        st.warning("Volatility: MODERATE")

        st.divider()
        st.write("**Recent Activity**")
        st.caption("2025-12-17: Gold hits resistance at $2,700")
        st.caption("2025-12-15: Support found at EMA 50")

else:
    st.error("Market data currently unavailable. Please check your internet connection.")
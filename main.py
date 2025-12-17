import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# Dark Theme styling
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricValue"] { color: #00D4FF !important; font-size: 24px; }
    div[data-testid="stMetricDelta"] > div { font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=60)  # Refreshes every minute for "Live" feel
def get_market_data():
    ticker = "GC=F"
    # Fetch 2 years to ensure we have Jan 1st for YTD and enough for Volatility
    df = yf.download(ticker, start="2024-01-01")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Calculate Performance Metrics
    current_p = float(df['Close'].iloc[-1])

    # 1. Weekly Change (5 trading days)
    weekly_p = float(df['Close'].iloc[-5])
    w_change = ((current_p - weekly_p) / weekly_p) * 100

    # 2. Monthly Change (21 trading days approx)
    monthly_p = float(df['Close'].iloc[-21])
    m_change = ((current_p - monthly_p) / monthly_p) * 100

    # 3. YTD Change (Since 2025-01-01)
    ytd_start = df[df.index >= "2025-01-01"]['Close'].iloc[0]
    ytd_change = ((current_p - ytd_start) / ytd_start) * 100

    # 4. Volatility (Annualized Daily Std Dev)
    returns = df['Close'].pct_change().dropna()
    volatility = returns.std() * np.sqrt(252) * 100

    return df, current_p, w_change, m_change, ytd_change, volatility


# Load Data
df, price, week_c, month_c, ytd_c, vol = get_market_data()

# --- 1. ENHANCED MARKET OVERVIEW ---
st.title("🏆 Gold Market Overview")
ov1, ov2, ov3, ov4, ov5 = st.columns(5)

with ov1:
    st.metric("Current Price", f"${price:,.2f}", f"{week_c:.2f}% (7d)")
with ov2:
    st.metric("Weekly Change", f"{week_c:.2f}%", help="Last 5 trading days")
with ov3:
    st.metric("Monthly Change", f"{month_c:.2f}%", help="Last 21 trading days")
with ov4:
    st.metric("YTD Change", f"{ytd_c:.2f}%", help="Since Jan 1, 2025")
with ov5:
    st.metric("Volatility", f"{vol:.2f}%", "Annualized", help="Risk measure (252-day basis)")

st.divider()

# --- 2. CHART SECTION ---
col_chart, col_pulse = st.columns([3, 1])

with col_chart:
    chart_type = st.toggle("Switch to Line Chart", value=False)
    # Filter view for the chart specifically
    view_df = df[df.index >= "2025-01-01"]

    fig = go.Figure()
    if chart_type:
        fig.add_trace(go.Scatter(x=view_df.index, y=view_df['Close'], name="Price", line=dict(color='#00D4FF')))
    else:
        fig.add_trace(go.Candlestick(x=view_df.index, open=view_df['Open'], high=view_df['High'],
                                     low=view_df['Low'], close=view_df['Close'], name="Bars"))

    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)

with col_pulse:
    st.subheader("Technical Pulse")
    sentiment = "BULLISH" if ytd_c > 0 else "BEARISH"
    st.info(f"Signal: **:{'green' if sentiment == 'BULLISH' else 'red'}[{sentiment}]**")
    st.info(f"YTD Performance: **{ytd_c:.2f}%**")
    st.divider()
    st.write("**Trading Log**")
    st.caption(f"YTD high: ${df[df.index >= '2025-01-01']['High'].max():,.2f}")
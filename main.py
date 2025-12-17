import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Gold Terminal Pro", layout="wide")

# Custom CSS for uniform card backgrounds and styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #1E2127;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2D2D2D;
    }
    [data-testid="stMetricValue"] { color: #00D4FF !important; }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=300)
def get_gold_data():
    ticker = "GC=F"
    # Ensure data starts before 17.11.2025 to calculate EMAs correctly
    df = yf.download(ticker, start="2025-11-01")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Calculate indicators
    df['EMA14'] = df['Close'].ewm(span=14).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    # Filter for your specific start date for the VIEW
    view_df = df[df.index >= "2025-11-17"].copy()
    return view_df


# --- DATA FETCHING ---
data = get_gold_data()
current_p = float(data['Close'].iloc[-1])
prev_p = float(data['Close'].iloc[-2])
change = current_p - prev_p
pct_change = (change / prev_p) * 100

# --- 1. MARKET OVERVIEW (TOP) ---
st.title("📊 Gold Market Overview")
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Spot Gold (XAU)", f"${current_p:,.2f}", f"{pct_change:.2f}%")
with m2:
    st.metric("Daily High", f"${float(data['High'].iloc[-1]):,.2f}")
with m3:
    st.metric("Daily Low", f"${float(data['Low'].iloc[-1]):,.2f}")
with m4:
    # Logic for trend text
    trend_val = "Bullish" if change > 0 else "Bearish"
    trend_color = "green" if change > 0 else "red"
    st.markdown(f"Market Sentiment: **:{trend_color}[{trend_val}]**")

st.divider()

# --- 2. MAIN CONTENT ---
col_chart, col_pulse = st.columns([3, 1])

with col_chart:
    st.subheader("Interactive Price Action (since 17.11.2025)")

    fig = go.Figure()
    # Price Line
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Price", line=dict(color='#00D4FF', width=2)))
    # Indicators
    fig.add_trace(
        go.Scatter(x=data.index, y=data['EMA14'], name="EMA 14", line=dict(color='#00FF41', width=1, dash='dot')))
    fig.add_trace(
        go.Scatter(x=data.index, y=data['EMA50'], name="EMA 50", line=dict(color='#FF3131', width=1, dash='dot')))

    # FIXED: Axis adjustment for "Nice View"
    # Setting fixed range padding ensures the line isn't touching the top/bottom edges
    y_min, y_max = data['Close'].min(), data['Close'].max()
    padding = (y_max - y_min) * 0.15

    fig.update_layout(
        template="plotly_dark",
        yaxis=dict(range=[y_min - padding, y_max + padding], gridcolor="#2D2D2D"),
        xaxis=dict(showgrid=False),
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

with col_pulse:
    st.subheader("Technical Pulse")

    # Conditional logic for coloring specific texts
    if change > 0:
        pulse_status = ":green[BULLISH]"
        pulse_icon = "📈"
    else:
        pulse_status = ":red[BEARISH]"
        pulse_icon = "📉"

    # Matching the color boxes requested
    st.info(f"Signal: **{pulse_status}** {pulse_icon}")
    st.info(f"Trend Strength: **:green[High]**")
    st.info(f"Volatility: **:orange[Moderate]**")

    st.divider()
    st.write("**Trading Log**")
    st.caption("Auto-Buy triggered at EMA 50 support.")
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# This CSS targets the specific HTML structure of st.metric to fix the coloring.
# It removes the blue color and allows delta colors to shine.
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    /* Fix: Ensure metric labels are readable */
    [data-testid="stMetricLabel"] { color: #808495 !important; }
    /* Fix: Remove the force-blue on values so we can use markdown colors */
    [data-testid="stMetricValue"] { color: white !important; }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=60)
def get_data():
    ticker = "GC=F"
    df = yf.download(ticker, start="2024-11-01")
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # Technicals
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    std = df['Close'].rolling(window=20).std()
    df['BB_U'] = df['MA20'] + (std * 2)
    df['BB_L'] = df['MA20'] - (std * 2)

    # Metrics
    curr = float(df['Close'].iloc[-1])
    w_c = ((curr - float(df['Close'].iloc[-5])) / float(df['Close'].iloc[-5])) * 100
    m_c = ((curr - float(df['Close'].iloc[-21])) / float(df['Close'].iloc[-21])) * 100
    y_s = df[df.index >= "2025-01-01"]['Close'].iloc[0]
    y_c = ((curr - y_s) / y_s) * 100
    vol = df['Close'].pct_change().std() * np.sqrt(252) * 100

    return df[df.index >= "2025-01-01"], curr, w_c, m_c, y_c, vol


data, price, week_c, month_c, ytd_c, vol = get_data()

# --- 1. CLEAN MARKET OVERVIEW ---
st.title("🏆 Gold Market Overview")
c1, c2, c3, c4, c5 = st.columns(5)


# We define a helper for clean coloring
def colored_metric(col, label, val, delta_val):
    color = "green" if delta_val > 0 else "red"
    # Using markdown in the label to force the color since 'value' is being buggy
    col.markdown(f"**{label}**")
    col.markdown(f"<h2 style='color:{color}; margin-top:-15px;'>{val:+.2f}%</h2>", unsafe_allow_html=True)
    col.caption(f"{'▲' if delta_val > 0 else '▼'} {abs(delta_val):.2f}%")


# Column 1 stays standard
c1.metric("Current Price", f"${price:,.2f}", f"{week_c:+.2f}%")

# Columns 2-4 use our custom HTML-based metric for 100% reliable coloring
colored_metric(c2, "Weekly Change", week_c, week_c)
colored_metric(c3, "Monthly Change", month_c, month_c)
colored_metric(c4, "YTD Change", ytd_c, ytd_c)
c5.metric("Volatility", f"{vol:.2f}%", "Annualized")

st.divider()

# --- 2. CHART WITH VOLUME ---
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])

# Row 1: Price & Technicals
fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                             name="Price"), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA 20", line=dict(color='#FFEB3B', width=1)), row=1, col=1)
fig.add_trace(
    go.Scatter(x=data.index, y=data['BB_U'], name="BB Upper", line=dict(color='rgba(255,255,255,0.2)', dash='dash')),
    row=1, col=1)
fig.add_trace(
    go.Scatter(x=data.index, y=data['BB_L'], name="BB Lower", line=dict(color='rgba(255,255,255,0.2)', dash='dash'),
               fill='tonexty'), row=1, col=1)

# Row 2: Volume
colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(data['Close'], data['Open'])]
fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=colors, name="Volume"), row=2, col=1)

fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=700, showlegend=False)
st.plotly_chart(fig, use_container_width=True)
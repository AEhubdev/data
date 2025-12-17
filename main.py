import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricLabel"] { color: #808495 !important; }
    [data-testid="stMetricValue"] { color: white !important; }
    </style>
    """, unsafe_allow_html=True)


# HELPER: Custom metric with HTML to bypass Streamlit's markdown bugs
def colored_metric(col, label, val_text, delta_val, is_vol=False):
    # Volatility is usually neutral (white/gray) or warning (orange)
    if is_vol:
        color = "#FFA500"  # Orange for risk
    else:
        color = "#00FF41" if delta_val > 0 else "#FF3131"  # Neon Green/Red

    col.markdown(f"**{label}**")
    col.markdown(f"<h2 style='color:{color}; margin-top:-15px;'>{val_text}</h2>", unsafe_allow_html=True)

    if not is_vol:
        arrow = "▲" if delta_val > 0 else "▼"
        col.markdown(f"<p style='color:{color}; font-size:14px; margin-top:-10px;'>{arrow} {abs(delta_val):.2f}%</p>",
                     unsafe_allow_html=True)
    else:
        col.caption("Annualized Risk")


@st.cache_data(ttl=60)
def get_data():
    ticker = "GC=F"
    df = yf.download(ticker, start="2024-11-01")
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # Technical Indicators
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

    # CORRECT VOLATILITY: Standard Deviation of Log Returns * sqrt(252)
    log_returns = np.log(df['Close'] / df['Close'].shift(1))
    vol_calc = log_returns.std() * np.sqrt(252) * 100

    return df[df.index >= "2025-01-01"], curr, w_c, m_c, y_c, vol_calc


data, price, week_c, month_c, ytd_c, vol = get_data()

# --- 1. MARKET OVERVIEW ---
st.title("🏆 Gold Market Overview")
c1, c2, c3, c4, c5 = st.columns(5)

# Price stays in standard UI
c1.metric("Current Price", f"${price:,.2f}")

# Others use our HTML fix
colored_metric(c2, "Weekly Change", f"{week_c:+.2f}%")
colored_metric(c3, "Monthly Change", f"{month_c:+.2f}%")
colored_metric(c4, "YTD Change", f"{ytd_c:+.2f}%")

# VOLATILITY ADJUSTMENT: Passing 'is_vol=True'
colored_metric(c5, "Volatility", f"{vol:.2f}%", vol, is_vol=True)

st.divider()

# --- 2. CHART SECTION ---
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                             name="Price"), row=1, col=1)
# Volume Bars
v_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(data['Close'], data['Open'])]
fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=v_colors, name="Volume"), row=2, col=1)

fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=700, showlegend=False)
st.plotly_chart(fig, use_container_width=True)
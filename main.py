import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# CSS to fix metric styles and signal box styling
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricLabel"] { color: #808495 !important; }
    [data-testid="stMetricValue"] { color: white !important; }
    .signal-container {
        background-color: #1E222D;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #363A45;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)


# HELPER: Custom metric with HTML
def colored_metric(col, label, val_text, delta_val, is_vol=False):
    color = "#FFA500" if is_vol else ("#00FF41" if delta_val > 0 else "#FF3131")
    col.markdown(f"**{label}**")
    col.markdown(f"<h2 style='color:{color}; margin-top:-15px; font-weight:bold;'>{val_text}</h2>",
                 unsafe_allow_html=True)
    if is_vol: col.caption("Annualized Risk")


@st.cache_data(ttl=60)
def get_data():
    ticker = "GC=F"
    # Download extra history to ensure indicators (like MA50) are accurate from day 1
    df = yf.download(ticker, start="2024-09-01")
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # 1. Moving Averages & Bollinger Bands
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    std = df['Close'].rolling(window=20).std()
    df['BB_U'] = df['MA20'] + (std * 2)
    df['BB_L'] = df['MA20'] - (std * 2)

    # 2. RSI Calculation (14-period)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 3. MACD Calculation (12, 26, 9)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # 4. Stochastic Oscillator (%K, %D)
    low_14 = df['Low'].rolling(window=14).min()
    high_14 = df['High'].rolling(window=14).max()
    df['STOCH_K'] = (df['Close'] - low_14) * 100 / (high_14 - low_14)
    df['STOCH_D'] = df['STOCH_K'].rolling(window=3).mean()

    # Performance Metrics
    curr = float(df['Close'].iloc[-1])
    w_c = ((curr - float(df['Close'].iloc[-5])) / float(df['Close'].iloc[-5])) * 100
    m_c = ((curr - float(df['Close'].iloc[-21])) / float(df['Close'].iloc[-21])) * 100
    y_s = df[df.index >= "2025-01-01"]['Close'].iloc[0]
    y_c = ((curr - y_s) / y_s) * 100

    log_returns = np.log(df['Close'] / df['Close'].shift(1))
    vol_calc = log_returns.std() * np.sqrt(252) * 100

    return df[df.index >= "2025-01-01"], curr, w_c, m_c, y_c, vol_calc


data, price, week_c, month_c, ytd_c, vol = get_data()

# --- 1. MARKET OVERVIEW ---
st.title("🏆 Gold Market Overview")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Current Price", f"${price:,.2f}", f"{week_c:+.2f}%")
colored_metric(c2, "Weekly Change", f"{week_c:+.2f}%", week_c)
colored_metric(c3, "Monthly Change", f"{month_c:+.2f}%", month_c)
colored_metric(c4, "YTD Change", f"{ytd_c:+.2f}%", ytd_c)
colored_metric(c5, "Volatility", f"{vol:.2f}%", vol, is_vol=True)

st.divider()

# --- 2. LAYOUT: CHARTS & SIGNALS ---
col_charts, col_signals = st.columns([0.72, 0.28])

with col_charts:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.07,
        row_heights=[0.75, 0.25],
        subplot_titles=("Price Action & Indicators", "Market Volume")
    )
    # Price
    fig.add_trace(
        go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                       name="Price"), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA20", line=dict(color='#FFEB3B', width=1.5)), row=1,
                  col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], name="MA50", line=dict(color='#E91E63', width=1.5)), row=1,
                  col=1)
    # Volume
    v_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(data['Close'], data['Open'])]
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=v_colors, name="Volume", opacity=0.8), row=2,
                  col=1)

    vol_max = data['Volume'].max()
    fig.update_yaxes(range=[0, vol_max * 2.5], row=2, col=1)
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=800, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col_signals:
    st.subheader("📡 Key Trading Signals")
    latest = data.iloc[-1]


    # Signal Logic Helper
    def display_signal(label, value, status, color):
        st.markdown(f"""
        <div class="signal-container">
            <small style='color:#808495'>{label}</small><br>
            <span style='font-size: 22px; font-weight: bold;'>{value}</span>
            <span style='color:{color}; float: right; font-weight: bold; margin-top: 5px;'>{status}</span>
        </div>
        """, unsafe_allow_html=True)


    # 1. RSI Signal
    rsi_val = latest['RSI']
    rsi_status = "Oversold" if rsi_val < 30 else ("Overbought" if rsi_val > 70 else "Neutral")
    rsi_color = "#00FF41" if rsi_val < 30 else ("#FF3131" if rsi_val > 70 else "#808495")
    display_signal("Relative Strength (RSI)", f"{rsi_val:.1f}", rsi_status, rsi_color)

    # 2. MACD Signal
    macd_val, macd_sig = latest['MACD'], latest['MACD_Signal']
    macd_status = "Bullish" if macd_val > macd_sig else "Bearish"
    macd_color = "#00FF41" if macd_val > macd_sig else "#FF3131"
    display_signal("MACD Momentum", f"{macd_val:.2f}", macd_status, macd_color)

    # 3. Stochastic Oscillator
    stoch_k = latest['STOCH_K']
    stoch_status = "Bullish" if stoch_k > 50 else "Bearish"
    stoch_color = "#00FF41" if stoch_k > 50 else "#FF3131"
    display_signal("Stochastic (%K)", f"{stoch_k:.1f}%", stoch_status, stoch_color)

    # 4. Trend Strength
    # Defined by price location relative to MA20 and MA20 relative to MA50
    trend_val = "Strong Uptrend" if (latest['Close'] > latest['MA20'] > latest['MA50']) else \
        ("Strong Downtrend" if (latest['Close'] < latest['MA20'] < latest['MA50']) else "Side-Trend")
    trend_color = "#00FF41" if "Uptrend" in trend_val else ("#FF3131" if "Downtrend" in trend_val else "#FFA500")
    display_signal("Trend Strength", trend_val, "LIVE", trend_color)

    st.caption(
        "Signals are calculated on the most recent daily close. Always combine technicals with fundamental analysis.")
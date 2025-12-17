import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# CSS to fix metric styles and signal window
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricLabel"] { color: #808495 !important; }
    [data-testid="stMetricValue"] { color: white !important; }
    .signal-card {
        background-color: #1E222D;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #FFEB3B;
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
    df = yf.download(ticker, start="2024-09-01")  # Longer start for indicator stability
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # 1. Moving Averages
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    # 2. Bollinger Bands
    std = df['Close'].rolling(window=20).std()
    df['BB_U'] = df['MA20'] + (std * 2)
    df['BB_L'] = df['MA20'] - (std * 2)

    # 3. RSI Calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 4. MACD Calculation
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # 5. Stochastic Oscillator
    low14 = df['Low'].rolling(window=14).min()
    high14 = df['High'].rolling(window=14).max()
    df['%K'] = (df['Close'] - low14) * 100 / (high14 - low14)
    df['%D'] = df['%K'].rolling(window=3).mean()

    # 6. Trend Strength (Simplified ADX logic)
    df['TR'] = np.maximum(df['High'] - df['Low'],
                          np.maximum(abs(df['High'] - df['Close'].shift(1)),
                                     abs(df['Low'] - df['Close'].shift(1))))
    df['ADX'] = df['TR'].rolling(window=14).mean()  # Proxy for trend volatility strength

    # Basic Metrics
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

# --- 2. LAYOUT: CHART + SIGNALS ---
col_left, col_right = st.columns([0.7, 0.3])

with col_left:
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.07,
        row_heights=[0.75, 0.25], subplot_titles=("Price Action", "Market Volume")
    )
    fig.add_trace(
        go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                       name="Price"), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA20", line=dict(color='#FFEB3B')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], name="MA50", line=dict(color='#E91E63')), row=1, col=1)

    v_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(data['Close'], data['Open'])]
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=v_colors, name="Volume", opacity=0.8), row=2,
                  col=1)

    vol_max = data['Volume'].max()
    fig.update_yaxes(range=[0, vol_max * 2.5], row=2, col=1)
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=750, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("📡 Key Trading Signals")

    # Get latest values
    latest = data.iloc[-1]
    rsi_val = latest['RSI']
    macd_val = latest['MACD']
    signal_val = latest['Signal_Line']
    stoch_k = latest['%K']
    trend_val = "Strong" if latest['MA20'] > latest['MA50'] else "Weak"


    # Display Logic
    def signal_box(name, value, status, color):
        st.markdown(f"""
        <div class="signal-card">
            <small style='color:#808495'>{name}</small><br>
            <span style='font-size:20px; font-weight:bold;'>{value}</span> 
            <span style='color:{color}; float:right; font-weight:bold;'>{status}</span>
        </div>
        """, unsafe_allow_html=True)


    # 1. RSI Signal
    rsi_stat = "Overbought" if rsi_val > 70 else ("Oversold" if rsi_val < 30 else "Neutral")
    rsi_col = "#FF3131" if rsi_val > 70 else ("#00FF41" if rsi_val < 30 else "#808495")
    signal_box("Relative Strength (RSI)", f"{rsi_val:.1f}", rsi_stat, rsi_col)

    # 2. MACD Signal
    macd_stat = "Bullish" if macd_val > signal_val else "Bearish"
    macd_col = "#00FF41" if macd_val > signal_val else "#FF3131"
    signal_box("Trend Momentum (MACD)", f"{macd_val:.2f}", macd_stat, macd_col)

    # 3. Stochastic
    stoch_stat = "Bullish" if stoch_k > 50 else "Bearish"
    stoch_col = "#00FF41" if stoch_k > 50 else "#FF3131"
    signal_box("Stochastic Oscillator", f"{stoch_k:.1f}%", stoch_stat, stoch_col)

    # 4. Trend Strength
    trend_col = "#00FF41" if trend_val == "Strong" else "#FFEB3B"
    signal_box("Overall Trend Strength", trend_val, "Active", trend_col)

    st.info("💡 Bullish signals on RSI (<30) combined with MACD crossover often indicate entry points.")
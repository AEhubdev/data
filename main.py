import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# CSS to fix metric styles and larger sidebar headers
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricLabel"] { color: #808495 !important; }
    [data-testid="stMetricValue"] { color: white !important; }

    /* Bigger, White Sidebar Header */
    .sidebar-header {
        color: white !important;
        font-size: 28px !important;
        font-weight: bold !important;
        font-family: 'Arial Black', sans-serif;
        margin-bottom: 20px;
        text-align: center;
    }

    .signal-container {
        background-color: #1E222D;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #363A45;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)


# HELPER: Custom metric
def colored_metric(col, label, val_text, delta_val, is_vol=False):
    color = "#FFA500" if is_vol else ("#00FF41" if delta_val > 0 else "#FF3131")
    col.markdown(f"**{label}**")
    col.markdown(f"<h2 style='color:{color}; margin-top:-15px; font-weight:bold;'>{val_text}</h2>",
                 unsafe_allow_html=True)
    if is_vol: col.caption("Annualized Risk")


@st.cache_data(ttl=60)
def get_data():
    ticker = "GC=F"
    df = yf.download(ticker, start="2024-09-01")
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # Technical Indicators
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    std = df['Close'].rolling(window=20).std()
    df['BB_U'] = df['MA20'] + (std * 2)
    df['BB_L'] = df['MA20'] - (std * 2)

    # RSI, MACD, Stoch
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    df['STOCH_K'] = (df['Close'] - df['Low'].rolling(14).min()) * 100 / (
            df['High'].rolling(14).max() - df['Low'].rolling(14).min())

    return df[df.index >= "2025-01-01"], float(df['Close'].iloc[-1]), df


data_display, price, df_full = get_data()
data = data_display  # For the chart section

# Calculate changes for metrics based on full dataframe
w_c = ((price - float(df_full['Close'].iloc[-5])) / float(df_full['Close'].iloc[-5])) * 100
m_c = ((price - float(df_full['Close'].iloc[-21])) / float(df_full['Close'].iloc[-21])) * 100
y_s = df_full[df_full.index >= "2025-01-01"]['Close'].iloc[0]
y_c = ((price - y_s) / y_s) * 100
vol_calc = np.log(df_full['Close'] / df_full['Close'].shift(1)).std() * np.sqrt(252) * 100

# --- 1. MARKET OVERVIEW ---
st.title("🏆 Gold Market Overview")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Current Price", f"${price:,.2f}", f"{w_c:+.2f}%")
colored_metric(c2, "Weekly Change", f"{w_c:+.2f}%", w_c)
colored_metric(c3, "Monthly Change", f"{m_c:+.2f}%", m_c)
colored_metric(c4, "YTD Change", f"{y_c:+.2f}%", y_c)
colored_metric(c5, "Volatility", f"{vol_calc:.2f}%", vol_calc, is_vol=True)
st.divider()

# --- 2. CHART SECTION ---
col_charts, col_signals = st.columns([0.72, 0.28])

with col_charts:
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.4, 0.15, 0.2, 0.25],
        subplot_titles=("MARKET TREND & INDICATORS", "TRADING VOLUME", "RELATIVE STRENGTH (RSI)", "MACD MOMENTUM")
    )

    # PRICE HISTORY
    fig.add_trace(
        go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                       name="Price"), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA 20", line=dict(color='#FFEB3B', width=1.5)), row=1,
                  col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], name="MA 50", line=dict(color='#E91E63', width=1.5)), row=1,
                  col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_U'], name="BB Upper",
                             line=dict(color='rgba(173, 216, 230, 0.5)', dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_L'], name="BB Lower",
                             line=dict(color='rgba(173, 216, 230, 0.5)', dash='dash'), fill='tonexty',
                             fillcolor='rgba(173, 216, 230, 0.05)'), row=1, col=1)

    # VOLUME HISTORY
    v_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(data['Close'], data['Open'])]
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=v_colors, name="Volume", opacity=0.8), row=2,
                  col=1)

    # RSI HISTORY
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name="RSI", line=dict(color='#BB86FC', width=2)), row=3,
                  col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#FF3131", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#00FF41", row=3, col=1)

    # MACD HISTORY
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name="MACD", line=dict(color='#00E5FF', width=2)), row=4,
                  col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD_Signal'], name="Signal", line=dict(color='#FFCA28', width=1.5)),
                  row=4, col=1)
    h_colors = ['#26a69a' if val >= 0 else '#ef5350' for val in data['MACD_Hist']]
    fig.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], name="Histogram", marker_color=h_colors), row=4, col=1)

    # MANUALLY FIXING OVERLAP: Shift headers above the plots
    fig.update_annotations(font=dict(size=22, color="white", family="Arial Black"))
    fig.layout.annotations[0].update(y=1.03)  # Price
    fig.layout.annotations[1].update(y=0.58)  # Vol
    fig.layout.annotations[2].update(y=0.40)  # RSI
    fig.layout.annotations[3].update(y=0.18)  # MACD

    fig.update_layout(
        template="plotly_dark", xaxis_rangeslider_visible=False, height=1400, showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=1.07, xanchor="center", x=0.5),
        margin=dict(t=150, b=40, l=40, r=40)
    )

    y_min, y_max = data['Low'].min() * 0.99, data['High'].max() * 1.01
    fig.update_yaxes(range=[y_min, y_max], row=1, col=1)
    st.plotly_chart(fig, use_container_width=True)

with col_signals:
    st.markdown('<div class="sidebar-header">📡 TRADING SIGNALS</div>', unsafe_allow_html=True)
    latest = data.iloc[-1]


    def display_signal(label, value, status, color):
        st.markdown(f"""
            <div class="signal-container">
                <div style='color:white; font-size:16px; font-weight:bold; margin-bottom:5px;'>{label}</div>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <span style='color:white; font-size:26px; font-weight:bold;'>{value}</span>
                    <span style='background-color:{color}; color:black; padding:2px 10px; border-radius:5px; font-weight:bold; font-size:12px;'>{status}</span>
                </div>
            </div>""", unsafe_allow_html=True)


    # Updated Logic for Strong Buy/Sell
    rsi_val = latest['RSI']
    rsi_stat = "STRONG SELL" if rsi_val > 70 else ("STRONG BUY" if rsi_val < 30 else "NEUTRAL")
    rsi_col = "#FF3131" if rsi_val > 70 else ("#00FF41" if rsi_val < 30 else "#808495")

    macd_val = latest['MACD']
    macd_stat = "STRONG BUY" if macd_val > latest['MACD_Signal'] else "STRONG SELL"
    macd_col = "#00FF41" if macd_val > latest['MACD_Signal'] else "#FF3131"

    display_signal("RSI (14)", f"{rsi_val:.1f}", rsi_stat, rsi_col)
    display_signal("MACD", f"{macd_val:.2f}", macd_stat, macd_col)
    display_signal("STOCH (%K)", f"{latest['STOCH_K']:.1f}%", "ACTIVE", "#FFA500")
    display_signal("TREND STRENGTH", "BULLISH" if latest['Close'] > latest['MA20'] else "BEARISH", "LIVE", "#00FF41")
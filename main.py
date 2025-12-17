import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# CSS for Window Styling
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricLabel"] { color: #808495 !important; }
    [data-testid="stMetricValue"] { color: white !important; }

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

    .window-header {
        color: white !important;
        font-size: 22px !important;
        font-weight: bold !important;
        font-family: 'Arial Black', sans-serif;
        margin-top: 25px;
        margin-bottom: 10px;
        padding-bottom: 5px;
        border-bottom: 1px solid #363A45;
    }

    .news-link {
        color: #FFD700 !important;
        font-size: 18px !important;
        font-weight: 500 !important;
        text-decoration: none !important;
        display: block;
        margin-bottom: 12px;
        padding: 10px;
        background: #1E222D;
        border-radius: 5px;
    }
    .news-link:hover { background: #262B3D; color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)


# Metric Helper
def colored_metric(col, label, val_text, delta_val, is_vol=False):
    color = "#FFA500" if is_vol else ("#00FF41" if delta_val > 0 else "#FF3131")
    col.markdown(f"**{label}**")
    col.markdown(f"<h2 style='color:{color}; margin-top:-15px; font-weight:bold;'>{val_text}</h2>",
                 unsafe_allow_html=True)


@st.cache_data(ttl=60)
def get_all_data():
    ticker_obj = yf.Ticker("GC=F")
    df = ticker_obj.history(start="2024-09-01")

    # INDICATORS RESTORED
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    std = df['Close'].rolling(20).std()
    df['BB_U'], df['BB_L'] = df['MA20'] + (std * 2), df['MA20'] - (std * 2)

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    ema12, ema26 = df['Close'].ewm(span=12).mean(), df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_S'] = df['MACD'].ewm(span=9).mean()
    df['MACD_H'] = df['MACD'] - df['MACD_S']
    df['STOCH_K'] = (df['Close'] - df['Low'].rolling(14).min()) * 100 / (
                df['High'].rolling(14).max() - df['Low'].rolling(14).min())

    return df[df.index >= "2025-01-01"], float(df['Close'].iloc[-1]), df, ticker_obj.news


data, price, df_full, news = get_all_data()

# CALCULATIONS RESTORED
w_c = ((price - float(df_full['Close'].iloc[-5])) / float(df_full['Close'].iloc[-5])) * 100
m_c = ((price - float(df_full['Close'].iloc[-21])) / float(df_full['Close'].iloc[-21])) * 100
y_s = df_full[df_full.index >= "2025-01-01"]['Close'].iloc[0]
y_c, vol_c = ((price - y_s) / y_s) * 100, np.log(df_full['Close'] / df_full['Close'].shift(1)).std() * np.sqrt(
    252) * 100

# --- 1. OVERVIEW ---
st.title("🏆 Gold Market Overview")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Current Price", f"${price:,.2f}", f"{w_c:+.2f}%")
colored_metric(c2, "Weekly Change", f"{w_c:+.2f}%", w_c)
colored_metric(c3, "Monthly Change", f"{m_c:+.2f}%", m_c)
colored_metric(c4, "YTD Change", f"{y_c:+.2f}%", y_c)
colored_metric(c5, "Volatility", f"{vol_c:.2f}%", vol_c, is_vol=True)
st.divider()

# --- 2. MULTI-WINDOW CHARTS ---
col_charts, col_signals = st.columns([0.72, 0.28])

with col_charts:
    # PRICE WINDOW
    st.markdown('<div class="window-header">MARKET TREND & INDICATORS</div>', unsafe_allow_html=True)
    f1 = go.Figure()
    f1.add_trace(
        go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                       name="Gold"))
    f1.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA20", line=dict(color='#FFEB3B')))
    f1.add_trace(go.Scatter(x=data.index, y=data['MA50'], name="MA50", line=dict(color='#E91E63')))
    f1.add_trace(
        go.Scatter(x=data.index, y=data['BB_U'], name="BB U", line=dict(color='rgba(173,216,230,0.4)', dash='dash')))
    f1.add_trace(
        go.Scatter(x=data.index, y=data['BB_L'], name="BB L", line=dict(color='rgba(173,216,230,0.4)', dash='dash'),
                   fill='tonexty'))
    f1.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(t=0, b=0))
    st.plotly_chart(f1, use_container_width=True)

    # VOLUME WINDOW
    st.markdown('<div class="window-header">TRADING VOLUME</div>', unsafe_allow_html=True)
    f2 = go.Figure(go.Bar(x=data.index, y=data['Volume'], marker_color=['#26a69a' if c >= o else '#ef5350' for c, o in
                                                                        zip(data['Close'], data['Open'])]))
    f2.update_layout(template="plotly_dark", height=200, margin=dict(t=0, b=0))
    st.plotly_chart(f2, use_container_width=True)

    # RSI WINDOW
    st.markdown('<div class="window-header">RELATIVE STRENGTH (RSI)</div>', unsafe_allow_html=True)
    f3 = go.Figure(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='#BB86FC')))
    f3.add_hline(y=70, line_dash="dash", line_color="#FF3131");
    f3.add_hline(y=30, line_dash="dash", line_color="#00FF41")
    f3.update_layout(template="plotly_dark", height=200, margin=dict(t=0, b=0))
    st.plotly_chart(f3, use_container_width=True)

    # MACD WINDOW
    st.markdown('<div class="window-header">MACD MOMENTUM</div>', unsafe_allow_html=True)
    f4 = go.Figure()
    f4.add_trace(go.Bar(x=data.index, y=data['MACD_H'],
                        marker_color=['#26a69a' if x >= 0 else '#ef5350' for x in data['MACD_H']]))
    f4.add_trace(go.Scatter(x=data.index, y=data['MACD'], line=dict(color='#00E5FF')))
    f4.add_trace(go.Scatter(x=data.index, y=data['MACD_S'], line=dict(color='#FFCA28')))
    f4.update_layout(template="plotly_dark", height=250, margin=dict(t=0, b=0))
    st.plotly_chart(f4, use_container_width=True)

    # --- NEWS WINDOW ---
    st.markdown('<div class="window-header">📰 LATEST MARKET HEADLINES</div>', unsafe_allow_html=True)
    for item in news[:8]:
        st.markdown(f'<a href="{item["link"]}" target="_blank" class="news-link">● {item["title"]}</a>',
                    unsafe_allow_html=True)

with col_signals:
    st.markdown('<div class="sidebar-header">📡 SIGNALS</div>', unsafe_allow_html=True)
    last = data.iloc[-1]


    def draw_sig(label, val, stat, col):
        st.markdown(f"""<div class="signal-container"><div style='color:#808495; font-size:14px;'>{label}</div>
            <div style='display:flex; justify-content:space-between;'>
            <span style='color:white; font-size:24px; font-weight:bold;'>{val}</span>
            <span style='background:{col}; color:black; padding:2px 8px; border-radius:4px; font-weight:bold; height:fit-content;'>{stat}</span>
            </div></div>""", unsafe_allow_html=True)


    r_v = last['RSI']
    r_s = "STRONG SELL" if r_v > 70 else ("STRONG BUY" if r_v < 30 else "NEUTRAL")
    r_c = "#FF3131" if r_v > 70 else ("#00FF41" if r_v < 30 else "#808495")

    m_v = last['MACD']
    m_s = "STRONG BUY" if m_v > last['MACD_S'] else "STRONG SELL"
    m_c = "#00FF41" if m_v > last['MACD_S'] else "#FF3131"

    draw_sig("RSI (14)", f"{r_v:.1f}", r_s, r_c)
    draw_sig("MACD", f"{m_v:.2f}", m_s, m_c)
    draw_sig("STOCH %K", f"{last['STOCH_K']:.1f}%", "LIVE", "#FFA500")
    draw_sig("TREND", "BULLISH" if last['Close'] > last['MA20'] else "BEARISH", "CONFIRMED", "#00FF41")
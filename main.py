import streamlit as st
import plotly.graph_objects as go
from data_engine import get_gold_data, get_overview_stats
from styles import apply_custom_css, colored_metric, display_signal_box

# 1. Config & Styles
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
apply_custom_css()

# 2. Data Fetching
data, price, df_full, news_list = get_gold_data()
w_c, m_c, y_c, vol_calc = get_overview_stats(price, df_full)

# 3. UI - Header
st.title("🏆 Gold Market Overview")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Current Price", f"${price:,.2f}", f"{w_c:+.2f}%")
colored_metric(c2, "Weekly Change", f"{w_c:+.2f}%", w_c)
colored_metric(c3, "Monthly Change", f"{m_c:+.2f}%", m_c)
colored_metric(c4, "YTD Change", f"{y_c:+.2f}%", y_c)
colored_metric(c5, "Volatility", f"{vol_calc:.2f}%", vol_calc, is_vol=True)
st.divider()

# 4. Charts & Signals
col_charts, col_signals = st.columns([0.72, 0.28])

with col_charts:
    st.markdown('<div class="window-header">MARKET TREND & INDICATORS</div>', unsafe_allow_html=True)
    fig1 = go.Figure()
    fig1.add_trace(
        go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                       name="Price"))
    fig1.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA 20", line=dict(color='#FFEB3B', width=1.5)))
    fig1.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig1, use_container_width=True)

    # ... (You can add the other RSI/MACD/Volume charts here similar to above) ...

    st.markdown('<div class="window-header">📰 LATEST MARKET HEADLINES</div>', unsafe_allow_html=True)
    for article in news_list:
        st.markdown(f'<a href="{article["link"]}" target="_blank" class="news-link">● {article["title"]}</a>',
                    unsafe_allow_html=True)

with col_signals:
    st.markdown('<div class="sidebar-header">📡 TRADING SIGNALS</div>', unsafe_allow_html=True)
    latest = data.iloc[-1]

    rsi_stat = "STRONG SELL" if latest['RSI'] > 70 else ("STRONG BUY" if latest['RSI'] < 30 else "NEUTRAL")
    rsi_col = "#FF3131" if latest['RSI'] > 70 else ("#00FF41" if latest['RSI'] < 30 else "#808495")

    display_signal_box("RSI (14)", f"{latest['RSI']:.1f}", rsi_stat, rsi_col)
    display_signal_box("TREND", "BULLISH" if latest['Close'] > latest['MA20'] else "BEARISH", "LIVE", "#00FF41")
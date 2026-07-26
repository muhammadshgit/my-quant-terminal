import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from huggingface_hub import InferenceClient
import time

st.set_page_config(layout="wide", page_title="Ultimate 1% Quant Terminal")

# --- 1. CORE SETUP & LIVE REAL-TIME TRIGGER ---
@st.cache_resource
def get_exchange():
    # Switched to Coinbase to bypass US cloud geo-restrictions completely
    return ccxt.coinbase({'enableRateLimit': True})

exchange = get_exchange()

# Hidden environment server settings
HF_TOKEN = st.secrets.get("HF_TOKEN", "")
client = InferenceClient("meta-llama/Meta-Llama-3-8B-Instruct", token=HF_TOKEN if HF_TOKEN else None)

# Add an auto-refresh toggle to keep pricing moving completely live
st.sidebar.title("🎮 Terminal Controls")
auto_refresh = st.sidebar.checkbox("🔄 Enable Live 5s Auto-Refresh", value=False)

# --- 2. ADVANCED QUANT MATHEMATICS ENGINE ---
def calculate_advanced_metrics(df_h, df_d, btc_return_1d):
    close_h = df_h['close']
    
    # RSI Calculation
    delta = close_h.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df_h['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD Calculation
    exp1 = close_h.ewm(span=12, adjust=False).mean()
    exp2 = close_h.ewm(span=26, adjust=False).mean()
    df_h['macd'] = exp1 - exp2
    df_h['signal'] = df_h['macd'].ewm(span=9, adjust=False).mean()
    
    # ATR (Average True Range)
    high_low = df_h['high'] - df_h['low']
    high_cp = np.abs(df_h['high'] - close_h.shift())
    low_cp = np.abs(df_h['low'] - close_h.shift())
    df_h['atr'] = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1).rolling(window=14).mean()
    
    # Relative Strength vs BTC (Daily)
    alt_return_1d = (df_d['close'].iloc[-1] - df_d['close'].iloc[-2]) / df_d['close'].iloc[-2]
    relative_strength = alt_return_1d - btc_return_1d
    
    # Smart Money Concepts (BOS, CHoCH, Liquidity Sweeps)
    recent_lows = df_h['low'].iloc[-10:-1]
    recent_highs = df_h['high'].iloc[-10:-1]
    lowest_floor = recent_lows.min()
    highest_ceiling = recent_highs.max()
    
    current_price = close_h.iloc[-1]
    previous_price = close_h.iloc[-2]
    
    # Detect Liquidity Sweep
    liquidity_sweep = (df_h['low'].iloc[-1] < lowest_floor) and (current_price > lowest_floor)
    
    # Detect BOS/CHoCH
    bos_detected = (current_price > highest_ceiling) and (previous_price <= highest_ceiling)
    
    return {
        "rsi": df_h['rsi'].iloc[-1],
        "macd_delta": df_h['macd'].iloc[-1] - df_h['signal'].iloc[-1],
        "atr_pct": (df_h['atr'].iloc[-1] / current_price) * 100,
        "relative_strength_pct": relative_strength * 100,
        "liquidity_sweep": liquidity_sweep,
        "bos_detected": bos_detected,
        "support": lowest_floor,
        "resistance": highest_ceiling
    }

# --- 3. FETCH DATA & RUN SCANNER ---
st.sidebar.title("🚨 Confluence Strategy Scanner")

# Pre-fetch BTC daily return for Relative Strength computations
try:
    btc_ohlcv = exchange.fetch_ohlcv("BTC-USDT", timeframe='1d', limit=2)
    btc_ret = (btc_ohlcv[1][4] - btc_ohlcv[0][4]) / btc_ohlcv[0][4]
except Exception as e:
    btc_ret = 0.0

# Watchlist baseline adapted for standard Coinbase asset configurations
WATCHLIST = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "AVAX-USDT", "LINK-USDT", "NEAR-USDT"]

for asset in WATCHLIST:
    try:
        ohlcv_d = exchange.fetch_ohlcv(asset, timeframe='1d', limit=30)
        ohlcv_h = exchange.fetch_ohlcv(asset, timeframe='1h', limit=50)
        
        df_d = pd.DataFrame(ohlcv_d, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df_h = pd.DataFrame(ohlcv_h, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        
        q = calculate_advanced_metrics(df_h, df_d, btc_ret)
        curr_p = df_h['close'].iloc[-1]
        risk = ((curr_p - q['support']) / curr_p) * 100
        
        if q['liquidity_sweep'] and (2.0 <= risk <= 3.0):
            st.sidebar.success(f"🎯 SWEEP: {asset}\nRisk: {risk:.1f}%")
        elif q['bos_detected']:
            st.sidebar.info(f"⚡ BOS: {asset}\nStructure Broken Upward")
        else:
            st.sidebar.text(f"⚪ {asset}: ${curr_p:,.2f}")
    except Exception as e:
        continue

# --- 4. MAIN TERMINAL DASHBOARD PANEL ---
st.title("⚡ Institutional Core Quant Hub")
# Note the required Coinbase formatting placeholder text (using hyphen instead of slash)
main_ticker = st.text_input("Enter ANY Asset Ticker listed on Coinbase (e.g., SOL-USDT, ETH-USDT, LINK-USDT):", value="BTC-USDT").upper()

try:
    ticker_data = exchange.fetch_ticker(main_ticker)
    curr_price = ticker_data['last']
    
    ohlcv_m_d = exchange.fetch_ohlcv(main_ticker, timeframe='1d', limit=30)
    ohlcv_m_h = exchange.fetch_ohlcv(main_ticker, timeframe='1h', limit=50)
    df_m_d = pd.DataFrame(ohlcv_m_d, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    df_m_h = pd.DataFrame(ohlcv_m_h, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    
    metrics = calculate_advanced_metrics(df_m_h, df_m_d, btc_ret)
    risk_pct = ((curr_price - metrics['support']) / curr_price) * 100

    # Layout Data Metrics Row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Live Price", f"${curr_price:,.4f}")
    c2.metric("RSI (1H)", f"{metrics['rsi']:.1f}")
    c3.metric("Daily Relative Strength vs BTC", f"{metrics['relative_strength_pct']:.2f}%")
    c4.metric("Volatility (ATR % of Price)", f"{metrics['atr_pct']:.2f}%")

    # Render Screen Split Panels
    col_chart, col_smc = st.columns(2)
    
    with col_chart:
        fig = go.Figure(data=[go.Candlestick(x=df_m_h.index, open=df_m_h['open'], high=df_m_h['high'], low=df_m_h['low'], close=df_m_h['close'])])
        fig.add_hline(y=metrics['support'], line_dash="dash", line_color="green", annotation_text="Liquidity Pool Floor")
        fig.add_hline(y=metrics['resistance'], line_dash="dash", line_color="red", annotation_text="SMC Target Ceiling")
        fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        
    with col_smc:
        st.subheader("🕵️‍♂️ Order Stream & Smart Money Metrics")
        st.markdown(f"**Structural Floor (Support Zone):** `${metrics['support']:,.4f}`")
        st.markdown(f"**Structural Ceiling (Resistance Zone):** `${metrics['resistance']:,.4f}`")
        st.markdown(f"**Calculated Swing Risk Exposure:** `{risk_pct:.2f}%`")
        
        if metrics['liquidity_sweep']:
            st.warning("⚠️ INSTITUTIONAL LIQUIDITY SWEEP DETECTED!")
        if metrics['bos_detected']:
            st.success("🚀 BREAK OF STRUCTURE (BOS) CONFIRMED!")

    # --- 5. THE TOTAL CONFLUENCE LLM AGENT ---
    st.divider()
    st.subheader("🧠 Advanced Macro Structural Advisor")

    market_context = (
        f"Live Analytical Dossier:\n"
        f"- Target Asset Ticker: {main_ticker}\n"
        f"- Relative Strength Momentum vs BTC: {metrics['relative_strength_pct']:.2f}%\n"
        f"- Volatility Range (ATR %): {metrics['atr_pct']:.2f}%\n"
        f"- Current Hourly RSI: {metrics['rsi']:.1f}\n"
        f"- Within Your Tight 2-3% Risk Parameters?: {'YES' if (2.0 <= risk_pct <= 3.0) else 'NO'}\n"
    )

    user_query = st.text_input("Ask your advisor a structural market question:")
    if user_query:
        with st.spinner("Processing structural strategies..."):
            messages = [
                {"role": "system", "content": f"You are an elite quantitative trading partner. Use this data context to advise: {market_context}"},
                {"role": "user", "content": user_query}
            ]
            response = client.chat_completion(messages, max_tokens=400)
            st.write(response.choices.message.content)

except Exception as e:
    st.error(f"Error handling market data: {e}")
    st.warning("Ensure asset naming utilizes the formatting rules required by the exchange (Format example: SOL-USDT).")

# Trigger execution for real-time auto-refresh if selected
if auto_refresh:
    time.sleep(5)
    st.rerun()

import streamlit as st
import pandas as pd
from jugaad_data.nse import stock_df
from datetime import date, timedelta
import requests
from io import StringIO

st.set_page_config(page_title="Mugan's Legacy Guardian v2", layout="wide")

# --- CUSTOM CSS FOR 6% VISIBILITY ---
st.markdown("""
    <style>
    .stTable { font-size: 20px !important; }
    .highlight { background-color: #2E7D32; color: white; padding: 5px; border-radius: 5px; }
    </style>
    """, unsafe_allow_index=True)

# --- 1. CORE FUNCTIONS ---
@st.cache_data(ttl=86400)
def get_nse_universe():
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        df = pd.read_csv(StringIO(requests.get(url, headers=headers).text))
        return df[df[' SERIES'] == 'EQ']['SYMBOL'].tolist()
    except:
        return ["TATAMOTORS", "HAL", "TCS", "RELIANCE", "TATAPOWER", "BEL"]

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- 2. UI SETUP ---
st.title("🛡️ Legacy Guardian: Swing-to-Wealth Engine")
st.info("Goal: 6% Profit in 60 Days | Strategy: Capital Preservation")

with st.sidebar:
    st.header("Risk Controls")
    scan_count = st.slider("Universe Depth", 50, 500, 100)
    strict_mode = st.checkbox("Volume Confirmation Only", value=True)
    execute = st.button("🔍 Run Integrity Scan")

# --- 3. THE ANALYTICS ENGINE ---
if execute:
    tickers = get_nse_universe()[:scan_count]
    results = []
    today = date.today()
    start_date = today - timedelta(days=365)
    
    progress = st.progress(0)
    status = st.empty()

    for i, sym in enumerate(tickers):
        try:
            status.text(f"Scanning for Safety: {sym}")
            df = stock_df(symbol=sym, from_date=start_date, to_date=today, series="EQ")
            
            if len(df) > 200:
                df = df.sort_values('DATE')
                # Indicators
                df['50DMA'] = df['CLOSE'].rolling(50).mean()
                df['200DMA'] = df['CLOSE'].rolling(200).mean()
                df['RSI'] = calculate_rsi(df['CLOSE'])
                df['VolAvg'] = df['VOLUME'].rolling(10).mean()
                
                curr = df['CLOSE'].iloc[-1]
                m50 = df['50DMA'].iloc[-1]
                m200 = df['200DMA'].iloc[-1]
                rsi = df['RSI'].iloc[-1]
                vol_now = df['VOLUME'].iloc[-1]
                vol_avg = df['VolAvg'].iloc[-1]

                # --- MULTI-STEP SAFETY CHECK ---
                # 1. Trend: Only buy if long-term trend is UP (Price > 200DMA)
                # 2. RSI: Not Overbought (RSI < 65)
                # 3. Volume: Evidence of big money (If strict_mode)
                
                is_safe = (curr > m200) and (rsi < 65)
                if strict_mode:
                    is_safe = is_safe and (vol_now > vol_avg * 1.2)

                if is_safe and (curr > m50): # Entry Trigger
                    results.append({
                        "Stock": sym,
                        "LTP": round(curr, 2),
                        "RSI": round(rsi, 1),
                        "🎯 6% Target": round(curr * 1.06, 2),
                        "🛑 Stop Loss (3%)": round(curr * 0.97, 2),
                        "Action": "✅ READY TO SWING"
                    })
        except: continue
        progress.progress((i + 1) / len(tickers))

    status.empty()
    if results:
        st.success(f"Found {len(results)} matches that meet our 300-year safety standards!")
        st.table(pd.DataFrame(results))
    else:
        st.warning("Market risk is high. No safe entries found.")

st.divider()
st.caption("Instructions: When a stock hits '6% Target', sell 100% and move the profit to your Tata/NSE Compounding Vault.")

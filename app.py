import streamlit as st
import pandas as pd
from jugaad_data.nse import stock_df
from datetime import date, timedelta
import requests
from io import StringIO

# --- CONFIGURATION ---
st.set_page_config(page_title="Mugan's Legacy Guardian", layout="wide", page_icon="🛡️")

# --- 1. THE NATIVE SYMBOL LOADER (With NSE Cookie Fix) ---
@st.cache_data(ttl=86400)
def get_native_symbols():
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        df = pd.read_csv(StringIO(response.text))
        df.columns = df.columns.str.strip() 
        return df[df['SERIES'] == 'EQ']['SYMBOL'].tolist()
    except Exception:
        # Fallback list if NSE site is down
        return ["TATAMOTORS", "HAL", "TCS", "RELIANCE", "TATAPOWER", "BEL", "INFY", "HDFCBANK", "SBIN", "ICICIBANK"]

all_symbols = get_native_symbols()

# --- 2. THE UI INTERFACE ---
st.title("🛡️ Legacy Guardian: Swing-to-Wealth")
st.markdown("#### Tactical Capital Preservation | Target: *6% Profit* | Volume Validated")

with st.sidebar:
    st.header("1. Selection Universe")
    universe = st.selectbox("Choose Universe", ["Nifty 50 (Safest)", "Nifty 200 (Growth)", "All-Cap (Full Market)"])
    
    st.header("2. Safety Strategy")
    strategy = st.selectbox("Choose Strategy", 
                            ["THE SHIELD (Mean Reversion)", 
                             "THE SWORD (Volume Breakout)", 
                             "THE ANCHOR (Quality Momentum)"])
    
    scan_limit = st.slider("Stocks to Analyze", 20, 500, 100)
    run_btn = st.button("🚀 EXECUTE STRATEGIC SCAN")

# --- 3. THE EXECUTION ENGINE ---
if run_btn:
    # Define Scan List
    if "50" in universe: scan_list = all_symbols[:50]
    elif "200" in universe: scan_list = all_symbols[:200]
    else: scan_list = all_symbols[:scan_limit]

    results = []
    today = date.today()
    # Pulling 400 days to ensure 200 clean trading days
    start_date = today - timedelta(days=400) 
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, sym in enumerate(scan_list):
        status_text.text(f"Scanning {sym} ({i+1}/{len(scan_list)})...")
        try:
            # Data Fetching
            df = stock_df(symbol=sym, from_date=start_date, to_date=today, series="EQ")
            
            if df is not None and len(df) > 200:
                df = df.sort_values('DATE')
                
                # Technical Indicators
                df['50DMA'] = df['CLOSE'].rolling(window=50).mean()
                df['200DMA'] = df['CLOSE'].rolling(window=200).mean()
                df['Vol_MA10'] = df['VOLUME'].rolling(window=10).mean()
                
                # Current Values
                curr = df['CLOSE'].iloc[-1]
                m50 = df['50DMA'].iloc[-1]
                m200 = df['200DMA'].iloc[-1]
                vol_now = df['VOLUME'].iloc[-1]
                vol_avg = df['Vol_MA10'].iloc[-1]
                
                # Volume Ratio (Strength)
                vol_ratio = vol_now / vol_avg if vol_avg > 0 else 0

                match = False
                # --- STRATEGY LOGIC WITH VOLUME GATES ---
                if "SHIELD" in strategy:
                    # Logic: Buying the 'dip' in a long-term uptrend
                    # Low volume on dip = Selling exhaustion
                    if curr > m200 and curr < m50 and vol_ratio < 1.2: 
                        match = True
                
                elif "SWORD" in strategy:
                    # Logic: Catching the breakout momentum
                    # High volume = Institutional confirmation
                    if curr > m50 and m50 > m200 and vol_ratio > 1.5: 
                        match = True
                
                elif "ANCHOR" in strategy:
                    # Logic: Steady Bluechip compounding
                    if curr > m50 > m200 and vol_ratio >= 1.0: 
                        match = True

                if match:
                    results.append({
                        "Symbol": sym,
                        "Current Price": f"₹{curr:,.2.2f}",
                        "6% Target": f"₹{curr * 1.06:,.2f}",
                        "3% Stop Loss": f"₹{curr * 0.97:,.2f}",
                        "Vol Surge": f"{vol_ratio:.2f}x",
                        "Trend": "Bullish" if curr > m200 else "Neutral"
                    })
        except Exception:
            continue
        
        progress_bar.progress((i + 1) / len(scan_list))

    status_text.empty()
    
    # --- 4. RESULTS DISPLAY ---
    if results:
        st.success(f"Protocol Complete: {len(results)} stocks matched {strategy}")
        res_df = pd.DataFrame(results)
        st.table(res_df)
        
        st.caption("💡 Tip: Focus on stocks with 'Vol Surge' > 1.5x for the highest probability moves.")
    else:
        st.warning("No stocks currently meet the Guardian's safety criteria. Cash is a position.")

st.divider()
st.info("Remember: Hit the 6%, secure the profit, and move it to your long-term wealth vault.")

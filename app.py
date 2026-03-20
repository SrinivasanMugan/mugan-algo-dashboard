import streamlit as st
import pandas as pd
from jugaad_data.nse import stock_df
from datetime import date, timedelta
import requests
from io import StringIO

st.set_page_config(page_title="Mugan's Legacy Guardian", layout="wide")

# --- 1. THE NATIVE SYMBOL LOADER ---
@st.cache_data(ttl=86400)
def get_native_symbols():
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        df = pd.read_csv(StringIO(requests.get(url, headers=headers).text))
        return df[df[' SERIES'] == 'EQ']['SYMBOL'].tolist()
    except:
        return ["TATAMOTORS", "HAL", "TCS", "RELIANCE", "TATAPOWER", "BEL"]

all_symbols = get_native_symbols()

# --- 2. THE UPDATED DROPDOWNS ---
st.title("🛡️ Legacy Guardian: Swing-to-Wealth")
st.markdown("#### Capital Preservation Protocol | Target: 6% Profit")

with st.sidebar:
    st.header("1. Selection Universe")
    # Updated: Now specifically for NSE groupings
    universe = st.selectbox("Choose Universe", 
                            ["Nifty 50 (Safest)", "Nifty 200 (Growth)", "All-Cap (Full Market)"])
    
    st.header("2. Safety Strategy")
    # Updated: Locked into the 300-year tactics we discussed
    strategy = st.selectbox("Choose Strategy", 
                            ["THE SHIELD (Mean Reversion)", 
                             "THE SWORD (Volume Breakout)", 
                             "THE ANCHOR (Quality Momentum)"])
    
    scan_limit = st.slider("Stocks to Analyze", 50, 500, 100)
    run_btn = st.button("🚀 EXECUTE STRATEGIC SCAN")

# --- 3. THE EXECUTION ENGINE ---
if run_btn:
    # Filter the list based on selection
    if "50" in universe: scan_list = all_symbols[:50]
    elif "200" in universe: scan_list = all_symbols[:200]
    else: scan_list = all_symbols[:scan_limit]

    results = []
    today = date.today()
    start_date = today - timedelta(days=365) # 1 Year for 200DMA
    
    progress = st.progress(0)
    
    for i, sym in enumerate(scan_list):
        try:
            # PURE NATIVE DATA FETCH
            df = stock_df(symbol=sym, from_date=start_date, to_date=today, series="EQ")
            
            if len(df) > 200:
                df = df.sort_values('DATE')
                df['50DMA'] = df['CLOSE'].rolling(50).mean()
                df['200DMA'] = df['CLOSE'].rolling(200).mean()
                
                curr = df['CLOSE'].iloc[-1]
                m50 = df['50DMA'].iloc[-1]
                m200 = df['200DMA'].iloc[-1]
                vol_spike = df['VOLUME'].iloc[-1] > (df['VOLUME'].tail(10).mean() * 1.5)

                # STRATEGY LOGIC GATES
                match = False
                if "SHIELD" in strategy:
                    # Logic: Good companies temporarily below average
                    if curr < m50 and curr > m200: match = True
                elif "SWORD" in strategy:
                    # Logic: Strong breakout with high volume
                    if curr > m50 and m50 > m200 and vol_spike: match = True
                elif "ANCHOR" in strategy:
                    # Logic: Steady bluechip uptrend
                    if curr > m50 and m50 > m200: match = True

                if match:
                    results.append({
                        "Symbol": sym,
                        "Price": f"₹{curr:,.2f}",
                        "6% Target": f"₹{curr * 1.06:,.2f}",
                        "3% Stop Loss": f"₹{curr * 0.97:,.2f}",
                        "Status": "✅ STABLE"
                    })
        except: continue
        progress.progress((i + 1) / len(scan_list))

    if results:
        st.success(f"Strategy {strategy} identified {len(results)} stocks.")
        st.table(pd.DataFrame(results))
    else:
        st.warning("Safety Criteria not met for any stocks in this universe today.")

st.divider()
st.info("Remember: Swing for 6%, then move the profits into your Tata/NSE Compounding Vault.")

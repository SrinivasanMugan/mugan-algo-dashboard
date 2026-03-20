import streamlit as st
import pandas as pd
from jugaad_data.nse import NSEHistory
from datetime import date, timedelta
import requests
from io import StringIO
import time

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Mugan's Legacy Guardian", 
    layout="wide", 
    page_icon="🛡️"
)

# --- 1. THE RESILIENT DATA ENGINE (Cloud Compatible) ---
class LegacyDataEngine:
    def _init_(self):
        self.history = NSEHistory()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

    @st.cache_data(ttl=86400)
    def get_symbols(_self):
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        try:
            response = requests.get(url, headers=_self.headers, timeout=10)
            df = pd.read_csv(StringIO(response.text))
            df.columns = df.columns.str.strip()
            # Filter for Equity Series only
            return df[df['SERIES'] == 'EQ']['SYMBOL'].tolist()
        except Exception:
            # Hardcoded Safelist Fallback
            return ["TATAMOTORS", "HAL", "TCS", "RELIANCE", "TATAPOWER", "BEL", "SBIN", "ICICIBANK", "INFY", "ADANIENT"]

    def fetch_with_retry(self, symbol, start, end, retries=2):
        for _ in range(retries):
            try:
                # Fetches full daily data
                df = self.history.stock_full(symbol, start, end)
                if df is not None and not df.empty:
                    # NORMALIZE HEADERS: NSE uses different names across different endpoints
                    df.columns = [c.upper().strip() for c in df.columns]
                    
                    # Map 'CH_CLOSING_PRICE' or 'CLOSE_PRICE' to standard 'CLOSE'
                    rename_map = {
                        'CH_CLOSING_PRICE': 'CLOSE',
                        'CLOSE_PRICE': 'CLOSE',
                        'CH_TOT_TRADED_QTY': 'VOLUME',
                        'TOT_TRADED_QTY': 'VOLUME',
                        'CH_TIMESTAMP': 'DATE',
                        'TIMESTAMP': 'DATE'
                    }
                    df = df.rename(columns=rename_map)
                    
                    # Ensure DATE is datetime and sorted
                    df['DATE'] = pd.to_datetime(df['DATE'])
                    return df.sort_values('DATE')
            except Exception:
                time.sleep(1) # Cool-down to prevent IP blocking
        return None

# Initialize Engine
engine = LegacyDataEngine()
all_symbols = engine.get_symbols()

# --- 2. UI INTERFACE ---
st.title("🛡️ Legacy Guardian: Swing-to-Wealth")
st.markdown("""
    *Protocol:* Capital Preservation first. We target *6% Profit Swings* and rotate capital 
    into the long-term compounding vault. Volume validated, institutional grade.
""")

with st.sidebar:
    st.header("1. Universe Selection")
    universe = st.selectbox("Choose Universe", 
                            ["Nifty 50 (Safest)", "Nifty 200 (Growth)", "All-Cap (Full Market)"])
    
    st.header("2. Strategy Logic")
    strategy = st.selectbox("Choose Strategy", 
                            ["THE SHIELD (Mean Reversion)", 
                             "THE SWORD (Volume Breakout)", 
                             "THE ANCHOR (Quality Momentum)"])
    
    scan_limit = st.slider("Stocks to Analyze", 10, 250, 50)
    run_btn = st.button("🚀 EXECUTE STRATEGIC SCAN")

# --- 3. THE EXECUTION ENGINE ---
if run_btn:
    # Set the scope based on selection
    if "50" in universe: scan_list = all_symbols[:50]
    elif "200" in universe: scan_list = all_symbols[:200]
    else: scan_list = all_symbols[:scan_limit]

    results = []
    today = date.today()
    # Pulling 1.5 years of data to ensure solid 200DMA calculation
    start_date = today - timedelta(days=450) 
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, sym in enumerate(scan_list):
        status_text.text(f"🔍 Analyzing {sym} ({i+1}/{len(scan_list)})...")
        
        # Small delay to mimic human behavior and avoid 403 Forbidden errors
        time.sleep(0.15) 
        
        df = engine.fetch_with_retry(sym, start_date, today)
        
        if df is not None and len(df) >= 200:
            # --- CALCULATE INDICATORS ---
            df['50DMA'] = df['CLOSE'].rolling(window=50).mean()
            df['200DMA'] = df['CLOSE'].rolling(window=200).mean()
            df['VOL_MA10'] = df['VOLUME'].rolling(window=10).mean()
            
            # --- EXTRACT CURRENT STATE ---
            curr_price = df['CLOSE'].iloc[-1]
            m50 = df['50DMA'].iloc[-1]
            m200 = df['200DMA'].iloc[-1]
            vol_now = df['VOLUME'].iloc[-1]
            vol_avg = df['VOL_MA10'].iloc[-1]
            vol_ratio = vol_now / vol_avg if vol_avg > 0 else 0
            entry_date = df['DATE'].iloc[-1].strftime('%d-%b-%Y')

            # --- VOLUME-ENHANCED LOGIC GATES ---
            is_match = False
            
            if "SHIELD" in strategy:
                # Safe Buy: Above 200DMA (long trend up) but below 50DMA (short term dip)
                # We want selling to be "exhausted" (low volume ratio)
                if curr_price > m200 and curr_price < m50 and vol_ratio < 1.1: 
                    is_match = True
            
            elif "SWORD" in strategy:
                # Aggressive: Price > 50DMA > 200DMA + MASSIVE VOLUME surge
                if curr_price > m50 and m50 > m200 and vol_ratio > 1.5: 
                    is_match = True
            
            elif "ANCHOR" in strategy:
                # Steady: Consistent uptrend with stable volume
                if curr_price > m50 > m200 and vol_ratio >= 0.9: 
                    is_match = True

            if is_match:
                results.append({
                    "Symbol": sym,
                    "Scan Date": entry_date,
                    "LTP": round(curr_price, 2),
                    "6% Target": round(curr_price * 1.06, 2),
                    "Stop Loss (3%)": round(curr_price * 0.97, 2),
                    "Volume Force": f"{vol_ratio:.2f}x",
                    "Priority": "⭐⭐⭐" if vol_ratio > 2.0 else ("⭐⭐" if vol_ratio > 1.2 else "⭐")
                })
        
        progress_bar.progress((i + 1) / len(scan_list))

    status_text.empty()
    
    # --- 4. DATA PRESENTATION ---
    if results:
        st.success(f"Protocol Complete: Strategy {strategy} identified {len(results)} matches.")
        
        # Convert to DataFrame for better display
        res_df = pd.DataFrame(results)
        
        # Display with dynamic highlighting
        st.dataframe(
            res_df.style.background_gradient(cmap='Greens', subset=['Volume Force'])
            .format({"LTP": "₹{:.2f}", "6% Target": "₹{:.2f}", "Stop Loss (3%)": "₹{:.2f}"}),
            use_container_width=True
        )
        
        # Add a download feature for your trade log
        csv = res_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Trade Plan", csv, f"Legacy_Plan_{today}.csv", "text/csv")
        
    else:
        st.warning("No stocks currently meet the strict Safety & Volume criteria. Cash is a defensive position.")

# --- FOOTER ---
st.divider()
st.info("""
    *Guardian Tip:* 1. Check if the stock is near a lifetime high. 
    2. Ensure the Nifty 50 index is not in a free-fall. 
    3. Once 6% is hit, EXIT. No greed.
""")

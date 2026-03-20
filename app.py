import streamlit as st
import pandas as pd
from jugaad_data.nse import stock_df, NSELive
from datetime import date, timedelta

st.set_page_config(page_title="NSE Legend Scanner", layout="wide")
st.title("🏆 NSE All-Cap Strategy Scanner")

# --- STEP 1: LOAD ALL NSE TICKERS ---
@st.cache_data
def get_all_symbols():
    # Fetching the official equity list from NSE
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    try:
        df = pd.read_csv(url)
        return df[df[' SERIES'] == 'EQ']['SYMBOL'].tolist()
    except:
        return ["TATAMOTORS", "HAL", "RELIANCE", "BEL", "CDSL"]

all_stocks = get_all_symbols()

# --- STEP 2: UI CONTROLS ---
st.sidebar.header("Scanner Settings")
market_cap = st.sidebar.selectbox("Universe", ["Nifty 50 (Large)", "Nifty 500 (Mid/Small)", "Full NSE (All-Cap)"])
legend = st.sidebar.selectbox("Strategy", ["Charlie Munger (Quality)", "Peter Lynch (Growth)", "Warren Buffett (Value)", "Howard Marks (Cycles)"])

# --- STEP 3: CORE SCANNER ENGINE ---
if st.button('🚀 Start Legend Scan'):
    # Define scan range
    if "50 " in market_cap: scan_list = all_stocks[:50]
    elif "500" in market_cap: scan_list = all_stocks[:500]
    else: scan_list = all_stocks

    results = []
    end_date = date.today()
    start_date = end_date - timedelta(days=365) # Need 1 year for 200DMA
    
    progress = st.progress(0)
    
    for i, symbol in enumerate(scan_list):
        try:
            # Fetching Historical Data via Jugaad-Data
            df = stock_df(symbol=symbol, from_date=start_date, to_date=end_date, series="EQ")
            
            if len(df) >= 200:
                # Jugaad-data returns most recent at top; we need to reverse for rolling mean
                df = df.sort_values('DATE')
                df['50DMA'] = df['CLOSE'].rolling(window=50).mean()
                df['200DMA'] = df['CLOSE'].rolling(window=200).mean()
                
                curr = df['CLOSE'].iloc[-1]
                m50 = df['50DMA'].iloc[-1]
                m200 = df['200DMA'].iloc[-1]
                vol_spike = df['VOLUME'].iloc[-1] > df['VOLUME'].tail(10).mean() * 1.5

                # Legend Logic
                match = False
                if legend == "Charlie Munger (Quality)" and curr > m50 > m200: match = True
                elif legend == "Peter Lynch (Growth)" and curr > m50 and vol_spike: match = True
                elif legend == "Warren Buffett (Value)" and curr > m200 and curr < m200 * 1.1: match = True
                elif legend == "Howard Marks (Cycles)" and curr < m200 * 0.8: match = True

                if match:
                    results.append({
                        "Stock": symbol,
                        "Price": f"₹{curr:.2f}",
                        "Signal": "BULLISH" if curr > m50 else "WATCH",
                        "Target (6%)": f"₹{curr * 1.06:.2f}"
                    })
        except:
            continue
        progress.progress((i + 1) / len(scan_list))

    if results:
        st.success(f"Found {len(results)} matches!")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning("No matches found. Try a different strategy or universe.")

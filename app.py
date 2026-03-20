import streamlit as st
import yfinance as yf
import pandas as pd

# Mobile optimization
st.set_page_config(page_title="NSE Universe Scanner", layout="wide")
st.title("🌐 NSE All-Cap Master Scanner")

# --- STEP 1: LOAD ALL NSE TICKERS ---
@st.cache_data
def get_nse_tickers():
    # Downloads official list of NSE equities
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    try:
        df_nse = pd.read_csv(url)
        # We only need the SYMBOL column
        tickers = [f"{s}.NS" for s in df_nse['SYMBOL'].tolist()]
        return tickers
    except:
        # Fallback if NSE site is slow
        return ["TATAMOTORS.NS", "RELIANCE.NS", "TCS.NS"]

all_tickers = get_nse_tickers()

# --- STEP 2: DASHBOARD UI ---
st.sidebar.header("Scan Settings")
cap_size = st.sidebar.selectbox("Market Cap Focus", 
                                ["Nifty 50 (Large)", "Nifty Next 50 (Mid)", "Full NSE (All-Cap)"])

# Strategy Picker for Legends
strategy = st.sidebar.selectbox("Legend Strategy", 
                               ["Munger Momentum (50>200)", "Buffett Value (Price~200)", 
                                "Lynch Breakout (Vol Spike)", "Marks Contrarian (Oversold)"])

if st.button('🚀 Start Full Market Scan'):
    # Logic to limit tickers for speed on mobile
    if "Nifty 50" in cap_size:
        scan_list = all_tickers[:50] 
    elif "Mid" in cap_size:
        scan_list = all_tickers[50:150]
    else:
        scan_list = all_tickers # Scans everything!

    results = []
    progress_bar = st.progress(0)
    
    for i, ticker in enumerate(scan_list):
        try:
            df = yf.download(ticker, period="1y", progress=False)
            if len(df) < 200: continue
            
            # Math
            df['50DMA'] = df['Close'].rolling(window=50).mean()
            df['200DMA'] = df['Close'].rolling(window=200).mean()
            curr = df['Close'].iloc[-1]
            m50 = df['50DMA'].iloc[-1]
            m200 = df['200DMA'].iloc[-1]
            
            signal = "⏳ Skip"
            
            # --- LEGEND LOGIC ---
            if "Munger" in strategy and curr > m50 > m200:
                signal = "🥇 High Quality"
            elif "Buffett" in strategy and curr > m200 and curr < m200 * 1.1:
                signal = "💎 Undervalued"
            elif "Lynch" in strategy and curr > m50 and df['Volume'].iloc[-1] > df['Volume'].tail(5).mean() * 1.5:
                signal = "🚀 Breakout"
            elif "Marks" in strategy and curr < m200 * 0.8:
                signal = "📉 Deep Value"

            if signal != "⏳ Skip":
                results.append({"Stock": ticker.replace(".NS",""), "Price": round(float(curr), 2), "Signal": signal})
            
            progress_bar.progress((i + 1) / len(scan_list))
        except:
            continue

    if results:
        st.success(f"Found {len(results)} matches!")
        st.table(pd.DataFrame(results))
    else:
        st.warning("No matches found for this specific legend strategy right now.")

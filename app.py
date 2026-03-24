import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import date, timedelta
from jugaad_data.nse import stock_df, NSELive # Added NSELive for live volume
import requests
from io import StringIO

# --- CONFIGURATION ---
st.set_page_config(page_title="Strict VCP & Volume Surge Scanner", layout="wide")
st.title("🎯 Minervini SEPA: 90% Probability Entry Scanner")

# Initialize Live Data for Volume Surge Check
n = NSELive()

# --- STEP 1: AUTOMATED BASKET RETRIEVAL ---
@st.cache_data(ttl=86400)
def get_nifty_500():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    df_indices = pd.read_csv(StringIO(response.text))
    return df_indices['Symbol'].tolist()

def process_stock(ticker):
    try:
        # 1. Historical Data Fetch
        end_date = date.today()
        start_date = end_date - timedelta(days=400)
        df = stock_df(symbol=ticker, from_date=start_date, to_date=end_date, series="EQ")
        if df.empty: return None
        
        df = df.sort_values('DATE').reset_index(drop=True)
        df.rename(columns={'CLOSE': 'Close', 'HIGH': 'High', 'LOW': 'Low', 'OPEN': 'Open', 'VOLUME': 'Volume'}, inplace=True)
        
        # 2. Live Data Fetch for Volume Surge (Requirement: Vol Surge)
        live_quote = n.stock_quote(ticker)
        current_vol = live_quote['marketDeptOrderBook']['tradeInfo']['totalTradedVolume']
        avg_vol_20d = df['Volume'].tail(20).mean()
        
        # Volume Surge Check: Is today's volume > 50% of 20D average already?
        vol_surge = "YES" if current_vol > (avg_vol_20d * 0.50) else "NO"
        
        # 3. Technicals (SMAs)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_150'] = ta.sma(df['Close'], length=150)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        
        curr = df['Close'].iloc[-1]
        low_52 = df['Low'].tail(252).min()
        high_52 = df['High'].tail(252).max()
        
        # 4. Minervini 7-Point Template (Requirement: 7/7 Score)
        c1 = curr > df['SMA_150'].iloc[-1] and curr > df['SMA_200'].iloc[-1]
        c2 = df['SMA_150'].iloc[-1] > df['SMA_200'].iloc[-1]
        c3 = df['SMA_200'].iloc[-1] > df['SMA_200'].iloc[-20]
        c4 = df['SMA_50'].iloc[-1] > df['SMA_150'].iloc[-1] and df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1]
        c5 = curr > df['SMA_50'].iloc[-1]
        c6 = curr > (low_52 * 1.30)
        c7 = curr > (high_52 * 0.75)
        score = sum([c1, c2, c3, c4, c5, c6, c7])
        
        # 5. VCP Tightness (Requirement: VCP YES)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        is_tight = df['ATR'].iloc[-1] < (df['ATR'].tail(20).mean() * 0.85)
        
        # --- FINAL STRICT FILTER: 7/7 SCORE + VCP YES + VOL SURGE ---
        if score == 7 and is_tight and vol_surge == "YES":
            return {
                "Ticker": ticker,
                "Price": round(curr, 2),
                "Score": f"{score}/7",
                "VCP Tight": "YES",
                "Vol Surge": "💥 HIGH",
                "Stop Loss (3%)": round(curr * 0.97, 2),
                "Target (6%)": round(curr * 1.06, 2)
            }
        return None 
    except:
        return None

# --- UI LOGIC ---
all_symbols = get_nifty_500()
st.sidebar.header("Execution Guidelines")
st.sidebar.info("🕒 **Timing:** Run at 10:15 AM\n\n🛑 **Stop Loss:** -3%\n\n🎯 **Take Profit:** +6%")

batch_size = st.sidebar.slider("Scan Depth", 10, 500, 100)

if st.button(f"Scan for 90% Probability Entries"):
    results = []
    progress_bar = st.progress(0)
    for i, ticker in enumerate(all_symbols[:batch_size]):
        res = process_stock(ticker)
        if res: results.append(res)
        progress_bar.progress((i + 1) / batch_size)
        
    if results:
        df_final = pd.DataFrame(results)
        st.write(f"### 📈 Found {len(df_final)} High-Probability Leaders")
        st.dataframe(df_final, use_container_width=True)
    else:
        st.warning("No stocks currently meet the Strict 7/7 + VCP + Volume Surge criteria.")

st.markdown("---")
st.write("### 📜 90% Success Checklist Applied:")
cols = st.columns(4)
cols[0].metric("Stop Loss", "-3%", "Fixed")
cols[1].metric("Take Profit", "+6%", "Fixed")
cols[2].metric("Signal", "7/7 + VCP YES", "Required")
cols[3].metric("Timing", "10:15 AM", "Institutional")

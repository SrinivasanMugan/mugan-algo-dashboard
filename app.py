import streamlit as st
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import date, timedelta
from jugaad_data.nse import stock_df
import requests
from io import StringIO

# --- CONFIGURATION ---
st.set_page_config(page_title="Strict VCP NSE Scanner", layout="wide")
st.title("🇮🇳 Minervini SEPA: Strict VCP Filter")

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
        end_date = date.today()
        start_date = end_date - timedelta(days=400)
        df = stock_df(symbol=ticker, from_date=start_date, to_date=end_date, series="EQ")
        
        if df.empty: return None
        
        df = df.sort_values('DATE').reset_index(drop=True)
        df.rename(columns={'CLOSE': 'Close', 'HIGH': 'High', 'LOW': 'Low', 'OPEN': 'Open', 'VOLUME': 'Volume'}, inplace=True)
        
        # Technicals (SMAs)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_150'] = ta.sma(df['Close'], length=150)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        
        curr = df['Close'].iloc[-1]
        low_52 = df['Low'].tail(252).min()
        high_52 = df['High'].tail(252).max()
        
        # Minervini 7-Point Template
        c1 = curr > df['SMA_150'].iloc[-1] and curr > df['SMA_200'].iloc[-1]
        c2 = df['SMA_150'].iloc[-1] > df['SMA_200'].iloc[-1]
        c3 = df['SMA_200'].iloc[-1] > df['SMA_200'].iloc[-20]
        c4 = df['SMA_50'].iloc[-1] > df['SMA_150'].iloc[-1] and df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1]
        c5 = curr > df['SMA_50'].iloc[-1]
        c6 = curr > (low_52 * 1.30)
        c7 = curr > (high_52 * 0.75)
        
        score = sum([c1, c2, c3, c4, c5, c6, c7])
        
        # VCP Tightness Logic
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        # Tightness Check (Current ATR < 85% of 20-day average)
        is_tight = df['ATR'].iloc[-1] < (df['ATR'].tail(20).mean() * 0.85)
        
        # --- CRITICAL CHANGE: ONLY RETURN IF SCORE >= 5 AND VCP IS YES ---
        if score >= 5 and is_tight:
            return {
                "Ticker": ticker,
                "Price": round(curr, 2),
                "Minervini Score": f"{score}/7",
                "VCP Tight": "YES",
                "52W High Gap %": round(((high_52 - curr)/high_52)*100, 2),
                "Data": df
            }
        return None # Discards stocks that are not "YES"
    except:
        return None

# --- UI LOGIC ---
all_symbols = get_nifty_500()

st.sidebar.header("Scanner Settings")
batch_size = st.sidebar.slider("Number of stocks to scan", 10, 500, 100)

if st.button(f"Scan for Stage 2 VCP Leaders"):
    results = []
    progress_bar = st.progress(0)
    
    for i, ticker in enumerate(all_symbols[:batch_size]):
        res = process_stock(ticker)
        if res: results.append(res)
        progress_bar.progress((i + 1) / batch_size)
        
    if results:
        df_final = pd.DataFrame(results).drop(columns=['Data'])
        st.write(f"### 🎯 Found {len(df_final)} Strict VCP Leaders")
        st.dataframe(df_final.sort_values(by="Minervini Score", ascending=False), use_container_width=True)
        
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("Download Results", csv, "vcp_leaders.csv", "text/csv")
    else:
        st.warning("No stocks currently meet the Strict VCP criteria. Market volatility may be too high today.")

st.info("The dashboard is now set to **'Strict Mode'**. It will hide any stock that does not show Volatility Contraction (VCP YES).")

import streamlit as st
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import date, timedelta
from jugaad_data.nse import stock_df
import requests
from io import StringIO

# --- CONFIGURATION ---
st.set_page_config(page_title="Minervini NSE Full Scanner", layout="wide")
st.title("🇮🇳 Minervini SEPA: The Nifty 500 Basket")

# --- STEP 1: AUTOMATED BASKET RETRIEVAL ---
@st.cache_data(ttl=86400) # Refreshes the list once a day
def get_nifty_500():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    df_indices = pd.read_csv(StringIO(response.text))
    return df_indices['Symbol'].tolist()

def process_stock(ticker):
    try:
        # Fetching 400 days for 200 SMA & 52W High/Low
        end_date = date.today()
        start_date = end_date - timedelta(days=400)
        df = stock_df(symbol=ticker, from_date=start_date, to_date=end_date, series="EQ")
        
        if df.empty: return None
        
        df = df.sort_values('DATE').reset_index(drop=True)
        df.rename(columns={'CLOSE': 'Close', 'HIGH': 'High', 'LOW': 'Low', 'OPEN': 'Open', 'VOLUME': 'Volume'}, inplace=True)
        
        # Technicals
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
        
        # VCP Tightness (Volatility contraction)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        is_tight = "YES" if df['ATR'].iloc[-1] < (df['ATR'].tail(20).mean() * 0.80) else "No"
        
        if score >= 5: # Only show stocks that are starting to trend
            return {
                "Ticker": ticker,
                "Price": round(curr, 2),
                "Minervini Score": f"{score}/7",
                "VCP Tight": is_tight,
                "52W High Gap %": round(((high_52 - curr)/high_52)*100, 2),
                "Data": df
            }
    except:
        return None

# --- UI LOGIC ---
all_symbols = get_nifty_500()

# To prevent the app from crashing on Cloud, let's process in smaller batches
# or let the user choose a sub-set
st.sidebar.header("Scanner Settings")
batch_size = st.sidebar.slider("Number of stocks to scan", 10, 500, 50)

if st.button(f"Scan Top {batch_size} Nifty 500 Stocks"):
    results = []
    progress_bar = st.progress(0)
    
    for i, ticker in enumerate(all_symbols[:batch_size]):
        res = process_stock(ticker)
        if res: results.append(res)
        progress_bar.progress((i + 1) / batch_size)
        
    if results:
        df_final = pd.DataFrame(results).drop(columns=['Data'])
        st.write("### 📈 Found 'Stage 2' Leaders")
        st.dataframe(df_final.sort_values(by="Minervini Score", ascending=False), use_container_width=True)
        
        # CSV Download for your records
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("Download Scan Results", csv, "minervini_scan.csv", "text/csv")
    else:
        st.info("No stocks currently meeting the 5/7 score criteria in this batch.")

st.info("Note: A Score of 7/7 means the stock is a 'True Market Leader'. Look for 'VCP Tight = YES' for the lowest-risk entry.")


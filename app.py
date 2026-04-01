import streamlit as st
from jugaad_data.nse import NSELive
import pandas as pd
import time

# Create a cached function to prevent constant NSE hits (which leads to IP bans)
@st.cache_data(ttl=60) # Refreshes every 1 minute
def fetch_underdog_data(symbol_list):
    n = NSELive()
    data_rows = []
    
    for symbol in symbol_list:
        try:
            # Adding a small sleep to avoid rapid-fire requests on cloud
            time.sleep(0.6) 
            quote = n.stock_quote(symbol)
            
            # The "Deep Value" Extraction
            price = quote['priceInfo']['lastPrice']
            mkt_cap = quote['securityWiseDP']['marketCapitalization']
            
            # Check for our 'No-Backfire' criteria
            pledge = quote['securityWiseDP'].get('promoterPledgedSharePercent', 0)
            
            # Placeholder for PB Ratio (Needs to be mapped from metadata)
            # In cloud, some metadata fields might be empty if the IP is throttled
            data_rows.append({
                "Symbol": symbol, 
                "Price": price, 
                "MCap (Cr)": mkt_cap,
                "Pledge %": pledge
            })
        except Exception as e:
            st.sidebar.error(f"Error fetching {symbol}: {e}")
            continue
    return pd.DataFrame(data_rows)

# Dashboard UI
st.title("Mugan's Underdog Miner 2.0")
watchlist = ["SOUTHBANK", "KARURVYSYA", "JINDALSAW", "FEDERALBNK"]

if st.button('Mine Real-Time Underdogs'):
    with st.spinner('Analyzing NSE Private Sector...'):
        df = fetch_underdog_data(watchlist)
        if not df.empty:
            st.dataframe(df.style.highlight_max(axis=0))
        else:
            st.warning("No data retrieved. NSE might be throttling the cloud connection.")
            

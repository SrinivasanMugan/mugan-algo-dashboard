import streamlit as st
import pandas as pd
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. REFRESH: 2 Minutes is the safest for NSE
st_autorefresh(interval=120 * 1000, key="nse_sync_safe")

class NSELiveSession:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }
        self.session.headers.update(self.headers)
        self.init_session()

    def init_session(self):
        """Must visit home page first to get cookies, or API will block you."""
        try:
            self.session.get("https://www.nseindia.com", timeout=10)
        except:
            st.error("NSE Connection Failed. Check your internet.")

    def get_price(self, symbol):
        """Fetches price using the active session cookies."""
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        try:
            # Small delay to look human
            time.sleep(1) 
            response = self.session.get(url, timeout=10)
            data = response.json()
            return float(data['priceInfo']['lastPrice'])
        except:
            # If session expires, re-init and try once more
            self.init_session()
            return None

# --- UI SETUP ---
st.set_page_config(layout="wide", page_title="Titan 9 Guardian")
st.title("🛡️ Titan 9: Live Indian Standard")

if 'nse' not in st.session_state:
    st.session_state.nse = NSELiveSession()

# Your Top Picks
watch_list = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "TITAN", "ICICIBANK", "AXISBANK", "BHARTIARTL", "LT"]

st.write(f"Last Sync: {time.strftime('%H:%M:%S')}")

cols = st.columns(3)
for i, symbol in enumerate(watch_list):
    price = st.session_state.nse.get_price(symbol)
    
    with cols[i % 3]:
        with st.container(border=True):
            if price:
                entry = price * 0.99 # Replace with your actual buy price
                tp = round(entry * 1.03, 2)
                sl = round(entry * 0.99, 2)
                
                st.metric(symbol, f"₹{price}")
                st.write(f"**Target:** :green[₹{tp}] | **Stop:** :red[₹{sl}]")
                
                if price >= tp: st.success("🎯 TARGET HIT")
                if price <= sl: st.error("🚨 STOP HIT")
            else:
                st.warning(f"{symbol}: Retrying...")

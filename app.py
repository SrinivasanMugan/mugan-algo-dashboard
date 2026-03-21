import streamlit as st
import pandas as pd
import time
import random
from jugaad_data.nse import NSELive
from streamlit_autorefresh import st_autorefresh

# 1. SLOW REFRESH: 2 Minutes (120s) to stay under the NSE radar
st_autorefresh(interval=120 * 1000, key="nse_safe_sync")

class TitanStealthEngine:
    def __init__(self):
        self.live = NSELive()
        # Set a User-Agent to mimic a real Chrome Browser
        self.live.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.nseindia.com/get-quotes/equity?symbol=SBIN",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def fetch_price(self, symbol):
        """Safely fetch price with a 'Human' delay."""
        try:
            # Random delay between 0.5 to 1.5 seconds per stock
            time.sleep(random.uniform(0.5, 1.5)) 
            quote = self.live.stock_quote(symbol)
            
            # Key safety check: Make sure NSE actually sent data
            if quote and 'priceInfo' in quote:
                return float(quote['priceInfo']['lastPrice'])
            return None
        except Exception as e:
            # If blocked or errored, return None quietly
            return None

# --- DASHBOARD UI ---
st.set_page_config(layout="wide", page_title="Titan 9 Stealth")
st.title("🛡️ Titan 9: NSE Live Guardian")

# Initialize Engine
if 'engine' not in st.session_state:
    st.session_state.engine = TitanStealthEngine()

# The Titan 9 Selection
watch_list = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "TITAN", "ICICIBANK", "AXISBANK", "BHARTIARTL", "LT"]

st.write(f"Refreshed at: {time.strftime('%H:%M:%S')}")

cols = st.columns(3)
for i, symbol in enumerate(watch_list):
    price = st.session_state.engine.fetch_price(symbol)
    
    with cols[i % 3]:
        with st.container(border=True):
            if price:
                # 3% Target and 1% Stop Loss calculation
                # (Entry price should ideally be your actual buy price from a database)
                entry_est = price * 0.99 
                target = round(entry_est * 1.03, 2)
                stop = round(entry_est * 0.99, 2)
                
                st.metric(symbol, f"₹{price}")
                st.write(f"**Target:** :green[₹{target}] | **Stop:** :red[₹{stop}]")
                
                # Visual Alert
                if price >= target: st.success("🎯 TARGET REACHED - ROLL OUT PROFIT")
                if price <= stop: st.error("🚨 STOP LOSS REACHED - EXIT NOW")
            else:
                st.warning(f"{symbol}: Waiting for NSE...")
                st.caption("NSE is rate-limiting. This will fix itself on the next 2-min sync.")

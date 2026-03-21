import streamlit as st
import pandas as pd
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. CLOUD OPTIMIZATION: 2-minute refresh to avoid IP bans
st_autorefresh(interval=120 * 1000, key="titan_sync")

class TitanFullEngine:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/"
        }
        self.session.headers.update(self.headers)
        # Visit home to get cookies
        try: self.session.get("https://www.nseindia.com", timeout=10)
        except: pass

    def get_live_stats(self, symbol):
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        try:
            time.sleep(1) # Human-like delay
            resp = self.session.get(url, timeout=10).json()
            return {
                "price": float(resp['priceInfo']['lastPrice']),
                "pChange": float(resp['priceInfo']['pChange'])
            }
        except: return None

# --- UI LAYER ---
st.set_page_config(layout="wide", page_title="Titan 9 Full")
st.title("🛡️ Titan 9: Full Strategy Engine")

if 'engine' not in st.session_state:
    st.session_state.engine = TitanFullEngine()

# THE TOP 9 SELECTION (Based on Lynch/Marks Analysis)
watch_list = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "TITAN", "ICICIBANK", "AXISBANK", "BHARTIARTL", "LT"]

cols = st.columns(3)
for i, symbol in enumerate(watch_list):
    data = st.session_state.engine.get_live_stats(symbol)
    with cols[i % 3]:
        with st.container(border=True):
            if data:
                p = data['price']
                tp = round(p * 1.03, 2)
                sl = round(p * 0.99, 2)
                st.metric(symbol, f"₹{p}", f"{data['pChange']}%")
                st.write(f"**Target (3%):** :green[₹{tp}]")
                st.write(f"**Stop (1%):** :red[₹{sl}]")
                # Compounding Logic Note
                st.caption(f"Goal: Roll into next trade after ₹{tp}")
            else:
                st.warning(f"{symbol}: Connection Refused")
                st.caption("NSE is rate-limiting the cloud server. Stand by...")

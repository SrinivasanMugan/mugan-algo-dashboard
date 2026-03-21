import streamlit as st
import pandas as pd
from jugaad_data.nse import NSELive
from streamlit_autorefresh import st_autorefresh
import time

# Refresh every 60 seconds to avoid NSE IP blocking
st_autorefresh(interval=60 * 1000, key="datarefresh")

class TitanGuardian:
    def __init__(self):
        # Using a single session to stay connected
        try:
            self.live = NSELive()
        except Exception as e:
            st.error(f"Failed to connect to NSE: {e}")

    def fetch_safe_price(self, symbol):
        """Safely fetches price without crashing on errors."""
        try:
            # Short pause to prevent 'spamming' the server
            time.sleep(0.2) 
            quote = self.live.stock_quote(symbol)
            # Check if the expected keys exist in the response
            if 'priceInfo' in quote and 'lastPrice' in quote['priceInfo']:
                return float(quote['priceInfo']['lastPrice'])
            return None
        except Exception:
            # If NSE returns an error or empty JSON, return None
            return None

# --- UI Setup ---
st.title("🛡️ Titan 9: Error-Proof Live View")
guardian = TitanGuardian()

# Your Top 360 selection (Top 9 for display)
watch_list = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "TITAN", "ICICIBANK", "AXISBANK", "BHARTIARTL", "LT"]

cols = st.columns(3)
for i, symbol in enumerate(watch_list):
    price = guardian.fetch_safe_price(symbol)
    
    with cols[i % 3]:
        with st.container(border=True):
            if price:
                st.metric(symbol, f"₹{price}")
                # 1:3 Logic
                entry = price * 0.99 # Hypothetical entry
                st.caption(f"Target (3%): ₹{round(entry * 1.03, 2)}")
                st.caption(f"Stop (1%): ₹{round(entry * 0.99, 2)}")
            else:
                st.warning(f"{symbol}: Data Timeout")
                st.info("NSE server busy. Retrying in 60s...")

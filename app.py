import streamlit as st
import pandas as pd
from jugaad_data.nse import NSELive
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# 1. LIVE REFRESH: Updates every 60 seconds (NSE Safe Limit)
st_autorefresh(interval=60 * 1000, key="live_update")

class TitanNinerLive:
    def __init__(self):
        self.live = NSELive()
        self.target_pct = 0.03 # 3% Target
        self.sl_pct = 0.01     # 1% Stop Loss

    def get_market_status(self):
        """Checks if the NSE is currently open."""
        try:
            status = self.live.market_status()
            return status['marketState'][0]['marketStatus']
        except:
            return "Exchange Closed"

    def fetch_price(self, symbol):
        """Pulls the Last Traded Price (LTP) live."""
        try:
            quote = self.live.stock_quote(symbol)
            return float(quote['priceInfo']['lastPrice'])
        except:
            return None

# --- UI SETUP ---
st.set_page_config(layout="wide", page_title="Titan 9 Live")
engine = TitanNinerLive()

st.title("🛡️ Titan 9 Live Execution")
status = engine.get_market_status()
st.sidebar.markdown(f"**Market Status:** {status}")
st.sidebar.write(f"Last Sync: {datetime.now().strftime('%H:%M:%S')}")

# 2. YOUR ACTIVE TRADES (The Top 9)
# In a full setup, these symbols come from your Daily Scanner results.
# For now, we input your current active watch-list.
watch_list = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "TITAN", "ICICIBANK", "AXISBANK", "BHARTIARTL", "LT"]

# 3. THE 3x3 EXECUTION GRID
st.subheader("Current Market Monitoring (1:3 Risk-Reward)")

for i in range(0, len(watch_list), 3):
    cols = st.columns(3)
    for j in range(3):
        if i + j < len(watch_list):
            symbol = watch_list[i + j]
            ltp = engine.fetch_price(symbol)
            
            if ltp:
                # Assuming entry was at previous close or 1% below current for demo
                # In your real version, 'entry_price' would be a fixed value from your trade log
                entry_price = ltp * 0.99 
                tp = round(entry_price * 1.03, 2)
                sl = round(entry_price * 0.99, 2)
                
                with cols[j]:
                    with st.container(border=True):
                        st.markdown(f"### {symbol}")
                        
                        # High Visibility Logic
                        if ltp >= tp:
                            st.success(f"🔥 TARGET HIT: ₹{ltp}")
                        elif ltp <= sl:
                            st.error(f"🚨 STOP LOSS HIT: ₹{ltp}")
                        else:
                            st.metric("LTP", f"₹{ltp}", delta=f"{round(((ltp/entry_price)-1)*100,2)}%")

                        st.write(f"**Entry:** ₹{round(entry_price, 2)}")
                        st.write(f"**Target (3%):** ₹{tp} | **Stop (1%):** ₹{sl}")
                        
                        # Progress bar towards 3%
                        progress = min(max((ltp - entry_price) / (tp - entry_price), 0), 1)
                        st.progress(progress)

# 4. EXECUTION GUIDELINE
st.divider()
with st.expander("Indian Standard Execution Rules"):
    st.write("""
    1. **Entry:** Only when Titan Score > 80% and Price > 20 EMA.
    2. **Exit (Profit):** Immediate exit at 3% or use a trailing stop if momentum is high.
    3. **Exit (Loss):** Hard exit if Daily Candle closes 1% below Entry.
    4. **Rotation:** Re-invest capital into the next 'Titan 9' pick immediately.
    """)

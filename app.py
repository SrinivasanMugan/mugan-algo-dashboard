import streamlit as st
import pandas as pd
import numpy as np
from jugaad_data.nse import stock_df
from datetime import datetime, timedelta

class TitanNineEngine:
    def __init__(self):
        self.tp_pct = 0.03  # 3% Monthly Target
        self.sl_pct = 0.01  # 1% Strict Stop Loss
        self.min_score = 80 # High-conviction threshold

    def get_data(self, symbol):
        try:
            end = datetime.now().date()
            start = end - timedelta(days=250)
            df = stock_df(symbol=symbol, from_date=start, to_date=end)
            return df.sort_values('DATE')
        except:
            return None

    def apply_titan_filters(self, df, peg, d_e):
        """
        STRICT FILTER LOGIC:
        1. Lynch: PEG < 1.0 & Debt/Equity < 1.2
        2. Marks: RSI between 40-60 (No Euphoria) & ATR < 1% (Low Noise)
        """
        # Technicals
        delta = df['CLOSE'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))
        
        # Volatility Check (ATR) - CRITICAL for 1% Stop Loss
        df['TR'] = np.maximum(df['HIGH'] - df['LOW'], 
                    np.maximum(abs(df['HIGH'] - df['CLOSE'].shift(1)), 
                    abs(df['LOW'] - df['CLOSE'].shift(1))))
        df['ATR_Pct'] = df['TR'].rolling(window=14).mean() / df['CLOSE']

        last = df.iloc[-1]
        score = 0

        # FILTER 1: PETER LYNCH (Fundamentals)
        if peg < 1.0: score += 40
        if d_e < 1.2: score += 10

        # FILTER 2: HOWARD MARKS (Cycle & Anti-Euphoria)
        # We target the 'Sweet Spot' where the stock is stable but ready.
        if 40 <= last['RSI'] <= 60: score += 30
        
        # SAFETY CHECK: If daily volatility > 1.2%, the 1% SL is too risky.
        if last['ATR_Pct'] < 0.012: score += 20 

        return score, last['CLOSE']

# --- STREAMLIT UI ---
st.set_page_config(layout="wide", page_title="Titan 9 Guardian")
st.title("🛡️ Mugan's Legacy: The Titan 9")
st.caption("Top 360 NSE | 1:3 Risk-Reward | Lynch-Marks Infusion")

# This would ideally be a loop through your Top 360 list
# For this audit, we display the results of a processed scan
def show_dashboard(results_list):
    # Sort and take exactly Top 9
    top_9 = pd.DataFrame(results_list).sort_values(by="Score", ascending=False).head(9)
    
    # 3x3 Grid Layout
    for i in range(0, len(top_9), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(top_9):
                stock = top_9.iloc[i + j]
                with cols[j]:
                    with st.container(border=True):
                        st.subheader(stock['Symbol'])
                        st.progress(stock['Score'] / 100)
                        
                        p = stock['Price']
                        tp = round(p * 1.03, 2)
                        sl = round(p * 0.99, 2)
                        
                        c1, c2 = st.columns(2)
                        c1.metric("Entry", f"₹{p}")
                        c1.metric("Score", f"{stock['Score']}%")
                        c2.write(f"**Target:** :green[₹{tp}]")
                        c2.write(f"**Stop:** :red[₹{sl}]")
                        st.caption("1:3 Ratio Verified")

# Mock results for visual validation
processed_stocks = [
    {"Symbol": "RELIANCE", "Score": 95, "Price": 2980},
    {"Symbol": "HDFCBANK", "Score": 92, "Price": 1460},
    {"Symbol": "TCS", "Score": 90, "Price": 3910},
    {"Symbol": "TITAN", "Score": 88, "Price": 3250},
    {"Symbol": "INFY", "Score": 85, "Price": 1620},
    {"Symbol": "AXISBANK", "Score": 84, "Price": 1080},
    {"Symbol": "ICICIBANK", "Score": 82, "Price": 1120},
    {"Symbol": "BHARTIARTL", "Score": 81, "Price": 1210},
    {"Symbol": "TATAMOTORS", "Score": 80, "Price": 940}
]

show_dashboard(processed_stocks)

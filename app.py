import streamlit as st
import pandas as pd
from jugaad_data.nse import bhavcopy_save
from datetime import date, timedelta
import os

# 1. SETUP & PAGE CONFIG
st.set_page_config(page_title="Mugan's Big Bull Guardian", layout="wide")
st.title("🛡️ Mugan's Legacy Guardian: Titan Edition")
st.subheader("Jhunjhunwala Conviction + Melvin Li Precision")

# 2. DATA FETCHING (Error-Resilient)
@st.cache_data(ttl=3600)
def get_market_data():
    try:
        # Fetching latest available Bhavcopy (avoiding weekends)
        today = date.today()
        # Find the most recent weekday
        target_date = today - timedelta(days=1) if today.weekday() < 5 else today - timedelta(days=(today.weekday() - 4))
        
        file_path = bhavcopy_save(target_date, ".")
        df = pd.read_csv(file_path)
        os.remove(file_path) # Clean up
        return df
    except Exception as e:
        st.error(f"NSE Connection Error: {e}")
        return None

data = get_market_data()

if data is not None:
    # 3. LOGIC ENGINE (The Plot)
    # Cleaning data for NSE specific columns
    df = data[data['SERIES'] == 'EQ'].copy()
    
    # Calculating basic metrics
    df['VOL_FORCE'] = df['TOTTRDQTY'] / df['TOTTRDQTY'].rolling(window=10).mean()
    df['CHANGE_PCT'] = ((df['CLOSE'] - df['PREVCLOSE']) / df['PREVCLOSE']) * 100

    # 4. STRATEGY CLASSIFICATION
    def apply_strategy(row):
        # Simplified DMA logic for the scanner (can be expanded with historical data)
        is_uptrend = row['CLOSE'] > row['PREVCLOSE'] 
        high_vol = row['VOL_FORCE'] > 1.5
        
        if is_uptrend and high_vol:
            return "THE SWORD (Breakout)", "🟢 BUY"
        elif is_uptrend and not high_vol:
            return "THE ANCHOR (Momentum)", "🟡 HOLD"
        else:
            return "WATCHLIST", "⚪ WAIT"

    df[['STRATEGY', 'BUY_ALERT']] = df.apply(lambda x: pd.Series(apply_strategy(x)), axis=1)

    # 5. THE DASHBOARD DISPLAY
    st.write(f"### Market Scan Results ({len(df)} Stocks Analyzed)")
    
    # Filter for Buy Alerts only to keep it "First-Class"
    final_df = df[df['BUY_ALERT'] == '🟢 BUY'].sort_values(by='VOL_FORCE', ascending=False)
    
    # Adding Target & Stop Loss Columns
    final_df['TARGET (6%)'] = (final_df['CLOSE'] * 1.06).round(2)
    final_df['STOP LOSS (3%)'] = (final_df['CLOSE'] * 0.97).round(2)

    # Displaying Final Results
    st.dataframe(final_df[['SYMBOL', 'CLOSE', 'CHANGE_PCT', 'VOL_FORCE', 'STRATEGY', 'BUY_ALERT', 'TARGET (6%)', 'STOP LOSS (3%)']], 
                 use_container_width=True)

else:
    st.warning("Please wait for NSE to update the daily Bhavcopy file (usually after 6:00 PM IST).")

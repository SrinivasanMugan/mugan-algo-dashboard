import streamlit as st
import pandas as pd
from jugaad_data.nse import bhavcopy_save
from datetime import date, timedelta
import os
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Mugan's Big Bull Guardian", layout="wide")
st.title("🛡️ Mugan's Legacy Guardian: Titan Edition")
st.markdown("### *Jhunjhunwala Quality + Melvin Li Precision*")

# --- 1. ROBUST DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_nse_data():
    for i in range(1, 7): # Look back up to 6 days to find a working day
        try:
            target_date = date.today() - timedelta(days=i)
            if target_date.weekday() >= 5: continue # Skip Sat/Sun
            
            csv_path = bhavcopy_save(target_date, ".")
            df = pd.read_csv(csv_path)
            
            # Clean up: remove the downloaded file to keep the server light
            if os.path.exists(csv_path):
                os.remove(csv_path)
            return df, target_date
        except Exception:
            time.sleep(1)
            continue
    return None, None

df_raw, data_date = fetch_nse_data()

if df_raw is not None:
    st.success(f"✅ Data Synced: {data_date.strftime('%d %b %Y')}")
    
    # --- 2. THE FILTERING LAYER ---
    # Only Equity (Mainboard) stocks
    df = df_raw[df_raw['SERIES'] == 'EQ'].copy()
    
    # Technical Calculations (The "Plot" Essentials)
    df['CHANGE_PCT'] = (((df['CLOSE'] - df['PREVCLOSE']) / df['PREVCLOSE']) * 100).round(2)
    df['VOL_FORCE'] = (df['TOTTRDQTY'] / df['TOTTRDQTY'].rolling(window=10).mean()).fillna(1).round(2)
    
    # --- 3. THE STRATEGY MATRIX (Shield, Sword, Anchor) ---
    def apply_strategy(row):
        # THE SWORD (Melvin Li Breakout)
        if row['CHANGE_PCT'] > 3.0 and row['VOL_FORCE'] > 1.8:
            return "🟢 BUY (THE SWORD)", "HIGH"
        
        # THE SHIELD (Jhunjhunwala Value Dip)
        elif -1.5 < row['CHANGE_PCT'] < 0.5 and row['VOL_FORCE'] > 1.2:
            return "🔵 HOLD (THE SHIELD)", "MEDIUM"
        
        # THE ANCHOR (Steady Momentum)
        elif 0.5 < row['CHANGE_PCT'] < 2.5 and row['VOL_FORCE'] > 0.9:
            return "🟡 WATCH (THE ANCHOR)", "LOW"
            
        return "WAIT", "NONE"

    df[['STRATEGY', 'ALERT_LVL']] = df.apply(lambda x: pd.Series(apply_strategy(x)), axis=1)

    # --- 4. EXECUTION PARAMETERS (6% / 3%) ---
    df['BUY_PRICE'] = df['CLOSE']
    df['TARGET (6%)'] = (df['CLOSE'] * 1.06).round(2)
    df['STOP LOSS (3%)'] = (df['CLOSE'] * 0.97).round(2)

    # --- 5. THE DASHBOARD VIEW ---
    # Filter only for stocks showing an active strategy
    final_df = df[df['ALERT_LVL'] != "NONE"].sort_values(by='VOL_FORCE', ascending=False)

    st.subheader("🔥 Live Buy Alerts")
    # Displaying the "First-Class" Table
    st.dataframe(
        final_df[['SYMBOL', 'CLOSE', 'CHANGE_PCT', 'VOL_FORCE', 'STRATEGY', 'TARGET (6%)', 'STOP LOSS (3%)']],
        use_container_width=True,
        hide_index=True
    )

    # --- 6. EXPORT FEATURE ---
    csv_data = final_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Today's Trade Plan", data=csv_data, file_name=f"Mugan_Alerts_{data_date}.csv", mime='text/csv')

else:
    st.error("NSE Data Server Timeout. Please refresh the page.")
    

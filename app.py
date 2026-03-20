import streamlit as st
import pandas as pd
from jugaad_data.nse import bhavcopy_save
from datetime import date, timedelta
import os
import time

st.set_page_config(page_title="Mugan's Big Bull Guardian", layout="wide")
st.title("🛡️ Mugan's Legacy Guardian: Titan Edition (2026)")

# --- 1. UDiFF DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_udiff_data():
    for i in range(1, 10): 
        try:
            target_date = date.today() - timedelta(days=i)
            if target_date.weekday() >= 5: continue
            
            # Fetching the bhavcopy
            csv_path = bhavcopy_save(target_date, ".")
            df = pd.read_csv(csv_path)
            
            # Clean spaces from column names
            df.columns = [str(c).strip() for c in df.columns]
            
            if os.path.exists(csv_path):
                os.remove(csv_path)
            return df, target_date
        except Exception:
            continue
    return None, None

df_raw, data_date = fetch_udiff_data()

if df_raw is not None:
    st.success(f"✅ UDiFF Data Synced: {data_date.strftime('%d %b %Y')}")
    
    # --- 2. 2026 COLUMN MAPPING ---
    # Mapping the new 2026 UDiFF headers to our logic
    mapping = {
        'SYMBOL': 'TCKRSYMB',
        'SERIES': 'SCTYSRS',
        'CLOSE': 'CLSPRIC',
        'PREV_CLOSE': 'PRVSCLSGPRIC',
        'VOLUME': 'TTLTRADGVOL'
    }

    # Filter for Equity (Standard 'EQ' or Trade-to-Trade 'BE')
    # Using the new SCTYSRS column
    df = df_raw[df_raw[mapping['SERIES']].isin(['EQ', 'BE'])].copy()
    
    # --- 3. THE STRATEGY ENGINE ---
    # Convert columns to numeric to prevent calculation errors
    for col in [mapping['CLOSE'], mapping['PREV_CLOSE'], mapping['VOLUME']]:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['CHANGE_PCT'] = (((df[mapping['CLOSE']] - df[mapping['PREV_CLOSE']]) / df[mapping['PREV_CLOSE']]) * 100).round(2)
    df['VOL_FORCE'] = (df[mapping['VOLUME']] / df[mapping['VOLUME']].mean()).round(2)
    
    def apply_logic(row):
        # THE SWORD: Melvin Li Momentum (High Vol + Price Breakout)
        if row['CHANGE_PCT'] > 3.0 and row['VOL_FORCE'] > 2.0:
            return "🟢 BUY (THE SWORD)"
        # THE SHIELD: Jhunjhunwala Value Dip (Buying the fear/flatness)
        elif -1.0 < row['CHANGE_PCT'] < 0.5 and row['VOL_FORCE'] > 1.2:
            return "🔵 HOLD (THE SHIELD)"
        return "WAIT"

    df['STRATEGY'] = df.apply(apply_logic, axis=1)
    df['TARGET (6%)'] = (df[mapping['CLOSE']] * 1.06).round(2)
    df['STOP LOSS (3%)'] = (df[mapping['CLOSE']] * 0.97).round(2)

    # --- 4. FIRST-CLASS DISPLAY ---
    results = df[df['STRATEGY'] != "WAIT"].sort_values(by='VOL_FORCE', ascending=False)
    
    st.subheader("🔥 Live Big Bull Alerts (NSE UDiFF)")
    
    # Rename columns for the user display
    display_df = results[[mapping['SYMBOL'], mapping['CLOSE'], 'CHANGE_PCT', 'VOL_FORCE', 'STRATEGY', 'TARGET (6%)', 'STOP LOSS (3%)']]
    display_df.columns = ['SYMBOL', 'LTP', 'CHG%', 'VOL_FORCE', 'STRATEGY', 'TARGET', 'STOPLOSS']
    
    st.table(display_df)
    
    # Download Feature
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Trade Plan", data=csv, file_name=f"Mugan_Alerts_{data_date}.csv")

else:
    st.error("❌ NSE UDiFF Server unreachable. Please try again.")
    

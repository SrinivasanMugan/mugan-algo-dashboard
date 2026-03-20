import streamlit as st
import pandas as pd
from jugaad_data.nse import bhavcopy_save
from datetime import date, timedelta
import os
import time

st.set_page_config(page_title="Mugan's Big Bull Guardian", layout="wide")
st.title("🛡️ Mugan's Legacy Guardian: Titan Edition")

# --- 1. ERROR-PROOF DATA FETCHING ---
@st.cache_data(ttl=3600)
def fetch_any_nse_data():
    for i in range(1, 10): 
        try:
            target_date = date.today() - timedelta(days=i)
            if target_date.weekday() >= 5: continue
            
            csv_path = bhavcopy_save(target_date, ".")
            df = pd.read_csv(csv_path)
            # Standardize all headers: Remove spaces and make Uppercase
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            if os.path.exists(csv_path):
                os.remove(csv_path)
            return df, target_date
        except Exception:
            continue
    return None, None

df_raw, data_date = fetch_any_nse_data()

if df_raw is not None:
    # --- 2. FUZZY COLUMN MAPPING (The Fix) ---
    cols = list(df_raw.columns)
    
    # We search for keywords instead of exact matches to avoid KeyErrors
    def find_col(keywords):
        for k in keywords:
            for c in cols:
                if k in c: return c
        return None

    # Map the most likely column names for 2026 UDiFF and Legacy formats
    sym_col = find_col(['TCKRSYMB', 'SYMBOL'])
    ser_col = find_col(['SCTYSRS', 'SERIES'])
    cls_col = find_col(['CLSPRIC', 'CLOSE'])
    prv_col = find_col(['PRVSCLSGPRIC', 'PREV'])
    vol_col = find_col(['TTLTRADGVOL', 'TOTTRDQTY', 'VOLUME'])

    if not all([sym_col, ser_col, cls_col, prv_col, vol_col]):
        st.error(f"Critical Columns Missing. Found: {cols}")
    else:
        st.success(f"✅ System Online: Data for {data_date.strftime('%d %b %Y')}")
        
        # --- 3. FILTERING & STRATEGY ---
        # Only keep 'EQ' (Standard) or 'BE' (Trade-to-trade)
        df = df_raw[df_raw[ser_col].str.contains('EQ|BE', na=False, case=False)].copy()
        
        # Convert to Numeric
        for c in [cls_col, prv_col, vol_col]:
            df[c] = pd.to_numeric(df[c], errors='coerce')

        df['CHANGE_%'] = (((df[cls_col] - df[prv_col]) / df[prv_col]) * 100).round(2)
        df['VOL_FORCE'] = (df[vol_col] / df[vol_col].median()).round(2)
        
        def get_signal(row):
            # Melvin Li 'Sword' (Price + Volume Breakout)
            if row['CHANGE_%'] > 3.0 and row['VOL_FORCE'] > 2.0:
                return "🟢 BUY (THE SWORD)"
            # Jhunjhunwala 'Shield' (Value accumulation)
            elif -1.0 < row['CHANGE_%'] < 0.5 and row['VOL_FORCE'] > 1.2:
                return "🔵 HOLD (THE SHIELD)"
            return "WAIT"

        df['STRATEGY'] = df.apply(get_signal, axis=1)
        df['TARGET(6%)'] = (df[cls_col] * 1.06).round(2)
        df['STOP(3%)'] = (df[cls_col] * 0.97).round(2)

        # --- 4. FIRST-CLASS DASHBOARD ---
        results = df[df['STRATEGY'] != "WAIT"].sort_values(by='VOL_FORCE', ascending=False)
        
        # Cleaner Column Names for UI
        ui_df = results[[sym_col, cls_col, 'CHANGE_%', 'VOL_FORCE', 'STRATEGY', 'TARGET(6%)', 'STOP(3%)']]
        ui_df.columns = ['SYMBOL', 'PRICE', 'CHG%', 'VOL_FORCE', 'STRATEGY', 'TARGET', 'STOPLOSS']
        
        st.subheader("🔥 Live Buy Alerts")
        st.table(ui_df)
        
        # CSV Export
        st.download_button("📥 Download Trade Plan", ui_df.to_csv(index=False), "TradePlan.csv")
else:
    st.error("Failed to connect to NSE. Please refresh.")
        

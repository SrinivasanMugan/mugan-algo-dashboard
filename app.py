import streamlit as st
import pandas as pd
from jugaad_data.nse import bhavcopy_save
from datetime import date, timedelta
import os
import time

st.set_page_config(page_title="Mugan's Big Bull Guardian", layout="wide")
st.title("🛡️ Mugan's Legacy Guardian: Titan Edition")

# --- 1. SMART DATA FETCHING ---
@st.cache_data(ttl=3600)
def fetch_guaranteed_data():
    for i in range(1, 10): 
        try:
            target_date = date.today() - timedelta(days=i)
            if target_date.weekday() >= 5: continue
            
            csv_path = bhavcopy_save(target_date, ".")
            df = pd.read_csv(csv_path)
            
            # CRITICAL FIX: Clean and standardize all column names
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            if os.path.exists(csv_path):
                os.remove(csv_path)
            return df, target_date
        except Exception:
            continue
    return None, None

df_raw, data_date = fetch_guaranteed_data()

if df_raw is not None:
    # --- 2. DYNAMIC MAPPING (Prevents KeyError) ---
    cols = df_raw.columns
    # This finds the column even if NSE changes "SYMBOL" to "SYMB" or " SERIES"
    sym_col = next((c for c in cols if 'SYMBOL' in c), None)
    ser_col = next((c for c in cols if 'SERIES' in c), None)
    cls_col = next((c for c in cols if 'CLOSE' in c), None)
    prv_col = next((c for c in cols if 'PREV' in c), None)
    vol_col = next((c for c in cols if 'TOTTRDQTY' in c or 'VOLUME' in c), None)

    if not all([sym_col, ser_col, cls_col, prv_col, vol_col]):
        st.error(f"⚠️ NSE Format Change Detected. Columns found: {list(cols)}")
    else:
        st.success(f"✅ Data Synced: {data_date.strftime('%d %b %Y')}")
        
        # Filter for Equity (Standard and Trade-for-Trade)
        df = df_raw[df_raw[ser_col].isin(['EQ', 'BE', ' EQ', ' BE'])].copy()
        
        # --- 3. THE STRATEGY ENGINE (Concluded Logic) ---
        df['CHANGE_PCT'] = (((df[cls_col] - df[prv_col]) / df[prv_col]) * 100).round(2)
        df['VOL_FORCE'] = (df[vol_col] / df[vol_col].mean()).round(2)
        
        def apply_logic(row):
            # THE SWORD: Melvin Li Momentum
            if row['CHANGE_PCT'] > 3.0 and row['VOL_FORCE'] > 2.0:
                return "🟢 BUY (THE SWORD)"
            # THE SHIELD: Jhunjhunwala Value Dip
            elif -1.0 < row['CHANGE_PCT'] < 0.5 and row['VOL_FORCE'] > 1.2:
                return "🔵 HOLD (THE SHIELD)"
            return "WAIT"

        df['STRATEGY'] = df.apply(apply_logic, axis=1)
        df['TARGET (6%)'] = (df[cls_col] * 1.06).round(2)
        df['STOP LOSS (3%)'] = (df[cls_col] * 0.97).round(2)

        # --- 4. FIRST-CLASS DISPLAY ---
        results = df[df['STRATEGY'] != "WAIT"].sort_values(by='VOL_FORCE', ascending=False)
        
        st.subheader("🔥 Live Big Bull Alerts")
        st.table(results[[sym_col, cls_col, 'CHANGE_PCT', 'VOL_FORCE', 'STRATEGY', 'TARGET (6%)', 'STOP LOSS (3%)']])
        
        # Download Feature
        csv = results.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Trade Plan", data=csv, file_name=f"Mugan_Alerts_{data_date}.csv")

else:
    st.error("❌ NSE Server unreachable. Please try again after 6 PM IST.")
                

import streamlit as st
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import date, timedelta
from jugaad_data.nse import stock_df

# --- CONFIGURATION ---
st.set_page_config(page_title="Minervini Pro - NSE India", layout="wide")
st.title("🎯 Minervini SEPA & VCP Pro Dashboard")
st.markdown("### Powered by `jugaad-data` for the Indian Market")

# Add your core watchlist here
TICKERS = ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "SBIN", "HAL", "TATASTEEL"]

def get_minervini_pro(ticker):
    try:
        # Fetching data (400 days to cover 200 SMA and 52W High/Low)
        end_date = date.today()
        start_date = end_date - timedelta(days=400) 
        df = stock_df(symbol=ticker, from_date=start_date, to_date=end_date, series="EQ")
        
        # Sort and Clean
        df = df.sort_values('DATE').reset_index(drop=True)
        df.rename(columns={'CLOSE': 'Close', 'HIGH': 'High', 'LOW': 'Low', 'OPEN': 'Open', 'VOLUME': 'Volume'}, inplace=True)
        
        # 1. TECHNICAL INDICATORS
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_150'] = ta.sma(df['Close'], length=150)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        df['Vol_Avg'] = ta.sma(df['Volume'], length=50)
        
        # 2. TREND TEMPLATE LOGIC
        curr = df['Close'].iloc[-1]
        low_52 = df['Low'].tail(252).min()
        high_52 = df['High'].tail(252).max()
        
        c1 = curr > df['SMA_150'].iloc[-1] and curr > df['SMA_200'].iloc[-1]
        c2 = df['SMA_150'].iloc[-1] > df['SMA_200'].iloc[-1]
        c3 = df['SMA_200'].iloc[-1] > df['SMA_200'].iloc[-20]
        c4 = df['SMA_50'].iloc[-1] > df['SMA_150'].iloc[-1] and df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1]
        c5 = curr > df['SMA_50'].iloc[-1]
        c6 = curr > (low_52 * 1.30)
        c7 = curr > (high_52 * 0.75)
        
        trend_score = sum([c1, c2, c3, c4, c5, c6, c7])
        
        # 3. VCP & BREAKOUT LOGIC (THE "JUGAAD" EXTRAS)
        # Check if Volatility is Contracting (Last 5 days range < Avg Range of last 20 days)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        current_atr = df['ATR'].iloc[-1]
        avg_atr = df['ATR'].tail(20).mean()
        is_tight = "YES" if current_atr < (avg_atr * 0.8) else "No"
        
        # Check for Volume Spike (Today's Volume > 150% of 50-day average)
        vol_spike = "🚀 SPIKE" if df['Volume'].iloc[-1] > (df['Vol_Avg'].iloc[-1] * 1.5) else "Normal"
        
        return {
            "Ticker": ticker,
            "Price": f"₹{curr:,.2f}",
            "Trend": f"{trend_score}/7",
            "VCP Tightness": is_tight,
            "Vol Breakout": vol_spike,
            "Gap to High": f"{((high_52 - curr)/high_52)*100:.1f}%",
            "Data": df
        }
    except:
        return None

# --- UI DISPLAY ---
results = []
with st.spinner("Scanning NSE for Superperformers..."):
    for t in TICKERS:
        data = get_minervini_pro(t)
        if data: results.append(data)

if results:
    df_res = pd.DataFrame(results).drop(columns=['Data'])
    
    # Highlight Row if Trend is 7/7 and VCP is Tight
    def highlight_picks(val):
        color = 'background-color: #1e3d2f' if val == "7/7" else ''
        return color

    st.dataframe(df_res.style.applymap(highlight_picks, subset=['Trend']), use_container_width=True)

    # Deep Dive Visualization
    st.divider()
    choice = st.selectbox("Inspect Chart for 'Cheat' Entry:", TICKERS)
    s_data = next(x for x in results if x["Ticker"] == choice)['Data'].tail(100)
    
    fig = go.Figure(data=[go.Candlestick(x=s_data['DATE'], open=s_data['Open'], high=s_data['High'], low=s_data['Low'], close=s_data['Close'], name="Price")])
    fig.add_trace(go.Scatter(x=s_data['DATE'], y=s_data['SMA_50'], name="50 SMA", line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=s_data['DATE'], y=s_data['SMA_200'], name="200 SMA", line=dict(color='red')))
    
    fig.update_layout(height=600, template="plotly_dark", title=f"{choice} - Look for Tight Price Action & Volume Spikes")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("NSE Data fetch failed. Ensure you have an active internet connection.")

st.sidebar.markdown("""
### 📖 How to use:
1. **Trend 7/7:** The stock is in a massive uptrend.
2. **VCP Tightness = YES:** The price is 'coiling' like a spring. This is where you look for an entry.
3. **Vol Breakout = SPIKE:** Institutions are buying. 
""")

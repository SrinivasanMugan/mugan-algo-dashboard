import pandas as pd
from jugaad_data.nse import stock_df
from datetime import date, timedelta

def get_jugaad_signals(symbol):
    try:
        # 1. Fetch data from NSE (Last 6 months to ensure enough for 50 EMA)
        end_date = date.today()
        start_date = end_date - timedelta(days=180)
        
        # Pulls directly from NSE - no more Yahoo mistakes
        df = stock_df(symbol=symbol, from_date=start_date, to_date=end_date, series="EQ")
        
        if df.empty:
            return None

        # Clean and Sort (Jugaad-data returns newest first)
        df = df.sort_values('DATE').reset_index(drop=True)
        
        # 2. Calculate Technicals (EMA, RSI, Vol)
        # 50 EMA
        df['EMA_50'] = df['CLOSE'].ewm(span=50, adjust=False).mean()
        
        # RSI 14
        delta = df['CLOSE'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))
        
        # 20-Day Avg Volume
        df['Avg_Vol'] = df['VOLUME'].rolling(window=20).mean()

        latest = df.iloc[-1]
        
        # 3. Enhanced Strategy Logic (The 6% Filter)
        # Condition 1: Above 50 EMA (Long-term Trend)
        # Condition 2: RSI > 60 (Active Momentum)
        # Condition 3: Volume > 1.5x Avg (Big money entering)
        
        is_bullish = (
            (latest['CLOSE'] > latest['EMA_50']) and 
            (latest['RSI'] > 60) and 
            (latest['VOLUME'] > 1.5 * latest['Avg_Vol'])
        )

        return {
            "Stock": symbol,
            "Price": round(latest['CLOSE'], 2),
            "Signal": "BULLISH" if is_bullish else "WATCH",
            "Target (6%)": round(latest['CLOSE'] * 1.06, 2),
            "Stop Loss (3%)": round(latest['CLOSE'] * 0.97, 2),
            "RSI": round(latest['RSI'], 1),
            "Vol_Surge": round(latest['VOLUME'] / latest['Avg_Vol'], 2)
        }

    except Exception as e:
        return {"Stock": symbol, "Signal": "ERROR", "Note": str(e)}

# Run for your list
stocks = ["AARTIIND", "ACMESOLAR", "ADANIENSOL", "3MINDIA", "AAATECH", "AARVI", "ABCAPITAL"]
results = [get_jugaad_signals(s) for s in stocks]
final_df = pd.DataFrame([r for r in results if r])

print(final_df)

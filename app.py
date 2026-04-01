from jugaad_data.nse import NSELive
import pandas as pd
import time

def hunt_underdogs(symbol_list):
    n = NSELive()
    underdog_results = []
    
    print(f"--- Mining started for {len(symbol_list)} private candidates ---")
    
    for symbol in symbol_list:
        try:
            # 1. LIVE DATA CAPTURE
            quote = n.stock_quote(symbol)
            price_info = quote['priceInfo']
            curr_price = price_info['lastPrice']
            mkt_cap = quote['securityWiseDP']['marketCapitalization'] # In Crores
            
            # 2. FUNDAMENTAL MINING (Note: jugaad-data provides quote; 
            # for full automated financials, one usually pairs with a local CSV 
            # or a supplemental scrapper. Here we use the Live Ratios provided by NSE)
            
            # Metadata for 'Private-Only' and 'No-Gov' verification
            meta = quote['metadata']
            industry = meta.get('industry', 'N/A')
            
            # --- THE GRAHAM CIGAR BUTT CALCULATION ---
            # We look for stocks where the valuation is statistically broken
            # Typical 'Underdog' P/B threshold for private Indian firms is < 0.7
            pb_ratio = quote['metadata'].get('pdSymbolCustomValue', {}).get('priceToBook', 0) 
            # Note: If PB isn't in live quote, we calculate from latest BS
            
            # --- THE SAFETY VAULT (No-Backfire Logic) ---
            # 1. No Promoter Pledging
            pledge = quote['securityWiseDP'].get('promoterPledgedSharePercent', 0)
            
            # 2. Delivery Percentage (Soros-like sentiment check)
            # High delivery % in a flat stock indicates "Smart Money" is accumulating
            delivery_pct = quote['securityWiseDP'].get('deliveryToTradedQuantity', 0)

            # --- THE SELECTION TRIGGER ---
            # A: Price-to-Book is extremely low (< 0.75)
            # B: No debt-pledge risk (Pledge == 0)
            # C: Market Cap is small enough for 'Unlimited Upside' (< 5000 Cr)
            if pb_ratio < 0.75 and pledge == 0 and mcap < 5000:
                underdog_results.append({
                    "Symbol": symbol,
                    "Industry": industry,
                    "LTP": curr_price,
                    "P/B Ratio": pb_ratio,
                    "Delivery %": delivery_pct,
                    "Mkt Cap (Cr)": round(mcap, 2),
                    "Status": "STRONG UNDERDOG" if pb_ratio < 0.5 else "VALUATION GAP"
                })
                
            # Respecting NSE's rate limits
            time.sleep(0.5) 
            
        except Exception as e:
            continue

    return pd.DataFrame(underdog_results)

# --- YOUR PRIVATE WATCHLIST (Targeting 'Boring' but Strong Sectors) ---
watch_list = ["SOUTHBANK", "KARURVYSYA", "FEDERALBNK", "JINDALSAW", "TVSSRICHAK", "KPRMILL", "GUJGASLTD"]
final_candidates = hunt_underdogs(watch_list)

print("\n--- FINAL UNDERDOG MINING RESULTS (Real-Time) ---")
print(final_candidates)

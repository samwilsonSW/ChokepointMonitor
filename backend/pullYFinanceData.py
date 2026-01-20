import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. FORCE CONSOLE DISPLAY TO 4 DECIMALS ---
# This ensures that when you print(df), it shows 85.1000 instead of 85.1
pd.options.display.float_format = '{:.4f}'.format

# Ticker Configuration
# CL=F: WTI (Americas)
# BZ=F: Brent (Global / Murban Proxy)
# FRO:  Frontline (Crude Tankers / Hormuz Proxy)
# STNG: Scorpio Tankers (Product Tankers / Red Sea Proxy)
# NG=F: Natural Gas (Hormuz/Qatar Proxy)
tickers = ["CL=F", "BZ=F", "FRO", "STNG", "NG=F"]

def get_chokepoint_data():
    print(f"Fetching data for: {tickers}...")
    
    try:
        # Fetch data
        data = yf.download(tickers, period="3mo", interval="1d")['Close']
        
        if data.empty:
            raise ValueError("No data returned from yfinance")
        
        print(f"Downloaded {len(data)} rows of data")
        
        # Fill missing values
        data = data.ffill().dropna()
        
        if data.empty:
            raise ValueError("Data is empty after forward fill and dropna")
        
        print(f"After processing: {len(data)} rows")
    except Exception as e:
        print(f"ERROR: Failed to fetch data - {e}")
        raise

    # Calculate Spread
    data['Spread_Brent_WTI'] = data['BZ=F'] - data['CL=F']

    # Normalize to 100 (Index)
    normalized_data = (data / data.iloc[0]) * 100

    return data, normalized_data

if __name__ == "__main__":
    raw_df, monitor_df = get_chokepoint_data()
    
    print("\n--- Recent Chokepoint Monitor (Normalized) ---")
    print(monitor_df.tail())

    # --- 2. FORCE CSV OUTPUT TO 4 DECIMALS ---
    # The float_format='%.4f' argument forces 4 decimal places in the text file
    raw_df.to_csv("geopolitics_oil_monitor.csv", float_format='%.4f')
    monitor_df.to_csv("normalized_monitor.csv", float_format='%.4f')
    
    print("\nSaved with forced 4-decimal formatting.")
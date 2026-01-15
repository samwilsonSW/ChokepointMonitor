import yfinance as yf
import pandas as pd

# CL=F: WTI (Americas)
# BZ=F: Brent (Europe/Global)
# DBLc1: Dubai Crude (Middle East / Hormuz)
# MRBNc1: Murban Crude (Abu Dhabi / Malacca / Asian Demand)
tickers = ["CL=F", "BZ=F", "DBLc1", "MRBNc1"]

def get_chokepoint_data():
    print("Fetching global oil benchmarks...")
    # Fetching the last 30 days to see trends
    df = yf.download(tickers, period="1mo", interval="1d")['Close']
    
    # Optional: Calculate the 'Brent-WTI Spread' 
    # This is a key indicator of shipping disruption costs
    df['Brent_WTI_Spread'] = df['BZ=F'] - df['CL=F']
    
    df.to_csv("global_oil_monitor.csv")
    print("Saved to global_oil_monitor.csv")
    return df

if __name__ == "__main__":
    data = get_chokepoint_data()
    print(data.tail())
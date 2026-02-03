import yfinance as yf
import pandas as pd
from supabase_client import insert_data, _get_client

TICKERS = ["CL=F", "BZ=F", "FRO", "STNG", "NG=F"]
TABLE_NAME = 'Financial-Data-By-Date-And-Ticker'

def fetch_full_ohlc(period="3mo"):
    data = yf.download(TICKERS, period=period, interval="1d")
    
    if data.empty:
        return []
    
    data.columns.names = ['Price_Type', 'Ticker']
    
    data_stacked = data.stack(level='Ticker').reset_index()
    
    records = []
    for _, row in data_stacked.iterrows():
        records.append({
            "date": row['Date'].date().isoformat(),
            "ticker": row['Ticker'], 
            "open_price": float(row['Open']),
            "high_price": float(row['High']),
            "low_price": float(row['Low']),
            "close_price": float(row['Close']),
            "volume": int(row['Volume']) if not pd.isna(row['Volume']) else 0
        })
        
    return records

def upload_to_supabase():
    client = _get_client()
    records = fetch_full_ohlc()
    
    batch_size = 500
    total = len(records)
    print(f'Preparing to insert {total} records into {TABLE_NAME} (batch size {batch_size})')

    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]
        try:
            insert_data(TABLE_NAME, batch)
            print(f'Inserted records {i+1}-{i+len(batch)}')
        except Exception as e:
            print(f'Error inserting batch starting at {i}: {e}')
            raise

if __name__ == "__main__":
    print(fetch_full_ohlc(period="5d"))
    # upload_to_supabase()
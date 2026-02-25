import yfinance as yf
import pandas as pd
from supabase_client import insert_data, _get_client

TICKERS = ["CL=F", "BZ=F", "FRO", "STNG", "NG=F"]
TABLE_NAME = 'financial_prices_daily'

def fetch_full_ohlc(period="2y"):
    """Fetch OHLCV data for all tracked tickers.
    
    Args:
        period: yfinance period string ("2y" = 2 years, "5y" = 5 years, "max" = all available)
        
    Returns:
        List of dict records ready for database insertion
    """
    print(f"Fetching {period} of data for tickers: {TICKERS}")
    data = yf.download(TICKERS, period=period, interval="1d")
    
    if data.empty:
        print("No data returned from yfinance")
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
    
    print(f"Prepared {len(records)} records for insertion")
    return records

def upload_to_supabase(period="2y"):
    """Fetch financial data and upload to Supabase.
    Uses upsert to handle duplicates gracefully.
    """
    client = _get_client()
    records = fetch_full_ohlc(period=period)
    
    if not records:
        print("No records to insert")
        return
    
    batch_size = 500
    total = len(records)
    inserted = 0
    errors = 0
    
    print(f'Preparing to insert {total} records into {TABLE_NAME} (batch size {batch_size})')

    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]
        try:
            # Use upsert to handle duplicates
            response = client.table(TABLE_NAME).upsert(batch).execute()
            inserted += len(batch)
            print(f'Upserted records {i+1}-{i+len(batch)}')
        except Exception as e:
            print(f'Error upserting batch starting at {i}: {e}')
            errors += len(batch)
    
    print(f"\nComplete: {inserted} records upserted, {errors} errors")

if __name__ == "__main__":
    # For testing: fetch 5 days without uploading
    # print(fetch_full_ohlc(period="5d"))
    
    # For production: upload 2 years of data
    upload_to_supabase(period="2y")
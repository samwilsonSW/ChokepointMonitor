"""Financial data ingestion from Yahoo Finance.

Fetches daily OHLCV data for commodities and tanker equities,
stores in Supabase for correlation analysis with conflict events.
"""

import yfinance as yf
import pandas as pd
from supabase_client import insert_data, _get_client

# Tickers we track:
# CL=F = WTI Crude Oil
# BZ=F = Brent Crude Oil  
# FRO = Frontline (tanker company)
# STNG = Scorpio Tankers
# NG=F = Natural Gas (less relevant for Hormuz but tracking anyway)
TICKERS = ["CL=F", "BZ=F", "FRO", "STNG", "NG=F"]

# New normalized table name
TABLE_NAME = 'financial_prices_daily'


def fetch_full_ohlc(period="2y"):
    """
    Fetch OHLCV data for all tracked tickers.
    
    Args:
        period: yfinance period string ("2y" = 2 years, "5y" = 5 years, "max" = all available)
        
    Returns:
        List of dict records ready for database insertion
    """
    print(f"Fetching {period} of data for tickers: {TICKERS}")
    data = yf.download(TICKERS, period=period, interval="1d", group_by='ticker')
    
    if data.empty:
        print("No data returned from yfinance")
        return []
    
    records = []
    
    # Handle single ticker vs multiple tickers
    if len(TICKERS) == 1:
        ticker = TICKERS[0]
        for date_idx, row in data.iterrows():
            records.append({
                "date": date_idx.date().isoformat(),
                "ticker": ticker,
                "open_price": float(row['Open']) if not pd.isna(row['Open']) else None,
                "high_price": float(row['High']) if not pd.isna(row['High']) else None,
                "low_price": float(row['Low']) if not pd.isna(row['Low']) else None,
                "close_price": float(row['Close']) if not pd.isna(row['Close']) else None,
                "volume": int(row['Volume']) if not pd.isna(row['Volume']) else 0
            })
    else:
        # Multi-ticker format
        for ticker in TICKERS:
            if ticker not in data.columns.levels[0]:
                print(f"Warning: No data for ticker {ticker}")
                continue
                
            ticker_data = data[ticker]
            for date_idx, row in ticker_data.iterrows():
                if pd.isna(row['Close']):
                    continue  # Skip days with no trading data
                    
                records.append({
                    "date": date_idx.date().isoformat(),
                    "ticker": ticker,
                    "open_price": float(row['Open']) if not pd.isna(row['Open']) else None,
                    "high_price": float(row['High']) if not pd.isna(row['High']) else None,
                    "low_price": float(row['Low']) if not pd.isna(row['Low']) else None,
                    "close_price": float(row['Close']),
                    "volume": int(row['Volume']) if not pd.isna(row['Volume']) else 0
                })
    
    print(f"Prepared {len(records)} records for insertion")
    return records


def upload_to_supabase(period="2y"):
    """
    Fetch financial data and upload to Supabase.
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


def get_price_range(ticker, start_date, end_date):
    """
    Get price data for a specific ticker and date range.
    
    Args:
        ticker: Ticker symbol (e.g., "BZ=F")
        start_date: ISO date string (YYYY-MM-DD)
        end_date: ISO date string (YYYY-MM-DD)
        
    Returns:
        List of price records
    """
    client = _get_client()
    
    response = (
        client.table(TABLE_NAME)
        .select("*")
        .eq("ticker", ticker)
        .gte("date", start_date)
        .lte("date", end_date)
        .order("date")
        .execute()
    )
    
    return response.data


def get_latest_prices():
    """
    Get the most recent price for each ticker.
    
    Returns:
        Dict mapping ticker to latest price record
    """
    client = _get_client()
    latest = {}
    
    for ticker in TICKERS:
        response = (
            client.table(TABLE_NAME)
            .select("*")
            .eq("ticker", ticker)
            .order("date", desc=True)
            .limit(1)
            .execute()
        )
        
        if response.data:
            latest[ticker] = response.data[0]
    
    return latest


if __name__ == "__main__":
    # For testing: fetch 5 days without uploading
    # print(fetch_full_ohlc(period="5d"))
    
    # For production: upload 2 years of data
    upload_to_supabase(period="2y")

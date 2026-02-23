-- Financial Prices Daily Table
-- Stores daily OHLCV data for commodities and equities

CREATE TABLE IF NOT EXISTS financial_prices_daily (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    open_price DECIMAL(12, 4),
    high_price DECIMAL(12, 4),
    low_price DECIMAL(12, 4),
    close_price DECIMAL(12, 4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicates
    CONSTRAINT unique_date_ticker UNIQUE (date, ticker)
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_financial_prices_date 
ON financial_prices_daily(date);

CREATE INDEX IF NOT EXISTS idx_financial_prices_ticker 
ON financial_prices_daily(ticker);

CREATE INDEX IF NOT EXISTS idx_financial_prices_ticker_date 
ON financial_prices_daily(ticker, date);

-- Comments for documentation
COMMENT ON TABLE financial_prices_daily IS 'Daily OHLCV prices for commodities and tanker equities';
COMMENT ON COLUMN financial_prices_daily.ticker IS 'Ticker symbol: CL=F (WTI), BZ=F (Brent), FRO, STNG, NG=F';

-- Migrate data from old table if it exists
-- NOTE: Run this manually after creating the new table
-- INSERT INTO financial_prices_daily (date, ticker, open_price, high_price, low_price, close_price, volume)
-- SELECT date, ticker, open_price, high_price, low_price, close_price, volume
-- FROM "Financial-Data-By-Date-And-Ticker"
-- ON CONFLICT (date, ticker) DO NOTHING;

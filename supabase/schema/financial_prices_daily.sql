-- Financial Prices Daily Table
-- Stores daily OHLCV data for commodities and tanker equities
-- Replaces: "Financial-Data-By-Date-And-Ticker" (deprecated)

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

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_financial_prices_updated_at ON financial_prices_daily;

CREATE TRIGGER update_financial_prices_updated_at
    BEFORE UPDATE ON financial_prices_daily
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS
ALTER TABLE financial_prices_daily ENABLE ROW LEVEL SECURITY;

-- Allow anonymous reads (price data is public)
CREATE POLICY "Allow anonymous read access" 
ON financial_prices_daily 
FOR SELECT 
TO anon, authenticated 
USING (true);

-- Comments for documentation
COMMENT ON TABLE financial_prices_daily IS 'Daily OHLCV prices for commodities and tanker equities. Replaces Financial-Data-By-Date-And-Ticker.';
COMMENT ON COLUMN financial_prices_daily.ticker IS 'Ticker symbol: CL=F (WTI), BZ=F (Brent), FRO (Frontline), STNG (Scorpio Tankers), NG=F (Natural Gas)';

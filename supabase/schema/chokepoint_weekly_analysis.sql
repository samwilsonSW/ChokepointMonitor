CREATE OR REPLACE VIEW chokepoint_weekly_analysis AS
WITH 
-- ACLED week definition: Saturday to Friday
-- Date_trunc('week') returns Monday, so we add 5 days to get to Saturday
acled_weeks AS (
    SELECT DISTINCT 
        (date_trunc('week', week::date) + interval '5 days')::date as acled_week
    FROM "ACLED-Aggregated-Conflict-Data"
    UNION
    SELECT DISTINCT
        (date_trunc('week', date) + interval '5 days')::date as acled_week
    FROM financial_prices_daily
),
-- Financial data aggregated to ACLED weeks
weekly_financials AS (
    SELECT 
        (date_trunc('week', date) + interval '5 days')::date AS acled_week,
        ticker,
        MIN(date) as week_start_date,
        MAX(date) as week_end_date,
        -- Get opening price from first trading day of week
        (SELECT open_price 
         FROM financial_prices_daily f2 
         WHERE f2.ticker = f1.ticker 
           AND f2.date >= (date_trunc('week', f1.date) + interval '5 days')::date
           AND f2.date < (date_trunc('week', f1.date) + interval '12 days')::date
         ORDER BY f2.date ASC 
         LIMIT 1) as weekly_open,
        -- Get closing price from last trading day of week
        (SELECT close_price 
         FROM financial_prices_daily f2 
         WHERE f2.ticker = f1.ticker 
           AND f2.date >= (date_trunc('week', f1.date) + interval '5 days')::date
           AND f2.date < (date_trunc('week', f1.date) + interval '12 days')::date
         ORDER BY f2.date DESC 
         LIMIT 1) as weekly_close,
        MAX(high_price) AS weekly_high,
        MIN(low_price) AS weekly_low,
        ROUND(AVG(close_price), 4) AS avg_close
    FROM financial_prices_daily f1
    GROUP BY 
        (date_trunc('week', date) + interval '5 days')::date,
        ticker
),
-- Conflict data by ACLED week and region
chokepoint_events AS (
    SELECT 
        (date_trunc('week', week::date) + interval '5 days')::date as acled_week,
        -- Red Sea region
        COUNT(*) FILTER (WHERE country IN ('Egypt', 'Sudan', 'Eritrea', 'Djibouti', 'Saudi Arabia', 'Yemen', 'Jordan', 'Israel')) as red_sea_events,
        SUM(fatalities) FILTER (WHERE country IN ('Egypt', 'Sudan', 'Eritrea', 'Djibouti', 'Saudi Arabia', 'Yemen', 'Jordan', 'Israel')) as red_sea_fatalities,
        -- Persian Gulf region  
        COUNT(*) FILTER (WHERE country IN ('Iran', 'Iraq', 'Kuwait', 'Bahrain', 'Qatar', 'United Arab Emirates', 'Oman', 'Saudi Arabia')) as persian_gulf_events,
        SUM(fatalities) FILTER (WHERE country IN ('Iran', 'Iraq', 'Kuwait', 'Bahrain', 'Qatar', 'United Arab Emirates', 'Oman', 'Saudi Arabia')) as persian_gulf_fatalities,
        -- Malacca region
        COUNT(*) FILTER (WHERE country IN ('Indonesia', 'Malaysia', 'Singapore', 'Thailand')) as malacca_events,
        SUM(fatalities) FILTER (WHERE country IN ('Indonesia', 'Malaysia', 'Singapore', 'Thailand')) as malacca_fatalities,
        -- Totals
        COUNT(*) as total_relevant_events,
        SUM(fatalities) as total_fatalities
    FROM "ACLED-Aggregated-Conflict-Data"
    WHERE country IN (
        'Egypt', 'Sudan', 'Eritrea', 'Djibouti', 'Saudi Arabia', 'Yemen', 'Jordan', 'Israel',
        'Iran', 'Iraq', 'Kuwait', 'Bahrain', 'Qatar', 'United Arab Emirates', 'Oman',
        'Somalia', 'Pakistan', 'Indonesia', 'Malaysia', 'Singapore', 'Thailand'
    )
    GROUP BY (date_trunc('week', week::date) + interval '5 days')::date
)
SELECT 
    w.acled_week,
    f.ticker,
    f.weekly_open,
    f.weekly_close,
    f.weekly_high,
    f.weekly_low,
    f.avg_close,
    -- Simple range volatility: how much did price swing this week?
    ROUND(((f.weekly_high - f.weekly_low) / NULLIF(f.weekly_low, 0)) * 100, 2) as range_volatility_pct,
    -- Weekly price change
    ROUND(((f.weekly_close - f.weekly_open) / NULLIF(f.weekly_open, 0)) * 100, 2) as weekly_change_pct,
    -- Regional conflict data (COALESCE to 0 for weeks with no events)
    COALESCE(c.red_sea_events, 0) as red_sea_events,
    COALESCE(c.red_sea_fatalities, 0) as red_sea_fatalities,
    COALESCE(c.persian_gulf_events, 0) as persian_gulf_events,
    COALESCE(c.persian_gulf_fatalities, 0) as persian_gulf_fatalities,
    COALESCE(c.malacca_events, 0) as malacca_events,
    COALESCE(c.malacca_fatalities, 0) as malacca_fatalities,
    COALESCE(c.total_relevant_events, 0) as total_events,
    COALESCE(c.total_fatalities, 0) as total_fatalities
FROM acled_weeks w
LEFT JOIN weekly_financials f ON w.acled_week = f.acled_week
LEFT JOIN chokepoint_events c ON w.acled_week = c.acled_week
WHERE f.ticker IS NOT NULL  -- Only return weeks where we have price data
ORDER BY w.acled_week, f.ticker;

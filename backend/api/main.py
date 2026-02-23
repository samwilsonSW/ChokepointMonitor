from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import date, timedelta
from typing import Optional
from .fetch_conflict_events import fetch_conflict_events, conflicts_to_geojson
from .chokepoint_metrics import fetch_chokepoint_metrics
from .correlation_engine import (
    calculate_correlation_summary,
    compare_lags,
    fetch_prices
)

app = FastAPI(title="Chokepoint Monitor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/conflicts")
def get_conflicts(start_date: str = None):
  rows = fetch_conflict_events(start_date=start_date)
  geojson = conflicts_to_geojson(rows)
  return geojson


@app.get("/chokepoint-metrics")
def get_chokepoint_metrics(start_date: str = None):
    """
    Get aggregated conflict metrics for each chokepoint region.

    Returns metrics including event counts, fatalities, risk levels,
    and geospatial data for rendering region polygons and badges.
    """
    metrics = fetch_chokepoint_metrics(start_date=start_date)
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": m["geojson_polygon"],
                "properties": {
                    "name": m["name"],
                    "display_name": m["display_name"],
                    "center_lat": m["center_lat"],
                    "center_lon": m["center_lon"],
                    "event_count": m["event_count"],
                    "total_events": m["total_events"],
                    "total_fatalities": m["total_fatalities"],
                    "last_event_date": m["last_event_date"],
                    "risk_level": m["risk_level"]
                }
            }
            for m in metrics
        ]
    }


@app.get("/prices")
def get_prices(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get historical price data for a ticker.

    Args:
        ticker: Ticker symbol (e.g., 'BZ=F', 'CL=F', 'FRO', 'STNG')
        start_date: Start date (YYYY-MM-DD), defaults to 1 year ago
        end_date: End date (YYYY-MM-DD), defaults to today

    Returns:
        List of daily price records
    """
    if not end_date:
        end_date = date.today().isoformat()
    if not start_date:
        start_date = (date.today() - timedelta(days=365)).isoformat()

    prices = fetch_prices(ticker, start_date, end_date)
    return {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "count": len(prices),
        "data": prices
    }


@app.get("/correlation")
def get_correlation(
    chokepoint: str,
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    window_days: int = 30,
    lag_days: int = 0
):
    """
    Calculate correlation between chokepoint conflict intensity and price changes.

    Args:
        chokepoint: Chokepoint region ('bab-el-mandeb', 'strait-of-hormuz', 'strait-of-malacca')
        ticker: Financial ticker (e.g., 'BZ=F', 'CL=F', 'FRO', 'STNG')
        start_date: Analysis start date (YYYY-MM-DD), defaults to 1 year ago
        end_date: Analysis end date (YYYY-MM-DD), defaults to today
        window_days: Rolling window size for correlation calculation (default: 30)
        lag_days: Days to lag conflict data (default: 0, meaning same-day correlation)

    Returns:
        Correlation summary with time series and statistics
    """
    if not end_date:
        end_date = date.today().isoformat()
    if not start_date:
        start_date = (date.today() - timedelta(days=365)).isoformat()

    result = calculate_correlation_summary(
        chokepoint=chokepoint,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        window_days=window_days,
        lag_days=lag_days
    )

    return result


@app.get("/correlation/lag-analysis")
def get_lag_analysis(
    chokepoint: str,
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    window_days: int = 30,
    max_lag: int = 5
):
    """
    Compare correlations at different lag periods to find optimal reaction time.

    Tests lags from 0 to max_lag days to see how quickly markets react to conflict events.

    Args:
        chokepoint: Chokepoint region
        ticker: Financial ticker
        start_date: Analysis start date
        end_date: Analysis end date
        window_days: Rolling window size
        max_lag: Maximum lag days to test (default: 5)

    Returns:
        Comparison of correlations at different lags, with optimal lag identified
    """
    if not end_date:
        end_date = date.today().isoformat()
    if not start_date:
        start_date = (date.today() - timedelta(days=365)).isoformat()

    result = compare_lags(
        chokepoint=chokepoint,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        window_days=window_days,
        max_lag=max_lag
    )

    return result


# If no endpoint is found ({BASE_URL}/conflicts for example), look in frontend for file
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    # This tells uvicorn to run the "app" object in this file
    uvicorn.run(app, host="0.0.0.0", port=8000)

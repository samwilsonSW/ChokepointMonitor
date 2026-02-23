"""Correlation calculation between conflict events and financial prices.

Supports multiple analysis types:
- Rolling window correlations (chronic risk)
- Event-window analysis (acute spikes)
- Lag analysis (how quickly markets react)
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from scipy import stats
import numpy as np
from ..supabase_client import _get_client


def fetch_conflict_intensity(chokepoint: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Calculate daily conflict intensity for a chokepoint region.
    
    Intensity = sum of (events + weighted_fatalities) per day
    
    Args:
        chokepoint: 'bab-el-mandeb', 'strait-of-hormuz', 'strait-of-malacca'
        start_date: ISO date string
        end_date: ISO date string
        
    Returns:
        List of daily intensity records
    """
    client = _get_client()
    
    # Get the region's bounding box
    region_response = (
        client.table("chokepoint_regions")
        .select("bounding_box")
        .eq("name", chokepoint)
        .execute()
    )
    
    if not region_response.data:
        return []
    
    bbox = region_response.data[0]["bounding_box"]
    
    # Aggregate conflicts by date within bounding box
    # Note: Full polygon containment would require PostGIS, using bbox for performance
    response = (
        client.table("conflict_events_enriched")
        .select("week, no_of_events, fatalities")
        .gte("week", start_date)
        .lte("week", end_date)
        .gte("longitude", bbox[0])
        .lte("longitude", bbox[2])
        .gte("latitude", bbox[1])
        .lte("latitude", bbox[3])
        .execute()
    )
    
    # Aggregate by date
    daily_intensity = {}
    for row in response.data:
        day = row["week"]
        events = row.get("no_of_events") or 0
        fatalities = row.get("fatalities") or 0
        
        # Weight fatalities more heavily (10x multiplier)
        intensity = events + (fatalities * 10)
        
        if day not in daily_intensity:
            daily_intensity[day] = 0
        daily_intensity[day] += intensity
    
    # Convert to sorted list
    result = [
        {"date": d, "intensity": i}
        for d, i in sorted(daily_intensity.items())
    ]
    
    return result


def fetch_prices(ticker: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Fetch daily closing prices for a ticker.
    
    Args:
        ticker: Ticker symbol (e.g., 'BZ=F', 'CL=F', 'FRO')
        start_date: ISO date string
        end_date: ISO date string
        
    Returns:
        List of daily price records
    """
    client = _get_client()
    
    response = (
        client.table("financial_prices_daily")
        .select("date, close_price")
        .eq("ticker", ticker)
        .gte("date", start_date)
        .lte("date", end_date)
        .order("date")
        .execute()
    )
    
    return response.data


def calculate_price_changes(prices: List[Dict[str, Any]], 
                           change_type: str = "absolute") -> List[Dict[str, Any]]:
    """
    Calculate daily price changes.
    
    Args:
        prices: List of price records with 'date' and 'close_price'
        change_type: 'absolute' (dollar change), 'percent' (percent change), 'log' (log return)
        
    Returns:
        List of price change records
    """
    if len(prices) < 2:
        return []
    
    changes = []
    
    for i in range(1, len(prices)):
        prev = prices[i - 1]
        curr = prices[i]
        
        prev_price = prev.get("close_price")
        curr_price = curr.get("close_price")
        
        if prev_price is None or curr_price is None or prev_price == 0:
            continue
        
        if change_type == "absolute":
            change = curr_price - prev_price
        elif change_type == "percent":
            change = ((curr_price - prev_price) / prev_price) * 100
        elif change_type == "log":
            change = np.log(curr_price / prev_price)
        else:
            change = curr_price - prev_price
        
        changes.append({
            "date": curr["date"],
            "price": curr_price,
            "change": change,
            "prev_price": prev_price
        })
    
    return changes


def calculate_rolling_correlation(conflict_data: List[Dict[str, Any]],
                                  price_changes: List[Dict[str, Any]],
                                  window_days: int = 30,
                                  lag_days: int = 0) -> List[Dict[str, Any]]:
    """
    Calculate rolling correlation between conflict intensity and price changes.
    
    Args:
        conflict_data: Daily intensity records
        price_changes: Daily price change records
        window_days: Size of rolling window
        lag_days: Shift conflict data forward by N days (how long markets take to react)
        
    Returns:
        List of correlation records with date, coefficient, p-value
    """
    # Convert to dicts for easy lookup
    conflict_by_date = {c["date"]: c["intensity"] for c in conflict_data}
    price_by_date = {p["date"]: p["change"] for p in price_changes}
    
    # Get all dates
    all_dates = sorted(set(conflict_by_date.keys()) | set(price_by_date.keys()))
    
    results = []
    
    for i in range(len(all_dates)):
        current_date = all_dates[i]
        
        # Get window dates
        window_start_idx = max(0, i - window_days + 1)
        window_dates = all_dates[window_start_idx:i+1]
        
        if len(window_dates) < 10:  # Need minimum data points
            continue
        
        # Build paired data for this window
        conflict_vals = []
        price_vals = []
        
        for d in window_dates:
            # Apply lag: conflict on day X correlates with price on day X+lag
            conflict_date = d
            price_date_obj = datetime.strptime(d, "%Y-%m-%d") + timedelta(days=lag_days)
            price_date = price_date_obj.strftime("%Y-%m-%d")
            
            if conflict_date in conflict_by_date and price_date in price_by_date:
                conflict_vals.append(conflict_by_date[conflict_date])
                price_vals.append(price_by_date[price_date])
        
        if len(conflict_vals) < 10:
            continue
        
        # Calculate correlation
        if np.std(conflict_vals) > 0 and np.std(price_vals) > 0:
            corr, p_value = stats.pearsonr(conflict_vals, price_vals)
            
            results.append({
                "date": current_date,
                "correlation": corr,
                "p_value": p_value,
                "sample_size": len(conflict_vals),
                "window_days": window_days,
                "lag_days": lag_days
            })
    
    return results


def calculate_correlation_summary(chokepoint: str,
                                  ticker: str,
                                  start_date: str,
                                  end_date: str,
                                  window_days: int = 30,
                                  lag_days: int = 0) -> Dict[str, Any]:
    """
    Calculate comprehensive correlation summary.
    
    Args:
        chokepoint: Chokepoint region name
        ticker: Financial ticker
        start_date: Analysis start date
        end_date: Analysis end date
        window_days: Rolling window size
        lag_days: Days to lag conflict data
        
    Returns:
        Summary dict with correlation stats and time series
    """
    # Fetch data
    conflict_data = fetch_conflict_intensity(chokepoint, start_date, end_date)
    prices = fetch_prices(ticker, start_date, end_date)
    
    if not conflict_data or not prices:
        return {
            "error": "Insufficient data",
            "chokepoint": chokepoint,
            "ticker": ticker,
            "conflict_points": len(conflict_data),
            "price_points": len(prices)
        }
    
    # Calculate price changes
    price_changes = calculate_price_changes(prices, change_type="percent")
    
    # Calculate rolling correlation
    rolling_corr = calculate_rolling_correlation(
        conflict_data, price_changes, window_days, lag_days
    )
    
    if not rolling_corr:
        return {
            "error": "Could not calculate correlation",
            "chokepoint": chokepoint,
            "ticker": ticker
        }
    
    # Calculate overall summary stats
    correlations = [r["correlation"] for r in rolling_corr if not np.isnan(r["correlation"])]
    
    summary = {
        "chokepoint": chokepoint,
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "window_days": window_days,
        "lag_days": lag_days,
        "summary": {
            "mean_correlation": np.mean(correlations) if correlations else None,
            "max_correlation": np.max(correlations) if correlations else None,
            "min_correlation": np.min(correlations) if correlations else None,
            "latest_correlation": correlations[-1] if correlations else None,
            "significant_periods": sum(1 for r in rolling_corr if r["p_value"] < 0.05)
        },
        "time_series": rolling_corr
    }
    
    return summary


def compare_lags(chokepoint: str,
                 ticker: str,
                 start_date: str,
                 end_date: str,
                 window_days: int = 30,
                 max_lag: int = 5) -> Dict[str, Any]:
    """
    Compare correlations at different lag periods to find optimal reaction time.
    
    Args:
        chokepoint: Chokepoint region name
        ticker: Financial ticker
        start_date: Analysis start date
        end_date: Analysis end date
        window_days: Rolling window size
        max_lag: Maximum lag days to test (0 to max_lag)
        
    Returns:
        Comparison of correlations at different lags
    """
    results = {}
    
    for lag in range(max_lag + 1):
        summary = calculate_correlation_summary(
            chokepoint, ticker, start_date, end_date, window_days, lag
        )
        
        if "error" not in summary:
            results[f"lag_{lag}d"] = {
                "mean_correlation": summary["summary"]["mean_correlation"],
                "latest_correlation": summary["summary"]["latest_correlation"],
                "significant_periods": summary["summary"]["significant_periods"]
            }
    
    # Find optimal lag
    best_lag = max(results.items(), key=lambda x: abs(x[1]["mean_correlation"])) if results else None
    
    return {
        "chokepoint": chokepoint,
        "ticker": ticker,
        "window_days": window_days,
        "lag_comparison": results,
        "optimal_lag_days": int(best_lag[0].split("_")[1].replace("d", "")) if best_lag else None,
        "optimal_correlation": best_lag[1]["mean_correlation"] if best_lag else None
    }

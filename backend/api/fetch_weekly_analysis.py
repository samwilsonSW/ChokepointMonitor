"""
Dataset fetch for a correlation between financial fetch and conflict events.

Provides weekly batched financial information on select tickers, collapsing daily financial
information into weekly averages, highs, lows, volatility percentages, as well as 
chokepoint based count of events, fatalities, and 'pending' for weeks that don't yet have data.
"""


from ..supabase_client import _get_client
from typing import List, Dict, Any

def fetch_weekly_analysis() -> List[Dict[str, Any]]:
    """
    Fetch all weekly aggregated conflict and financial data from the view.
    Synchronous function to run in executor.
    Client filters by date range and ticker as needed.
    """
    client = _get_client()

    response = (
        client
        .table("chokepoint_weekly_analysis")
        .select("*")
        .order("acled_week")
        .order("ticker")
        .execute()
    )
    
    return response.data

"""
Dataset fetch for a correlation between financial fetch and conflict events.

Provides weekly batched financial information on select tickers, collapsing daily financial
information into weekly averages, highs, lows, volatility percentages, as well as 
chokepoint based count of events, fatalities, and 'pending' for weeks that don't yet have data.
"""


from ..supabase_client import _get_client
from typing import List, Dict, Any


def fetch_weekly_analysis(start_week: str = None, end_week: str = None) -> List[Dict[str, Any]]:
    """
    Fetch all weekly aggregated conflict and financial data from the view.
    Synchronous function to run in executor.
    Client filters by date range and ticker as needed.
    """
    client = _get_client()

    query = client.table("chokepoint_weekly_analysis").select("*")

    if start_week:
        query = query.gte("acled_week", start_week)
    if end_week:
        query = query.lte("acled_week", end_week)

    response = query.order("acled_week").execute()

    return response.data

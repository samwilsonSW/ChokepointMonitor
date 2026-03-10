"""
Dataset fetch for a correlation between financial fetch and conflict events.

Provides weekly batched financial information on select tickers, collapsing daily financial
information into weekly averages, highs, lows, volatility percentages, as well as 
chokepoint based count of events, fatalities, and 'pending' for weeks that don't yet have data.
"""


from ..supabase_client import _get_client
from typing import List, Dict, Any

def fetch_weekly_analysis(start_week: str, end_week: str) -> List[Dict[str, Any]]:
    """
    Fetch weekly aggregated conflict and financial data from the view `chokepoint_weekly_analysis`.
    Synchronous function to run in executor.
    """
    # response = supabase_client.table("chokepoint_weekly_analysis") \
    #     .select("*") \
    #     .eq("ticker", ticker) \
    #     .gte("acled_week", start_week) \
    #     .lte("acled_week", end_week) \
    #     .order("acled_week") \
    #     .execute()

    var client = _get_client()

    query = (
        client
        .table("chokepoint_weekly_analysis") \
        .select("*")
        .gte("acled_week", start_week)
        .order("acled_week", end_week)
        .order("acled_week") \
        .execute();
    )
    
    return response.data
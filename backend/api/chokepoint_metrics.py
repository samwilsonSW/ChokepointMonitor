"""Chokepoint metrics calculation for geospatial conflict analysis.

Provides aggregated conflict statistics for defined chokepoint regions,
including event counts, fatalities, and risk scoring.
"""

from datetime import date, datetime, timezone
from typing import List, Dict, Any
from ..supabase_client import _get_client


def fetch_chokepoint_regions() -> List[Dict[str, Any]]:
    """
    Fetch chokepoint region definitions (polygons, centers) without metrics.
    Used for client-side metric calculation.
    """
    try:
        client = _get_client()
        regions_response = client.table("chokepoint_regions").select("*").execute()
        return regions_response.data or []
    except Exception as e:
        print(f"Error fetching chokepoint regions: {e}")
        raise


def fetch_chokepoint_metrics(start_date: str = None) -> List[Dict[str, Any]]:
    """
    Calculate conflict metrics for each chokepoint region.
    
    For each defined chokepoint polygon:
    - Count total conflict events within the region
    - Sum fatalities
    - Find most recent event date
    - Calculate a composite risk score
    
    Args:
        start_date: Optional ISO date string (YYYY-MM-DD) to filter events from
        
    Returns:
        List of dicts with metrics per chokepoint region
    """
    client = _get_client()

    # user is "session_user", RPC was very upset by all this (annoying)
    # print(client.rpc("whoami", {}).execute().data)
    
    # Default to 3 years ago if no start date
    if start_date and start_date not in ["[object Object]", "null", ""]:
        try:
            filter_date = date.fromisoformat(start_date)
        except ValueError:
            filter_date = date(datetime.now().year - 3, 1, 1)
    else:
        filter_date = date(datetime.now().year - 3, 1, 1)
    
    filter_date_str = filter_date.isoformat()
    
    # Fetch all chokepoint regions
    regions_response = client.table("chokepoint_regions").select("*").execute()
    regions = regions_response.data
    
    if not regions:
        return []
    
    metrics = []
    
    for region in regions:
        region_name = region["name"]
        display_name = region["display_name"]
        center_lat = region["center_lat"]
        center_lon = region["center_lon"]
        bbox = region["bounding_box"]
        
        payload = {
            "filter_date": filter_date_str,
            "region_geojson": region["geojson_polygon"],
            "min_lon": float(bbox[0]),
            "min_lat": float(bbox[1]),
            "max_lon": float(bbox[2]),
            "max_lat": float(bbox[3]),
        }

        result = client.rpc("region_conflict_stats", payload).execute()
        
        # If rpc doesn't work, fallback to Python-side filtering
        if not result.data:
            # Fallback: fetch all events in bounding box, filter in Python
            events_response = (
                client.table("conflict_events_enriched")
                .select("week, no_of_events, fatalities, latitude, longitude")
                .gte("week", filter_date_str)
                .gte("longitude", bbox[0])
                .lte("longitude", bbox[2])
                .gte("latitude", bbox[1])
                .lte("latitude", bbox[3])
                .execute()
            )
            
            events = events_response.data
            
            # Manual polygon containment check (less efficient but works without PostGIS functions)
            import json
            polygon = json.loads(region["geojson_polygon"])
            contained_events = [
                e for e in events 
                if _point_in_polygon(e["longitude"], e["latitude"], polygon["coordinates"][0])
            ]
            
            event_count = len(contained_events)
            total_events = sum(e.get("no_of_events", 0) or 0 for e in contained_events)
            total_fatalities = sum(e.get("fatalities", 0) or 0 for e in contained_events)
            last_event_date = max(
                (e["week"] for e in contained_events if e.get("week")), 
                default=None
            )
            
        else:
            stats = result.data[0] if result.data else {}
            event_count = stats.get("event_count", 0) or 0
            total_events = stats.get("total_events", 0) or 0
            total_fatalities = stats.get("total_fatalities", 0) or 0
            last_event_date = stats.get("last_event_date")
        
        # Calculate risk level based on event density and recency
        risk_level = _calculate_risk_level(event_count, total_fatalities, last_event_date)
        
        metrics.append({
            "name": region_name,
            "display_name": display_name,
            "center_lat": center_lat,
            "center_lon": center_lon,
            "event_count": event_count,
            "total_events": total_events,
            "total_fatalities": int(total_fatalities),
            "last_event_date": last_event_date,
            "risk_level": risk_level,
            "geojson_polygon": region["geojson_polygon"]
        })
    
    return metrics


def _point_in_polygon(lon: float, lat: float, polygon: List[List[float]]) -> bool:
    """
    Ray casting algorithm to check if point is inside polygon.
    Simple implementation for fallback when PostGIS not available.
    """
    n = len(polygon)
    inside = False
    j = n - 1
    
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    
    return inside


def _calculate_risk_level(event_count: int, fatalities: int, last_event_date: str) -> str:
    """
    Calculate risk level based on event metrics.
    
    Risk scoring:
    - high: >20 events OR >50 fatalities OR event within last 7 days
    - medium: 5-20 events OR 10-50 fatalities OR event within last 30 days
    - low: <5 events AND <10 fatalities AND no recent events
    """
    if event_count == 0:
        return "none"
    
    # Check recency
    if last_event_date:
        try:
            last_date = datetime.fromisoformat(last_event_date.replace('Z', '+00:00')).date()
            days_since = (date.today() - last_date).days
            
            if days_since <= 7:
                return "high"
            if days_since <= 30 and event_count >= 5:
                return "medium"
        except:
            pass
    
    # Check volume thresholds
    if event_count > 20 or fatalities > 50:
        return "high"
    if event_count >= 5 or fatalities >= 10:
        return "medium"
    
    return "low"

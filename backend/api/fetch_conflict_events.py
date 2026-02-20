"""Utilities to fetch conflict events and convert to GeoJSON.

Use package-relative imports so this module works when the package
`backend` is imported or when running as a module (recommended):

    python -m backend.api.main

"""
from datetime import date, datetime, timezone
from ..supabase_client import _get_client
def fetch_conflict_events(start_date: str = None):
    today = date.today()
    if start_date:
        start_date_obj = date.fromisoformat(start_date)
        start_date_str = start_date
    else:
        start_date_obj = date(today.year - 3, 1, 1)      # for recency math
        start_date_str = start_date_obj.isoformat()      # for Supabase query
    print("start date:")
    print(start_date_str)
    client = _get_client()
    all_rows = []
    
    
    PAGE_SIZE = 1000
    offset = 0

    while True:
        query = (
            client
            .table("conflict_events_enriched")
            .select("week, country, country_admin, event_type, sub_event_type, no_of_events, fatalities, disorder_type, acled_id, latitude, longitude, effective_latitude, effective_longitude") 
            .gte("week", start_date_str)
            .order("week", desc=False)
            .range(offset, offset + PAGE_SIZE - 1)
        )

        response = query.execute()
        rows = response.data

        if not rows:
            break

        all_rows.extend(rows)
        offset += PAGE_SIZE
        
        if len(rows) < PAGE_SIZE:
            break

    all_rows = compute_recency_for_heatmap(all_rows, start_date_obj)
    return all_rows

def conflicts_to_geojson(rows):
    """ 
    In order for MapLibre to work, this is the object we need (GeoJSON FeatureCollection)
    Adds meta.data_through = max(week) observed in the returned rows.
    """
    features = []

    # get newest week in order to attach to metadata, disclaimer will be "data through xx-xx-xxxx"
    weeks = [row.get("week") for row in rows if row.get("week")]
    data_from = min(weeks) if weeks else None
    data_through = max(weeks) if weeks else None

    for row in rows:
        lon = row.get("longitude")
        lat = row.get("latitude")

        if lat is None or lon is None:
            continue

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]   # longitude comes first in GeoJSON
            },
            "properties": {
                "week": row.get("week"),
                # "region": row.get("region"),
                "country": row.get("country"),
                "country_admin": row.get("country_admin"),
                "event_type": row.get("event_type"),
                "sub_event_type": row.get("sub_event_type"),
                "no_of_events": row.get("no_of_events"),
                "fatalities": row.get("fatalities"),
                # "population_exposure": row.get("population_exposure"),
                "disorder_type": row.get("disorder_type"),
                "acled_id": row.get("acled_id"),
                "recency": row.get("recency")
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            "data_from": data_from,
            "data_through": data_through
        }
    }

def compute_recency_for_heatmap(data, start_date):
    """
    Adds a `recency` field (0.0–1.0) to each row given.
    `row["week"]` is expected to be an ISO date string (YYYY-MM-DD).
    """

    # Normalize start_date → datetime
    if isinstance(start_date, datetime):
        start_dt = start_date
    else:
        start_dt = datetime.combine(start_date, datetime.min.time())

    start_dt = start_dt.replace(tzinfo=timezone.utc)

    # Normalize all row dates once
    for row in data:
        row["_event_dt"] = datetime.fromisoformat(row["week"]).replace(
            tzinfo=timezone.utc
        )

    # Window end = most recent event date
    end_dt = max(row["_event_dt"] for row in data)

    total_seconds = (end_dt - start_dt).total_seconds()

    # Guard against bad windows
    if total_seconds <= 0:
        for row in data:
            row["recency"] = 1.0
            del row["_event_dt"]
        return data

    # Compute recency
    for row in data:
        recency = (row["_event_dt"] - start_dt).total_seconds() / total_seconds
        row["recency"] = max(0.0, min(1.0, recency))
        del row["_event_dt"]  # cleanup temp field

    return data


    
if __name__ == "__main__":
    # events = fetch_conflict_events(start_date="2025-01-01", end_date="2025-12-31")
    events = fetch_conflict_events()
    print(events)
    if events is not None:
        geojson_data = conflicts_to_geojson(events)

    import json
    print(json.dumps(geojson_data, indent=2))
    print(len(geojson_data["features"]))
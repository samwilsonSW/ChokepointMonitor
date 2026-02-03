from supabase_client import query_data
def fetch_conflict_events(start_date=None, end_date=None):
    """
    Get events from database, optionally filtered by start_date and/or end_date.
    """
    filters = {}
    if start_date:
        filters['week'] = {'gte': start_date}
    if end_date:
        filters['week'] = {'lte': end_date}

    events = query_data('conflict_events_enriched', filters)

    return events


def conflicts_to_geojson(rows):
    """ 
    In order for MapLibre to work, this is the object we need (GeoJSON FeatureCollection)
    """
    features = []

    for row in rows:
        lon = row["effective_longitude"]
        lat = row["effective_latitude"]

        if lat is None or lon is None:
            continue

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]   # As a note, longitude always comes first in GeoJSON
            },
            "properties": {
                "week": row.get("week"),
                "region": row.get("region"),
                "country": row.get("country"),
                "country_admin": row.get("country_admin"),
                "event_type": row.get("event_type"),
                "sub_event_type": row.get("sub_event_type"),
                "no_of_events": row.get("no_of_events"),
                "fatalities": row.get("fatalities"),
                "population_exposure": row.get("population_exposure"),
                "disorder_type": row.get("disorder_type"),
                "acled_id": row.get("acled_id")
            }
        })

        return {
            "type": "FeatureCollection",
            "features": features
        }
    
if __name__ == "__main__":
    # from services.conflicts import fetch_conflict_events, conflicts_to_geojson

    # Example usage: get all conflicts for 2025
    events = fetch_conflict_events(start_date="2025-01-01", end_date="2025-12-31")

    # Convert to GeoJSON
    geojson_data = conflicts_to_geojson(events)

    # Print pretty JSON to inspect in terminal
    import json
    print(json.dumps(geojson_data, indent=2))
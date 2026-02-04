from supabase_client import _get_client

def fetch_conflict_events(start_date=None, end_date=None):
    """
    Get events from database, optionally filtered by start_date and/or end_date.
    """
    client = _get_client()

    filters = {}
    if start_date:
        filters['week'] = {'gte': start_date}
    if end_date:
        filters['week'] = {'lte': end_date}

    events = query = client.table('conflict_events_enriched').select("*")
    if start_date:
        query = query.gte('week', start_date)
    if end_date:
        query = query.lte('week', end_date)

    response = events.execute()

    return response.data


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
    # events = fetch_conflict_events(start_date="2025-01-01", end_date="2025-12-31")
    events = fetch_conflict_events()
    print(events)
    if events is not None:
        geojson_data = conflicts_to_geojson(events)

    import json
    print(json.dumps(geojson_data, indent=2))
    print(len(geojson_data["features"]))
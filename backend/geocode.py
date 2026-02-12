from geopy.geocoders import Nominatim
from backend.supabase_client import _get_client

def geocode(locations, client):
    geolocator = Nominatim(user_agent="geo_app_admin_handler_v1")
    table_name = "Admin-Effective-Location"
    batch_size = 50
    location_rows = []

    for index, (region, country, country_admin) in enumerate(locations):
        query_string = f"{country_admin}, {country}"
        try:
            location = geolocator.geocode(
                query_string, 
                exactly_one=True,
                timeout=10
            )
            if not location:
                query_string = country_admin
                location = geolocator.geocode(
                    query_string,
                    exactly_one=True,
                    timeout=10
                )
            if location:
                location_data = {
                    "region": region,
                    "country": country,
                    "country_admin": country_admin,
                    "latitude": location.latitude,
                    "longitude": location.longitude
                }
                location_rows.append(location_data)
                print(f"Geocoded: {query_string} -> ({location.latitude}, {location.longitude})")
            else:
                # Later, set up an email for all this so I can receive email alerts. For now, this is fine.
                print(f"Failed to geocode: {country_admin}, {country}")
        except Exception as e:
            print(f"Error geocoding {country_admin}, {country}: {e}")

        # Insert in batches of 50
        if len(location_rows) >= batch_size or index == len(locations) - 1:
            if location_rows:
                client.table(table_name).insert(location_rows).execute()
                location_rows = []


def get_location_data():
    client = _get_client()

    # --- Get unique locations (A) and locations with coordinates (B) to compare, only want A - B
    table_name_a = "unique_region_country_admin"
    response_a = client.table(table_name_a).select("*").execute()
    unique_rca = response_a.data

    table_name_b = "Admin-Effective-Location"
    response_b = client.table(table_name_b).select("*").execute()
    location_data = response_b.data

    # we are gonna use tuples(sets) here, i think it makes things simpler?
    set_a = {(row['region'], row['country'], row['country_admin']) for row in unique_rca}
    set_b = {(row['region'], row['country'], row['country_admin']) for row in location_data}
    locations_needing_geocoding = set_a - set_b

    geocode(locations_needing_geocoding, client)
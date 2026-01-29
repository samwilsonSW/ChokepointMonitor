from geopy.geocoders import Nominatim
from supabase_client import _get_client

def geocode(locations, client):
    # geolocator = Nominatim(user_agent="geo_app_admin_handler_v1")
    # table_name = "Admin-Effective-Location"
    # batch_size = 50
    # location_rows = []

    # for idx, (region, country, country_admin) in enumerate(locations):
    #     query_string = f"{country_admin}, {country}"
    #     try:
    #         location = geolocator.geocode(
    #             query_string, 
    #             exactly_one=True,
    #             timeout=10
    #         )
    #         if location:
    #             location_data = {
    #                 "region": region,
    #                 "country": country,
    #                 "country_admin": country_admin,
    #                 "latitude": location.latitude,
    #                 "longitude": location.longitude,
    #                 "address": location.address
    #             }
    #             location_rows.append(location_data)
    #             print(f"Geocoded: {query_string} -> ({location.latitude}, {location.longitude})")
    #         else:
    #             print(f"Failed to geocode: {query_string}")
    #     except Exception as e:
    #         print(f"Error geocoding {query_string}: {e}")

    #     # Insert in batches
    #     if len(location_rows) >= batch_size or idx == len(locations) - 1:
    #         if location_rows:
    #             client.table(table_name).insert(location_rows).execute()
    #             location_rows = []

def get_location_data():
    client = _get_client()

    # --- Get unique locations (A) and locations with coordinates (B) to compare, only want A - B
    table_name_a = "unique_region_country_admin"
    response_a = client.table(table_name_a).select("*").execute()
    unique_rca = response_a.data 

    table_name_b = "Admin-Effective-Location"
    response_b = client.table(table_name_b).select("*").execute()
    location_data = response_b.data

    # we are gonna use tuples here, i think it makes things simpler?
    set_a = {(row['region'], row['country'], row['country_admin']) for row in unique_rca}
    set_b = {(row['region'], row['country'], row['country_admin']) for row in location_data}
    locations_needing_geocoding = set_a - set_b

    geocode(locations_needing_geocoding, client)




# def get_coordinates():#(city, country):
    

    
    


#     # 1. Initialize the geolocator
#     # ALWAYS provide a unique user_agent to identify your app
#     geolocator = Nominatim(user_agent="geo_app_user_123")

#     # 2. Construct the location string
#     geolocator = Nominatim(user_agent="geo_app_admin_handler_v1")

#     # Strategy 1: Structured Query (More Precise)
#     # We define country explicitly to narrow the search.
#     # We pass the unknown area simply as a query string combined with country,
#     # or try to map it to 'state' if we are fairly confident.
    
#     # Ideally, we try to construct a query that looks like: "AdminArea, Country"
#     # This is often safer than trying to force it into 'city=' or 'state=' keys
#     # if you don't know which one it is.
#     query_string = f"{admin_area}, {country}"

#     try:
#         # 'exactly_one=True' ensures we get the best match, but you might want 
#         # to set it to False to see all options if ambiguity is high.
#         location = geolocator.geocode(
#             query_string, 
#             exactly_one=True,
#             timeout=10 # Increase timeout for slower responses
#         )
        
#         if location:
#             return {
#                 "address": location.address,
#                 "lat": location.latitude,
#                 "lon": location.longitude,
#                 "type": location.raw.get("type"), # Useful: tells you if it matched a 'city', 'administrative', etc.
#                 "class": location.raw.get("class") # Useful: broadly categorizes the place (e.g., 'place', 'boundary')
#             }
#         else:
#             # Fallback Strategy: Search ONLY the administration area
#             # (Sometimes adding the country constrains it too much if the country name format differs)
#             print(f"  - strict match failed for '{query_string}', trying loose match...")
#             location = geolocator.geocode(admin_area)
#             if location and country.lower() in location.address.lower():
#                 return {
#                     "address": location.address,
#                     "lat": location.latitude,
#                     "lon": location.longitude,
#                     "type": location.raw.get("type"),
#                     "class": location.raw.get("class")
#                 }
            
#     except GeocoderTimedOut:
#         return "Error: Service Timed Out"
#     except Exception as e:
#         return f"Error: {e}"

#     return None

# # --- Testing the Variance ---
# test_data = [
#     ("California", "United States"),  # State
#     ("Paris", "France"),              # City
#     ("Kyoto Prefecture", "Japan"),    # Province/Prefecture
#     ("Bavaria", "Germany"),           # Region/State
#     ("Hennepin County", "USA"),       # County
# ]

# print(f"{'Input':<30} | {'Found Type':<15} | {'Coords'}")
# print("-" * 75)

# for admin, country in test_data:
#     result = get_flexible_location(admin, country)
#     if result and isinstance(result, dict):
#         # We print the 'type' to verify what the API recognized it as
#         print(f"{admin}, {country:<15} | {result['type']:<15} | {result['lat']:.2f}, {result['lon']:.2f}")
#     else:
#         print(f"{admin}, {country:<15} | Not Found")
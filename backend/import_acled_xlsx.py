import math
from typing import List

import pandas as pd
from supabase_client import insert_data, _get_client

def import_and_publish_no_duplicate(filename: str, table_name: str = 'ACLED-Aggregated-Conflict-Data', batch_size: int = 500, min_year: int = 2023):
    #Set identifier for which ACLED data file we are uplaoding, region field is not reliable enough so we must add this
    from_spreadsheet = ""     
    filename_lower = filename.lower()
    if 'africa' in filename_lower:
        from_spreadsheet = 'Africa'
    elif 'asia' in filename_lower and 'pacific' in filename_lower:
        from_spreadsheet = 'Asia Pacific'
    elif 'middle' in filename_lower:
        from_spreadsheet = 'Middle East'
    
    # Expected mapping from spreadsheet headers to DB column names
    mapping = {
        'WEEK': 'week',
        'REGION': 'region',
        'COUNTRY': 'country',
        'ADMIN1': 'country_admin',
        'EVENT_TYPE': 'event_type',
        'SUB_EVENT_TYPE': 'sub_event_type',
        'EVENTS': 'no_of_events',
        'FATALITIES': 'fatalities',
        'POPULATION_EXPOSURE': 'population_exposure',
        'DISORDER_TYPE': 'disorder_type',
        'ID': 'acled_id',
        'CENTROID_LATITUDE': 'latitude',
        'CENTROID_LONGITUDE': 'longitude',
        'FROM_SPREADSHEET': 'from_spreadsheet'
    }

    # Open given excel file 
    df = pd.read_excel(filename, engine='openpyxl') 

    # Normalize column names to uppercase stripped strings so mapping is robust
    df.columns = [str(c).strip().upper() for c in df.columns]

    # Rename/map columns
    rename_map = {col: mapping[col] for col in df.columns if col in mapping}
    df = df.rename(columns=rename_map)

    # Convert week to (YYYY-MM-DD)
    if 'week' in df.columns:
        df['week'] = pd.to_datetime(df['week'], errors='coerce').dt.date

    # Filter by minimum year: keep only records where week.year > min_year
    if 'week' in df.columns and min_year is not None:
        df = df[df['week'].notna() & df['week'].apply(lambda d: getattr(d, 'year', None) is not None and d.year > min_year)]

    # Remove duplicate events (xls file has all events accumulative, so we remove previously imported events)
    client = _get_client()
    #Modify this variable to do a "where" region = region
    latest_event_date_data = client.table(table_name) \
                .select("week") \
                .eq("from_spreadsheet", from_spreadsheet) \
                .order("week", desc=True) \
                .limit(1) \
                .execute()
    
    
    if 'week' in df.columns and latest_event_date_data.data:
        print(f"Latest event date data from Supabase:", latest_event_date_data.data)
        # Extract the raw string from Supabase and convert to date object
        raw_latest_week = latest_event_date_data.data[0]['week']
        latest_week = pd.to_datetime(raw_latest_week).date()

        # Filter the dataframe to only include rows newer than the latest_week
        # then sort by week ascending and reset the index for a clean result
        df = df[df['week'] > latest_week].sort_values(by='week', ascending=True).reset_index(drop=True)

    # BEGIN INSERT LOGIC
    
    # Numeric conversions
    if 'no_of_events' in df.columns:
        df['no_of_events'] = pd.to_numeric(df['no_of_events'], errors='coerce').apply(lambda x: int(x) if not (pd.isna(x) or math.isinf(x)) else None)
    if 'fatalities' in df.columns:
        df['fatalities'] = pd.to_numeric(df['fatalities'], errors='coerce').apply(lambda x: int(x) if not (pd.isna(x) or math.isinf(x)) else None)
    if 'population_exposure' in df.columns:
        # remove common thousand separators and convert
        df['population_exposure'] = df['population_exposure'].astype(str).str.replace(',', '').replace({'nan': None})
        df['population_exposure'] = pd.to_numeric(df['population_exposure'], errors='coerce').apply(lambda x: int(x) if not (pd.isna(x) or math.isinf(x)) else None)
    if 'acled_id' in df.columns:
        df['acled_id'] = pd.to_numeric(df['acled_id'], errors='coerce').apply(lambda x: int(x) if not (pd.isna(x) or math.isinf(x)) else None)
    if 'latitude' in df.columns:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    if 'longitude' in df.columns:
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

    # Normalize empty strings to None
    df = df.replace({'': None})
    # Add our custom identifier field
    df['from_spreadsheet'] = from_spreadsheet

    # Only keep columns that match our mapping values
    allowed_cols = set(mapping.values())
    present_cols = [c for c in df.columns if c in allowed_cols]
    df = df[present_cols]

    # Replace NaN's for JSON serialization
    records: List[dict] = df.where(pd.notnull(df), None).to_dict(orient='records')

    # Insert in batches (500 by default)
    total = len(records)
    if total == 0:
        print('No records found in the file.')
        return

    print(f'Preparing to insert {total} records into {table_name} (batch size {batch_size})')

    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]
        try:
            insert_data(table_name, batch)
            print(f'Inserted records {i+1}-{i+len(batch)}')
        except Exception as e:
            print(f'Error inserting batch starting at {i}: {e}')
            raise


    # Uncomment this if you want to verify what was inserted
    # latest_week_str = latest_week.isoformat() if hasattr(latest_week, 'isoformat') else str(latest_week)

    # get_new_data_just_inserted = client.table(table_name) \
    #     .select("week") \
    #     .gt("week", latest_week_str) \
    #     .order("week", desc=True) \
    #     .execute()
    
    # print(f"Data: {get_new_data_just_inserted.data}")


    print('Import complete.')
    
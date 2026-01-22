import math
from typing import List

import pandas as pd

from supabase_client import insert_data


def import_and_publish(filename: str, table_name: str = 'ACLED-Aggregated-Conflict-Data', batch_size: int = 500, min_year: int = 2023):
    """Read an XLSX file and publish its rows to Supabase.

    - `filename` is the path to the Excel file.
    - `table_name` is the Supabase table to insert into.
    - `batch_size` controls how many records to insert per request.

    The function maps XLSX columns to DB columns, normalizes types, and
    inserts records in batches using `supabase_client.insert_data`.
    """
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
    }

    df = pd.read_excel(filename, engine='openpyxl')

    # Normalize column names to uppercase stripped strings so mapping is robust
    df.columns = [str(c).strip().upper() for c in df.columns]

    # Rename only columns we have mappings for
    rename_map = {col: mapping[col] for col in df.columns if col in mapping}
    df = df.rename(columns=rename_map)

    # Convert week to ISO date string (YYYY-MM-DD) where possible
    if 'week' in df.columns:
        df['week'] = pd.to_datetime(df['week'], errors='coerce').dt.date

    # Filter by minimum year: keep only records where week.year > min_year
    if 'week' in df.columns and min_year is not None:
        before_count = len(df)
        df = df[df['week'].notna() & df['week'].apply(lambda d: getattr(d, 'year', None) is not None and d.year > min_year)]
        after_count = len(df)
        print(f'Filtered by week year > {min_year}: removed {before_count - after_count} rows, {after_count} remain')

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

    # Only keep columns that match our mapping values
    allowed_cols = set(mapping.values())
    present_cols = [c for c in df.columns if c in allowed_cols]
    df = df[present_cols]

    # Replace NaN with None for JSON-friendly serialization
    records: List[dict] = df.where(pd.notnull(df), None).to_dict(orient='records')

    # Insert in batches
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

    print('Import complete.')

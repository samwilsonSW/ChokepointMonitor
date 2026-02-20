import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional
from datetime import date, datetime
import pandas as pd

# This looks for the .env in the same folder as this script
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

# print("ENV_PATH exists:", ENV_PATH.exists())
# print("Reading from:", ENV_PATH)
# print("SUPABASE_URL =", repr(os.getenv("SUPABASE_URL")))
# print("SUPABASE_KEY =", repr(os.getenv("SUPABASE_KEY")))

_supabase: Optional[Client] = None

def _get_client() -> Client:
    """Lazily initialize and return a Supabase Client."""
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        # If OS environment is empty, manually parse the file
        if not url or not key:
            if ENV_PATH.exists():
                with open(ENV_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        # Clean up the line: remove whitespace and ignore comments
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        
                        # Split by the first '=' found
                        if "=" in line:
                            k, v = line.split("=", 1)
                            # Remove any surrounding quotes or spaces from the value
                            clean_v = v.strip().strip("'").strip('"')
                            if k.strip() == "SUPABASE_URL":
                                url = clean_v
                            elif k.strip() == "SUPABASE_KEY":
                                key = clean_v

        if not url or not key:
            # Final fail-safe diagnostic
            print(f"DEBUG: File exists at {ENV_PATH}")
            if ENV_PATH.exists():
                with open(ENV_PATH, 'r') as f:
                    print(f"DEBUG: Raw file content starts with: {f.read(10)}...")
            raise ValueError(f"Failed to parse SUPABASE_URL/KEY from {ENV_PATH}")

        _supabase = create_client(url, key)
    return _supabase
    
def insert_data(table: str, data):
    try:
        client = _get_client()

        if isinstance(data, list):
            data = [
                {k: serialize_for_json(v) for k, v in row.items()}
                for row in data
            ]
        else:
            data = {k: serialize_for_json(v) for k, v in data.items()}

        response = client.table(table).insert(data).execute()
        return response.data

    except Exception as e:
        print(f"Error inserting data: {e}")
        raise


def query_data(table: str, filters: dict = None):
    try:
        client = _get_client()
        query = client.table(table).select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        response = query.execute()
        return response.data
    except Exception as e:
        print(f"Error querying data: {e}")
        raise

def update_data(table: str, record_id: int, data: dict):
    try:
        client = _get_client()
        response = client.table(table).update(data).eq("id", record_id).execute()
        return response.data
    except Exception as e:
        print(f"Error updating data: {e}")
        raise

def delete_data(table: str, record_id: int):
    try:
        client = _get_client()
        response = client.table(table).delete().eq("id", record_id).execute()
        return response.data
    except Exception as e:
        print(f"Error deleting data: {e}")
        raise


## Separator for helper functions 


def serialize_for_json(obj):
    #Handle null/NaN values (empty cells)
    if pd.isna(obj):
        return None
    
    # 2. Handle Floats that are actually Integers
    if isinstance(obj, float) and obj.is_integer():
        return int(obj)

    #Handle dates to convert to mm/dd/yyyy format
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    
    return obj


if __name__ == "__main__":
    try:
        _get_client()
        print("Supabase client initialized successfully!")
    except Exception as e:
        print(f"Initialization failed: {e}")
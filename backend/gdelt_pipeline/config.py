"""
Configuration module for GDELT ingestion pipeline.
Loads environment variables and defines constants.
"""

import os
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv
from google.cloud import bigquery
from ..supabase_client import _get_client, Client

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"

load_dotenv(dotenv_path=ENV_PATH)


# Chokepoint bounding boxes (lat_min, lat_max, lon_min, lon_max)
CHOKEPOINTS: Dict[str, Dict[str, Any]] = {
    'bab_al_mandeb': {
        'lat_min': 12.0,
        'lat_max': 14.0,
        'lon_min': 42.5,
        'lon_max': 44.5,
        'countries': ['YEM', 'DJI', 'ERI', 'SAU'],
        'description': 'Bab el-Mandeb Strait - Yemen/Djibouti/Eritrea'
    },
    'hormuz': {
        'lat_min': 25.0,
        'lat_max': 27.5,
        'lon_min': 56.0,
        'lon_max': 57.0,
        'countries': ['IRN', 'OMN', 'ARE'],
        'description': 'Strait of Hormuz - Iran/Oman/UAE'
    },
    'malacca': {
        'lat_min': 1.0,
        'lat_max': 7.0,
        'lon_min': 99.0,
        'lon_max': 104.0,
        'countries': ['MYS', 'IDN', 'SGP'],
        'description': 'Strait of Malacca - Malaysia/Indonesia/Singapore'
    }
}


# CAMEO conflict event codes to monitor
CONFLICT_CODES = [
    '17', '18', '19', '20',  # Conflict-related root codes
    '171', '172', '173', '174',  # Coerce variants
    '180', '181', '182', '183', '184',  # Assault variants
    '190', '191', '192', '193', '194', '195', '196',  # Use force variants
    '200', '201', '202', '203', '204',  # Demonstration variants
]


# CAMEO to ACLED event type mapping
CAMEO_TO_ACLED_MAPPING: Dict[str, str] = {
    '17': 'Violence against civilians',
    '170': 'Violence against civilians',
    '171': 'Violence against civilians',
    '172': 'Violence against civilians',
    '173': 'Violence against civilians',
    '174': 'Violence against civilians',
    '175-199': 'Violence against civilians',
    '18': 'Violence against civilians',
    '180': 'Violence against civilians',
    '181': 'Violence against civilians',
    '182': 'Violence against civilians',
    '183': 'Violence against civilians',
    '184': 'Violence against civilians',
    '19': 'Battles',
    '190': 'Battles',
    '191': 'Battles',
    '192': 'Battles',
    '193': 'Battles',
    '194': 'Remote violence',
    '195': 'Remote violence',
    '196': 'Remote violence',
    '20': 'Protests',
    '200': 'Protests',
    '201': 'Protests',
    '202': 'Protests',
    '203': 'Protests',
    '204': 'Riots',
}


# Confidence score thresholds
CONFIDENCE_THRESHOLDS = {
    'verified': 0.8,
    'likely': 0.5,
    'unverified': 0.3,
    'false_positive': 0.0
}


# BigQuery configuration
BIGQUERY_PROJECT = 'gdelt-bq'
BIGQUERY_DATASET = 'gdeltv2'

def get_bigquery_client() -> bigquery.Client:
    # 1. Manually define the path to your .env
    # Based on your logs, this is the absolute path:
    env_path = "/workspaces/ChokepointMonitor/backend/.env"
    
    # 2. Force load it into the OS environment
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded .env from {env_path}")
    else:
        print(f"❌ Could not find .env at {env_path}")

    # 3. Check if the variable is actually there now
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    print(f"Showing creds path: {creds_path}")
    if not creds_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not found in environment!")
    else:
        # Convert relative path to absolute if necessary
        # If your .env says "backend/gdelt_pipeline/creds.json", 
        # we ensure it's absolute for the BigQuery library.
        if not os.path.isabs(creds_path):
            creds_path = os.path.join("/workspaces/ChokepointMonitor", creds_path)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
        
        print(f"✅ Using credentials at: {creds_path}")

    # 4. Now initialize (it will check os.environ automatically)
    return bigquery.Client()

def get_chokepoint_for_country(country_code: str) -> list:
    """Return list of chokepoint regions that include a country."""
    regions = []
    for name, bounds in CHOKEPOINTS.items():
        if country_code in bounds.get('countries', []):
            regions.append(name)
    return regions


def main():
    """Test the configuration and connections."""
    print("--- GDELT Pipeline Config Test ---")
    print(f"Base Directory: {BASE_DIR}")
    print(f"Env Path: {ENV_PATH}")
    
    try:
        print("\nTesting Supabase Connection...")
        sb = _get_client()
        print("✅ Supabase client initialized.")
        
        print("\nTesting BigQuery Connection...")
        bq = get_bigquery_client()
        print(f"✅ BigQuery client initialized for project: {bq.project}")
        
        print("\nConfiguration looks solid!")
        
    except Exception as e:
        print(f"\n❌ Configuration Error: {e}")

if __name__ == "__main__":
    main()
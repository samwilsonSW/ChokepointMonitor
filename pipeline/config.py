"""
Configuration module for GDELT ingestion pipeline.
Loads environment variables and defines constants.
"""

import os
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv
from google.cloud import bigquery
from supabase import create_client, Client

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / "backend" / ".env"

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


def get_supabase_client() -> Client:
    """Initialize and return Supabase client from environment."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        # Try manual parsing if env vars not loaded
        if ENV_PATH.exists():
            with open(ENV_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        clean_v = v.strip().strip("'\"").strip('"')
                        if k.strip() == 'SUPABASE_URL':
                            url = clean_v
                        elif k.strip() == 'SUPABASE_KEY':
                            key = clean_v
    
    if not url or not key:
        raise ValueError(
            f"SUPABASE_URL and SUPABASE_KEY must be set. "
            f"Checked env vars and {ENV_PATH}"
        )
    
    return create_client(url, key)


def get_bigquery_client() -> bigquery.Client:
    """Initialize and return BigQuery client."""
    # GOOGLE_APPLICATION_CREDENTIALS should be set in environment
    return bigquery.Client()


def get_chokepoint_for_country(country_code: str) -> list:
    """Return list of chokepoint regions that include a country."""
    regions = []
    for name, bounds in CHOKEPOINTS.items():
        if country_code in bounds.get('countries', []):
            regions.append(name)
    return regions

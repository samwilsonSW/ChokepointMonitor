import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validate that credentials are set
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def insert_data(table: str, data: dict):
    """Insert a record into a Supabase table"""
    try:
        response = supabase.table(table).insert(data).execute()
        return response.data
    except Exception as e:
        print(f"Error inserting data: {e}")
        raise


def query_data(table: str, filters: dict = None):
    """Query data from a Supabase table with optional filters"""
    try:
        query = supabase.table(table).select("*")
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        response = query.execute()
        return response.data
    except Exception as e:
        print(f"Error querying data: {e}")
        raise


def update_data(table: str, record_id: int, data: dict):
    """Update a record in a Supabase table"""
    try:
        response = supabase.table(table).update(data).eq("id", record_id).execute()
        return response.data
    except Exception as e:
        print(f"Error updating data: {e}")
        raise


def delete_data(table: str, record_id: int):
    """Delete a record from a Supabase table"""
    try:
        response = supabase.table(table).delete().eq("id", record_id).execute()
        return response.data
    except Exception as e:
        print(f"Error deleting data: {e}")
        raise


if __name__ == "__main__":
    # Example usage
    print("Supabase client initialized successfully!")

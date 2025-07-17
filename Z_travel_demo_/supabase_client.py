# File: supabase_client.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# This variable will hold our single, shared database connection.
# The underscore indicates it's intended for internal use in this module.
_supabase_client: Client = None

def get_supabase_client() -> Client:
    """
    This is a "factory" function. It creates the Supabase client once
    and then returns the same instance on every subsequent call.
    This prevents creating multiple connections to the database.
    """
    global _supabase_client

    # If the client has already been created, just return it.
    if _supabase_client:
        return _supabase_client

    # --- First-time initialization ---
    load_dotenv()
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("⚠️ Supabase credentials not found in .env file. Database tools will fail.")
        return None

    try:
        # Create the client and store it in our global variable for future use.
        _supabase_client = create_client(url, key)
        print("✅ Successfully connected to Supabase.")
        return _supabase_client
    except Exception as e:
        print(f"🔥 Failed to connect to Supabase: {e}")
        return None
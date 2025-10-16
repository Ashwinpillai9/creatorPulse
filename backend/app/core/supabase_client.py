import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment vars from .env for local development.
load_dotenv()

def get_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in environment.")
    return create_client(url, key)

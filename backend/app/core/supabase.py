from dotenv import load_dotenv
load_dotenv()

import os
from supabase import create_client, Client
from app.core.config import SUPABASE_URL, SUPABASE_KEY
for proxy_var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
    os.environ.pop(proxy_var, None)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
def get_supabase() -> Client:
    """FastAPI dependency — injects the Supabase client into routes."""
    return supabase

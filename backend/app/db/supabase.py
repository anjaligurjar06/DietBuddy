from supabase import create_client,Client
from dotenv import load_dotenv
from app.core.config import SUPABASE_URL, SUPABASE_KEY
import os

for proxy_var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
    os.environ.pop(proxy_var, None)

supabase: Client =create_client(SUPABASE_URL, SUPABASE_KEY)
load_dotenv()

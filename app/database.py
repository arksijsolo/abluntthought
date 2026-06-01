from supabase import create_client

SUPABASE_URL = "https://fnlhexaifsnfwvpfawrh.supabase.co"
SUPABASE_KEY = "sb_publishable_gO5ooU1bZ2e5hFBOyuAmpw_poZsZ28C"

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)
from supabase import create_client, Client
from config import settings

supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_recent_posts(limit: int = 10):
    return supabase_client.table("posts").select("*").order("id", desc=True).limit(limit).execute().data
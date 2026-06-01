import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str = os.getenv("https://fnlhexaifsnfwvpfawrh.supabase.co", "")
    SUPABASE_KEY: str = os.getenv("sb_publishable_gO5ooU1bZ2e5hFBOyuAmpw_poZsZ28C", "")
    SESSION_EXPIRY: int = 1800

settings = Settings()

from dotenv import load_dotenv
import os
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")

class Settings:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    ADMIN_USER = os.getenv("ADMIN_USER")
    ADMIN_PASS = os.getenv("ADMIN_PASS")
    SECRET_KEY = os.getenv("SECRET_KEY")

settings = Settings()


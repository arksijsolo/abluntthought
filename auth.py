from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv
import os

load_dotenv()

def get_serializer():
    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise Exception("SECRET_KEY missing in .env")
    return URLSafeTimedSerializer(secret)


ACTIVE_SESSIONS = set()


def check_login(username, password):
    return username == os.getenv("ADMIN_USER") and password == os.getenv("ADMIN_PASS")


def create_session(username):
    s = get_serializer()
    token = s.dumps(username)
    ACTIVE_SESSIONS.add(token)
    return token


def verify_session(token, max_age=1800):
    if not token or token not in ACTIVE_SESSIONS:
        return None

    try:
        s = get_serializer()
        return s.loads(token, max_age=max_age)
    except:
        return None


def destroy_session(token):
    ACTIVE_SESSIONS.discard(token)
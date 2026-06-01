from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from services.database import get_recent_posts
from auth import verify_session

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def render_homepage(request: Request):
    posts = get_recent_posts()
    user = verify_session(request.cookies.get("session"))
    return templates.TemplateResponse("index.html", {"request": request, "posts": posts, "user": user})
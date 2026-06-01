import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services.database import supabase
from auth import verify_session

router = APIRouter()

# Resolve templates location relative to app root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    posts = supabase.table("posts").select("*").order("id", desc=True).execute().data
    user = verify_session(request.cookies.get("session"))

    return templates.TemplateResponse(
        "index.html", {"request": request, "posts": posts, "user": user}
    )

@router.get("/post/{slug}", response_class=HTMLResponse)
def post(request: Request, slug: str):
    res = supabase.table("posts").select("*").eq("slug", slug).execute()
    post_data = res.data if res.data else None

    if not post_data:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    user = verify_session(request.cookies.get("session"))

    return templates.TemplateResponse(
        "post.html", {"request": request, "post": post_data, "user": user}
    )
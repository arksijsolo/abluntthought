import os
import uuid
import requests
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from services.database import supabase
from config import settings
from auth import check_login, create_session, destroy_session, verify_session

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ---------------- SECURITY ACCESS INTERCEPTOR ----------------
def secure_access(request: Request):
    return verify_session(request.cookies.get("session"))

# ---------------- LOGIN / LOGOUT MANAGEMENT ----------------
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if secure_access(request):
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if check_login(username, password):
        token = create_session(username)
        res = RedirectResponse("/admin", status_code=303)
        res.set_cookie("session", token, httponly=True, max_age=1800, samesite="lax")
        return res
    return RedirectResponse("/routers/login", status_code=303)

@router.get("/logout")
def logout(request: Request):
    token = request.cookies.get("session")
    if token:
        destroy_session(token)
    res = RedirectResponse("/login", status_code=303)
    res.delete_cookie("session")
    return res

# ---------------- ADMIN WORKSPACE ----------------
@router.get("", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    user = secure_access(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    posts = supabase.table("posts").select("*").order("id", desc=True).execute().data
    return templates.TemplateResponse("admin.html", {"request": request, "posts": posts, "user": user})

# ---------------- WRITE / MODIFY MUTATIONS ----------------
@router.post("/create")
def create(request: Request, title: str = Form(...), content: str = Form(...)):
    if not secure_access(request):
        return RedirectResponse("/login", status_code=303)

    slug = title.lower().strip().replace(" ", "-")
    supabase.table("posts").insert({"title": title, "slug": slug, "content": content}).execute()
    return RedirectResponse("/admin", status_code=303)

@router.post("/update/{id}")
def update(id: int, request: Request, title: str = Form(...), content: str = Form(...)):
    if not secure_access(request):
        return RedirectResponse("/login", status_code=303)

    slug = title.lower().strip().replace(" ", "-")
    supabase.table("posts").update({"title": title, "content": content, "slug": slug}).eq("id", id).execute()
    return RedirectResponse("/admin", status_code=303)

@router.get("/delete/{id}")
def delete(id: int, request: Request):
    if not secure_access(request):
        return RedirectResponse("/login", status_code=303)

    supabase.table("posts").delete().eq("id", id).execute()
    return RedirectResponse("/admin", status_code=303)


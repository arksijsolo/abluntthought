import os
import uuid
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import requests
from fastapi import FastAPI
from routers import home, admin

app = FastAPI(title="A Blunt Thought API Engine")

from auth import check_login, create_session, destroy_session, verify_session
from services.db import supabase

app = FastAPI()

# Absolute template configuration path resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# ---------------- HOME DIAGNOSTIC ----------------
@app.get("/")
def home(request: Request):
    import os
    expected_path = os.path.join(BASE_DIR, "templates")
    exists = os.path.exists(expected_path)
    
    # List whatever files are actually inside that directory if it exists
    files = os.listdir(expected_path) if exists else []
    
    return {
        "current_working_directory": os.getcwd(),
        "looking_in_path": expected_path,
        "does_folder_exist": exists,
        "files_found": files
    }


# ---------------- SINGLE POST ----------------
@app.get("/post/{slug}", response_class=HTMLResponse)
def post(request: Request, slug: str):
    res = supabase.table("posts").select("*").eq("slug", slug).execute()
    post_data = res.data if res.data else None

    if not post_data:
        return templates.TemplateResponse(
            "404.html", {"request": request}, status_code=404
        )

    user = verify_session(request.cookies.get("session"))

    return templates.TemplateResponse(
        "post.html", {"request": request, "post": post_data, "user": user}
    )


# ---------------- LOGIN ----------------
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if verify_session(request.cookies.get("session")):
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if check_login(username, password):
        token = create_session(username)
        res = RedirectResponse("/admin", status_code=303)
        res.set_cookie(
            "session", token, httponly=True, max_age=1800, samesite="lax"
        )
        return res

    return RedirectResponse("/login", status_code=303)


# ---------------- LOGOUT ----------------
@app.get("/logout")
def logout(request: Request):
    token = request.cookies.get("session")
    if token:
        destroy_session(token)

    res = RedirectResponse("/login", status_code=303)
    res.delete_cookie("session")
    return res


# ---------------- ADMIN ----------------
@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    user = verify_session(request.cookies.get("session"))
    if not user:
        return RedirectResponse("/login", status_code=303)

    posts = (
        supabase.table("posts")
        .select("*")
        .order("id", desc=True)
        .execute()
        .data
    )

    return templates.TemplateResponse(
        "admin.html", {"request": request, "posts": posts, "user": user}
    )


# ---------------- CREATE POST ----------------
@app.post("/create")
def create(request: Request, title: str = Form(...), content: str = Form(...)):
    if not verify_session(request.cookies.get("session")):
        return RedirectResponse("/login", status_code=303)

    slug = title.lower().strip().replace(" ", "-")

    supabase.table("posts").insert(
        {"title": title, "slug": slug, "content": content}
    ).execute()

    return RedirectResponse("/admin", status_code=303)


# ---------------- UPDATE ----------------
@app.post("/update/{id}")
def update(
    id: int, request: Request, title: str = Form(...), content: str = Form(...)
):
    if not verify_session(request.cookies.get("session")):
        return RedirectResponse("/login", status_code=303)

    slug = title.lower().strip().replace(" ", "-")

    supabase.table("posts").update(
        {"title": title, "content": content, "slug": slug}
    ).eq("id", id).execute()

    return RedirectResponse("/admin", status_code=303)


# ---------------- DELETE ----------------
@app.get("/delete/{id}")
def delete(id: int, request: Request):
    if not verify_session(request.cookies.get("session")):
        return RedirectResponse("/login", status_code=303)

    supabase.table("posts").delete().eq("id", id).execute()

    return RedirectResponse("/admin", status_code=303)





# Mount structural domain routers
app.include_router(home.router)
app.include_router(admin.router, prefix="/admin")
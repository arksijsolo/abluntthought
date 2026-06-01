from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from db import supabase
from auth import check_login, create_session, verify_session, destroy_session

import requests
import uuid
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# ---------------- HOME ----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    posts = supabase.table("posts").select("*").execute().data

    user = verify_session(request.cookies.get("session"))

    return templates.TemplateResponse("index.html", {
        "request": request,
        "posts": posts,
        "user": user
    })


# ---------------- SINGLE POST ----------------
@app.get("/post/{slug}", response_class=HTMLResponse)
def post(request: Request, slug: str):

    res = supabase.table("posts").select("*").eq("slug", slug).execute()
    post = res.data[0] if res.data else None

    user = verify_session(request.cookies.get("session"))

    return templates.TemplateResponse("post.html", {
        "request": request,
        "post": post,
        "user": user
    })


# ---------------- LOGIN ----------------
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):

    if check_login(username, password):
        token = create_session(username)

        res = RedirectResponse("/admin", status_code=302)
        res.set_cookie("session", token, httponly=True, max_age=1800)
        return res

    return RedirectResponse("/login", status_code=302)


# ---------------- LOGOUT ----------------
@app.get("/logout")
def logout(request: Request):

    token = request.cookies.get("session")
    if token:
        destroy_session(token)

    res = RedirectResponse("/login", status_code=302)
    res.delete_cookie("session")
    return res


# ---------------- ADMIN ----------------
@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):

    user = verify_session(request.cookies.get("session"))
    if not user:
        return RedirectResponse("/login")

    posts = supabase.table("posts").select("*").execute().data

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "posts": posts,
        "user": user
    })


# ---------------- CREATE POST ----------------
@app.post("/create")
def create(title: str = Form(...), content: str = Form(...)):

    slug = title.lower().replace(" ", "-")

    supabase.table("posts").insert({
        "title": title,
        "slug": slug,
        "content": content
    }).execute()

    return RedirectResponse("/admin", status_code=302)


# ---------------- UPDATE ----------------
@app.post("/update/{id}")
def update(id: int, title: str = Form(...), content: str = Form(...)):

    slug = title.lower().replace(" ", "-")

    supabase.table("posts").update({
        "title": title,
        "content": content,
        "slug": slug
    }).eq("id", id).execute()

    return RedirectResponse("/admin", status_code=302)


# ---------------- DELETE ----------------
@app.get("/delete/{id}")
def delete(id: int):

    supabase.table("posts").delete().eq("id", id).execute()

    return RedirectResponse("/admin", status_code=302)


# ---------------- IMAGE UPLOAD (QUILL) ----------------
@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):

    file_ext = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_ext}"

    url = f"{SUPABASE_URL}/storage/v1/object/blog-images/{file_name}"

    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": file.content_type
    }

    content = await file.read()

    res = requests.post(url, headers=headers, data=content)

    if res.status_code in [200, 201]:
        image_url = f"{SUPABASE_URL}/storage/v1/object/public/blog-images/{file_name}"
        return JSONResponse({"url": image_url})

    return JSONResponse({"error": "upload failed"}, status_code=400)
import os
import uuid
import base64

from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from supabase import create_client

# ======================
# LOAD ENV (FIXED)
# ======================
load_dotenv(dotenv_path=".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 🔥 DEBUG (REMOVE AFTER FIX)
print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_KEY:", "LOADED" if SUPABASE_KEY else None)

# 🚨 SAFETY CHECK (prevents your error)
if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY in .env file")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================
# FLASK APP
# ======================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

# ======================
# ADMIN (simple version)
# ======================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Password123"

# ======================
# HOME PAGE
# ======================
@app.route("/")
def index():
    blogs = supabase.table("blogs").select("*").order("created_at", desc=True).execute().data
    return render_template("index.html", blogs=blogs)

# ======================
# LOGIN
# ======================
@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("dashboard"))

        flash("Invalid login")
        return redirect(url_for("login"))

    return render_template("login.html")

# ======================
# DASHBOARD
# ======================
@app.route("/admin/blogs", methods=["GET", "POST"])
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        image_file = request.files.get("image")

        if not title or not content:
            flash("Title and content required")
            return redirect(url_for("dashboard"))

        image_data = None

        if image_file and image_file.filename:
            encoded = base64.b64encode(image_file.read()).decode()
            image_data = f"data:{image_file.content_type};base64,{encoded}"

        try:
            response = supabase.table("blogs").insert({
                "id": str(uuid.uuid4()),
                "title": title,
                "content": content,
                "image": image_data
            }).execute()

            print("INSERT RESPONSE:", response)

        except Exception as e:
            return f"Insert failed: {str(e)}", 500

        return redirect(url_for("dashboard"))

    blogs = supabase.table("blogs").select("*").order("created_at", desc=True).execute().data
    return render_template("manage_blogs.html", blogs=blogs)
# ======================
# DELETE BLOG
# ======================
@app.route("/admin/delete/<blog_id>", methods=["POST"])
def delete(blog_id):
    if not session.get("admin"):
        return redirect(url_for("login"))

    supabase.table("blogs").delete().eq("id", blog_id).execute()
    return redirect(url_for("dashboard"))

# ======================
# EDIT BLOG
# ======================
@app.route("/admin/edit/<blog_id>", methods=["GET", "POST"])
def edit(blog_id):
    if not session.get("admin"):
        return redirect(url_for("login"))

    blog = supabase.table("blogs").select("*").eq("id", blog_id).single().execute().data

    if request.method == "POST":
        supabase.table("blogs").update({
            "title": request.form.get("title"),
            "content": request.form.get("content")
        }).eq("id", blog_id).execute()

        return redirect(url_for("dashboard"))

    return render_template("edit_blog.html", blog=blog)










@app.route("/admin/blogs/create", methods=["GET", "POST"])
def create_blog():
    if not session.get("admin"):
        return redirect("/admin/login")

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        image_file = request.files.get("image")

        if not title or not content:
            return "Title and content required", 400

        image_data = None

        if image_file and image_file.filename:
            import base64
            encoded = base64.b64encode(image_file.read()).decode()
            image_data = f"data:{image_file.content_type};base64,{encoded}"

        supabase.table("blogs").insert({
            "id": str(uuid.uuid4()),
            "title": title,
            "content": content,
            "image": image_data
        }).execute()

        return redirect("/admin/blogs")

    return render_template("create_blog.html")

# ======================
# LOGOUT
# ======================
@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ======================
# RUN
# ======================
if __name__ == "__main__":
    app.run(debug=True)
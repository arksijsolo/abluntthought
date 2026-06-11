import os
import uuid
import base64
from flask import session
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from supabase import create_client




# ======================
# LOAD ENV
# ======================
load_dotenv(".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================
# FLASK APP
# ======================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

# ======================
# ADMIN CONFIG
# ======================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Password123"


# ======================
# SLUG APP
# ======================
@app.route("/blog/<slug>")
def blog_detail(slug):

    response = supabase.table("blogs") \
        .select("*") \
        .eq("slug", slug) \
        .single() \
        .execute()

    blog = response.data

    return render_template("blog_detail.html", blog=blog)

# ======================
# HELPERS
# ======================
def get_setting(key, default=None):
    result = supabase.table("settings") \
        .select("setting_value") \
        .eq("setting_key", key) \
        .execute()

    if result.data:
        return result.data[0]["setting_value"]
    return default


def require_admin():
    return session.get("admin_logged_in")


# ======================
# BEFORE REQUEST GUARD
# ======================
@app.before_request
def admin_guard():
    if request.path.startswith("/admin") and request.path != "/admin/login":
        if not session.get("admin_logged_in"):
            return redirect(url_for("login"))


# ======================
# HOME PAGE
# ======================

@app.route("/")
@app.route("/page/<int:page>")
def index(page=1):

    posts_per_page = int(get_setting("posts_per_page", 6))

    offset = (page - 1) * posts_per_page

    response = supabase.table("blogs") \
        .select("*") \
        .order("created_at", desc=True) \
        .range(offset, offset + posts_per_page - 1) \
        .execute()

    blogs = response.data

    count_response = supabase.table("blogs") \
        .select("*", count="exact") \
        .execute()

    total_posts = count_response.count or 0
    total_pages = (total_posts + posts_per_page - 1) // posts_per_page

    return render_template(
        "index.html",
        blogs=blogs,
        page=page,
        total_pages=total_pages
    )

# ======================
# LOGIN
# ======================
@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))

        flash("Invalid login")
        return redirect(url_for("login"))

    return render_template("login.html")


# ======================
# LOGOUT
# ======================
@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ======================
# ADMIN DASHBOARD (ONLY ONE)
# ======================
@app.route("/admin/dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if request.method == "POST":
        posts_per_page = request.form.get("posts_per_page")

        supabase.table("settings").upsert({
            "setting_key": "posts_per_page",
            "setting_value": posts_per_page
        }).execute()

        flash("Settings updated successfully", "success")
        return redirect(url_for("admin_dashboard"))

    posts_per_page = get_setting("posts_per_page", 6)

    blogs = supabase.table("blogs") \
        .select("*") \
        .order("created_at", desc=True) \
        .execute()

    return render_template(
        "admin_dashboard.html",
        posts_per_page=posts_per_page,
        blogs=blogs.data
    )


# ======================
# Manage BLOG
# ======================

@app.route("/admin/posts")
def admin_posts():

    blogs = supabase.table("blogs") \
        .select("*") \
        .order("created_at", desc=True) \
        .execute()

    return render_template("admin_posts.html", blogs=blogs.data)


# ======================
# CREATE BLOG
# ======================
@app.route("/admin/blogs/create", methods=["GET", "POST"])
def create_blog():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        image_file = request.files.get("image")

        if not title or not content:
            return "Title and content required", 400

        image_data = None

        if image_file and image_file.filename:
            encoded = base64.b64encode(image_file.read()).decode()
            image_data = f"data:{image_file.content_type};base64,{encoded}"

        supabase.table("blogs").insert({
            "id": str(uuid.uuid4()),
            "title": title,
            "content": content,
            "image": image_data
        }).execute()

        return redirect(url_for("admin_dashboard"))

    return render_template("create_blog.html")


# ======================
# EDIT BLOG
# ======================
@app.route("/admin/edit/<blog_id>", methods=["GET", "POST"])
def edit(blog_id):
    blog = supabase.table("blogs") \
        .select("*") \
        .eq("id", blog_id) \
        .single() \
        .execute().data

    if request.method == "POST":
        supabase.table("blogs").update({
            "title": request.form.get("title"),
            "content": request.form.get("content")
        }).eq("id", blog_id).execute()

        return redirect(url_for("admin_dashboard"))

    return render_template("edit_blog.html", blog=blog)


# ======================
# DELETE BLOG
# ======================
@app.route("/admin/delete/<blog_id>", methods=["POST"])
def delete(blog_id):
    supabase.table("blogs").delete().eq("id", blog_id).execute()
    return redirect(url_for("admin_dashboard"))





# ======================
# PASSWORD RESET
# ======================

@app.route("/admin/change-password", methods=["GET", "POST"])
def change_password():

    if request.method == "POST":

        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")

        # Get current admin
        admin = supabase.table("admin") \
            .select("*") \
            .eq("username", "admin") \
            .single() \
            .execute()

        if admin.data["password"] != old_password:
            flash("Old password is incorrect", "danger")
            return redirect("/admin/change-password")

        # Update password
        supabase.table("admin") \
            .update({"password": new_password}) \
            .eq("username", "admin") \
            .execute()

        flash("Password updated successfully", "success")
        return redirect("/admin/dashboard")

    return render_template("change_password.html")


@app.before_request
def session_timeout_check():

    if "admin_logged_in" in session:

        now = datetime.utcnow()

        last_activity = session.get("last_activity")

        # First time login
        if last_activity is None:
            session["last_activity"] = now.isoformat()
            return

        last_activity_time = datetime.fromisoformat(last_activity)

        # Check inactivity (3 minutes = 180 sec)
        if now - last_activity_time > timedelta(minutes=3):
            session.clear()
            return redirect("/admin/login")

        # Update last activity time
        session["last_activity"] = now.isoformat()

# ======================
# RUN APP
# ======================
if __name__ == "__main__":
    app.run(debug=True)
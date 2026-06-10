import os
import json
import uuid
import base64
from datetime import timedelta  # ⏱️ New import to handle session durations
from flask import Flask, render_template, request, flash, redirect, url_for, session
from cryptography.fernet import Fernet

app = Flask(__name__)
app.secret_key = "super_secret_session_key_change_me_later"

# ⏱️ SECURITY CONFIGURATION: Define the maximum idle timeout window
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)

BLOG_FILE = "blogs.json"
CONFIG_FILE = "config.json"

ENCRYPTION_KEY = b'kCZVE5_hlkePOLexPPYf-VHZEd0GzTjLSIhPMWVLwhc=' 
fernet = Fernet(ENCRYPTION_KEY)

DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "Password123"


# --- CONFIGURATION ENGINE ---

def initialize_admin_config():
    if not os.path.exists(CONFIG_FILE):
        initial_credentials = {"username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD}
        save_encrypted_file(initial_credentials, CONFIG_FILE)

def load_admin_credentials():
    if not os.path.exists(CONFIG_FILE):
        initialize_admin_config()
    try:
        with open(CONFIG_FILE, "rb") as f:
            encrypted_content = f.read().strip()
            if not encrypted_content:
                return {"username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD}
            return json.loads(fernet.decrypt(encrypted_content).decode())
    except Exception:
        return {"username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD}


# --- STORAGE UTILITIES ---

def load_encrypted_file(filepath):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "rb") as f:
            encrypted_content = f.read().strip()
            if not encrypted_content:
                return []
            return json.loads(fernet.decrypt(encrypted_content).decode())
    except Exception:
        return []

def save_encrypted_file(data, filepath):
    try:
        json_string = json.dumps(data, indent=4)
        encrypted_data = fernet.encrypt(json_string.encode())
        with open(filepath, "wb") as f:
            f.write(encrypted_data)
    except Exception as e:
        print(f"Error writing to {filepath}: {e}")


# --- PUBLIC SYSTEM ROADS ---

@app.route("/")
@app.route("/index")
def index():
    blogs = load_encrypted_file(BLOG_FILE)
    return render_template("index.html", blogs=reversed(blogs))


# --- 🔐 SECURE ADMIN GATEWAYS ---

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        current_admin = load_admin_credentials()
        
        if username == current_admin["username"] and password == current_admin["password"]:
            # ⏱️ Mark the session as permanent to activate the lifetime timeout config
            session.permanent = True
            session["admin_logged_in"] = True
            flash("Welcome back, Admin!", "success")
            return redirect(url_for("manage_blogs"))
        
        flash("Invalid credentials.", "danger")
        return redirect(url_for("admin_login"))
    return render_template("login.html")


@app.route("/admin/blogs", methods=["GET", "POST"])
def manage_blogs():
    # Session verification layer
    if not session.get("admin_logged_in"):
        flash("Your session has expired or access was denied. Please log in.", "danger")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        image_file = request.files.get("image")

        if not title or not content:
            flash("Fields cannot be blank!", "danger")
            return redirect(url_for("manage_blogs"))

        image_data = ""
        if image_file and image_file.filename != "":
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            image_data = f"data:{image_file.content_type};base64,{encoded_string}"

        blogs = load_encrypted_file(BLOG_FILE)
        blogs.append({"id": str(uuid.uuid4()), "title": title, "content": content, "image": image_data})
        save_encrypted_file(blogs, BLOG_FILE)
        flash("Blog published successfully!", "success")
        return redirect(url_for("manage_blogs"))

    active_tab = request.args.get("tab", "blogs")
    blogs = load_encrypted_file(BLOG_FILE)
    return render_template("manage_blogs.html", blogs=reversed(blogs), active_tab=active_tab)


@app.route("/admin/change-password", methods=["POST"])
def change_password():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    current_password_input = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    current_admin = load_admin_credentials()

    if current_password_input != current_admin["password"]:
        flash("Error: Current password verification failed.", "danger")
        return redirect(url_for("manage_blogs", tab="security"))

    if new_password != confirm_password:
        flash("Error: New passwords do not match.", "danger")
        return redirect(url_for("manage_blogs", tab="security"))

    save_encrypted_file({"username": current_admin["username"], "password": new_password}, CONFIG_FILE)
    
    flash("Success! Password changed. Session reset required.", "success")
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


@app.route("/admin/blogs/edit/<string:blog_id>", methods=["GET", "POST"])
def edit_blog(blog_id):
    if not session.get("admin_logged_in"):
        flash("Session expired.", "danger")
        return redirect(url_for("admin_login"))
        
    blogs = load_encrypted_file(BLOG_FILE)
    blog = next((b for b in blogs if b["id"] == blog_id), None)
    
    if request.method == "POST" and blog:
        blog["title"] = request.form.get("title", "").strip()
        blog["content"] = request.form.get("content", "").strip()
        image_file = request.files.get("image")
        if image_file and image_file.filename != "":
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            blog["image"] = f"data:{image_file.content_type};base64,{encoded_string}"
        save_encrypted_file(blogs, BLOG_FILE)
        flash("Updated!", "success")
        return redirect(url_for("manage_blogs"))
    return render_template("edit_blog.html", blog=blog)


@app.route("/admin/blogs/delete/<string:blog_id>", methods=["POST"])
def delete_blog(blog_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    blogs = load_encrypted_file(BLOG_FILE)
    save_encrypted_file([b for b in blogs if b["id"] != blog_id], BLOG_FILE)
    flash("Deleted!", "success")
    return redirect(url_for("manage_blogs"))


@app.route("/admin/logout")
def admin_logout():
    session.clear() # 🧹 Clear all variables completely on manual exit
    return redirect(url_for("admin_login"))

initialize_admin_config()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
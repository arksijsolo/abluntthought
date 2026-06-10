import os
import json
from flask import Flask, render_template, request

app = Flask(__name__)

DATA_FILE = "data.json"


# ✅ Safe JSON loader (prevents crash on empty, missing, or malformed files)
def load_data():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r") as f:
            content = f.read().strip()

            if not content:
                return []

            data = json.loads(content)
            
            # Double-check that the file contains a list so .append() works
            if isinstance(data, list):
                return data
            return []  # Fallback if the file somehow contains a dict {} instead of a list []

    except (json.JSONDecodeError, IOError):
        return []


# ✅ Save data safely with clean formatting
def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Error writing to file: {e}")


# ✅ Home page route
@app.route("/")
def home():
    return render_template("form.html")


# ✅ Submit form route
@app.route("/submit", methods=["POST"])
def submit():
    try:
        data = load_data()

        # Extract data matching the 'name' attributes in your HTML form
        new_entry = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "message": request.form.get("message")
        }

        # Check to ensure at least one field isn't empty before saving
        if not any(new_entry.values()):
            return "Error: Cannot submit an empty form.", 400

        data.append(new_entry)
        save_data(data)

        return "Saved successfully!"

    except Exception as e:
        return f"Server Error: {e}", 500


if __name__ == "__main__":
    # Standard Flask port 5000 bound strictly to localhost for reliable connection
    app.run(host="127.0.0.1", port=5000, debug=True)
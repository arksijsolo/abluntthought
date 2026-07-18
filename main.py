from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html", active="home")

@app.route("/about")
def about():
    return render_template("about.html", active="about")

@app.route("/contact")
def contact():
    return render_template("contact.html", active="contact")

if __name__ == "__main__":
    app.run(debug=True)
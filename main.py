import os
import smtplib
import threading
import time
from datetime import datetime
from email.mime.text import MIMEText

import requests
from dotenv import load_dotenv
from flask import Flask, render_template

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)


# --- Configuration ---------------------------------------------------------

GOLD_API_URL = os.getenv(
    "GOLD_API_URL",
    "https://api.gold-api.com/price/XAU"
)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

CHECK_INTERVAL_SECONDS = int(
    os.getenv("CHECK_INTERVAL_SECONDS", "300")
)


# --- Gold Price API --------------------------------------------------------

def get_gold_price() -> dict:
    """
    Fetch current gold price in USD per troy ounce.
    """
    response = requests.get(
        GOLD_API_URL,
        timeout=10
    )

    response.raise_for_status()

    return response.json()



# --- Email Builder ---------------------------------------------------------

def build_email_body(gold_data: dict) -> str:

    price = gold_data.get("price", "N/A")
    updated_at = gold_data.get("updatedAt", "N/A")

    checked_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return (
        "Gold Price Update\n"
        "=================\n\n"
        f"Current Price : ${price} USD per troy ounce\n"
        f"API Updated   : {updated_at}\n"
        f"Checked Time  : {checked_at}\n"
    )



# --- Send Email ------------------------------------------------------------

def send_email(subject: str, body: str) -> None:

    sender = os.getenv("SENDER_EMAIL")
    password = os.getenv("SENDER_PASSWORD")
    receiver = os.getenv("RECEIVER_EMAIL")


    missing = []

    if not sender:
        missing.append("SENDER_EMAIL")

    if not password:
        missing.append("SENDER_PASSWORD")

    if not receiver:
        missing.append("RECEIVER_EMAIL")


    if missing:
        raise RuntimeError(
            "Missing environment variable(s): "
            + ", ".join(missing)
        )


    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver


    with smtplib.SMTP(
        SMTP_SERVER,
        SMTP_PORT
    ) as server:

        server.starttls()

        server.login(
            sender,
            password
        )

        server.sendmail(
            sender,
            receiver,
            msg.as_string()
        )



# --- Background Scheduler --------------------------------------------------

def gold_price_loop():

    """
    Send gold price email every configured interval.
    """

    while True:

        try:

            gold_data = get_gold_price()

            body = build_email_body(
                gold_data
            )

            send_email(
                subject="Gold Price Update",
                body=body
            )


            print(
                f"[{datetime.now()}] "
                "Gold price email sent successfully."
            )


        except Exception as e:

            print(
                f"[{datetime.now()}] "
                f"Email failed: {e}"
            )


        time.sleep(
            CHECK_INTERVAL_SECONDS
        )



def start_scheduler():

    thread = threading.Thread(
        target=gold_price_loop,
        daemon=True
    )

    thread.start()



# --- Flask Routes ----------------------------------------------------------

@app.route("/")
def home():

    return render_template(
        "index.html",
        active="home"
    )



@app.route("/about")
def about():

    return render_template(
        "about.html",
        active="about"
    )



@app.route("/contact")
def contact():

    return render_template(
        "contact.html",
        active="contact"
    )



@app.route("/gold")
def gold():

    try:

        gold_data = get_gold_price()

        body = build_email_body(
            gold_data
        )

        send_email(
            subject="Gold Price Update",
            body=body
        )


        return (
            "<pre>"
            "Email sent successfully!\n\n"
            + body +
            "</pre>"
        )


    except requests.RequestException as e:

        return (
            f"Gold API error: {e}",
            502
        )


    except RuntimeError as e:

        return (
            f"Email configuration error: {e}",
            500
        )



# --- Application Start -----------------------------------------------------

if __name__ == "__main__":


    # Avoid duplicate scheduler when Flask debug reloads
    if (
        os.environ.get("WERKZEUG_RUN_MAIN") == "true"
        or not app.debug
    ):

        start_scheduler()


    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
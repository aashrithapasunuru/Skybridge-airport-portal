from flask import Flask, session, redirect, url_for
from flask import request, render_template
from datetime import datetime
from user_agents import parse
import sqlite3
import random

from database import init_db

app = Flask(__name__)
app.secret_key = "your_secret_key"

init_db()

def save_log(data):
    conn = sqlite3.connect("wifi_logs.db")
    c = conn.cursor()

    c.execute("""
    INSERT INTO logs (
    timestamp, ip, browser, os, device_type, username, wifi_id, latitude, longitude, user_agent) VALUES (?,?,?,?,?,?,?,?,?,?)""", data)

    conn.commit()
    conn.close()
    

@app.route("/")
def home():

    return render_template("home.html")

@app.route("/connect", methods=["POST"])
def connect():

    username = request.form.get("fullname")

    if not username or username.strip() == "":
        username = "Guest"

    lat = request.form.get("lat", "unknown")
    lon = request.form.get("lon", "unknown")

    user_agent_string = request.headers.get("User-Agent", "")
    ua = parse(user_agent_string)
    

    browser = ua.browser.family
    os_name = ua.os.family

    device_type = (
            "Mobile" if ua.is_mobile else
            "Tablet" if ua.is_tablet else
            "Desktop"
            )


    ip = request.remote_addr
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    
    wifi_id = f"WIFI-{random.randint(1000,9999)}"

    session["username"] = username
    session["wifi_id"] = wifi_id


    save_log((
            timestamp,
            ip,
            browser,
            os_name,
            device_type,
            username,
            wifi_id,
            lat,
            lon,
            user_agent_string
            ))
        

    return redirect(url_for("success", username=username, wifi_id=wifi_id))

@app.route("/success")
def success():

    username = session.get("username", "Guest")
    wifi_id = session.get("wifi_id", "N/A")

    return render_template(
            "success.html",
            username=username,
            wifi_id=wifi_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )


@app.route("/admin/logs")
def logs():

    conn = sqlite3.connect("wifi_logs.db")

    c = conn.cursor()

    c.execute("SELECT * FROM logs ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    return render_template("dashboard.html", logs=rows)
       


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

from flask import Flask, session, redirect, url_for
from flask import request, render_template
from datetime import datetime
from user_agents import parse
import sqlite3
import random
import re
import os

from database import init_db

app = Flask(__name__)
app.secret_key = "your_secret_key"

init_db()

def save_log(data):
    print("INSERTING:", data)
    conn = sqlite3.connect("wifi_logs.db")
    c = conn.cursor()

    c.execute("""
    INSERT INTO logs (
    timestamp, ip, browser, os, device_type, username, phone, email, wifi_id, location_status, latitude, longitude, user_agent_string, connection_status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", data)

    conn.commit()
    conn.close()
    

@app.route("/")
def home():

    return render_template("airport_portal.html")


@app.route("/guest")
def guest():
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


    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip = ip.split(",")[0].strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    
    email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    phone_pattern = r'^[0-9]{10}$'

    

    if not re.match(email_pattern, email):
      email = "invalid"

    if not re.match(phone_pattern, phone):
      phone = "invalid"

    
    wifi_id = f"WIFI-{random.randint(1000,9999)}"

    session["username"] = username
    session["wifi_id"] = wifi_id

    location_status = "Allowed"
    connection_status = "Connected"
    session["connection_status"] = connection_status


    save_log((
            timestamp,
            ip,
            browser,
            os_name,
            device_type,
            username,
            phone,
            email,
            wifi_id,
            location_status,
            lat,
            lon,
            user_agent_string,
            connection_status
            ))
        

    return redirect(url_for("success", username=username, wifi_id=wifi_id))

@app.route("/success")
def success():

    username = session.get("username", "Guest")
    wifi_id = session.get("wifi_id", "N/A")
    connection_status = session.get("connection_status", "Unknown")

    return render_template(
            "success.html",
            username=username,
            wifi_id=wifi_id,
            connection_status=connection_status,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )


@app.route("/admin/logs")
def logs():

    conn = sqlite3.connect("wifi_logs.db")
    print("DB PATH:", os.path.abspath("wifi_logs.db"))

    c = conn.cursor()

    rows = c.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()
    conn.close()

    return render_template("dashboard.html", logs=rows)
       


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

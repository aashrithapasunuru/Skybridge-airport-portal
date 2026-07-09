from flask import Flask, session, redirect, url_for
from flask import request, render_template
from datetime import datetime
from user_agents import parse
from flask import flash
import sqlite3
import random
import re
import os
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import secrets
import string


from database import init_db

def get_db_connection():
    conn = sqlite3.connect("wifi_logs.db")
    conn.row_factory = sqlite3.Row
    return conn


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



@app.route("/employee/login", methods=["GET", "POST"])
def employee_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()

        employee = conn.execute(
            "SELECT * FROM employees WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        # User not found
        if employee is None:
            return "Invalid username or password"

        # Account locked
        if employee["account_status"] == "Locked":
            return "Your account has been locked. Please contact the administrator."
                
            
            return redirect(url_for("employee_login"))

        # Wrong password
        if not check_password_hash(employee["password"], password):
            return "Invalid username or password"

        # Successful login
        session["employee"] = employee["username"]
        session["role"] = employee["role"]

        if employee["must_change_password"] == "Yes":
            return redirect(url_for("change_password"))

        if employee["role"] == "Super Admin":
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("employee_dashboard"))

    # GET request
    return render_template("employee_login.html")


@app.route("/admin/logs")
def guest_logs():

    conn = sqlite3.connect("wifi_logs.db")
    print("DB PATH:", os.path.abspath("wifi_logs.db"))

    c = conn.cursor()

    rows = c.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()
    conn.close()

    return render_template("dashboard.html", logs=rows)


@app.route("/admin/employees")
def employees():

    conn = sqlite3.connect("wifi_logs.db")

    c = conn.cursor()

    rows = c.execute("SELECT * FROM employees ORDER BY id DESC").fetchall()
    conn.close()

    total_employees = len(rows)

    high_risk_users = sum(
            1 for e in rows if int(e[11]) >= 3
            )

    locked_accounts = sum(
            1 for e in rows if e[6] == "Locked"
            )
    suspicious_accounts = sum(
            1 for e in rows if e[6] == "Suspicious"
            )

    return render_template(
            "employees.html", 
             employees=rows,
             total_employees=total_employees,
             high_risk_users=high_risk_users,
             locked_accounts=locked_accounts,
             suspicious_accounts=suspicious_accounts
             )


@app.route("/admin/employee/<int:employee_id>")
def view_employee(employee_id):

    conn = get_db_connection()

    employee = conn.execute(
            "SELECT * FROM employees WHERE id = ?",
            (employee_id,)
            ).fetchone()

    conn.close()

    if employee is None:
        return "Employee not found", 404

    return render_template(
            "view_employee.html",
            employee=employee

            )

@app.route("/admin/employee/<int:employee_id>/lock")
def lock_employee(employee_id):

    conn = get_db_connection()

    employee = conn.execute(
            "SELECT * FROM employees WHERE id = ?",
            (employee_id,)
            ).fetchone()

    if employee is None:
        conn.close()
        return "Employee not found", 404

    conn.execute("""
        UPDATE employees
        SET account_status = 'Locked'
        WHERE id = ?
        """, (employee_id,))

    conn.execute("""
       INSERT INTO security_logs
       (
         timestamp,
         employee_id,
         username,
         event_type,
         ip_address,
         location_status,
         connection_status,
         severity,
         notes
         )
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

         """, (
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             employee["employee_id"],
             employee["username"],
             "Account Locked",
             request.remote_addr,
             "Internal",
             "Success",
             "High",
             "Locked by administrator"

             ))

    

    conn.commit()
    conn.close()

    return redirect(url_for("employees"))

@app.route("/admin/employee/<int:employee_id>/unlock")
def unlock_employee(employee_id):

    conn = get_db_connection()

    employee = conn.execute(
            "SELECT * FROM employees WHERE id = ?",
            (employee_id,)
            ).fetchone()

    if employee is None:
     conn.close()
     return "Employee not found", 404

    conn.execute("""
      UPDATE employees
      SET account_status = 'Active'
      WHERE id = ?
      """, (employee_id,))

    conn.execute("""
       INSERT INTO security_logs (
           timestamp,
           employee_id,
           username,
           event_type,
           ip_address,
           location_status,
           connection_status,
           severity,
           notes
           )
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           """, (
               datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               employee["employee_id"],
               employee["username"],
               "Account Unlocked",
               request.remote_addr,
               "Internal",
               "Success",
               "Medium",
               "Unlocked by administrator"
               ))

    conn.commit()
    conn.close()

    return redirect(url_for("employees"))


@app.route("/admin/employee/<int:employee_id>/reset_password")
def reset_employee_password(employee_id):

    conn = get_db_connection()


    employee = conn.execute(
            "SELECT * FROM employees WHERE id = ?",
            (employee_id,)
            ).fetchone()

    if employee is None:

        conn.close()
        return "Employee not found", 404


    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"

    temporary_password = "".join(
       secrets.choice(alphabet) for _ in range(12)
       )

    hashed_password = generate_password_hash(temporary_password)

    conn.execute("""
      UPDATE employees
      SET password = ?,
         must_change_password = 'Yes',
         password_last_changed = ?
      WHERE id = ?
      """, (
          hashed_password,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          employee_id
          ))

    conn.execute("""
          INSERT INTO security_logs (
              timestamp,
              employee_id,
              username,
              event_type,
              ip_address,
              location_status,
              connection_status,
              severity,
              notes

              )
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
              """, (
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  employee["employee_id"],
                  employee["username"],
                  "Password Reset",
                  request.remote_addr,
                  "Internal",
                  "Success",
                  "Medium",
                  "Administrator reset employee password"
                  ))

    conn.commit()
    conn.close()

    flash(
            f"Temporary password for {employee['username']}: {temporary_password}",
            "success"

            )
    return redirect(url_for("employees"))



@app.route("/admin/security_logs")
def security_logs():

    conn = get_db_connection()

    logs = conn.execute("""
        SELECT * FROM security_logs
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "security_logs.html",
        logs=logs
    )

@app.route("/employee/dashboard")
def employee_dashboard():

    if "employee" not in session:
        return redirect(url_for("employee_login"))

    conn = get_db_connection()

    employee = conn.execute(
            "SELECT * FROM employees WHERE username = ?",
            (session["employee"],)
            ).fetchone()
    
    emails = conn.execute("""
       SELECT *
       FROM emails
       WHERE employee_id = ?
       ORDER BY received_at DESC
       """, (
           employee["employee_id"],
           )).fetchall()


    conn.close()


    return render_template("employee_dashboard.html", 
                           employee=employee,
                           emails=emails
                           )

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("employee_login"))

@app.route("/change_password", methods=["GET", "POST"])
def change_password():

    if "employee" not in session:
        return redirect(url_for("employee_login"))

    if request.method == "POST":

        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            return "Passwords do not match"

        hashed_password = generate_password_hash(new_password)

        conn = get_db_connection()

        employee = conn.execute(
                "SELECT * FROM employees WHERE username = ?",
                (session["employee"],)
                ).fetchone()

        conn.execute("""
            UPDATE employees
            SET password = ?,
                password_last_changed = ?,
                must_change_password = 'No'
            WHERE username = ?
        """, (
            hashed_password,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            session["employee"]
        ))

        conn.execute("""
        INSERT INTO security_logs (
          timestamp,
          employee_id,
          username,
          event_type,
          ip_address,
          location_status,
          connection_status,
          severity,
          notes
       )

      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      """, (
      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      employee["employee_id"],
      employee["username"],
      "Password Changed",
      request.remote_addr,
      "Internal",
      "Success",
      "Medium",
      "User changed temporary password"
  ))

        conn.commit()
        conn.close()

        return redirect(url_for("employee_dashboard"))

    return render_template("change_password.html")



@app.route("/admin/dashboard")
def admin_dashboard():
    
    conn = sqlite3.connect("wifi_logs.db")
    cursor = conn.cursor()

    #Total employees
    cursor.execute("SELECT COUNT(*) FROM employees")
    total_employees = cursor.fetchone()[0]

    #Total accounts locked
    cursor.execute("""SELECT COUNT(*) FROM employees WHERE account_status = 'Locked'""")
    locked_accounts = cursor.fetchone()[0]

    #Password change required
    cursor.execute("""SELECT COUNT(*) FROM employees WHERE must_change_password = 'Yes'""")
    password_change_required = cursor.fetchone()[0]

    conn.close()

    return render_template("admin_dashboard.html",
                           total_employees=total_employees,
                           locked_accounts=locked_accounts,
                           password_change_required=password_change_required
                           )


@app.route("/employee/inbox")
def employee_inbox():

    if "employee" not in session:
        return redirect(url_for("employee_login"))

    conn = get_db_connection()

    employee = conn.execute(
        "SELECT * FROM employees WHERE username = ?",
        (session["employee"],)
    ).fetchone()

    emails = conn.execute("""
        SELECT *
        FROM emails
        WHERE employee_id = ?
        ORDER BY received_at DESC
    """, (
        employee["employee_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "employee_inbox.html",
        employee=employee,
        emails=emails
    )


@app.route("/employee/email/<int:email_id>")
def view_email(email_id):

    if "employee" not in session:
        return redirect(url_for("employee_login"))

    conn = get_db_connection()

    email = conn.execute(
        "SELECT * FROM emails WHERE id = ?",
        (email_id,)
    ).fetchone()

    conn.execute(
        "UPDATE emails SET is_read = 1 WHERE id = ?",
        (email_id,)
    )

    conn.commit()
    conn.close()

    return render_template(
        "view_email.html",
        email=email
    ) 


       
@app.route("/admin/send_email", methods=["GET", "POST"])
def send_email():

    conn = get_db_connection()

    employees = conn.execute("""
        SELECT employee_id, username
        FROM employees
        ORDER BY username
    """).fetchall()

    if request.method == "POST":

        employee_id = request.form["employee_id"]
        subject = request.form["subject"]
        body = request.form["body"]

        if employee_id == "ALL":

            all_users = conn.execute("""
              SELECT employee_id
              FROM employees
              """).fetchall()
            
            for user in all_users:
                conn.execute("""
                INSERT INTO emails (
                employee_id,
                sender,
                subject,
                body,
                received_at,
                is_read
                )
                VALUES (?, ?, ?, ?, datetime('now'), 0)
              """, (
                user["employee_id"],
                "Airport SOC",
                subject,
                body
                ))
        else:

             conn.execute("""
                INSERT INTO emails (
                employee_id,
                sender,
                subject,
                body,
                received_at,
                is_read
                )
                VALUES (?, ?, ?, ?, datetime('now'), 0)
                """, (
                    employee_id,
                    "Airport SOC",
                    subject,
                    body
                    ))


        conn.commit()

        flash("Email sent successfully!", "success")

        return redirect(url_for("send_email"))

    conn.close()

    return render_template(
        "send_email.html",
        employees=employees
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

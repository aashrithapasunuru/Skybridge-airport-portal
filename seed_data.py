import sqlite3
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

conn = sqlite3.connect("wifi_logs.db")
cursor = conn.cursor()

departments = [
    "SOC",
    "IT Support",
    "Network Operations",
    "Security Engineering",
    "HR",
    "Finance",
    "Management"
]

roles = [
    "SOC Analyst L1",
    "SOC Analyst L2",
    "Network Analyst",
    "System Administrator",
    "Help Desk",
    "HR Manager",
    "Finance Analyst"
]

statuses = ["Active", "Locked", "Suspicious"]
mfa_options = ["Yes", "No"]

# -------------------------
# Create 100 Employees
# -------------------------

for i in range(1, 101):

    employee_id = f"EMP{i:03}"

    username = f"user{i}"


    full_name = f"Employee {i}"

    department = random.choice(departments)

    role = random.choice(roles)

    if i <= 80:
        account_status = "Active"
    elif i <= 90:
        account_status = "Locked"
    else:
        account_status = "Suspicious"

    mfa_enabled = random.choices(
        ["Yes", "No"],
        weights=[75, 25]
    )[0]

    failed_attempts = random.randint(0, 6)

    last_login = (
        datetime.now() -
        timedelta(days=random.randint(0, 30))
    ).strftime("%Y-%m-%d %H:%M:%S")

    created_date = (
        datetime.now() -
        timedelta(days=random.randint(30, 365))
    ).strftime("%Y-%m-%d")

    password_changed = (
        datetime.now() -
        timedelta(days=random.randint(1, 180))
    ).strftime("%Y-%m-%d")

    account_locked_until = None

    if account_status == "Locked":
        account_locked_until = (
            datetime.now() +
            timedelta(hours=2)
        ).strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute("""
        INSERT INTO employees (
            employee_id,
            username,
            full_name,
            department,
            role,
            account_status,
            mfa_enabled,
            last_login,
            created_by,
            created_date,
            failed_login_attempts,
            password_last_changed,
            account_locked_until
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            employee_id,
            username,
            full_name,
            department,
            role,
            account_status,
            mfa_enabled,
            last_login,
            "admin",
            created_date,
            failed_attempts,
            password_changed,
            account_locked_until
        ))

    except sqlite3.IntegrityError:
        pass

# -------------------------
# Create 500 Security Logs
# -------------------------

event_types = [
    ("Login Success", "Low"),
    ("Failed Login", "Medium"),
    ("Password Reset", "High"),
    ("Location Denied", "Medium"),
    ("Account Locked", "High"),
    ("Suspicious Activity", "High")
]

for _ in range(500):

    employee_num = random.randint(1, 100)

    employee_id = f"EMP{employee_num:03}"

    username = f"user{employee_num}"

    event_type, severity = random.choice(event_types)

    timestamp = (
        datetime.now() -
        timedelta(hours=random.randint(0, 720))
    ).strftime("%Y-%m-%d %H:%M:%S")

    ip_address = (
        f"192.168.{random.randint(1,10)}."
        f"{random.randint(1,254)}"
    )

    location_status = random.choice(
        ["Allowed", "Denied"]
    )

    connection_status = random.choice(
        ["Connected", "Disconnected"]
    )

    notes = f"{event_type} generated for testing"

    cursor.execute("""
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
        timestamp,
        employee_id,
        username,
        event_type,
        ip_address,
        location_status,
        connection_status,
        severity,
        notes
    ))

conn.commit()
conn.close()

print("100 employees created")
print("500 security logs created")

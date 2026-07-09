import sqlite3


def init_db():
    conn = sqlite3.connect("wifi_logs.db")

    c = conn.cursor()

    c.execute("""

    CREATE TABLE IF NOT EXISTS logs (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    ip TEXT,
    browser TEXT,
    os TEXT,
    device_type TEXT,
    username TEXT,
    phone TEXT,
    email TEXT,
    wifi_id TEXT,
    location_status TEXT,
    latitude TEXT,
    longitude TEXT,
    user_agent_string TEXT,
    connection_status TEXT
    )
    """)

    c.execute("""

    CREATE TABLE IF NOT EXISTS emails (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    received_at TEXT NOT NULL,
    is_read INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


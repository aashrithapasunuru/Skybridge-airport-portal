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
    wifi_id TEXT,
    latitude TEXT,
    longitude TEXT,
    user_agent TXT
    )
    """)

    conn.commit()
    conn.close()


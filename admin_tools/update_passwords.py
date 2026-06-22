import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

conn = sqlite3.connect("wifi_logs.db")
cursor = conn.cursor()

hashed_password = generate_password_hash("Password123!")
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

cursor.execute("""
UPDATE employees
SET password = ?,
    password_last_changed = ?    
""", (hashed_password, now))

conn.commit()
conn.close()

print("Passwords updated successfully.")

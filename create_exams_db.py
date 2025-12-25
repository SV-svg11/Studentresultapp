
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_DB = os.path.join(BASE_DIR, "exams.db")

conn = sqlite3.connect(USERS_DB)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_name TEXT UNIQUE NOT NULL
);
""")

conn.commit()
conn.close()

print("✅ users.db created successfully")

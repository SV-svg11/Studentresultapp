import sqlite3

conn = sqlite3.connect("results.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    subject1 INTEGER,
    subject2 INTEGER,
    subject3 INTEGER,
    total INTEGER,
    grade TEXT
)
""")

conn.commit()
conn.close()

print("Database created successfully!")



import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_DB = os.path.join(BASE_DIR, "marks.db")

conn = sqlite3.connect(USERS_DB)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    exam_id INTEGER,
    subject TEXT,
    marks INTEGER,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (exam_id) REFERENCES exams(id)
);
""")

conn.commit()
conn.close()

print("✅ users.db created successfully")

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "results.db")

print("Trying DB:", DB_PATH)

conn = sqlite3.connect(DB_PATH)
print("DB opened successfully!")
conn.close()

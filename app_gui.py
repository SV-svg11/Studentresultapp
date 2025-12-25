import tkinter as tk
from tkinter import messagebox
import sqlite3

# ---------- DATABASE FUNCTIONS ----------
def calculate_grade(total):
    if total >= 270:
        return "A"
    elif total >= 210:
        return "B"
    elif total >= 150:
        return "C"
    else:
        return "Fail"

def add_student():
    name = entry_name.get()
    s1 = entry_s1.get()
    s2 = entry_s2.get()
    s3 = entry_s3.get()

    if not name or not s1 or not s2 or not s3:
        messagebox.showerror("Error", "All fields are required")
        return

    total = int(s1) + int(s2) + int(s3)
    grade = calculate_grade(total)

    conn = sqlite3.connect("results.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO students (name, subject1, subject2, subject3, total, grade)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, s1, s2, s3, total, grade))
    conn.commit()
    conn.close()

    messagebox.showinfo("Success", f"Total: {total} | Grade: {grade}")
    clear_fields()

def view_results():
    conn = sqlite3.connect("results.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, total, grade FROM students")
    rows = cursor.fetchall()
    conn.close()

    result_text.delete("1.0", tk.END)
    for r in rows:
        result_text.insert(tk.END, f"Name: {r[0]} | Total: {r[1]} | Grade: {r[2]}\n")

def clear_fields():
    entry_name.delete(0, tk.END)
    entry_s1.delete(0, tk.END)
    entry_s2.delete(0, tk.END)
    entry_s3.delete(0, tk.END)

# ---------- GUI ----------
root = tk.Tk()
root.title("Student Result Management System")
root.geometry("450x450")

tk.Label(root, text="Student Result System", font=("Arial", 16)).pack(pady=10)

tk.Label(root, text="Student Name").pack()
entry_name = tk.Entry(root)
entry_name.pack()

tk.Label(root, text="Subject 1 Marks").pack()
entry_s1 = tk.Entry(root)
entry_s1.pack()

tk.Label(root, text="Subject 2 Marks").pack()
entry_s2 = tk.Entry(root)
entry_s2.pack()

tk.Label(root, text="Subject 3 Marks").pack()
entry_s3 = tk.Entry(root)
entry_s3.pack()

tk.Button(root, text="Add Result", command=add_student).pack(pady=10)
tk.Button(root, text="View Results", command=view_results).pack()

result_text = tk.Text(root, height=10)
result_text.pack(pady=10)

root.mainloop()

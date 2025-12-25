import os
import sqlite3
import tkinter as tk
from tkinter import messagebox
import pandas as pd
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "results.db")
USERS_DB = os.path.join(BASE_DIR, "users.db")

def init_users_db():
    pass
def init_students_db():
    DB_PATH = os.path.join(BASE_DIR, "results.db")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students
                   ( 
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admission_year INTEGER NOT NULL,
        admission_no TEXT NOT NULL UNIQUE,
        student_name TEXT NOT NULL,
        class_name TEXT NOT NULL,
                   );
                
            """)
    conn.commit()
    conn.close()

class StudentResultApp:
    def __init__(self):    
        init_users_db()
        init_students_db()
        self.show_login()

    def show_login(self):
        self.login_window = tk.Tk()
        self.login_window.title("Teacher Login / Signup")
        self.login_window.geometry("350x300")

        tk.Label(
            self.login_window,
            text="Student Result System",
            font=("Arial", 16)
        ).pack(pady=10)

        tk.Label(self.login_window, text="Username").pack()
        self.entry_username = tk.Entry(self.login_window)
        self.entry_username.pack()

        tk.Label(self.login_window, text="Password").pack()
        self.entry_password = tk.Entry(self.login_window, show="*")
        self.entry_password.pack()

        tk.Button(
            self.login_window,
            text="Login",
            width=15,
            command=self.login
        ).pack(pady=10)

        tk.Button(
            self.login_window,
            text="Sign Up",
            width=15,
            command=self.signup
        ).pack()

        self.login_window.mainloop()
    def login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "All fields required")
            return

        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            self.login_window.destroy()
            self.show_main_app()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
    def signup(self):
            
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "All fields required")
            return

        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
            messagebox.showinfo(
                "Success",
                "Signup successful! You can now login."
            )
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
        finally:
            conn.close()
    def show_main_app(self):
        self.root = tk.Tk()
        self.root.title("Student Result Management System")
        self.root.geometry("480x550")

        tk.Label(self.root, text="Student Result System",
                 font=("Arial", 16)).pack(pady=10)

        tk.Button(self.root, text="Logout",
                  fg="red", command=self.logout).pack()

        tk.Label(self.root, text="Student Name").pack()
        self.entry_name = tk.Entry(self.root)
        self.entry_name.pack()

        tk.Label(self.root, text="Subject 1 Marks").pack()
        self.entry_s1 = tk.Entry(self.root)
        self.entry_s1.pack()

        tk.Label(self.root, text="Subject 2 Marks").pack()
        self.entry_s2 = tk.Entry(self.root)
        self.entry_s2.pack()

        tk.Label(self.root, text="Subject 3 Marks").pack()
        self.entry_s3 = tk.Entry(self.root)
        self.entry_s3.pack()

        tk.Button(self.root, text="Add Result",
                  command=self.add_student).pack(pady=5)

        tk.Label(self.root, text="Search (Name / ID)").pack()
        self.entry_search = tk.Entry(self.root)
        self.entry_search.pack()

        tk.Button(self.root, text="Search",
                  command=self.search_student).pack(pady=5)

        tk.Button(self.root, text="View Results",
                  command=self.view_results).pack(pady=5)

        tk.Button(self.root, text="Export to Excel",
                  command=self.export_to_excel).pack(pady=5)

        self.result_text = tk.Text(self.root, height=10)
        self.result_text.pack(pady=10)

        self.root.mainloop()
    def calculate_grade(self, total):
        if total >= 270:
            return "A"
        elif total >= 210:
            return "B"
        elif total >= 150:
            return "C"
        else:
            return "Fail"
    def add_student(self):
        name = self.entry_name.get().strip()
        s1 = self.entry_s1.get().strip()
        s2 = self.entry_s2.get().strip()
        s3 = self.entry_s3.get().strip()

        if not name or not s1 or not s2 or not s3:
            messagebox.showerror("Error", "All fields required")
            return

        if not (s1.isdigit() and s2.isdigit() and s3.isdigit()):
            messagebox.showerror("Error", "Marks must be numbers")
            return

        s1, s2, s3 = int(s1), int(s2), int(s3)

        for m in (s1, s2, s3):
            if m < 0 or m > 100:
                messagebox.showerror("Error", "Marks must be 0–100")
                return

        total = s1 + s2 + s3
        grade = self.calculate_grade(total)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students
            (name, subject1, subject2, subject3, total, grade)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, s1, s2, s3, total, grade))
        conn.commit()
        conn.close()

        messagebox.showinfo("Success",
                            f"Total: {total}\nGrade: {grade}")

        self.clear_fields()
    def search_student(self):
        keyword = self.entry_search.get()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if keyword.isdigit():
            cursor.execute(
                "SELECT name, total, grade FROM students WHERE id=?",
                (int(keyword),))
        else:
            cursor.execute(
                "SELECT name, total, grade FROM students WHERE name LIKE ?",
                (f"%{keyword}%",))

        rows = cursor.fetchall()
        conn.close()

        self.result_text.delete("1.0", tk.END)

        if rows:
            for r in rows:
                self.result_text.insert(
                    tk.END, f"{r[0]} | {r[1]} | {r[2]}\n")
        else:
            self.result_text.insert(tk.END, "No record found\n")
    def view_results(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, total, grade FROM students")
        rows = cursor.fetchall()
        conn.close()

        self.result_text.delete("1.0", tk.END)
        for r in rows:
            self.result_text.insert(
                tk.END, f"{r[0]} | {r[1]} | {r[2]}\n")
    def export_to_excel(self):
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            "SELECT name, subject1, subject2, subject3, total, grade FROM students",
            conn)
        conn.close()

        if df.empty:
            messagebox.showwarning("No Data", "No records found")
            return

        df.to_excel("Student_Results.xlsx", index=False)
        messagebox.showinfo("Success", "Exported to Excel")
    def clear_fields(self):
        self.entry_name.delete(0, tk.END)
        self.entry_s1.delete(0, tk.END)
        self.entry_s2.delete(0, tk.END)
        self.entry_s3.delete(0, tk.END)
    def logout(self):
        self.root.destroy()
        self.show_login()
if __name__ == "__main__":
    StudentResultApp()

#needed modules for the application
import os
import sqlite3
import tkinter as tk
from tkinter import messagebox
import pandas as pd

#-------------------------------------------------------------------------------------------------------------------------------------------#

#Databases paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "results.db")
USERS_DB = os.path.join(BASE_DIR, "users.db")

#-------------------------------------------------------------------------------------------------------------------------------------------#

def init_users_db():
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def init_students_db():
    DB_PATH = os.path.join(BASE_DIR, "results.db")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students( 
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admission_year INTEGER NOT NULL,
        admission_no TEXT NOT NULL UNIQUE,
        student_name TEXT NOT NULL,
        class_name TEXT NOT NULL,
        year_serial INTEGER NOT NULL
                   );
                
            """)
    conn.commit()
    conn.close()
def generate_admission_no(admission_year):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT MAX(year_serial) FROM students WHERE admission_year=?""", (admission_year,))
    max_serial = cursor.fetchone()[0]
    if max_serial is None:
        max_serial = 0

    next_serial = max_serial + 1
    admission_no = f"{admission_year}-{next_serial:03d}"
    conn.close()
    return next_serial, admission_no
def init_exams_db():
    DB_PATH = os.path.join(BASE_DIR, "results.db")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exams(
                id INTEGER PRIMARY KEY AUTOINCREMENT,   
                max_marks INTEGER NOT NULL,
                exam_name TEXT NOT NULL,
                exam_type TEXT NOT NULL,
                academic_year TEXT NOT NULL
                ); """)
    conn.commit()
    conn.close()
def init_marks_db():
    DB_PATH = os.path.join(BASE_DIR, "results.db")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,  
                admission_no TEXT NOT NULL,
                exam_id INTEGER NOT NULL, 
                score INTEGER NOT NULL

                ); """)
    conn.commit()
    conn.close()
class StudentResultApp:
    def open_register_student(self):
        self.register_window = tk.Toplevel(self.root)
        self.register_window.title("Register Student")
        self.register_window.geometry("400x300")
        tk.Label(self.register_window, text="Student Registration", font=("Calibri", 20, "bold")).pack()


    
    def add_exam(self):
        exam_type = self.exam_type_var.get()
        exam_number = self.entry_exam_number.get().strip()
        academic_year = self.entry_exam_year.get().strip()
        max_marks = self.entry_max_marks.get().strip()

        if not exam_number or not academic_year or not max_marks or not exam_type:
            messagebox.showerror("Error", "All fields required")
            return
        if not max_marks.isdigit():
            messagebox.showerror("Error", "Max marks must be a number")
            return
        if not exam_number.isdigit():
            messagebox.showerror("Error", "Exam number must be a number")
            return
        
        academic_year = academic_year

        if "-" not in academic_year:
            messagebox.showerror("Error", "Academic year must be in format YYYY-YY")
            return
        
        parts = academic_year.split("-")
        if len(parts) !=2:
            messagebox.showerror("Error", "Academic year must be in format YYYY-YY")
            return
        
        start_year = parts[0]
        end_year = parts[1]

        if len(start_year) !=4 or len(end_year) !=2 or not start_year.isdigit() or not end_year.isdigit():
            messagebox.showerror("Error", "Academic year must be in format YYYY-YY")
            return

        exam_number = int(exam_number)
        max_marks = int(max_marks)

        exam_name = f"{exam_type}-{exam_number}"
        print(exam_name)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO exams (exam_name, exam_type, academic_year, max_marks)
            VALUES (?, ?, ?, ?)
        """, (exam_name, exam_type, academic_year, max_marks))
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", f"Exam {exam_name} added successfully")
    def __init__(self):    
        init_users_db()
        init_students_db()
        init_exams_db()
        init_marks_db()
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

        tk.Label(self.root, text="Admission Year").pack()
        self.entry_year = tk.Entry(self.root)
        self.entry_year.pack()

        tk.Label(self.root, text="Class Name").pack()
        self.entry_class = tk.Entry(self.root)
        self.entry_class.pack()
        
        """tk.Label(self.root, text="Subject 1 Marks").pack()
        self.entry_s1 = tk.Entry(self.root)
        self.entry_s1.pack()

        tk.Label(self.root, text="Subject 2 Marks").pack()
        self.entry_s2 = tk.Entry(self.root)
        self.entry_s2.pack()

        tk.Label(self.root, text="Subject 3 Marks").pack()
        self.entry_s3 = tk.Entry(self.root)
        self.entry_s3.pack()"""

        tk.Button(self.root, text="Add Result", command=self.add_student).pack(pady=5)
        tk.Button(self.root,text="Register Student",command=self.open_register_student).pack(pady=5)


        tk.Label(self.root, text="Search (Name / ID)").pack()
        self.entry_search = tk.Entry(self.root)
        self.entry_search.pack()

        tk.Button(self.root,text="Enter Marks",command=self.open_marks_window).pack(pady=5)


        #tk.Button(self.root, text="Search", command=self.search_student).pack(pady=5)

        #tk.Button(self.root, text="View Results",command=self.view_results).pack(pady=5)

        #tk.Button(self.root, text="Export to Excel",  command=self.export_to_excel).pack(pady=5)

        self.result_text = tk.Text(self.root, height=10)
        self.result_text.pack(pady=10)

        tk.Label(self.root, text="Exam Management", font=("Arial", 16)).pack()

        self.entry_exam_number = tk.Entry(self.root)
        self.entry_exam_number.pack()

        tk.Label(self.root, text="Academic Year").pack()
        self.entry_exam_year = tk.Entry(self.root)
        self.entry_exam_year.pack()

        tk.Label(self.root, text="Max Marks").pack()
        self.entry_max_marks = tk.Entry(self.root)
        self.entry_max_marks.pack()

        self.exam_type_var = tk.StringVar()
        self.exam_type_var.set("PT")   # default value

        tk.OptionMenu(
            self.root,
            self.exam_type_var,
            "PT",
            "TE"
        ).pack()


        tk.Button(self.root, text="Add Exam" , command=self.add_exam).pack(pady=5)


        self.root.mainloop()
    def open_marks_window(self):
        self.marks_window=tk.Toplevel(self.root)
        self.marks_window.title("Enter Marks")  
        self.marks_window.geometry("400x300")

        tk.Label(self.marks_window, text="Enter Marks for Each Subject").pack(pady=10)
        DB_PATH = os.path.join(BASE_DIR, "results.db")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, exam_name, academic_year FROM exams")
        rows = cursor.fetchall()
        conn.close()
        exams = [rows[1] for rows in rows]
        self.exam_var = tk.StringVar()
        tk.OptionMenu(self.marks_window, self.exam_var, *exams).pack(pady=5)
        tk.Label(self.marks_window, text="Admission No").pack()
        self.entry_admission_no = tk.Entry(self.marks_window)
        self.entry_admission_no.pack()

        selected_exam = self.exam_var.get()

        tk.Label(self.marks_window, text="Score").pack()
        self.entry_score = tk.Entry(self.marks_window)
        self.entry_score.pack()

        def save_marks():
            admission_no = self.entry_admission_no.get().strip()
            selected_exam = self.exam_var.get()
            score = self.entry_score.get().strip()
            if not admission_no or not selected_exam or not score:
                messagebox.showerror("Error", "All fields required")
                return
            if not score.isdigit():
                messagebox.showerror("Error", "Score must be a number")
                return
            score = int(score)
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM students WHERE admission_no=?", (admission_no,))
            if not cursor.fetchone():
                messagebox.showerror("Error", "No student found")
                conn.close()
                return
            cursor.execute("SELECT id FROM exams WHERE exam_name=?", (selected_exam,))
            row = cursor.fetchone()
            if row is None:
                messagebox.showerror("Error", "Invalid exam")
                conn.close()
                return
            exam_id = row[0]
            cursor.execute("""
                INSERT INTO marks (student_admission_no, exam_id, score)
                VALUES (?, ?, ?)
            """, (admission_no, exam_id, score))

            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Marks saved successfully")

        tk.Button(self.marks_window, text="Save Marks", command=save_marks).pack(pady=10)



        print(rows)
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
        admission_year = self.entry_year.get().strip()
        class_name = self.entry_class.get().strip()
        student_name = self.entry_name.get().strip()

        # 1) Presence check FIRST
        if not student_name or not admission_year or not class_name:
            messagebox.showerror("Error", "All fields required")
            return

        # 2) Format check
        if not admission_year.isdigit():
            messagebox.showerror("Error", "Admission year must be a number")
            return

        # 3) Convert
        admission_year = int(admission_year)

        # 4) Generate admission number
        year_serial, admission_no = generate_admission_no(admission_year)

        # 5) Insert into DB
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students
            (admission_year, year_serial, admission_no, student_name, class_name)
            VALUES (?, ?, ?, ?, ?)
        """, (admission_year, year_serial, admission_no, student_name, class_name))
        conn.commit()
        conn.close()          
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

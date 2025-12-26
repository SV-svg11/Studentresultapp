#needed modules for the application
from email.mime import text
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

def migrate_users_table():
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT")
        cursor.execute("UPDATE users SET role='supervisor' WHERE role IS NULL")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists

    conn.close()


def fetch_class_exam_report(class_name, exam_name):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            s.admission_no,
            s.student_name,
            m.score,
            e.max_marks,
            ROUND((m.score * 100.0) / e.max_marks, 2) AS percentage

            FROM students s
            JOIN marks m ON s.admission_no = m.admission_no
            JOIN exams e ON m.exam_id = e.id
            WHERE s.class_name = ?
            AND e.exam_name = ?
        """, (class_name, exam_name))

        rows = cursor.fetchall()
        conn.close()
        return rows
def init_users_db():
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('supervisor', 'account'))
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

        tk.Label(
            self.register_window,
            text="Student Registration",
            font=("Calibri", 20, "bold")
        ).pack(pady=10)

        tk.Label(self.register_window, text="Student Name").pack()
        self.reg_entry_name = tk.Entry(self.register_window)
        self.reg_entry_name.pack(pady=5)

        tk.Label(self.register_window, text="Admission Year").pack()
        self.reg_entry_year = tk.Entry(self.register_window)
        self.reg_entry_year.pack(pady=5)

        tk.Label(self.register_window, text="Class Name").pack()
        self.reg_entry_class = tk.Entry(self.register_window)
        self.reg_entry_class.pack(pady=5)

        tk.Button(
            self.register_window,
            text="Register",
            command=self.register_student
        ).pack(pady=10)
    def register_student(self):
        student_name = self.reg_entry_name.get().strip()
        admission_year = self.reg_entry_year.get().strip()
        class_name = self.reg_entry_class.get().strip()

        if not admission_year.isdigit():
            messagebox.showerror("Error", "Admission year must be a number")
            return
        admission_year = int(admission_year)
        year_serial, admission_no = generate_admission_no(admission_year)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students(admission_year, year_serial, admission_no, student_name, class_name)
               VALUES (?, ?, ?, ?, ?)
        """, (admission_year, year_serial, admission_no, student_name, class_name))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", f"Student registered successfully\nAdmission No: {admission_no}")
        tk.Button(self.register_window, text="Register", command=self.register_student).pack(pady=10)
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
        migrate_users_table()

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

        tk.Label(self.login_window, text="Role").pack()

        self.role_var = tk.StringVar()
        self.role_var.set("supervisor")

        tk.OptionMenu(
            self.login_window,
            self.role_var,
            "supervisor",
            "account"
            ).pack()


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

        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role FROM users WHERE username=? AND password=?",
            (username, password)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            self.user_role = row[0]   # 🔑 store role
            self.login_window.destroy()
            self.show_main_app()
        else:
            messagebox.showerror("Login Failed", "Invalid credentials")

    def signup(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        role = self.role_var.get()

        if not username or not password:
            messagebox.showerror("Error", "All fields required")
            return

        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role)
            )
            conn.commit()
            messagebox.showinfo("Success", "User created successfully")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
        finally:
            conn.close()


    def get_grade(self, percent):
        if percent >= 90:
            return "A"
        elif percent >= 75:
            return "B"
        elif percent >= 60:
            return "C"
        else:
            return "Fail"

    def show_main_app(self):
        self.root = tk.Tk()
        self.root.title("Student Result Management System")
        self.root.geometry("480x550")

        tk.Label(self.root, text="Student Result System",
                 font=("Arial", 16)).pack(pady=10)

        tk.Button(self.root, text="Logout",
                  fg="red", command=self.logout).pack()
        
        # Supervisor-only buttons
        if self.user_role == "supervisor":
            tk.Button(self.root, text="Register Student",
                    command=self.open_register_student).pack(pady=5)

            tk.Button(self.root, text="Enter Marks",
                     command=self.open_marks_window).pack(pady=5)

            tk.Button(self.root, text="Add Exam",
                     command=self.add_exam).pack(pady=5)

# Common buttons
        tk.Button(self.root, text="View Report",
                     command=self.open_report_window).pack(pady=5)


        



        

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




        tk.Button(self.root, text="Export Results to Excel", command=self.export_to_excel).pack(pady=5)



        self.root.mainloop()
    def open_marks_window(self):
        self.marks_window = tk.Toplevel(self.root)
        self.marks_window.title("Enter Marks")
        self.marks_window.geometry("400x350")

        tk.Label(self.marks_window, text="Enter Marks", font=("Arial", 14)).pack(pady=10)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # --- Fetch exams ---
        cursor.execute("SELECT id, exam_name FROM exams")
        exam_rows = cursor.fetchall()
        exams = [row[1] for row in exam_rows]

        # --- Fetch students ---
        cursor.execute("SELECT admission_no, student_name FROM students")
        student_rows = cursor.fetchall()
        students = [f"{row[0]} | {row[1]}" for row in student_rows]

        conn.close()

        if not students or not exams:
            messagebox.showerror("Error", "Add students and exams first")
            return

        # --- Student dropdown ---
        tk.Label(self.marks_window, text="Select Student").pack()
        self.student_var = tk.StringVar()
        self.student_var.set(students[0])
        tk.OptionMenu(self.marks_window, self.student_var, *students).pack(pady=5)

        # --- Exam dropdown ---
        tk.Label(self.marks_window, text="Select Exam").pack()
        self.exam_var = tk.StringVar()
        self.exam_var.set(exams[0])
        tk.OptionMenu(self.marks_window, self.exam_var, *exams).pack(pady=5)

        # --- Score ---
        tk.Label(self.marks_window, text="Score").pack()
        self.entry_score = tk.Entry(self.marks_window)
        self.entry_score.pack(pady=5)

        def save_marks():
            student_text = self.student_var.get()
            admission_no = student_text.split(" | ")[0]

            exam_name = self.exam_var.get()
            score = self.entry_score.get().strip()

            if not score.isdigit():
                messagebox.showerror("Error", "Score must be a number")
                return

            score = int(score)

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM exams WHERE exam_name=?", (exam_name,))
            exam_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO marks (admission_no, exam_id, score)
                VALUES (?, ?, ?)
            """, (admission_no, exam_id, score))

            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Marks saved successfully")

            print(admission_no, exam_name, score)

        tk.Button(self.marks_window, text="Save Marks", command=save_marks).pack(pady=10)
    def open_report_window(self):
        self.report_rows = []

        report_win = tk.Toplevel(self.root)
        report_win.title("Class Report")
        report_win.geometry("600x450")

        # ---- Fetch classes ----
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT class_name FROM students")
        classes = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT exam_name FROM exams")
        exams = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not classes or not exams:
            messagebox.showerror("Error", "No classes or exams found")
            return

        # ---- Class dropdown ----
        tk.Label(report_win, text="Class").pack()
        self.class_var = tk.StringVar()
        self.class_var.set(classes[0])
        tk.OptionMenu(report_win, self.class_var, *classes).pack()

        # ---- Exam dropdown ----
        tk.Label(report_win, text="Exam").pack()
        self.report_exam_var = tk.StringVar()
        self.report_exam_var.set(exams[0])
        tk.OptionMenu(report_win, self.report_exam_var, *exams).pack()

        # ---- Report text ----
        text = tk.Text(report_win, width=70, height=15)
        text.pack(pady=10)

        def load_report():
            class_name = self.class_var.get()
            exam_name = self.report_exam_var.get()

            rows = fetch_class_exam_report(class_name, exam_name)
            self.report_rows = rows

            text.delete("1.0", tk.END)
            text.insert(tk.END, "Admn No | Name | Score | Max | % | Grade\n")
            text.insert(tk.END, "-" * 65 + "\n")

            for r in rows:
                percent = round((r[2] * 100) / r[3], 2)
                grade = self.get_grade(percent)
                text.insert(
                    tk.END,
                    f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {percent}% | {grade}\n"
                )

        def export_report():
            if not self.report_rows:
                messagebox.showerror("Error", "Generate report first")
                return

            data = []
            for r in self.report_rows:
                percent = round((r[2] * 100) / r[3], 2)
                grade = self.get_grade(percent)
                data.append([r[0], r[1], r[2], r[3], percent, grade])

            df = pd.DataFrame(
                data,
                columns=["Admission No", "Student Name", "Score", "Max Marks", "Percentage", "Grade"]
            )

            filename = f"{self.class_var.get()}_{self.report_exam_var.get()}_Report.xlsx"
            df.to_excel(filename, index=False)
            messagebox.showinfo("Success", f"Exported {filename}")

        tk.Button(report_win, text="Generate Report", command=load_report).pack(pady=5)
        tk.Button(report_win, text="Export to Excel", command=export_report).pack(pady=5)

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

    

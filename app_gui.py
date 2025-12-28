#


#Needed modules for the application
from email.mime import text
import os
import sqlite3
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import hashlib
import hmac

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
def migrate_users_passwords():
    """Add password_hash column and migrate existing plaintext passwords to hashed form."""
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists

    # For any user rows that don't have password_hash filled, generate one from the existing password
    cursor.execute("SELECT id, password FROM users WHERE password IS NOT NULL AND (password_hash IS NULL OR password_hash = '')")
    rows = cursor.fetchall()
    for uid, plain in rows:
        if not plain:
            continue
        ph = hash_password(plain)
        cursor.execute("UPDATE users SET password_hash=? WHERE id=?", (ph, uid))

    # Optionally clear plaintext passwords to avoid accidental reuse
    try:
        cursor.execute("UPDATE users SET password='' WHERE password IS NOT NULL")
    except Exception:
        pass

    conn.commit()
    conn.close()
def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256. Returns salt$hash hex string."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return salt.hex() + "$" + dk.hex()

def verify_password(password: str, stored: str) -> bool:
    """Verify a plaintext password against stored salt$hash."""
    try:
        salt_hex, hash_hex = stored.split("$")
    except Exception:
        return False
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(hash_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return hmac.compare_digest(dk, expected)
def migrate_exams_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE exams ADD COLUMN max_marks INTEGER")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()
def migrate_exam_subjects():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE exam_subjects ADD COLUMN class_name TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
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
            password TEXT,
            password_hash TEXT,
            role TEXT NOT NULL CHECK(role IN ('supervisor', 'teacher', 'account'))
        )
    """)
    conn.commit()
    conn.close()
def init_subjects_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()
    conn.close()
def init_class_subjects_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS class_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER,
            subject_id INTEGER,
            UNIQUE(class_id, subject_id)
        )
    """)
    conn.commit()
    conn.close()
def init_exam_subjects_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER,
            class_name TEXT,
            subject_id INTEGER,
            max_marks INTEGER
        )
    """)
    conn.commit()
    conn.close()
def seed_subjects():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    subjects = [
        "English", "2l", "3l",
        "Maths", "Science", "Social",
        "EVS", "Computer", "GK" 
    ]

    for s in subjects:
        cursor.execute(
            "INSERT OR IGNORE INTO subjects (subject_name) VALUES (?)",
            (s,)
        )

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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_no TEXT NOT NULL,
            exam_subject_id INTEGER NOT NULL,
            score INTEGER NOT NULL
        );
    """)
    conn.commit()
    conn.close()
def init_classes_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_number TEXT NOT NULL,
            section TEXT NOT NULL,
            UNIQUE(class_number, section)
        )
    """)
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

# ---- Class Number ----
        tk.Label(self.register_window, text="Class").pack()

        class_numbers = ["Nursery", "LKG", "UKG"] + [str(i) for i in range(1, 11)]
        self.class_num_var = tk.StringVar()
        self.class_num_var.set(class_numbers[0])

        tk.OptionMenu(
            self.register_window,
            self.class_num_var,
            *class_numbers
        ).pack(pady=5)

        # ---- Section ----
        tk.Label(self.register_window, text="Section").pack()

        sections = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
        self.section_var = tk.StringVar()
        self.section_var.set(sections[0])

        tk.OptionMenu(
            self.register_window,
            self.section_var,
            *sections
        ).pack(pady=5)


        tk.Button(
            self.register_window,
            text="Register",
            command=self.register_student
        ).pack(pady=10)
    def register_student(self):
        student_name = self.reg_entry_name.get().strip()
        admission_year = self.reg_entry_year.get().strip()
        class_number = self.class_num_var.get()
        section = self.section_var.get()

        class_name = f"{class_number}{section}"


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
        migrate_users_passwords()
        init_subjects_db()
        seed_subjects()  
        init_students_db()
        init_exams_db()
        migrate_exams_table() 
        init_marks_db()
        init_classes_db()
        init_class_subjects_db()
        init_exam_subjects_db()
        migrate_exam_subjects()

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
            "teacher",
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
        cursor.execute("SELECT password_hash, role FROM users WHERE username=?", (username,))
        row = cursor.fetchone()
        conn.close()

        if row and row[0] and verify_password(password, row[0]):
            self.user_role = row[1]
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
            p_hash = hash_password(password)
            # store plaintext password as empty string and keep the hash in password_hash
            cursor.execute(
                "INSERT INTO users (username, password, password_hash, role) VALUES (?, ?, ?, ?)",
                (username, '', p_hash, role)
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

        # Supervisor – full access
        if self.user_role == "supervisor":

            tk.Button(self.root, text="Register Student",
                    command=self.open_register_student).pack(pady=5)

            tk.Button(self.root, text="Configure Subjects / Exams",
                    command=self.open_exam_subjects_window).pack(pady=5)

            tk.Button(self.root, text="Enter Marks",
                    command=self.open_marks_window).pack(pady=5)

            tk.Button(self.root, text="View Reports",
                    command=self.open_report_window).pack(pady=5)
            
            tk.Button(self.root, text="Add Exam",
                    command=self.add_exam).pack(pady=5)


        # Teacher – marks + reports only
        elif self.user_role == "teacher":

            tk.Button(self.root, text="Enter Marks",
                    command=self.open_marks_window).pack(pady=5)

            tk.Button(self.root, text="View Reports",
                    command=self.open_report_window).pack(pady=5)
            
            tk.Button(self.root, text="Add Exam",
                    command=self.add_exam).pack(pady=5)


        # Account – students + subjects + exams
        elif self.user_role == "account":

            tk.Button(self.root, text="Register Student",
                    command=self.open_register_student).pack(pady=5)

            tk.Button(self.root, text="Configure Subjects / Exams",
                    command=self.open_exam_subjects_window).pack(pady=5)

            tk.Button(self.root, text="View Reports",
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








        self.root.mainloop()
    def open_marks_window(self):
        self.marks_window = tk.Toplevel(self.root)
        self.marks_window.title("Enter Marks")
        self.marks_window.geometry("450x500")

        tk.Label(self.marks_window, text="Enter Subject-wise Marks", font=("Arial", 14)).pack(pady=10)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Exams
        cursor.execute("SELECT exam_name FROM exams")
        exams = [row[0] for row in cursor.fetchall()]

        # Students
        cursor.execute("SELECT admission_no, student_name FROM students")
        students = [f"{row[0]} | {row[1]}" for row in cursor.fetchall()]

        conn.close()

        if not students or not exams:
            messagebox.showerror("Error", "Add students and exams first")
            return

        # Student dropdown
        tk.Label(self.marks_window, text="Student").pack()
        self.student_var = tk.StringVar(value=students[0])
        tk.OptionMenu(self.marks_window, self.student_var, *students).pack()

        # Exam dropdown
        tk.Label(self.marks_window, text="Exam").pack()
        self.exam_var = tk.StringVar(value=exams[0])
        tk.OptionMenu(self.marks_window, self.exam_var, *exams).pack()

        


        marks_frame = tk.Frame(self.marks_window)
        marks_frame.pack(pady=10)

        self.subject_entries = {}

        def load_subjects():
            for widget in marks_frame.winfo_children():
                widget.destroy()

            exam_name = self.exam_var.get()
            admission_no = self.student_var.get().split(" | ")[0]

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # ---- exam_id ----
            cursor.execute("SELECT id FROM exams WHERE exam_name=?", (exam_name,))
            row = cursor.fetchone()
            print("DEBUG exam_name:", exam_name)
            print("DEBUG exam_row:", row)

            if not row:
                messagebox.showerror("Error", "Invalid exam")
                conn.close()
                return
            exam_id = row[0]

            # ---- class_name ----
            cursor.execute(
                "SELECT class_name FROM students WHERE admission_no=?",
                (admission_no,)
            )
            row = cursor.fetchone()
            print("DEBUG admission_no:", admission_no)
            print("DEBUG student_class:", row)

            if not row:
                messagebox.showerror("Error", "Student class not found")
                conn.close()
                return
            class_name = row[0]

            # ---- exam_subjects ----
            cursor.execute("""
                SELECT es.id, s.subject_name
                FROM exam_subjects es
                JOIN subjects s ON es.subject_id = s.id
                WHERE es.exam_id = ? AND es.class_name = ?
            """, (exam_id, class_name))

            rows = cursor.fetchall()
            print("DEBUG exam_subject_rows:", rows)

            conn.close()

            if not rows:
                messagebox.showerror(
                    "No Subjects",
                    f"No subjects configured for {class_name} - {exam_name}"
                )
                return

            self.subject_entries = {}
            for exam_subject_id, subject_name in rows:
                tk.Label(marks_frame, text=subject_name).pack()
                entry = tk.Entry(marks_frame)
                entry.pack()
                self.subject_entries[exam_subject_id] = entry


        tk.Button(self.marks_window, text="Load Subjects", command=load_subjects).pack(pady=5)

        def save_marks():
            admission_no = self.student_var.get().split(" | ")[0]

            if not self.subject_entries:
                messagebox.showerror("Error", "Load subjects first")
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            for exam_subject_id, entry in self.subject_entries.items():
                score = entry.get().strip()

                if not score.isdigit():
                    continue

                cursor.execute("""
                    INSERT INTO marks (admission_no, exam_subject_id, score)
                    VALUES (?, ?, ?)
                """, (admission_no, exam_subject_id, int(score)))

            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Marks saved successfully")



        tk.Button(self.marks_window, text="Save Marks", command=save_marks).pack(pady=10)
    def open_exam_subjects_window(self):
        win = tk.Toplevel(self.root)
        win.title("Exam Subject Configuration")
        win.geometry("520x600")

        tk.Label(win, text="Configure Exam Subjects",
                font=("Arial", 16, "bold")).pack(pady=10)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT class_name FROM students")
        classes = [row[0] for row in cursor.fetchall()]

        if not classes:
            messagebox.showerror("Error", "Register at least one student first")
            win.destroy()
            return

        cursor.execute("SELECT id, exam_name FROM exams")
        exam_rows = cursor.fetchall()

        cursor.execute("SELECT id, subject_name FROM subjects")
        subject_rows = cursor.fetchall()
        conn.close()
        print("SUBJECT ROWS:", subject_rows)


        tk.Label(win, text="Class").pack()
        class_var = tk.StringVar(value=classes[0])
        tk.OptionMenu(win, class_var, *classes).pack()

        tk.Label(win, text="Exam Type").pack()
        exam_type_var = tk.StringVar(value="PT")
        tk.Radiobutton(win, text="PT", variable=exam_type_var, value="PT").pack()
        tk.Radiobutton(win, text="TE", variable=exam_type_var, value="TE").pack()

        tk.Label(win, text="Exam").pack()
        exam_map = {e[1]: e[0] for e in exam_rows}
        exam_var = tk.StringVar(value=exam_rows[0][1])
        tk.OptionMenu(win, exam_var, *exam_map.keys()).pack()

        frame = tk.Frame(win)
        frame.pack(pady=15, fill="both", expand=True)

        subject_vars = {}
        for sid, sname in subject_rows:
            row = tk.Frame(frame)
            row.pack(fill="x", pady=2)

            var = tk.IntVar()
            tk.Checkbutton(row, text=sname, variable=var, width=20, anchor="w").pack(side="left")
            entry = tk.Entry(row, width=8)
            entry.pack(side="left", padx=5)

            subject_vars[sid] = (var, entry)

        def save_config():
            exam_id = exam_map[exam_var.get()]
            class_name = class_var.get()

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM exam_subjects WHERE exam_id=? AND class_name=?",
                (exam_id, class_name)
            )

            saved = False
            for subject_id, (chk, entry) in subject_vars.items():
                if chk.get():
                    if not entry.get().isdigit():
                        messagebox.showerror("Error", "Max marks must be numeric")
                        conn.close()
                        return

                    cursor.execute("""
                        INSERT INTO exam_subjects (exam_id, class_name, subject_id, max_marks)
                        VALUES (?, ?, ?, ?)
                    """, (exam_id, class_name, subject_id, int(entry.get())))
                    saved = True

            conn.commit()
            conn.close()

            if saved:
                messagebox.showinfo("Success", "Subjects configured successfully")
            else:
                messagebox.showwarning("Warning", "No subjects selected")

        def discard_config():
            """Reset all subject checkboxes and max-mark entries after confirmation."""
            if not messagebox.askyesno("Discard Changes", "Discard unsaved changes?"):
                return
            for subject_id, (var, entry) in subject_vars.items():
                try:
                    var.set(0)
                except Exception:
                    pass
                try:
                    entry.delete(0, tk.END)
                except Exception:
                    pass
            messagebox.showinfo("Discarded", "Unsaved changes have been discarded")

        tk.Button(win, text="Save Configuration",
                font=("Arial", 11),
                command=save_config).pack(pady=10)

        tk.Button(win, text="Discard Changes",
                font=("Arial", 11),
                command=discard_config).pack(pady=5)

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

    

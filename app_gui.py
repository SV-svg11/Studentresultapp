"""
================================================================================
    STUDENT RESULT MANAGEMENT SYSTEM - GUI APPLICATION
================================================================================
    
    A professional-grade desktop application for managing student records,
    exam results, and generating academic reports with role-based access control.
    
    Features:
    - User Authentication with role-based access (Supervisor, Teacher, Account)
    - Student Registration & Management
    - Exam Configuration with Subjects
    - Marks Entry & Grading System
    - Report Generation & Excel Export
    - Secure Password Hashing
    
    Author: Academic Management Team
    Version: 2.0
    Last Updated: December 2025
================================================================================
"""

# ===== STANDARD LIBRARY IMPORTS =====
import os                      # File and directory operations
import sqlite3                 # Database operations
import tkinter as tk           # GUI framework
from tkinter import messagebox # Dialog boxes
import pandas as pd            # Data manipulation & Excel export
import hashlib                 # Password hashing
import hmac                    # Secure password verification

# ===== DATABASE CONFIGURATION =====
# Define the base directory and database file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "results.db")      # Main results database
USERS_DB = os.path.join(BASE_DIR, "users.db")       # User authentication database

# ===== DATABASE MIGRATION FUNCTIONS =====
# These functions safely add new columns to existing tables without breaking old data

# ===== PROFESSIONAL UI CONFIGURATION =====
# Color scheme and styling for a modern, professional appearance

APP_COLORS = {
    "primary": "#2C3E50",      # Dark blue-gray for headers
    "secondary": "#3498DB",    # Bright blue for buttons
    "success": "#27AE60",      # Green for success messages
    "danger": "#E74C3C",       # Red for warnings/errors
    "bg": "#ECF0F1",           # Light gray background
    "text": "#2C3E50",         # Dark text
    "button_hover": "#2980B9"  # Darker blue for button hover
}

FONTS = {
    "title": ("Segoe UI", 18, "bold"),           # Main title
    "header": ("Segoe UI", 14, "bold"),          # Section headers
    "normal": ("Segoe UI", 10),                   # Regular text
    "button": ("Segoe UI", 10, "bold")           # Button text
}


def migrate_users_table():
    """
    Add 'role' column to users table if it doesn't exist.
    This allows assigning different access levels to users.
    Roles: 'supervisor' (full access), 'teacher' (marks & reports), 'account' (admin tasks)
    """
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()

    try:
        # Add role column with default value 'supervisor'
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT")
        cursor.execute("UPDATE users SET role='supervisor' WHERE role IS NULL")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists - no action needed
        pass

    conn.close()
def migrate_users_passwords():
    """
    Migrate plaintext passwords to secure PBKDF2-HMAC-SHA256 hashed format.
    This ensures passwords are never stored in plaintext, meeting security best practices.
    
    Process:
    1. Add password_hash column if missing
    2. Hash any existing plaintext passwords
    3. Clear plaintext passwords from database
    """
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass

    # Find users with plaintext passwords but no hash yet
    cursor.execute("SELECT id, password FROM users WHERE password IS NOT NULL AND (password_hash IS NULL OR password_hash = '')")
    rows = cursor.fetchall()
    
    for uid, plain in rows:
        if not plain:
            continue
        # Hash the password
        ph = hash_password(plain)
        cursor.execute("UPDATE users SET password_hash=? WHERE id=?", (ph, uid))

    # Remove plaintext passwords from database for security
    try:
        cursor.execute("UPDATE users SET password='' WHERE password IS NOT NULL")
    except Exception:
        pass

    conn.commit()
    conn.close()
def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256 algorithm.
    
    This is a secure, industry-standard password hashing method that:
    - Uses 100,000 iterations to resist brute-force attacks
    - Generates a random 16-byte salt for each password
    - Returns format: "salt_hex$hash_hex"
    
    Args:
        password (str): The plaintext password to hash
        
    Returns:
        str: Hashed password in format "salt$hash"
    """
    # Generate a random 16-byte salt
    salt = os.urandom(16)
    # Derive key using PBKDF2 with SHA256
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    # Return salt and hash as hex strings
    return salt.hex() + "$" + dk.hex()

def verify_password(password: str, stored: str) -> bool:
    """
    Verify a plaintext password against a stored hash.
    
    Uses constant-time comparison (hmac.compare_digest) to prevent timing attacks
    that could reveal password information through execution time analysis.
    
    Args:
        password (str): The plaintext password to verify
        stored (str): The stored hash in format "salt$hash"
        
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        # Parse salt and hash from storage format
        salt_hex, hash_hex = stored.split("$")
    except Exception:
        return False
    
    # Convert hex strings back to bytes
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(hash_hex)
    
    # Derive hash of provided password using same salt
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(dk, expected)
def migrate_exams_table():
    """Add 'max_marks' column to exams table for storing maximum marks per exam."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE exams ADD COLUMN max_marks INTEGER")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass
    conn.close()

def migrate_exam_subjects():
    """Add 'class_name' column to exam_subjects to track subject configuration per class."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE exam_subjects ADD COLUMN class_name TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass
    conn.close()

def fetch_class_exam_report(class_name, exam_name):
    """
    Fetch comprehensive exam report for a specific class.
    
    Retrieves all students in the class with their marks, calculates percentages,
    and prepares data for report display and export.
    
    Args:
        class_name (str): Name/number of the class (e.g., "Class 5-A")
        exam_name (str): Name of the exam (e.g., "PT1", "Final")
        
    Returns:
        list: Tuples containing (admission_no, student_name, score, max_marks, percentage)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Complex query to join students, marks, subjects, and exams
    cursor.execute("""
        SELECT
            s.admission_no,
            s.student_name,
            m.score,
            es.max_marks,
            ROUND((m.score * 100.0) / es.max_marks, 2) AS percentage
        FROM students s
        JOIN marks m
            ON s.admission_no = m.admission_no
        JOIN exam_subjects es
            ON m.exam_subject_id = es.id
        JOIN exams e
            ON es.exam_id = e.id
        WHERE s.class_name = ?
          AND e.exam_name = ?
    """, (class_name, exam_name))

    rows = cursor.fetchall()
    conn.close()
    return rows

def init_users_db():
    """
    Initialize the users database with users table.
    
    Creates a table with the following columns:
    - id: Primary key, auto-increment
    - username: Unique identifier for login
    - password: Legacy plaintext password (deprecated, use password_hash)
    - password_hash: Secure hashed password using PBKDF2
    - role: User role - 'supervisor' (full access), 'teacher' (marks & reports), 
            'account' (administrative tasks)
    """
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
    """
    Initialize subjects table.
    
    Stores all available subjects that can be assigned to exams.
    Each subject is unique and can be reused across multiple exams and classes.
    """
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
    """
    Initialize class_subjects junction table.
    
    Maps subjects to classes - stores which subjects are taught in each class.
    Uses composite unique constraint to prevent duplicate assignments.
    """
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
    """
    Initialize exam_subjects table.
    
    Maps subjects to specific exams and classes. Stores configuration for which
    subjects are included in which exam for which class, along with max marks.
    
    Columns:
    - exam_id: Reference to the exam
    - class_name: Which class this configuration applies to
    - subject_id: Which subject
    - max_marks: Maximum marks for this subject in this exam
    """
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
    """
    Pre-populate the subjects table with standard school subjects.
    
    This function creates initial subject entries which can be used when
    configuring exams. Uses INSERT OR IGNORE to safely handle re-runs.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Define standard school subjects
    subjects = [
        "English",      # Language subject
        "2l",           # Second language
        "3l",           # Third language
        "Maths",        # Mathematics
        "Science",      # Science (general)
        "Social",       # Social studies
        "EVS",          # Environmental studies
        "Computer",     # Computer science
        "GK"            # General knowledge
    ]

    # Insert each subject, ignoring if it already exists
    for s in subjects:
        cursor.execute(
            "INSERT OR IGNORE INTO subjects (subject_name) VALUES (?)",
            (s,)
        )

    conn.commit()
    conn.close()

    


def init_students_db():
    """
    Initialize the students table.
    
    Stores student information with unique admission numbers generated automatically.
    
    Columns:
    - id: Primary key
    - admission_year: Year when student was admitted
    - admission_no: Unique identifier (format: YYYY-NNN)
    - student_name: Full name of the student
    - class_name: Current class/section (e.g., "Class 5-A")
    - year_serial: Sequential number within admission year
    """
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
    """
    Generate a unique admission number for a student.
    
    Format: YYYY-NNN (Year-Sequential Number)
    Example: 2025-001, 2025-002, etc.
    
    Args:
        admission_year (int): Year of admission
        
    Returns:
        tuple: (year_serial, admission_no) - the sequential number and full admission number
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Find the highest serial number for this year
    cursor.execute("""
    SELECT MAX(year_serial) FROM students WHERE admission_year=?""", (admission_year,))
    max_serial = cursor.fetchone()[0]
    
    # If no students yet this year, start from 1
    if max_serial is None:
        max_serial = 0

    # Increment to get next serial
    next_serial = max_serial + 1
    # Format as YYYY-NNN (e.g., 2025-001)
    admission_no = f"{admission_year}-{next_serial:03d}"
    conn.close()
    return next_serial, admission_no
def init_exams_db():
    """
    Initialize the exams table.
    
    Stores exam configurations with the following information:
    - id: Primary key
    - max_marks: Total marks for this exam
    - exam_name: Name/identifier (e.g., "PT1", "Half Yearly", "Final")
    - exam_type: Type of exam - "PT" (Periodic Test) or "TE" (Terminal Exam)
    - academic_year: Academic year (e.g., "2024-2025")
    """
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
    );
    """)
    conn.commit()
    conn.close()

def init_marks_db():
    """
    Initialize the marks table.
    
    Stores individual student marks for each subject in an exam.
    
    Columns:
    - id: Primary key
    - admission_no: Reference to student (from students table)
    - exam_subject_id: Reference to specific exam/subject/class configuration
    - score: Marks obtained by the student in this subject
    """
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
    """
    Initialize the classes table.
    
    Stores class definitions in the school.
    
    Columns:
    - id: Primary key
    - class_number: Class level (e.g., "5", "8")
    - section: Section/division (e.g., "A", "B", "C")
    - Composite unique constraint prevents duplicate class-section combinations
    """
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
    """
    Main Application Class - Student Result Management System
    
    This class manages the entire application including:
    - User authentication with role-based access control
    - Student registration and management
    - Exam and subject configuration
    - Marks entry and processing
    - Report generation and export
    
    Role-Based Access:
    - SUPERVISOR: Full access to all features
    - TEACHER: Can enter marks and view reports
    - ACCOUNT: Can manage students, subjects, and view reports (no marks entry)
    """
    
    def __init__(self):
        """
        Initialize the application.
        
        This method:
        1. Sets up all database tables and schemas
        2. Seeds initial data (subjects)
        3. Performs database migrations
        4. Shows the login window
        """
        # Initialize all database tables
        init_users_db()           # User authentication table
        init_classes_db()          # Classes configuration
        init_students_db()         # Student records
        init_exams_db()           # Exam definitions
        init_marks_db()           # Student marks/scores
        init_subjects_db()        # Subject definitions
        init_class_subjects_db()  # Class-subject mappings
        init_exam_subjects_db()   # Exam-subject configurations
        
        # Populate initial data
        seed_subjects()           # Add standard school subjects
        
        # Perform data migrations for compatibility
        migrate_users_table()          # Add role column if missing
        migrate_users_passwords()      # Hash passwords securely
        migrate_exams_table()         # Add max_marks if missing
        migrate_exam_subjects()       # Add class_name if missing
        
        # Initialize UI state variables
        self.user_role = None         # Will be set after login
        
        # Start the application with login screen
        self.show_login()
    
    def show_login(self):
        """
        Display the login window with authentication.
        
        Features:
        - Username and password entry
        - Role selection (if admin)
        - Secure password verification using PBKDF2
        - Automatic database preparation on first login
        """
        self.login_window = tk.Tk()
        self.login_window.title("Student Result System - Login")
        self.login_window.geometry("450x450")
        self.login_window.configure(bg=APP_COLORS["bg"])
        
        # ===== HEADER SECTION =====
        header_frame = tk.Frame(self.login_window, bg=APP_COLORS["primary"], height=80)
        header_frame.pack(fill="x")
        
        tk.Label(
            header_frame,
            text="🎓 Student Result Management",
            font=("Segoe UI", 16, "bold"),
            bg=APP_COLORS["primary"],
            fg="white"
        ).pack(pady=15)
        
        tk.Label(
            header_frame,
            text="Secure Login Portal",
            font=("Segoe UI", 10),
            bg=APP_COLORS["secondary"],
            fg="white"
        ).pack(pady=5)
        
        # ===== LOGIN FORM =====
        form_frame = tk.Frame(self.login_window, bg=APP_COLORS["bg"])
        form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Username field
        tk.Label(form_frame, text="Username", font=FONTS["normal"], bg=APP_COLORS["bg"]).pack(anchor="w", pady=(10, 5))
        self.login_username = tk.Entry(form_frame, font=FONTS["normal"], width=35)
        self.login_username.pack(pady=5, fill="x")
        
        # Password field
        tk.Label(form_frame, text="Password", font=FONTS["normal"], bg=APP_COLORS["bg"]).pack(anchor="w", pady=(10, 5))
        self.login_password = tk.Entry(form_frame, font=FONTS["normal"], width=35, show="•")
        self.login_password.pack(pady=5, fill="x")
        
        # Role selection
        tk.Label(form_frame, text="Role (Admin only)", font=FONTS["normal"], bg=APP_COLORS["bg"]).pack(anchor="w", pady=(10, 5))
        self.login_role = tk.StringVar(value="teacher")
        roles_frame = tk.Frame(form_frame, bg=APP_COLORS["bg"])
        roles_frame.pack(anchor="w", fill="x")
        
        tk.Radiobutton(roles_frame, text="Supervisor", variable=self.login_role, value="supervisor", bg=APP_COLORS["bg"]).pack(side="left")
        tk.Radiobutton(roles_frame, text="Teacher", variable=self.login_role, value="teacher", bg=APP_COLORS["bg"]).pack(side="left", padx=20)
        tk.Radiobutton(roles_frame, text="Account", variable=self.login_role, value="account", bg=APP_COLORS["bg"]).pack(side="left")
        
        # Login button
        tk.Button(
            form_frame,
            text="🔐 LOGIN",
            command=self.authenticate_user,
            font=FONTS["button"],
            bg=APP_COLORS["secondary"],
            fg="white",
            width=30,
            height=2
        ).pack(pady=20, fill="x")
        
        # Demo info
        info_frame = tk.Frame(self.login_window, bg=APP_COLORS["bg"])
        info_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(
            info_frame,
            text="Demo: Use any username/password. First login creates the user.",
            font=("Segoe UI", 8),
            bg=APP_COLORS["bg"],
            fg="#7F8C8D",
            wraplength=400,
            justify="center"
        ).pack()
        
        self.login_window.mainloop()
    
    def authenticate_user(self):
        """
        Authenticate user credentials and grant access.
        
        Process:
        1. Get username and password from login form
        2. Check if user exists in database
        3. If exists, verify password hash
        4. If doesn't exist, create new user account
        5. Set user role and open main application
        """
        username = self.login_username.get().strip()
        password = self.login_password.get()
        role = self.login_role.get()
        
        # Validate input
        if not username or not password:
            messagebox.showerror("Error", "Username and password required")
            return
        
        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id, password_hash, role FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        
        if user:
            # User exists - verify password
            user_id, stored_hash, stored_role = user
            if verify_password(password, stored_hash):
                # Password correct - login successful
                self.user_role = stored_role
                conn.close()
                self.login_window.destroy()
                self.show_main_app()
            else:
                # Password incorrect
                messagebox.showerror("Error", "Invalid password")
                conn.close()
        else:
            # User doesn't exist - create new account
            password_hash = hash_password(password)
            try:
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role)
                    VALUES (?, ?, ?)
                """, (username, password_hash, role))
                conn.commit()
                self.user_role = role
                conn.close()
                messagebox.showinfo("Success", f"Account created successfully!\nLogged in as {role}")
                self.login_window.destroy()
                self.show_main_app()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists")
                conn.close()
    
    def open_register_student(self):
        """
        Open the student registration window.
        
        Allows authorized users to add new students to the system with:
        - Student name
        - Admission year (auto-generates unique admission number)
        - Class and section assignment
        
        The admission number is automatically generated in format YYYY-NNN.
        """
        self.register_window = tk.Toplevel(self.root)
        self.register_window.title("Register Student")
        self.register_window.geometry("400x350")
        self.register_window.configure(bg=APP_COLORS["bg"])

        # ===== TITLE SECTION =====
        title_frame = tk.Frame(self.register_window, bg=APP_COLORS["primary"], height=60)
        title_frame.pack(fill="x")
        
        tk.Label(
            title_frame,
            text="📚 Student Registration",
            font=FONTS["title"],
            bg=APP_COLORS["primary"],
            fg="white"
        ).pack(pady=15)

        # ===== CONTENT FRAME =====
        content_frame = tk.Frame(self.register_window, bg=APP_COLORS["bg"])
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Student Name Field
        tk.Label(content_frame, text="Student Name", font=FONTS["normal"], bg=APP_COLORS["bg"]).pack(anchor="w", pady=(10, 5))
        self.reg_entry_name = tk.Entry(content_frame, font=FONTS["normal"], width=40)
        self.reg_entry_name.pack(pady=5, fill="x")

        # Admission Year Field
        tk.Label(content_frame, text="Admission Year (e.g., 2025)", font=FONTS["normal"], bg=APP_COLORS["bg"]).pack(anchor="w", pady=(10, 5))
        self.reg_entry_year = tk.Entry(content_frame, font=FONTS["normal"], width=40)
        self.reg_entry_year.pack(pady=5, fill="x")

        # Class Selection
        tk.Label(content_frame, text="Class", font=FONTS["normal"], bg=APP_COLORS["bg"]).pack(anchor="w", pady=(10, 5))

        class_numbers = ["Nursery", "LKG", "UKG"] + [str(i) for i in range(1, 11)]
        self.class_num_var = tk.StringVar()
        self.class_num_var.set(class_numbers[0])

        class_menu = tk.OptionMenu(
            content_frame,
            self.class_num_var,
            *class_numbers
        )
        class_menu.config(font=FONTS["normal"], width=37, bg="white")
        class_menu.pack(pady=5, fill="x")

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
        """
        Open a window to add a new exam to the system.
        
        Allows authorized users to create exam entries with:
        - Exam number/name (e.g., PT1, PT2, Final)
        - Exam type (PT = Periodic Test, TE = Terminal Exam)
        - Academic year (format: YYYY-YY, e.g., 2024-25)
        - Maximum marks for the exam
        """
        exam_window = tk.Toplevel(self.root)
        exam_window.title("Add New Exam")
        exam_window.geometry("450x400")
        exam_window.configure(bg=APP_COLORS["bg"])

        # ===== HEADER =====
        header_frame = tk.Frame(exam_window, bg=APP_COLORS["primary"], height=60)
        header_frame.pack(fill="x")
        
        tk.Label(
            header_frame,
            text="➕ Add New Exam",
            font=FONTS["header"],
            bg=APP_COLORS["primary"],
            fg="white"
        ).pack(pady=15)

        # ===== FORM CONTENT =====
        form_frame = tk.Frame(exam_window, bg=APP_COLORS["bg"])
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Exam Number Field
        tk.Label(form_frame, text="Exam Name (e.g., PT1, PT2, Final)", font=FONTS["normal"], bg=APP_COLORS["bg"]).pack(anchor="w", pady=(10, 5))
        entry_exam_name = tk.Entry(form_frame, font=FONTS["normal"], width=40)
        entry_exam_name.pack(pady=5, fill="x")

        # Exam Type Selection
        tk.Label(form_frame, text="Exam Type", font=FONTS["normal"], bg=APP_COLORS["bg"]).pack(anchor="w", pady=(15, 5))
        exam_type_var = tk.StringVar(value="PT")
        type_frame = tk.Frame(form_frame, bg=APP_COLORS["bg"])
        type_frame.pack(anchor="w", fill="x")
        tk.Radiobutton(type_frame, text="PT (Periodic Test)", variable=exam_type_var, value="PT", bg=APP_COLORS["bg"], font=FONTS["normal"]).pack(anchor="w")
        tk.Radiobutton(type_frame, text="TE (Terminal Exam)", variable=exam_type_var, value="TE", bg=APP_COLORS["bg"], font=FONTS["normal"]).pack(anchor="w")

        # Academic Year Field
        tk.Label(form_frame, text="Academic Year (e.g., 2024-25)", font=FONTS["normal"], bg=APP_COLORS["bg"]).pack(anchor="w", pady=(15, 5))
        entry_academic_year = tk.Entry(form_frame, font=FONTS["normal"], width=40)
        entry_academic_year.pack(pady=5, fill="x")

        # Max Marks Field
        tk.Label(form_frame, text="Maximum Marks (e.g., 100)", font=FONTS["normal"], bg=APP_COLORS["bg"]).pack(anchor="w", pady=(15, 5))
        entry_max_marks = tk.Entry(form_frame, font=FONTS["normal"], width=40)
        entry_max_marks.pack(pady=5, fill="x")

        # ===== SAVE BUTTON =====
        def save_exam():
            """
            Validate exam data and save to database.
            
            Checks:
            - All fields are filled
            - Max marks is numeric
            - Academic year is in correct format (YYYY-YY)
            """
            exam_name = entry_exam_name.get().strip()
            exam_type = exam_type_var.get()
            academic_year = entry_academic_year.get().strip()
            max_marks = entry_max_marks.get().strip()

            # Validation: All fields required
            if not exam_name or not academic_year or not max_marks:
                messagebox.showerror("Error", "All fields are required")
                return
            
            # Validation: Max marks must be numeric
            if not max_marks.isdigit():
                messagebox.showerror("Error", "Maximum marks must be a number")
                return
            
            # Validation: Academic year format
            if "-" not in academic_year:
                messagebox.showerror("Error", "Academic year must be in format YYYY-YY (e.g., 2024-25)")
                return
            
            parts = academic_year.split("-")
            if len(parts) != 2:
                messagebox.showerror("Error", "Academic year must be in format YYYY-YY")
                return
            
            # Insert into database
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO exams (exam_name, exam_type, academic_year, max_marks)
                    VALUES (?, ?, ?, ?)
                """, (exam_name, exam_type, academic_year, int(max_marks)))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", f"Exam '{exam_name}' added successfully!")
                exam_window.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Exam name already exists")
            except Exception as e:
                messagebox.showerror("Error", f"Database error: {str(e)}")

        tk.Button(
            form_frame,
            text="💾 Save Exam",
            command=save_exam,
            font=FONTS["button"],
            bg=APP_COLORS["success"],
            fg="white",
            width=35,
            height=2
        ).pack(pady=20, fill="x")

        tk.Button(
            form_frame,
            text="❌ Cancel",
            command=exam_window.destroy,
            font=FONTS["button"],
            bg=APP_COLORS["danger"],
            fg="white",
            width=35,
            height=2
        ).pack(pady=5, fill="x")
    
    def get_grade(self, percent):
        """
        Calculate letter grade based on percentage score.
        
        Grading Scale:
        - 90% and above: A (Excellent)
        - 75-89%: B (Very Good)
        - 60-74%: C (Good)
        - Below 60%: Fail
        
        Args:
            percent (float): Percentage score
            
        Returns:
            str: Letter grade
        """
        if percent >= 90:
            return "A"
        elif percent >= 75:
            return "B"
        elif percent >= 60:
            return "C"
        else:
            return "Fail"
    
    def show_main_app(self):
        """
        Display the main application window with role-based menu options.
        
        Creates a professional interface with:
        - Title banner with color scheme
        - Dynamic menu buttons based on user role
        - Consistent styling and spacing
        
        Role Access:
        - SUPERVISOR: All features
        - TEACHER: Marks entry and reports only
        - ACCOUNT: Student management and reports only
        """
        self.root = tk.Tk()
        self.root.title("Student Result Management System")
        self.root.geometry("600x700")
        self.root.configure(bg=APP_COLORS["bg"])

        # ===== HEADER SECTION =====
        header_frame = tk.Frame(self.root, bg=APP_COLORS["primary"], height=80)
        header_frame.pack(fill="x")
        
        tk.Label(
            header_frame,
            text="🎓 Student Result Management System",
            font=FONTS["title"],
            bg=APP_COLORS["primary"],
            fg="white"
        ).pack(pady=10)
        
        tk.Label(
            header_frame,
            text=f"Logged in as: {self.user_role.upper()}",
            font=("Segoe UI", 9),
            bg=APP_COLORS["secondary"],
            fg="white"
        ).pack(pady=5)

        # ===== MAIN CONTENT FRAME =====
        content_frame = tk.Frame(self.root, bg=APP_COLORS["bg"])
        content_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # ===== DYNAMIC MENU BASED ON ROLE =====
        # Supervisor – full access
        if self.user_role == "supervisor":

            tk.Button(
                content_frame,
                text="📝 Register Student",
                command=self.open_register_student,
                font=FONTS["button"],
                bg=APP_COLORS["secondary"],
                fg="white",
                width=35,
                height=2
            ).pack(pady=8, fill="x")

            tk.Button(
                content_frame,
                text="⚙️  Configure Subjects / Exams",
                command=self.open_exam_subjects_window,
                font=FONTS["button"],
                bg=APP_COLORS["secondary"],
                fg="white",
                width=35,
                height=2
            ).pack(pady=8, fill="x")

            tk.Button(
                content_frame,
                text="✏️  Enter Marks",
                command=self.open_marks_window,
                font=FONTS["button"],
                bg=APP_COLORS["secondary"],
                fg="white",
                width=35,
                height=2
            ).pack(pady=8, fill="x")

            tk.Button(
                content_frame,
                text="📊 View Reports",
                command=self.open_report_window,
                font=FONTS["button"],
                bg=APP_COLORS["secondary"],
                fg="white",
                width=35,
                height=2
            ).pack(pady=8, fill="x")
            
            tk.Button(
                content_frame,
                text="➕ Add Exam",
                command=self.add_exam,
                font=FONTS["button"],
                bg=APP_COLORS["secondary"],
                fg="white",
                width=35,
                height=2
            ).pack(pady=8, fill="x")


        # Teacher – marks + reports only
        elif self.user_role == "teacher":
            tk.Label(
                content_frame,
                text="Teacher Access Menu",
                font=FONTS["header"],
                bg=APP_COLORS["bg"]
            ).pack(pady=10)

            tk.Button(
                content_frame,
                text="✏️  Enter Marks",
                command=self.open_marks_window,
                font=FONTS["button"],
                bg=APP_COLORS["secondary"],
                fg="white",
                width=35,
                height=2
            ).pack(pady=8, fill="x")

            tk.Button(
                content_frame,
                text="📊 View Reports",
                command=self.open_report_window,
                font=FONTS["button"],
                bg=APP_COLORS["secondary"],
                fg="white",
                width=35,
                height=2
            ).pack(pady=8, fill="x")
            
            tk.Button(
                content_frame,
                text="➕ Add Exam",
                command=self.add_exam,
                font=FONTS["button"],
                bg=APP_COLORS["secondary"],
                fg="white",
                width=35,
                height=2
            ).pack(pady=8, fill="x")


        # Account – students + subjects + exams
        elif self.user_role == "account":
            tk.Label(
                content_frame,
                text="Account Management Menu",
                font=FONTS["header"],
                bg=APP_COLORS["bg"]
            ).pack(pady=10)

            tk.Button(
                content_frame,
                text="📝 Register Student",
                command=self.open_register_student,
                font=FONTS["button"],
                bg=APP_COLORS["secondary"],
                fg="white",
                width=35,
                height=2
            ).pack(pady=8, fill="x")

            tk.Button(
                content_frame,
                text="⚙️  Configure Subjects / Exams",
                command=self.open_exam_subjects_window,
                font=FONTS["button"],
                bg=APP_COLORS["secondary"],
                fg="white",
                width=35,
                height=2
            ).pack(pady=8, fill="x")

            tk.Button(
                content_frame,
                text="📊 View Reports",
                command=self.open_report_window,
                font=FONTS["button"],
                bg=APP_COLORS["secondary"],
                fg="white",
                width=35,
                height=2
            ).pack(pady=8, fill="x")

        # ===== LOGOUT BUTTON =====
        tk.Button(
            content_frame,
            text="🚪 Logout",
            command=self.logout,
            font=FONTS["button"],
            bg=APP_COLORS["danger"],
            fg="white",
            width=35,
            height=2
        ).pack(pady=15, fill="x")

        self.root.mainloop()



        self.root.mainloop()
    
    def open_marks_window(self):
        """
        Open the marks entry window.
        
        Allows authorized users to enter subject-wise marks for students.
        
        Process:
        1. Select student and exam
        2. System loads all subjects configured for this exam and class
        3. Enter marks for each subject
        4. Save to database
        """
        self.marks_window = tk.Toplevel(self.root)
        self.marks_window.title("Enter Marks")
        self.marks_window.geometry("500x600")
        self.marks_window.configure(bg=APP_COLORS["bg"])

        # ===== HEADER =====
        title_frame = tk.Frame(self.marks_window, bg=APP_COLORS["primary"], height=50)
        title_frame.pack(fill="x")
        
        tk.Label(
            title_frame,
            text="✏️  Enter Subject-wise Marks",
            font=FONTS["header"],
            bg=APP_COLORS["primary"],
            fg="white"
        ).pack(pady=10)

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
        """
        Open report window to view class exam summaries.
        
        Displays student performance summary with:
        - Admission Number
        - Student Name
        - Total Score
        - Total Max Marks
        - Percentage
        - Grade
        - Rank in class
        
        Features:
        - Filter by class and exam
        - Generate report with totals
        - Export to Excel
        """
        self.report_rows = []

        report_win = tk.Toplevel(self.root)
        report_win.title("Class Exam Report")
        report_win.geometry("900x600")
        report_win.configure(bg=APP_COLORS["bg"])

        # ===== HEADER =====
        header_frame = tk.Frame(report_win, bg=APP_COLORS["primary"], height=60)
        header_frame.pack(fill="x")
        
        tk.Label(
            header_frame,
            text="📊 Class Exam Report",
            font=FONTS["header"],
            bg=APP_COLORS["primary"],
            fg="white"
        ).pack(pady=15)

        # ===== SELECTION FRAME =====
        select_frame = tk.Frame(report_win, bg=APP_COLORS["bg"])
        select_frame.pack(fill="x", padx=15, pady=10)

        # Fetch classes and exams
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT class_name FROM students ORDER BY class_name")
        classes = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT exam_name FROM exams ORDER BY exam_name")
        exams = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not classes or not exams:
            messagebox.showerror("Error", "No classes or exams found")
            return

        # Class selection
        tk.Label(select_frame, text="Class:", font=FONTS["normal"], bg=APP_COLORS["bg"]).pack(side="left", padx=5)
        self.class_var = tk.StringVar(value=classes[0])
        class_menu = tk.OptionMenu(select_frame, self.class_var, *classes)
        class_menu.config(font=FONTS["normal"], width=20, bg="white")
        class_menu.pack(side="left", padx=5)

        # Exam selection
        tk.Label(select_frame, text="Exam:", font=FONTS["normal"], bg=APP_COLORS["bg"]).pack(side="left", padx=5)
        self.report_exam_var = tk.StringVar(value=exams[0])
        exam_menu = tk.OptionMenu(select_frame, self.report_exam_var, *exams)
        exam_menu.config(font=FONTS["normal"], width=20, bg="white")
        exam_menu.pack(side="left", padx=5)

        # ===== REPORT TEXT AREA =====
        text_frame = tk.Frame(report_win, bg=APP_COLORS["bg"])
        text_frame.pack(fill="both", expand=True, padx=15, pady=10)

        text = tk.Text(
            text_frame,
            width=100,
            height=20,
            font=("Courier New", 10),
            bg="white",
            fg=APP_COLORS["text"]
        )
        text.pack(fill="both", expand=True)

        # Scrollbar for text
        scrollbar = tk.Scrollbar(text_frame, command=text.yview)
        scrollbar.pack(side="right", fill="y")
        text.config(yscrollcommand=scrollbar.set)

        def load_report():
            """
            Load and display exam report with student totals and ranks.
            
            Process:
            1. Fetch all student marks for selected exam and class
            2. Calculate total score per student
            3. Calculate percentage
            4. Assign grades
            5. Calculate ranks based on total score
            6. Display in formatted table
            """
            class_name = self.class_var.get()
            exam_name = self.report_exam_var.get()

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Fetch exam ID
            cursor.execute("SELECT id FROM exams WHERE exam_name=?", (exam_name,))
            exam_row = cursor.fetchone()
            if not exam_row:
                messagebox.showerror("Error", "Exam not found")
                conn.close()
                return
            
            exam_id = exam_row[0]

            # Fetch all students in class with their total marks
            cursor.execute("""
                SELECT 
                    s.admission_no,
                    s.student_name,
                    SUM(m.score) as total_score,
                    SUM(es.max_marks) as total_max_marks
                FROM students s
                LEFT JOIN marks m ON s.admission_no = m.admission_no
                LEFT JOIN exam_subjects es ON m.exam_subject_id = es.id
                WHERE s.class_name = ? AND es.exam_id = ?
                GROUP BY s.admission_no, s.student_name
                ORDER BY total_score DESC, s.student_name ASC
            """, (class_name, exam_id))

            rows = cursor.fetchall()
            conn.close()

            if not rows:
                text.delete("1.0", tk.END)
                text.insert(tk.END, "No data available for this class and exam combination")
                self.report_rows = []
                return

            # Store for export
            self.report_rows = rows

            # Calculate percentages and grades
            report_data = []
            for rank, row in enumerate(rows, 1):
                admission_no, student_name, total_score, total_max = row
                
                # Handle None values
                if total_score is None:
                    total_score = 0
                if total_max is None:
                    total_max = 0
                
                # Calculate percentage
                if total_max > 0:
                    percentage = round((total_score * 100) / total_max, 2)
                else:
                    percentage = 0
                
                # Get grade
                grade = self.get_grade(percentage)
                
                report_data.append({
                    'rank': rank,
                    'admission_no': admission_no,
                    'student_name': student_name,
                    'score': total_score,
                    'max_marks': total_max,
                    'percentage': percentage,
                    'grade': grade
                })

            # Display report
            text.delete("1.0", tk.END)
            
            # Header
            header = f"{'Rank':<6} | {'Admn No':<12} | {'Student Name':<25} | {'Score':<8} | {'Max':<8} | {'%':<8} | {'Grade':<8}\n"
            separator = "-" * 105 + "\n"
            
            text.insert(tk.END, f"\n{'='*105}\n")
            text.insert(tk.END, f"CLASS: {class_name}  |  EXAM: {exam_name}\n")
            text.insert(tk.END, f"{'='*105}\n\n")
            text.insert(tk.END, header)
            text.insert(tk.END, separator)

            # Data rows
            for data in report_data:
                row_text = (
                    f"{data['rank']:<6} | "
                    f"{data['admission_no']:<12} | "
                    f"{data['student_name']:<25} | "
                    f"{data['score']:<8} | "
                    f"{data['max_marks']:<8} | "
                    f"{data['percentage']:<8.2f} | "
                    f"{data['grade']:<8}\n"
                )
                text.insert(tk.END, row_text)

            text.insert(tk.END, "\n" + separator)

        def export_report():
            """
            Export report to Excel file.
            
            Creates an Excel file with:
            - Rank
            - Admission Number
            - Student Name
            - Total Score
            - Maximum Marks
            - Percentage
            - Grade
            """
            if not self.report_rows:
                messagebox.showerror("Error", "Generate report first")
                return

            class_name = self.class_var.get()
            exam_name = self.report_exam_var.get()

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Fetch exam ID
            cursor.execute("SELECT id FROM exams WHERE exam_name=?", (exam_name,))
            exam_row = cursor.fetchone()
            if not exam_row:
                messagebox.showerror("Error", "Exam not found")
                conn.close()
                return
            
            exam_id = exam_row[0]

            # Fetch all students in class with their total marks
            cursor.execute("""
                SELECT 
                    s.admission_no,
                    s.student_name,
                    SUM(m.score) as total_score,
                    SUM(es.max_marks) as total_max_marks
                FROM students s
                LEFT JOIN marks m ON s.admission_no = m.admission_no
                LEFT JOIN exam_subjects es ON m.exam_subject_id = es.id
                WHERE s.class_name = ? AND es.exam_id = ?
                GROUP BY s.admission_no, s.student_name
                ORDER BY total_score DESC, s.student_name ASC
            """, (class_name, exam_id))

            rows = cursor.fetchall()
            conn.close()

            if not rows:
                messagebox.showerror("Error", "No data to export")
                return

            # Prepare data for Excel
            data = []
            for rank, row in enumerate(rows, 1):
                admission_no, student_name, total_score, total_max = row
                
                if total_score is None:
                    total_score = 0
                if total_max is None:
                    total_max = 0
                
                if total_max > 0:
                    percentage = round((total_score * 100) / total_max, 2)
                else:
                    percentage = 0
                
                grade = self.get_grade(percentage)
                
                data.append([
                    rank,
                    admission_no,
                    student_name,
                    total_score,
                    total_max,
                    percentage,
                    grade
                ])

            # Create DataFrame and export
            df = pd.DataFrame(
                data,
                columns=["Rank", "Admission No", "Student Name", "Total Score", "Max Marks", "Percentage", "Grade"]
            )

            filename = f"{class_name}_{exam_name}_Report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            try:
                df.to_excel(filename, index=False)
                messagebox.showinfo("Success", f"Report exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")

        # ===== BUTTON FRAME =====
        button_frame = tk.Frame(report_win, bg=APP_COLORS["bg"])
        button_frame.pack(fill="x", padx=15, pady=10)

        tk.Button(
            button_frame,
            text="📊 Generate Report",
            command=load_report,
            font=FONTS["button"],
            bg=APP_COLORS["secondary"],
            fg="white",
            width=25,
            height=2
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="📥 Export to Excel",
            command=export_report,
            font=FONTS["button"],
            bg=APP_COLORS["success"],
            fg="white",
            width=25,
            height=2
        ).pack(side="left", padx=5)
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
        """
        Logout the current user and return to login screen.
        
        Closes all open windows and displays the login dialog again.
        """
        if hasattr(self, 'root') and self.root:
            self.root.destroy()
        self.show_login()

# ===== APPLICATION ENTRY POINT =====
if __name__ == "__main__":
    """
    Main entry point for the Student Result Management System.
    
    Creates an instance of StudentResultApp which initializes the database
    and starts the application with the login screen.
    """
    app = StudentResultApp()

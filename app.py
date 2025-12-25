import sqlite3

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
    name = input("Student Name: ")
    s1 = int(input("Subject 1 Marks: "))
    s2 = int(input("Subject 2 Marks: "))
    s3 = int(input("Subject 3 Marks: "))

    total = s1 + s2 + s3
    grade = calculate_grade(total)

    conn = sqlite3.connect("results.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO students (name, subject1, subject2, subject3, total, grade)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (name, s1, s2, s3, total, grade))

    conn.commit()
    conn.close()

    print("✅ Student result added successfully!")

def view_results():
    conn = sqlite3.connect("results.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    rows = cursor.fetchall()

    print("\nID | Name | Total | Grade")
    print("-" * 30)
    for r in rows:
        print(r[0], r[1], r[5], r[6])

    conn.close()

while True:
    print("\n--- Student Result Management ---")
    print("1. Add Student Result")
    print("2. View Results")
    print("3. Exit")

    choice = input("Enter choice: ")

    if choice == "1":
        add_student()
    elif choice == "2":
        view_results()
    elif choice == "3":
        break
    else:
        print("❌ Invalid choice")

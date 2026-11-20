"""
Smart Student Record Management System
Mini Project - Data Structures and Algorithms Using Python

Data structures used:
    - list: students = [...]  -> holds all student records
    - dict: one dictionary per student
            {'student_id': 'S101', 'name': 'Amina Rahman',
             'major': 'Computer Science', 'cgpa': 3.75}

Sample test data (enter manually using option 1):
    S101 | Amina Rahman | Computer Science    | 3.75
    S102 | Daniel Smith | Cybersecurity       | 3.40
    S103 | Maria Lopez  | Computer Science    | 3.90
    S104 | John Carter  | Information Systems | 3.10
    S105 | Carol        | Data Science        | 3.65
"""


students = []

# Linear search: check records one by one until the ID is found: O(n)
def find_student(student_id):
    for student in students:
        if student["student_id"] == student_id:
            return student
    return None

# Ask until the user enters a non-empty value
def get_non_empty(message):
    while True:
        value = input(message).strip()

        if value != "":
            return value

        print("Error: This field cannot be empty.")


# Ask for a valid CGPA (numeric and between 0.00 and 4.00)
# If allow_empty is True, an empty input returns None (keep the old value)
def get_cgpa(message, allow_empty=False):
    while True:
        value = input(message).strip()

        if allow_empty and value == "":
            return None

        try:
            cgpa = float(value)

            if 0.0 <= cgpa <= 4.0:
                return cgpa

            print("Error: CGPA must be between 0.00 and 4.00.")

        except ValueError:
            print("Error: Please enter a number.")


# 1. Add a student: duplicate check O(n) + append O(1)
def add_student():
    print("\n--- Add Student ---")

    # The ID must be non-empty and unique
    while True:
        student_id = get_non_empty("Student ID: ").upper()

        if find_student(student_id) is not None:
            print("Error: This Student ID already exists.")
        else:
            break

    name = get_non_empty("Student Name: ")
    major = get_non_empty("Major: ")
    cgpa = get_cgpa("CGPA (0.00 - 4.00): ")

    student = {
        "student_id": student_id,
        "name": name,
        "major": major,
        "cgpa": cgpa
    }

    students.append(student)
    print("Student added successfully!")


# 2. Display all students: list traversal O(n)
def display_students():
    print("\n--- All Students ---")

    if not students:
        print("No student records found.")
        return
 
    print(f'{"Student ID":<12}{"Name":<22}{"Major":<25}{"CGPA":>6}')
    print("-" * 65)
 
    for student in students:
        print(f'{student["student_id"]:<12}{student["name"]:<22}'
              f'{student["major"]:<25}{student["cgpa"]:>6.2f}')
 
 
# 3. Search a student using linear search: O(n)
def search_student():
    print("\n--- Search Student ---")
 
    student_id = get_non_empty("Enter Student ID: ").upper()
    student = find_student(student_id)
 
    if student is None:
        print("Student not found.")
    else:
        print("Student ID:", student["student_id"])
        print("Name:", student["name"])
        print("Major:", student["major"])
        print("CGPA:", format(student["cgpa"], ".2f"))
 
 
# 4. Update an existing dictionary: O(n) to find the student
def update_student():
    print("\n--- Update Student ---")
 
    student_id = get_non_empty("Enter Student ID: ").upper()
    student = find_student(student_id)
 
    if student is None:
        print("Student not found.")
        return
 
    print("Press Enter to keep the current value.")
 
    name = input("New name: ").strip()
    major = input("New major: ").strip()
    cgpa = get_cgpa("New CGPA (0.00 - 4.00): ", allow_empty=True)
 
    if name != "":
        student["name"] = name
 
    if major != "":
        student["major"] = major
 
    if cgpa is not None:
        student["cgpa"] = cgpa
 
    print("Student updated successfully!")
 
 
# 5. Search and remove a student (later elements shift): O(n)
def delete_student():
    print("\n--- Delete Student ---")
 
    student_id = get_non_empty("Enter Student ID: ").upper()
    student = find_student(student_id)
 
    if student is None:
        print("Student not found.")
        return
 
    print("Student ID:", student["student_id"])
    print("Name:", student["name"])
    print("Major:", student["major"])
    print("CGPA:", format(student["cgpa"], ".2f"))
 
    confirmation = input("Delete this student? (y/n): ").strip().lower()
 
    if confirmation == "y":
        students.remove(student)
        print("Student deleted successfully!")
    else:
        print("Deletion cancelled.")
 
 
# 6. Statistics: O(n) to sum all CGPAs
def show_statistics():
    print("\n--- Summary Statistics ---")
 
    total = len(students)
    print("Total students:", total)
 
    if total == 0:
        print("Average CGPA: N/A (no students)")
        return
 
    total_cgpa = 0
 
    for student in students:
        total_cgpa += student["cgpa"]
 
    average = total_cgpa / total
    print("Average CGPA:", format(average, ".2f"))
 
 
# 7. Main menu keeps running until Exit
def main():
    while True:
        print("\n===== SMART STUDENT RECORD MANAGEMENT =====")
        print("1. Add Student")
        print("2. Display All Students")
        print("3. Search Student by ID")
        print("4. Update Student Record")
        print("5. Delete Student Record")
        print("6. Show Summary Statistics")
        print("7. Exit")
 
        choice = input("Choose an option (1-7): ").strip()
 
        if choice == "1":
            add_student()
        elif choice == "2":
            display_students()
        elif choice == "3":
            search_student()
        elif choice == "4":
            update_student()
        elif choice == "5":
            delete_student()
        elif choice == "6":
            show_statistics()
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please choose a number from 1 to 7.")
 
 
if __name__ == "__main__":
    main()
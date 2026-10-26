import services


marks_rows = [{
    'Enrollment Number': '23STUCHH001',
    'Student Name': 'Alice',
    'DM': 80,
    'DSC': 75,
    'COA': 88,
    'Python': 90,
    'ML': 84,
    'Department': 'AI & Data Science',
    'Section': 'A',
}]

attendance_rows = [{
    'Enrollment Number': '23STUCHH001',
    'Student Name': 'Alice',
    'DS': 87,
    'EG': 90,
    'EVS': 83,
    'HC': 78,
    'PHYSICS': 95,
    'Department': 'AI & Data Science',
    'Section': 'A',
}]

marks, has_invalid = services.normalize_student_rows(marks_rows, academic_year='2024-2025', department='AI & Data Science', section='A')
assert not has_invalid
assert marks[0]['department'] == 'AI & Data Science'
assert marks[0]['section'] == 'A'

attendance, has_invalid_row, subjects = services.normalize_attendance_rows(attendance_rows, headers=list(attendance_rows[0].keys()), academic_year='2024-2025', department='AI & Data Science', section='A')
assert not has_invalid_row
assert attendance[0]['department'] == 'AI & Data Science'
assert attendance[0]['section'] == 'A'
assert attendance[0]['subjects'] == ['DS', 'EG', 'EVS', 'HC', 'PHYSICS']
print('department/section support ok')

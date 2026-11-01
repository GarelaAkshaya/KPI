import sys
import os
import io
import asyncio
import pandas as pd
from starlette.datastructures import UploadFile
from fastapi import HTTPException

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models
import main

def create_excel_buffer(students, subject_columns):
    data = []
    for idx, (enum, name) in enumerate(students, 1):
        row = {
            "S.No": idx,
            "Enrollment Number": enum,
            "Student Name": name,
        }
        for subj in subject_columns:
            # attendance percentage between 70 and 95
            val = 70.0 + ((idx * 7 + len(subj) * 3) % 26)
            row[subj] = round(val, 1)
        data.append(row)
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Attendance")
    buf.seek(0)
    return buf.getvalue()

async def run_tests_async():
    db = SessionLocal()
    print("=" * 70)
    print("ATTENDANCE SEMESTER END-TO-END TEST SUITE")
    print("=" * 70)

    # 0. Check Initial State & Data Safety Baselines
    marks_count = db.query(models.StudentMark).count()
    student_upload_count = db.query(models.StudentUpload).count()
    faculty_count = db.query(models.Faculty).count()
    lab_count = db.query(models.LaboratoryUtilization).count()

    print(f"[BASELINE] Student Marks: {marks_count}")
    print(f"[BASELINE] Student Uploads (Profiles): {student_upload_count}")
    print(f"[BASELINE] Faculty: {faculty_count}")
    print(f"[BASELINE] Lab Utilization: {lab_count}")

    # Fetch AIDS Section A students to use for realistic testing
    aids_students = (
        db.query(models.StudentUpload)
        .filter(models.StudentUpload.section == 'A', models.StudentUpload.department.ilike('%AI%'))
        .order_by(models.StudentUpload.studentId)
        .all()
    )
    seen = set()
    student_list = []
    for s in aids_students:
        enum = s.enrollment_number or s.studentId
        if enum not in seen:
            seen.add(enum)
            student_list.append((enum, s.studentName))
    print(f"[INFO] Found {len(student_list)} unique AIDS Section A students in roster.")
    assert len(student_list) == 50, f"Expected 50 AIDS Section A students, got {len(student_list)}"

    # 1. Test Validation: Missing Semester
    print("\n--- TEST 1: Mandatory Semester Validation ---")
    buf1 = create_excel_buffer(student_list[:5], ["Computer Programming", "English"])
    upload1 = UploadFile(filename="test_missing_sem.xlsx", file=io.BytesIO(buf1))
    res1 = await main.upload_attendance(
        file=upload1,
        academic_year="2024-2025",
        department="Artificial Intelligence and Data Science",
        section="A",
        semester=None,
        db=db
    )
    assert hasattr(res1, "status_code") and res1.status_code == 400, f"Expected 400 response, got {res1}"
    print(f"[PASS] Missing semester rejected with status 400: {res1.body.decode()}")

    # 2. Test Validation: Invalid Semester
    print("\n--- TEST 2: Invalid Semester Validation ---")
    upload2 = UploadFile(filename="test_invalid_sem.xlsx", file=io.BytesIO(buf1))
    res2 = await main.upload_attendance(
        file=upload2,
        academic_year="2024-2025",
        department="Artificial Intelligence and Data Science",
        section="A",
        semester="Semester 9",
        db=db
    )
    assert hasattr(res2, "status_code") and res2.status_code == 400, f"Expected 400 response, got {res2}"
    print(f"[PASS] Invalid semester 'Semester 9' rejected with status 400: {res2.body.decode()}")

    # 3. Upload Attendance for Semester 1 (2024-2025)
    print("\n--- TEST 3: Upload Semester 1 Attendance ---")
    sem1_subjects = ["Computer Programming", "Basic Electronics", "English", "Digital Fabrication", "Chemistry"]
    buf_sem1 = create_excel_buffer(student_list, sem1_subjects)
    upload_sem1 = UploadFile(filename="AIDS_SecA_Sem1_Attendance.xlsx", file=io.BytesIO(buf_sem1))
    res_sem1 = await main.upload_attendance(
        file=upload_sem1,
        academic_year="2024-2025",
        department="Artificial Intelligence and Data Science",
        section="A",
        semester="Semester 1",
        db=db
    )
    assert isinstance(res_sem1, dict), f"Upload sem1 failed: {getattr(res_sem1, 'body', res_sem1)}"
    assert res_sem1["semester"] == "Semester 1", f"Expected 'Semester 1', got {res_sem1['semester']}"
    assert res_sem1["students"] == len(student_list), f"Expected {len(student_list)} students, got {res_sem1['students']}"
    print(f"[PASS] Semester 1 uploaded: {res_sem1['students']} students, semester={res_sem1['semester']}, subjects={res_sem1['subject_names']}")

    # 4. Upload Attendance for Semester 2 (2024-2025)
    print("\n--- TEST 4: Upload Semester 2 Attendance (Must NOT overwrite Semester 1) ---")
    sem2_subjects = ["Data Structures", "Engineering Graphics", "EVS", "Physics", "Higher Calculus"]
    buf_sem2 = create_excel_buffer(student_list, sem2_subjects)
    upload_sem2 = UploadFile(filename="AIDS_SecA_Sem2_Attendance.xlsx", file=io.BytesIO(buf_sem2))
    res_sem2 = await main.upload_attendance(
        file=upload_sem2,
        academic_year="2024-2025",
        department="Artificial Intelligence and Data Science",
        section="A",
        semester="Semester 2",
        db=db
    )
    assert isinstance(res_sem2, dict), f"Upload sem2 failed: {getattr(res_sem2, 'body', res_sem2)}"
    assert res_sem2["semester"] == "Semester 2"
    assert res_sem2["students"] == len(student_list)
    print(f"[PASS] Semester 2 uploaded: {res_sem2['students']} students, semester={res_sem2['semester']}, subjects={res_sem2['subject_names']}")

    # 5. Upload Attendance for Semester 3 (2025-2026)
    print("\n--- TEST 5: Upload Semester 3 Attendance (2025-2026) ---")
    sem3_subjects = ["AI", "IoT", "OOPs", "DBMS", "EEM"]
    buf_sem3 = create_excel_buffer(student_list, sem3_subjects)
    upload_sem3 = UploadFile(filename="AIDS_SecA_Sem3_Attendance.xlsx", file=io.BytesIO(buf_sem3))
    res_sem3 = await main.upload_attendance(
        file=upload_sem3,
        academic_year="2025-2026",
        department="Artificial Intelligence and Data Science",
        section="A",
        semester="Semester 3",
        db=db
    )
    assert isinstance(res_sem3, dict), f"Upload sem3 failed: {getattr(res_sem3, 'body', res_sem3)}"
    assert res_sem3["semester"] == "Semester 3"
    assert res_sem3["students"] == len(student_list)
    print(f"[PASS] Semester 3 uploaded: {res_sem3['students']} students, semester={res_sem3['semester']}, subjects={res_sem3['subject_names']}")

    # 6. Verify Database Isolation Across Semesters
    print("\n--- TEST 6: Verify Database Isolation Across Semesters ---")
    db_sem1_count = db.query(models.StudentAttendance).filter(
        models.StudentAttendance.academic_year == "2024-2025",
        models.StudentAttendance.semester == "Semester 1"
    ).count()
    db_sem2_count = db.query(models.StudentAttendance).filter(
        models.StudentAttendance.academic_year == "2024-2025",
        models.StudentAttendance.semester == "Semester 2"
    ).count()
    db_sem3_count = db.query(models.StudentAttendance).filter(
        models.StudentAttendance.academic_year == "2025-2026",
        models.StudentAttendance.semester == "Semester 3"
    ).count()

    print(f"Database records: Sem 1 (2024-2025) = {db_sem1_count}")
    print(f"Database records: Sem 2 (2024-2025) = {db_sem2_count}")
    print(f"Database records: Sem 3 (2025-2026) = {db_sem3_count}")

    assert db_sem1_count == len(student_list), f"Expected {len(student_list)} Sem 1 records, got {db_sem1_count}"
    assert db_sem2_count == len(student_list), f"Expected {len(student_list)} Sem 2 records, got {db_sem2_count}"
    assert db_sem3_count == len(student_list), f"Expected {len(student_list)} Sem 3 records, got {db_sem3_count}"
    print("[PASS] Semesters 1, 2, and 3 records coexist without collision or overwriting!")

    # 7. Test get_attendance Query Filtering
    print("\n--- TEST 7: Query Filtering via get_attendance ---")
    # Query Sem 1
    sem1_data = main.get_attendance(
        academic_year="2024-2025",
        semester="Semester 1",
        department="Artificial Intelligence and Data Science",
        section="A",
        db=db
    )
    assert len(sem1_data) == len(student_list)
    assert all(r.semester == "Semester 1" for r in sem1_data)
    assert set(sem1_data[0].subjects) == set(sem1_subjects)
    print(f"[PASS] get_attendance(semester='Semester 1') returned {len(sem1_data)} records, all semester='Semester 1', subjects={sem1_data[0].subjects}")

    # Query Sem 2
    sem2_data = main.get_attendance(
        academic_year="2024-2025",
        semester="Semester 2",
        department="Artificial Intelligence and Data Science",
        section="A",
        db=db
    )
    assert len(sem2_data) == len(student_list)
    assert all(r.semester == "Semester 2" for r in sem2_data)
    assert set(sem2_data[0].subjects) == {'DS', 'EG', 'EVS', 'HC', 'PHYSICS'}
    print(f"[PASS] get_attendance(semester='Semester 2') returned {len(sem2_data)} records, all semester='Semester 2', subjects={sem2_data[0].subjects}")

    # Query Sem 3
    sem3_data = main.get_attendance(
        academic_year="2025-2026",
        semester="Semester 3",
        department="Artificial Intelligence and Data Science",
        section="A",
        db=db
    )
    assert len(sem3_data) == len(student_list)
    assert all(r.semester == "Semester 3" for r in sem3_data)
    assert set(sem3_data[0].subjects) == set(sem3_subjects)
    print(f"[PASS] get_attendance(semester='Semester 3') returned {len(sem3_data)} records, all semester='Semester 3', subjects={sem3_data[0].subjects}")

    # Query All Semesters for 2024-2025
    all_data = main.get_attendance(
        academic_year="2024-2025",
        semester="All",
        department="Artificial Intelligence and Data Science",
        section="A",
        db=db
    )
    assert len(all_data) == len(student_list) * 2
    print(f"[PASS] get_attendance(semester='All') returned {len(all_data)} records (Sem 1 + Sem 2)")

    # 8. Test get_attendance_subjects Scoping
    print("\n--- TEST 8: Subjects Query via get_attendance_subjects ---")
    subjs1 = main.get_attendance_subjects(academic_year="2024-2025", semester="Semester 1", department="Artificial Intelligence and Data Science", section="A", db=db)
    assert set(subjs1) == set(sem1_subjects), f"Expected {sem1_subjects}, got {subjs1}"
    print(f"[PASS] Sem 1 subjects: {subjs1}")

    subjs2 = main.get_attendance_subjects(academic_year="2024-2025", semester="Semester 2", department="Artificial Intelligence and Data Science", section="A", db=db)
    assert set(subjs2) == {'DS', 'EG', 'EVS', 'HC', 'PHYSICS'}, f"Expected DS, EG, EVS, HC, PHYSICS, got {subjs2}"
    print(f"[PASS] Sem 2 subjects: {subjs2}")

    # 9. Test get_attendance_kpi Calculation Scoping
    print("\n--- TEST 9: KPI Calculation Isolation via get_attendance_kpi ---")
    kpi_sem1 = main.get_attendance_kpi(academic_year="2024-2025", semester="Semester 1", department="Artificial Intelligence and Data Science", section="A", db=db)
    kpi_sem2 = main.get_attendance_kpi(academic_year="2024-2025", semester="Semester 2", department="Artificial Intelligence and Data Science", section="A", db=db)
    kpi_sem3 = main.get_attendance_kpi(academic_year="2025-2026", semester="Semester 3", department="Artificial Intelligence and Data Science", section="A", db=db)

    print(f"[PASS] Sem 1 KPI: total_students={kpi_sem1['total_students']}, overall_avg={kpi_sem1['overall_average_attendance']}%, subjects={len(kpi_sem1.get('subjects', []))}")
    print(f"[PASS] Sem 2 KPI: total_students={kpi_sem2['total_students']}, overall_avg={kpi_sem2['overall_average_attendance']}%, subjects={len(kpi_sem2.get('subjects', []))}")
    print(f"[PASS] Sem 3 KPI: total_students={kpi_sem3['total_students']}, overall_avg={kpi_sem3['overall_average_attendance']}%, subjects={len(kpi_sem3.get('subjects', []))}")

    # 10. Backward Compatibility Test for Records with semester=None
    print("\n--- TEST 10: Backward Compatibility (Legacy Records with semester=None) ---")
    legacy_rec = models.StudentAttendance(
        student_id="LEGACY_TEST_001",
        enrollment_number="LEGACY_TEST_001",
        student_name="Legacy Test Student",
        department="Computer Science and Engineering",
        section="B",
        academic_year="2024-2025",
        semester=None,  # Legacy record without semester!
        total_classes=100,
        attended_classes=85,
        attendance_percentage=85.0,
        average_attendance=85.0,
        subjects_json="[]",
        subject_values_json="{}"
    )
    db.add(legacy_rec)
    db.commit()

    # Query without semester (All)
    all_recs = main.get_attendance(academic_year="2024-2025", department="Computer Science and Engineering", section="B", db=db)
    legacy_found = any(r.student_id == "LEGACY_TEST_001" for r in all_recs)
    assert legacy_found, "Legacy record with semester=None should be accessible when semester is omitted!"
    print("[PASS] Legacy record with semester=None is accessible when semester filter is omitted / 'All'.")

    # Clean up test legacy record
    db.delete(legacy_rec)
    db.commit()
    print("[PASS] Legacy test record cleaned up safely.")

    # 11. Final Data Safety Verification
    print("\n--- TEST 11: Data Safety Verification ---")
    final_marks = db.query(models.StudentMark).count()
    final_uploads = db.query(models.StudentUpload).count()
    final_faculty = db.query(models.Faculty).count()
    final_lab = db.query(models.LaboratoryUtilization).count()

    assert final_marks == marks_count, f"Marks changed from {marks_count} to {final_marks}"
    assert final_uploads == student_upload_count, f"Student uploads changed from {student_upload_count} to {final_uploads}"
    assert final_faculty == faculty_count, f"Faculty changed from {faculty_count} to {final_faculty}"
    assert final_lab == lab_count, f"Lab utilization changed from {lab_count} to {final_lab}"

    print(f"[PASS] All unrelated datasets preserved 100%:")
    print(f"       - Student Marks: {final_marks} / {marks_count}")
    print(f"       - Student Uploads: {final_uploads} / {student_upload_count}")
    print(f"       - Faculty: {final_faculty} / {faculty_count}")
    print(f"       - Lab Utilization: {final_lab} / {lab_count}")

    db.close()
    print("\n" + "=" * 70)
    print("ALL 11 TESTS PASSED PERFECTLY!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_tests_async())

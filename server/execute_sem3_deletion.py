import os
import sys
import json
from datetime import datetime
from sqlalchemy import text

# Force UTF-8 encoding on standard output for Windows console compatibility
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database
import services

def run_sem3_deletion():
    print("=" * 70)
    print("SEMESTER 3 STUDENT MARKS DELETION - SUPABASE POSTGRESQL")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Host: {database.engine.url.host}")
    print(f"Database: {database.engine.url.database}")
    print("=" * 70)

    # 1. Identification and Pre-Deletion Inspection
    print("\n[Step 1] Inspecting matching Semester 3 records...")
    with database.engine.connect() as conn:
        # Check student_marks (granular subject-wise marks table)
        sm_rows = conn.execute(text("""
            SELECT id, student_id, enrollment_number, student_name, department, section, academic_year, semester, subject, test1, lab1, test2, lab2, compre, total
            FROM student_marks
            WHERE academic_year = '2024-2025'
              AND department IN ('AI & Data Science', 'Artificial Intelligence and Data Science (AIDS)')
              AND section = 'A'
              AND semester IN ('Semester 3', '3')
        """)).mappings().all()
        
        # Check student_uploads (consolidated marks records for Semester 3)
        su_rows = conn.execute(text("""
            SELECT id, "studentId", enrollment_number, "studentName", department, section, academic_year, semester, "totalMarks", percentage, subject_marks_json
            FROM student_uploads
            WHERE academic_year = '2024-2025'
              AND department IN ('AI & Data Science', 'Artificial Intelligence and Data Science (AIDS)')
              AND section = 'A'
              AND semester IN ('Semester 3', '3')
        """)).mappings().all()

        # Subject breakdown in student_marks
        sm_by_subj = conn.execute(text("""
            SELECT subject, count(*) as cnt
            FROM student_marks
            WHERE academic_year = '2024-2025'
              AND department IN ('AI & Data Science', 'Artificial Intelligence and Data Science (AIDS)')
              AND section = 'A'
              AND semester IN ('Semester 3', '3')
            GROUP BY subject
        """)).mappings().all()

        print(f"  Exact table storing subject-wise student marks: 'student_marks'")
        print(f"  Total matching Semester 3 records in 'student_marks': {len(sm_rows)}")
        for r in sm_by_subj:
            print(f"    - Subject '{r['subject']}': {r['cnt']} records")

        print(f"\n  Consolidated Semester 3 records in 'student_uploads': {len(su_rows)}")

        # Check preserved tables baseline
        baseline = {
            "faculty": conn.execute(text('SELECT count(*) FROM faculty')).scalar(),
            "laboratory_utilization": conn.execute(text('SELECT count(*) FROM laboratory_utilization')).scalar(),
            "departments": conn.execute(text('SELECT count(*) FROM departments')).scalar(),
            "kpis": conn.execute(text('SELECT count(*) FROM kpis')).scalar(),
            "admin_users": conn.execute(text('SELECT count(*) FROM admin_users')).scalar(),
            "student_attendance": conn.execute(text('SELECT count(*) FROM student_attendance')).scalar(),
            "student_marks_sem1": conn.execute(text("SELECT count(*) FROM student_marks WHERE semester = 'Semester 1'")).scalar(),
            "student_marks_sem2": conn.execute(text("SELECT count(*) FROM student_marks WHERE semester = 'Semester 2'")).scalar(),
            "student_uploads_sem1": conn.execute(text("SELECT count(*) FROM student_uploads WHERE semester = 'Semester 1'")).scalar(),
            "student_uploads_sem2": conn.execute(text("SELECT count(*) FROM student_uploads WHERE semester = 'Semester 2'")).scalar(),
        }

        print("\n[Step 2] Baseline verification of records to preserve:")
        for k, v in baseline.items():
            print(f"  - {k}: {v} records (Preserved)")

        # 2. Backup Semester 3 data before deletion
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backup")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"student_marks_sem3_backup_{timestamp}.json")

        backup_payload = {
            "timestamp": timestamp,
            "scope": {
                "department": "Artificial Intelligence and Data Science (AIDS)",
                "academic_year": "2024-2025",
                "section": "A",
                "semester": "Semester 3"
            },
            "student_marks_count": len(sm_rows),
            "student_uploads_count": len(su_rows),
            "student_marks": [dict(r) for r in sm_rows],
            "student_uploads": [dict(r) for r in su_rows]
        }
        with open(backup_file, "w", encoding="utf-8") as bf:
            json.dump(backup_payload, bf, indent=2, default=str)
        print(f"\n[Step 3] Backup saved to: {backup_file}")

    # 3. Transactional Execution
    print("\n[Step 4] Executing deletion inside atomic transaction...")
    with database.engine.begin() as conn:
        # 1. Delete from student_marks (granular subject marks table)
        del_sm = conn.execute(text("""
            DELETE FROM student_marks
            WHERE academic_year = '2024-2025'
              AND department IN ('AI & Data Science', 'Artificial Intelligence and Data Science (AIDS)')
              AND section = 'A'
              AND semester IN ('Semester 3', '3')
        """))
        deleted_sm_count = del_sm.rowcount
        print(f"  - Deleted from 'student_marks': {deleted_sm_count} records")

        # 2. Delete Semester 3 consolidated marks records from student_uploads
        del_su = conn.execute(text("""
            DELETE FROM student_uploads
            WHERE academic_year = '2024-2025'
              AND department IN ('AI & Data Science', 'Artificial Intelligence and Data Science (AIDS)')
              AND section = 'A'
              AND semester IN ('Semester 3', '3')
        """))
        deleted_su_count = del_su.rowcount
        print(f"  - Deleted from 'student_uploads': {deleted_su_count} Semester 3 records")

        # 4. In-transaction verification
        rem_sm3 = conn.execute(text("""
            SELECT count(*) FROM student_marks
            WHERE academic_year = '2024-2025'
              AND department IN ('AI & Data Science', 'Artificial Intelligence and Data Science (AIDS)')
              AND section = 'A'
              AND semester IN ('Semester 3', '3')
        """)).scalar()
        if rem_sm3 != 0:
            raise RuntimeError(f"Integrity check failed: Expected 0 Semester 3 records in student_marks, found {rem_sm3}")

        rem_su3 = conn.execute(text("""
            SELECT count(*) FROM student_uploads
            WHERE academic_year = '2024-2025'
              AND department IN ('AI & Data Science', 'Artificial Intelligence and Data Science (AIDS)')
              AND section = 'A'
              AND semester IN ('Semester 3', '3')
        """)).scalar()
        if rem_su3 != 0:
            raise RuntimeError(f"Integrity check failed: Expected 0 Semester 3 records in student_uploads, found {rem_su3}")

        # Safety verification for preserved non-student and other semester records
        for k, expected_count in baseline.items():
            if k == "faculty":
                cur = conn.execute(text('SELECT count(*) FROM faculty')).scalar()
            elif k == "laboratory_utilization":
                cur = conn.execute(text('SELECT count(*) FROM laboratory_utilization')).scalar()
            elif k == "departments":
                cur = conn.execute(text('SELECT count(*) FROM departments')).scalar()
            elif k == "kpis":
                cur = conn.execute(text('SELECT count(*) FROM kpis')).scalar()
            elif k == "admin_users":
                cur = conn.execute(text('SELECT count(*) FROM admin_users')).scalar()
            elif k == "student_attendance":
                cur = conn.execute(text('SELECT count(*) FROM student_attendance')).scalar()
            elif k == "student_marks_sem1":
                cur = conn.execute(text("SELECT count(*) FROM student_marks WHERE semester = 'Semester 1'")).scalar()
            elif k == "student_marks_sem2":
                cur = conn.execute(text("SELECT count(*) FROM student_marks WHERE semester = 'Semester 2'")).scalar()
            elif k == "student_uploads_sem1":
                cur = conn.execute(text("SELECT count(*) FROM student_uploads WHERE semester = 'Semester 1'")).scalar()
            elif k == "student_uploads_sem2":
                cur = conn.execute(text("SELECT count(*) FROM student_uploads WHERE semester = 'Semester 2'")).scalar()
            else:
                continue

            if cur != expected_count:
                raise RuntimeError(f"SAFETY VIOLATION: {k} changed from {expected_count} to {cur}! Transaction rolling back.")
            print(f"  [PRESERVED] {k}: {cur} records (intact)")

    print("\n[SUCCESS] Transaction committed successfully to Supabase PostgreSQL.")

    # 5. Verify KPI calculations
    print("\n[Step 5] Checking KPI calculations...")
    with database.SessionLocal() as session:
        # Semester 3 Pass Percentage KPI
        kpi_sem3 = services.get_pass_percentage_kpi(
            session,
            academic_year="2024-2025",
            department="Artificial Intelligence and Data Science (AIDS)",
            section="A",
            semester="Semester 3"
        )
        print(f"  - Semester 3 Pass Percentage KPI:")
        print(f"      Total Students Evaluated: {kpi_sem3.get('total_students_evaluated')}")
        print(f"      Overall Pass %: {kpi_sem3.get('overall_pass_percentage')}%")

        # Semester 1 & 2 Pass Percentage KPIs (Must remain active)
        kpi_sem1 = services.get_pass_percentage_kpi(
            session,
            academic_year="2024-2025",
            department="Artificial Intelligence and Data Science (AIDS)",
            section="A",
            semester="Semester 1"
        )
        print(f"  - Semester 1 Pass Percentage KPI (Preserved): Evaluated = {kpi_sem1.get('total_students_evaluated')}, Pass % = {kpi_sem1.get('overall_pass_percentage')}%")

        kpi_sem2 = services.get_pass_percentage_kpi(
            session,
            academic_year="2024-2025",
            department="Artificial Intelligence and Data Science (AIDS)",
            section="A",
            semester="Semester 2"
        )
        print(f"  - Semester 2 Pass Percentage KPI (Preserved): Evaluated = {kpi_sem2.get('total_students_evaluated')}, Pass % = {kpi_sem2.get('overall_pass_percentage')}%")

        # Average marks across remaining active records
        avg_marks = services.get_average_student_marks(
            session,
            academic_year="2024-2025",
            department="AI & Data Science",
            section="A"
        )
        print(f"  - Cohort Average Student Marks (Semesters 1 & 2 only): {avg_marks}")

        # Unique student count in cohort
        stu_cnt = services.get_student_count(
            session,
            academic_year="2024-2025",
            department="AI & Data Science",
            section="A"
        )
        print(f"  - Cohort Distinct Students Count (Preserved): {stu_cnt}")

    print("\n" + "=" * 70)
    print("SEMESTER 3 CLEANUP COMPLETED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    run_sem3_deletion()


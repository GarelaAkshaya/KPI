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

def execute_cleanup():
    print("=" * 70)
    print("SUPABASE POSTGRESQL STUDENT MARKS CLEANUP")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Database Host: {database.engine.url.host}")
    print(f"Target Database: {database.engine.url.database}")
    print("=" * 70)

    # 1. Take a full backup of affected records
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backup")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"student_marks_backup_{timestamp}.json")

    with database.engine.connect() as conn:
        print("\n[Step 1] Backing up affected records...")
        sm_rows = conn.execute(text("""
            SELECT * FROM student_marks 
            WHERE academic_year = '2024-2025' 
              AND department IN ('AI & Data Science', 'Artificial Intelligence and Data Science (AIDS)')
              AND section = 'A'
              AND semester IN ('Semester 1', 'Semester 2')
        """)).mappings().all()
        
        su_rows = conn.execute(text("""
            SELECT * FROM student_uploads 
            WHERE academic_year = '2024-2025' 
              AND department IN ('AI & Data Science', 'Artificial Intelligence and Data Science (AIDS)')
              AND section = 'A'
              AND (semester IN ('Semester 1', 'Semester 2') OR semester IS NULL)
        """)).mappings().all()

        backup_data = {
            "backup_timestamp": timestamp,
            "target_scope": {
                "department": "Artificial Intelligence and Data Science (AIDS)",
                "academic_year": "2024-2025",
                "section": "A",
                "semesters": ["Semester 1", "Semester 2"]
            },
            "student_marks_count": len(sm_rows),
            "student_uploads_count": len(su_rows),
            "student_marks": [dict(r) for r in sm_rows],
            "student_uploads": [dict(r) for r in su_rows]
        }

        # Convert datetimes to string for JSON serialization
        def default_serializer(o):
            if isinstance(o, datetime):
                return o.isoformat()
            return str(o)

        with open(backup_file, "w", encoding="utf-8") as bf:
            json.dump(backup_data, bf, indent=2, default=default_serializer)
        print(f"  Backup saved successfully ({len(sm_rows)} marks, {len(su_rows)} student profiles) to:")
        print(f"  {backup_file}")

        # 2. Check baseline counts of preserved tables
        print("\n[Step 2] Baseline count verification of preserved tables...")
        baseline = {
            "faculty": conn.execute(text('SELECT count(*) FROM faculty')).scalar(),
            "laboratory_utilization": conn.execute(text('SELECT count(*) FROM laboratory_utilization')).scalar(),
            "departments": conn.execute(text('SELECT count(*) FROM departments')).scalar(),
            "kpis": conn.execute(text('SELECT count(*) FROM kpis')).scalar(),
            "admin_users": conn.execute(text('SELECT count(*) FROM admin_users')).scalar(),
            "student_attendance": conn.execute(text('SELECT count(*) FROM student_attendance')).scalar(),
        }
        for tbl, count in baseline.items():
            print(f"  - {tbl}: {count} records")

    # 3. Transactional Execution using engine.begin()
    print("\n[Step 3] Executing transactional cleanup...")
    with database.engine.begin() as conn:
        # Delete from student_marks
        del_res = conn.execute(text("""
            DELETE FROM student_marks 
            WHERE academic_year = '2024-2025' 
              AND department IN ('AI & Data Science', 'Artificial Intelligence and Data Science (AIDS)')
              AND section = 'A'
              AND semester IN ('Semester 1', 'Semester 2')
        """))
        deleted_marks_count = del_res.rowcount
        print(f"  - student_marks deleted: {deleted_marks_count} records")

        # Clear marks in student_uploads while preserving student identity
        upd_res = conn.execute(text("""
            UPDATE student_uploads 
            SET "totalMarks" = 0,
                percentage = 0.0,
                subject_marks_json = '{}',
                component_marks_json = '{}',
                dm = NULL,
                dsc = NULL,
                coa = NULL,
                python_marks = NULL,
                ml = NULL
            WHERE academic_year = '2024-2025' 
              AND department IN ('AI & Data Science', 'Artificial Intelligence and Data Science (AIDS)')
              AND section = 'A'
              AND (semester IN ('Semester 1', 'Semester 2') OR semester IS NULL)
        """))
        updated_uploads_count = upd_res.rowcount
        print(f"  - student_uploads marks cleared (identities preserved): {updated_uploads_count} records")

        # 4. Integrity verification inside the transaction
        print("\n[Step 4] Verifying table integrity inside transaction...")
        post_sm = conn.execute(text("""
            SELECT count(*) FROM student_marks 
            WHERE academic_year = '2024-2025' 
              AND department IN ('AI & Data Science', 'Artificial Intelligence and Data Science (AIDS)')
              AND section = 'A'
              AND semester IN ('Semester 1', 'Semester 2')
        """)).scalar()
        if post_sm != 0:
            raise RuntimeError(f"Safety check failed: Expected 0 marks in student_marks, found {post_sm}")

        for tbl, expected_count in baseline.items():
            cur_cnt = conn.execute(text(f'SELECT count(*) FROM {tbl}')).scalar()
            if cur_cnt != expected_count:
                raise RuntimeError(f"CRITICAL VIOLATION: {tbl} count changed from {expected_count} to {cur_cnt}! Aborting.")
            print(f"  [PRESERVED] {tbl}: {cur_cnt} rows (unchanged)")

    print("\n[SUCCESS] Transaction committed successfully to Supabase PostgreSQL.")

    # 5. Verify KPI calculations
    print("\n[Step 5] Checking KPI calculations...")
    with database.SessionLocal() as session:
        pass_kpi = services.get_pass_percentage_kpi(
            session,
            academic_year="2024-2025",
            department="Artificial Intelligence and Data Science (AIDS)",
            section="A",
            semester="Semester 1"
        )
        print(f"  - Pass Percentage KPI: Total Evaluated = {pass_kpi.get('total_students_evaluated')}, Overall Pass % = {pass_kpi.get('overall_pass_percentage')}%")

        avg_marks = services.get_average_student_marks(
            session,
            academic_year="2024-2025",
            department="AI & Data Science",
            section="A"
        )
        print(f"  - Average Student Marks: {avg_marks}")

        summary = services.get_kpi_summary(session, academic_year="2024-2025")
        print(f"  - KPI Summary Average Student Marks: {summary.get('average_student_marks')}")

    print("\n" + "=" * 70)
    print("CLEANUP COMPLETED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    execute_cleanup()

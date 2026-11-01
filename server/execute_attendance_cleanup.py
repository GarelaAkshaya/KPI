import sys
import os
from sqlalchemy import inspect, text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
import models

def main():
    print("=" * 80)
    print("STUDENT ATTENDANCE CLEANUP SCRIPT (SUPABASE POSTGRESQL)")
    print("=" * 80)

    insp = inspect(engine)
    all_tables = insp.get_table_names()
    print(f"\n1. Database Inspection:")
    print(f"   Connected database dialect: {engine.dialect.name}")
    print(f"   All database tables ({len(all_tables)}): {all_tables}")

    attendance_tables = [t for t in all_tables if "attend" in t.lower()]
    print(f"   Attendance tables identified: {attendance_tables}")

    # Check foreign keys pointing to or from attendance tables
    for t in attendance_tables:
        fks = insp.get_foreign_keys(t)
        print(f"   Foreign keys defined on table '{t}': {fks}")

    db = SessionLocal()

    # Pre-deletion counts across all application tables
    print(f"\n2. Pre-Deletion Table Counts:")
    pre_counts = {}
    for t in sorted(all_tables):
        cnt = db.execute(text(f'SELECT count(*) FROM "{t}"')).scalar()
        pre_counts[t] = cnt
        marker = " <--- ATTENDANCE TABLE" if t in attendance_tables else ""
        print(f"   {t:<30}: {cnt}{marker}")

    attendance_count_before = pre_counts.get("student_attendance", 0)

    # Detailed breakdown of student_attendance before deletion
    if attendance_count_before > 0:
        print(f"\n3. Pre-Deletion Attendance Breakdown:")
        breakdown = db.execute(text("""
            SELECT academic_year, semester, department, section, count(*) as count
            FROM student_attendance
            GROUP BY academic_year, semester, department, section
            ORDER BY academic_year, semester, department, section
        """)).fetchall()
        for row in breakdown:
            print(f"   Year: {row[0]}, Sem: {row[1]}, Dept: {row[2]}, Sec: {row[3]} -> Count: {row[4]}")

    # Execute deletion inside a transaction
    print(f"\n4. Executing Attendance Deletion...")
    total_deleted = 0
    try:
        deleted = db.query(models.StudentAttendance).delete(synchronize_session=False)
        db.commit()
        total_deleted = deleted
        print(f"   Successfully committed deletion of {total_deleted} records from 'student_attendance'.")
    except Exception as e:
        db.rollback()
        print(f"   [ERROR] Deletion failed and was rolled back: {e}")
        db.close()
        sys.exit(1)

    # Post-deletion verification
    print(f"\n5. Post-Deletion Verification:")
    post_counts = {}
    for t in sorted(all_tables):
        cnt = db.execute(text(f'SELECT count(*) FROM "{t}"')).scalar()
        post_counts[t] = cnt
        status = "ZERO (VERIFIED)" if t == "student_attendance" and cnt == 0 else "PRESERVED"
        print(f"   {t:<30}: Before={pre_counts[t]:<5} After={cnt:<5} [{status}]")

    attendance_count_after = post_counts.get("student_attendance", 0)
    assert attendance_count_after == 0, f"Expected 0 attendance records, got {attendance_count_after}"

    # Verify unrelated tables
    for t in all_tables:
        if t not in attendance_tables:
            assert pre_counts[t] == post_counts[t], (
                f"SAFETY CHECK FAILED: Table '{t}' changed from {pre_counts[t]} to {post_counts[t]}!"
            )

    print("\n" + "=" * 80)
    print("ATTENDANCE CLEANUP AND VERIFICATION COMPLETED SUCCESSFULLY!")
    print(f"Records deleted: {total_deleted}")
    print(f"Remaining student attendance records: {attendance_count_after}")
    print("All student profiles, marks, faculty, lab utilization, and other tables are 100% intact.")
    print("=" * 80)

    db.close()

if __name__ == "__main__":
    main()


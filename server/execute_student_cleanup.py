import sys
import os
from sqlalchemy import text

# Force utf-8 encoding on standard output for Windows console compatibility
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure server path is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database

def run_cleanup(dry_run: bool = True):
    print("=" * 60)
    print("SUPABASE POSTGRESQL CLEANUP EXECUTION")
    print(f"Mode: {'DRY RUN (No changes will be committed)' if dry_run else 'LIVE EXECUTION (Changes will be committed)'}")
    print(f"Target Database Host: {database.engine.url.host}")
    print(f"Target Database: {database.engine.url.database}")
    print("=" * 60)

    with database.engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Baseline verification of preserved tables
            print("\n[1] Checking baseline counts for non-student tables...")
            baseline_counts = {
                "faculty": conn.execute(text('SELECT count(*) FROM "faculty"')).scalar(),
                "laboratory_utilization": conn.execute(text('SELECT count(*) FROM "laboratory_utilization"')).scalar(),
                "departments": conn.execute(text('SELECT count(*) FROM "departments"')).scalar(),
                "admin_users": conn.execute(text('SELECT count(*) FROM "admin_users"')).scalar(),
                "kpis": conn.execute(text('SELECT count(*) FROM "kpis"')).scalar(),
            }
            for tbl, cnt in baseline_counts.items():
                print(f"  - {tbl}: {cnt} rows")

            # 2. Counts of records to delete
            print("\n[2] Checking target records for deletion...")
            del_queries = {
                "student_attendance (2024-2025 & 2025-2026)": (
                    'SELECT count(*) FROM "student_attendance" WHERE academic_year IN (\'2024-2025\', \'2025-2026\')',
                    'DELETE FROM "student_attendance" WHERE academic_year IN (\'2024-2025\', \'2025-2026\')'
                ),
                "student_uploads (2024-2025 & 2025-2026)": (
                    'SELECT count(*) FROM "student_uploads" WHERE academic_year IN (\'2024-2025\', \'2025-2026\')',
                    'DELETE FROM "student_uploads" WHERE academic_year IN (\'2024-2025\', \'2025-2026\')'
                ),
                "student_feedback (2024-2025 & 2025-2026)": (
                    'SELECT count(*) FROM "student_feedback" WHERE academic_year IN (\'2024-2025\', \'2025-2026\')',
                    'DELETE FROM "student_feedback" WHERE academic_year IN (\'2024-2025\', \'2025-2026\')'
                ),
            }

            deletion_stats = {}
            for label, (count_sql, delete_sql) in del_queries.items():
                count = conn.execute(text(count_sql)).scalar()
                deletion_stats[label] = count
                print(f"  - {label}: {count} records found")

            # 3. Perform scoped deletion
            print("\n[3] Executing scoped deletions within transaction...")
            actual_deleted = {}
            for label, (count_sql, delete_sql) in del_queries.items():
                res = conn.execute(text(delete_sql))
                actual_deleted[label] = res.rowcount
                print(f"  [DELETED] {label}: {res.rowcount} rows targeted")

            # 4. Verify post-deletion state of student tables
            post_student_attendance = conn.execute(text('SELECT count(*) FROM "student_attendance"')).scalar()
            post_student_uploads = conn.execute(text('SELECT count(*) FROM "student_uploads"')).scalar()
            post_student_feedback = conn.execute(text('SELECT count(*) FROM "student_feedback"')).scalar()
            print(f"\nRemaining rows in student tables inside transaction:")
            print(f"  - student_attendance: {post_student_attendance}")
            print(f"  - student_uploads: {post_student_uploads}")
            print(f"  - student_feedback: {post_student_feedback}")

            # 5. Integrity verification of preserved tables
            print("\n[4] Verifying preservation of non-student tables...")
            for tbl, expected_cnt in baseline_counts.items():
                current_cnt = conn.execute(text(f'SELECT count(*) FROM "{tbl}"')).scalar()
                if current_cnt != expected_cnt:
                    raise RuntimeError(
                        f"CRITICAL SAFETY VIOLATION: {tbl} record count changed from {expected_cnt} to {current_cnt}!"
                    )
                print(f"  [PRESERVED] {tbl}: {current_cnt} rows (unchanged)")

            # 6. Commit or rollback
            if dry_run:
                trans.rollback()
                print("\n[!] DRY RUN COMPLETED: Transaction rolled back successfully. No data was modified.")
            else:
                trans.commit()
                print("\n[SUCCESS] LIVE EXECUTION COMPLETED: Transaction committed successfully.")

            return {
                "baseline": baseline_counts,
                "deleted": actual_deleted,
                "remaining_student": {
                    "student_attendance": post_student_attendance,
                    "student_uploads": post_student_uploads,
                    "student_feedback": post_student_feedback,
                }
            }

        except Exception as e:
            trans.rollback()
            print(f"\n[ERROR] Transaction rolled back due to error: {e}")
            raise

if __name__ == "__main__":
    is_live = "--live" in sys.argv
    run_cleanup(dry_run=not is_live)

import sys
import os
import json

# Ensure server folder is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database
from sqlalchemy import text

def inspect():
    with database.engine.connect() as conn:
        print("=== Connected to Supabase PostgreSQL ===")
        print(f"Dialect: {database.engine.dialect.name}")
        print(f"Host: {database.engine.url.host}")
        print(f"Database: {database.engine.url.database}")
        print()

        # 1. All user tables
        res = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in res.fetchall()]
        print("Tables in public schema:")
        for t in tables:
            print(f" - {t}")
        print()

        # 2. Foreign keys in public schema
        print("=== Foreign Key Constraints ===")
        fk_res = conn.execute(text("""
            SELECT
                tc.table_name AS source_table,
                kcu.column_name AS source_column,
                ccu.table_name AS target_table,
                ccu.column_name AS target_column,
                tc.constraint_name
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public';
        """))
        fks = fk_res.fetchall()
        if not fks:
            print("No foreign keys defined in public schema.")
        else:
            for fk in fks:
                print(f" - {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]} ({fk[4]})")
        print()

        # 3. Columns and counts for each table
        print("=== Table Details and Row Counts ===")
        for t in tables:
            # count
            count_res = conn.execute(text(f'SELECT count(*) FROM "{t}"'))
            row_count = count_res.scalar()

            # columns
            cols_res = conn.execute(text(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = '{t}'
                ORDER BY ordinal_position;
            """))
            cols = cols_res.fetchall()
            col_names = [c[0] for c in cols]
            print(f"Table '{t}': {row_count} rows")
            print(f"  Columns: {', '.join(col_names)}")

            # Check if academic_year column exists
            if 'academic_year' in col_names:
                ay_res = conn.execute(text(f"""
                    SELECT academic_year, count(*) 
                    FROM "{t}" 
                    GROUP BY academic_year 
                    ORDER BY academic_year;
                """))
                ay_counts = ay_res.fetchall()
                print("  Academic year breakdown:")
                for ay, c in ay_counts:
                    print(f"    - '{ay}': {c} rows")
            print()

        # 4. Check contents of kpis table
        if 'kpis' in tables:
            print("=== KPIs Table Sample / Breakdown ===")
            kpi_res = conn.execute(text('SELECT id, name, academic_year, value, target, status, category FROM "kpis"'))
            kpi_rows = kpi_res.fetchall()
            for r in kpi_rows:
                print(f"  KPI {r[0]}: {r[1]} | AY: {r[2]} | Val: {r[3]} | Target: {r[4]} | Status: {r[5]} | Category: {r[6]}")
            print()

        # 5. Check student_feedback table
        if 'student_feedback' in tables:
            print("=== Student Feedback Table Sample ===")
            fb_res = conn.execute(text('SELECT count(*) FROM "student_feedback"'))
            fb_count = fb_res.scalar()
            print(f"  Total feedback rows: {fb_count}")
            if fb_count > 0:
                sample_fb = conn.execute(text('SELECT id, academic_year, department, created_at FROM "student_feedback" LIMIT 5')).fetchall()
                for sf in sample_fb:
                    print(f"    Feedback {sf[0]}: AY: {sf[1]} | Dept: {sf[2]} | Created: {sf[3]}")
            print()

if __name__ == "__main__":
    inspect()


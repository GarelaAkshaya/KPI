"""
Utility script to migrate existing SQLite data (ifhe_kpi.db) to a target PostgreSQL database specified by DATABASE_URL.
"""

import os
import sys
import sqlite3
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

raw_db_url = os.getenv("DATABASE_URL", "").strip()

if not raw_db_url:
    print("ERROR: DATABASE_URL environment variable is not set.")
    print("Please set DATABASE_URL in your environment or server/.env file before running migration.")
    sys.exit(1)

if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "ifhe_kpi.db")

if not os.path.exists(SQLITE_DB_PATH):
    print(f"ERROR: SQLite database file not found at {SQLITE_DB_PATH}")
    sys.exit(1)

import models
import database

def migrate():
    print(f"Connecting to target database...")
    pg_engine = database.engine
    
    # Initialize schema on target PostgreSQL DB
    database.init_db()

    # Open SQLite connection
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    pg_session = database.SessionLocal()

    tables = [
        ("student_uploads", models.StudentUpload),
        ("laboratory_utilization", models.LaboratoryUtilization),
        ("faculty", models.Faculty),
        ("departments", models.Department),
        ("kpis", models.KPI),
        ("student_attendance", models.StudentAttendance),
    ]

    try:
        for table_name, model_cls in tables:
            sqlite_cur.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cur.fetchall()
            print(f"Migrating table '{table_name}': {len(rows)} records found in SQLite.")

            columns = [column[0] for column in sqlite_cur.description]

            for row in rows:
                data = dict(zip(columns, row))

                # Check if record already exists by ID
                existing = None
                if 'id' in data:
                    existing = pg_session.query(model_cls).filter_by(id=data['id']).first()

                if not existing:
                    obj = model_cls(**data)
                    pg_session.add(obj)

            pg_session.commit()
            print(f"Table '{table_name}' migrated successfully.")

        # Reset primary key sequences for PostgreSQL
        if pg_engine.dialect.name == 'postgresql':
            for table_name, _ in tables:
                try:
                    seq_sql = f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), COALESCE(MAX(id), 1)) FROM {table_name};"
                    pg_session.execute(text(seq_sql))
                    pg_session.commit()
                except Exception as seq_err:
                    pg_session.rollback()

        print("\nAll data migrated successfully from SQLite to PostgreSQL!")

    except Exception as e:
        pg_session.rollback()
        print(f"\nMigration failed with error: {e}")
    finally:
        pg_session.close()
        sqlite_conn.close()

if __name__ == "__main__":
    migrate()

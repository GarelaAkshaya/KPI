import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event

# Load environment variables from .env file
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ifhe_kpi.db")

raw_db_url = os.getenv("DATABASE_URL", "").strip()

if raw_db_url:
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif raw_db_url.startswith("postgresql://"):
        raw_db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    SQLALCHEMY_DATABASE_URL = raw_db_url
else:
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine_kwargs = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_kwargs)
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def _migrate_sqlite_feedback_table(conn):
    tables = {
        row[0]
        for row in conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "student_feedback" not in tables:
        return

    columns = {
        row[1]
        for row in conn.exec_driver_sql("PRAGMA table_info(student_feedback)").fetchall()
    }
    table_sql = conn.exec_driver_sql(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='student_feedback'"
    ).scalar_one_or_none() or ""
    foreign_keys = {
        (row[2], row[3], row[4])
        for row in conn.exec_driver_sql("PRAGMA foreign_key_list(student_feedback)").fetchall()
    }
    required_columns = {
        "faculty_id",
        "department_id",
        "academic_year",
        "subject",
        "teaching_quality",
        "subject_knowledge",
        "communication_skills",
        "student_interaction",
        "overall_rating",
        "comments",
        "token_id",
        "created_at",
    }
    required_foreign_keys = {
        ("faculty", "faculty_id", "faculty_id"),
        ("departments", "department_id", "id"),
        ("anonymous_feedback_tokens", "token_id", "id"),
    }
    has_unique_token = any(
        index[2] == 1
        and [
            item[2]
            for item in conn.exec_driver_sql(
                f"PRAGMA index_info('{index[1]}')"
            ).fetchall()
        ] == ["token_id"]
        for index in conn.exec_driver_sql("PRAGMA index_list(student_feedback)").fetchall()
    )
    has_legacy_rating_checks = "between 1 and 5" in table_sql.casefold()
    if (
        required_columns <= columns
        and required_foreign_keys <= foreign_keys
        and has_unique_token
        and not has_legacy_rating_checks
    ):
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_student_feedback_academic_year ON student_feedback (academic_year)"
        )
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_student_feedback_faculty_year ON student_feedback (faculty_id, academic_year)"
        )
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_student_feedback_faculty_id ON student_feedback (faculty_id)"
        )
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_student_feedback_department ON student_feedback (department)"
        )
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_student_feedback_department_year ON student_feedback (department_id, academic_year)"
        )
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_student_feedback_created_at ON student_feedback (created_at)"
        )
        return

    if "student_feedback_new" in tables:
        conn.exec_driver_sql("DROP TABLE student_feedback_new")

    conn.exec_driver_sql(
        """
        CREATE TABLE student_feedback_new (
            id INTEGER PRIMARY KEY,
            faculty_id VARCHAR NULL REFERENCES faculty(faculty_id),
            department_id INTEGER NULL REFERENCES departments(id),
            academic_year VARCHAR NOT NULL,
            subject VARCHAR NULL,
            teaching_quality INTEGER NULL CHECK (teaching_quality IS NULL OR teaching_quality BETWEEN 0 AND 10),
            subject_knowledge INTEGER NULL CHECK (subject_knowledge IS NULL OR subject_knowledge BETWEEN 0 AND 10),
            communication_skills INTEGER NULL CHECK (communication_skills IS NULL OR communication_skills BETWEEN 0 AND 10),
            student_interaction INTEGER NULL CHECK (student_interaction IS NULL OR student_interaction BETWEEN 0 AND 10),
            overall_rating INTEGER NULL CHECK (overall_rating IS NULL OR overall_rating BETWEEN 0 AND 10),
            comments TEXT NULL,
            token_id INTEGER NULL UNIQUE REFERENCES anonymous_feedback_tokens(id),
            created_at DATETIME NOT NULL,
            department VARCHAR NULL,
            faculty_rating INTEGER NULL,
            course_content INTEGER NULL,
            learning_resources INTEGER NULL,
            faculty_support INTEGER NULL,
            overall_satisfaction INTEGER NULL,
            comment TEXT NULL,
            semester VARCHAR NULL,
            course_difficulty VARCHAR NULL,
            google_sheet_response_hash VARCHAR NULL UNIQUE,
            improvement_areas TEXT NULL,
            suggestions TEXT NULL
        )
        """
    )
    existing_columns = columns

    def source(column, fallback="NULL"):
        return f'"{column}"' if column in existing_columns else fallback

    department_source = source("department")
    faculty_source = source("faculty_id")
    department_id_source = source("department_id")
    academic_year_source = (
        f"COALESCE({source('academic_year')}, '')"
        if "academic_year" in existing_columns
        else "''"
    )
    created_source = f"COALESCE({source('created_at')}, CURRENT_TIMESTAMP)"
    faculty_expression = (
        f"CASE WHEN EXISTS (SELECT 1 FROM faculty f WHERE f.faculty_id = {faculty_source}) "
        f"THEN {faculty_source} ELSE NULL END"
    )
    department_value = (
        f"COALESCE(NULLIF(trim({department_source}), ''), "
        f"(SELECT f.department FROM faculty f WHERE f.faculty_id = {faculty_source} LIMIT 1))"
    )
    department_expression = (
        f"CASE WHEN EXISTS (SELECT 1 FROM departments d WHERE d.id = {department_id_source}) "
        f"THEN {department_id_source} "
        f"WHEN EXISTS (SELECT 1 FROM departments d WHERE lower(trim(d.name)) = lower(trim({department_value})) "
        f"OR lower(trim(d.code)) = lower(trim({department_value}))) "
        f"THEN (SELECT d.id FROM departments d WHERE lower(trim(d.name)) = lower(trim({department_value})) "
        f"OR lower(trim(d.code)) = lower(trim({department_value})) LIMIT 1) ELSE NULL END"
    )
    expressions = [
        source("id"),
        faculty_expression,
        department_expression,
        academic_year_source,
        source("subject"),
        source("teaching_quality"),
        source("subject_knowledge"),
        source("communication_skills"),
        source("student_interaction"),
        source("overall_rating"),
        source("comments", source("comment")),
        source("token_id"),
        created_source,
        department_source,
        source("faculty_rating"),
        source("course_content"),
        source("learning_resources"),
        source("faculty_support"),
        source("overall_satisfaction"),
        source("comment"),
        source("semester"),
        source("course_difficulty"),
        source("google_sheet_response_hash"),
        source("improvement_areas"),
        source("suggestions"),
    ]
    target_columns = (
        "id, faculty_id, department_id, academic_year, subject, teaching_quality, "
        "subject_knowledge, communication_skills, student_interaction, overall_rating, "
        "comments, token_id, created_at, department, faculty_rating, course_content, "
        "learning_resources, faculty_support, overall_satisfaction, comment, "
        "semester, course_difficulty, google_sheet_response_hash, improvement_areas, suggestions"
    )
    conn.exec_driver_sql(
        f"INSERT INTO student_feedback_new ({target_columns}) "
        f"SELECT {', '.join(expressions)} FROM student_feedback"
    )
    conn.exec_driver_sql("DROP TABLE student_feedback")
    conn.exec_driver_sql("ALTER TABLE student_feedback_new RENAME TO student_feedback")
    conn.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_student_feedback_academic_year ON student_feedback (academic_year)"
    )
    conn.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_student_feedback_faculty_year ON student_feedback (faculty_id, academic_year)"
    )
    conn.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_student_feedback_faculty_id ON student_feedback (faculty_id)"
    )
    conn.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_student_feedback_department ON student_feedback (department)"
    )
    conn.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_student_feedback_department_year ON student_feedback (department_id, academic_year)"
    )
    conn.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_student_feedback_created_at ON student_feedback (created_at)"
    )
    violations = conn.exec_driver_sql("PRAGMA foreign_key_check(student_feedback)").fetchall()
    if violations:
        raise RuntimeError(f"Student feedback migration created foreign-key violations: {violations[:5]}")


def _migrate_feedback_code_issuances(conn):
    tables = {
        row[0]
        for row in conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "feedback_code_issuances" not in tables:
        return

    columns = {
        row[1]
        for row in conn.exec_driver_sql("PRAGMA table_info(feedback_code_issuances)").fetchall()
    }
    required = {"id", "faculty_id", "academic_year", "code_hash", "is_redeemed", "created_at"}
    if not required <= columns:
        raise RuntimeError(
            "Cannot migrate feedback_code_issuances: required legacy columns are missing."
        )
    conn.exec_driver_sql(
        """
        INSERT OR IGNORE INTO anonymous_feedback_tokens
            (id, token_hash, faculty_id, academic_year, used, used_at, created_at)
        SELECT issuance.id, issuance.code_hash, issuance.faculty_id, issuance.academic_year,
               CASE WHEN issuance.is_redeemed != 0 THEN 1 ELSE 0 END,
               NULL, issuance.created_at
        FROM feedback_code_issuances AS issuance
        JOIN faculty ON faculty.faculty_id = issuance.faculty_id
        """
    )
    unmigrated = conn.exec_driver_sql(
        """
        SELECT COUNT(*)
        FROM feedback_code_issuances AS issuance
        WHERE NOT EXISTS (
            SELECT 1 FROM anonymous_feedback_tokens AS token
            WHERE token.token_hash = issuance.code_hash
              AND token.faculty_id = issuance.faculty_id
              AND token.academic_year = issuance.academic_year
              AND token.used = CASE WHEN issuance.is_redeemed != 0 THEN 1 ELSE 0 END
        )
        """
    ).scalar_one()
    if unmigrated:
        raise RuntimeError(
            f"Cannot migrate feedback_code_issuances: {unmigrated} token records could not be preserved."
        )
    conn.exec_driver_sql("DROP TABLE feedback_code_issuances")


def init_db():
    import models
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        if engine.dialect.name == "sqlite":
            _migrate_feedback_code_issuances(conn)
            _migrate_sqlite_feedback_table(conn)
            for table_name, table in Base.metadata.tables.items():
                result = conn.exec_driver_sql(f"PRAGMA table_info({table_name})")
                existing_cols = {row[1] for row in result.fetchall()}
                for col in table.columns:
                    if col.name not in existing_cols:
                        col_type = col.type.compile(engine.dialect)
                        conn.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}")
        elif engine.dialect.name == "postgresql":
            for table_name, table in Base.metadata.tables.items():
                result = conn.exec_driver_sql(
                    f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'"
                )
                existing_cols = {row[0].lower() for row in result.fetchall()}
                for col in table.columns:
                    if col.name.lower() not in existing_cols:
                        col_type = col.type.compile(engine.dialect)
                        conn.exec_driver_sql(f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS "{col.name}" {col_type}')
            for col_name in ["course_content", "learning_resources", "faculty_support", "teaching_quality", "overall_satisfaction"]:
                try:
                    conn.exec_driver_sql(f'ALTER TABLE "student_feedback" ALTER COLUMN "{col_name}" DROP NOT NULL')
                except Exception:
                    pass

        if engine.dialect.name == "sqlite":
            conn.exec_driver_sql(
                "UPDATE student_uploads SET academic_year = '2024-2025' WHERE academic_year IS NULL OR academic_year = ''"
            )
            conn.exec_driver_sql(
                "UPDATE student_attendance SET academic_year = '2024-2025' WHERE academic_year = '2024-25' OR academic_year IS NULL OR academic_year = ''"
            )
            conn.exec_driver_sql(
                "UPDATE laboratory_utilization SET academic_year = '2024-2025' WHERE academic_year = '2024-25' OR academic_year IS NULL OR academic_year = ''"
            )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    import models
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        try:
            if engine.dialect.name == "sqlite":
                for table_name, table in Base.metadata.tables.items():
                    result = conn.exec_driver_sql(f"PRAGMA table_info({table_name})")
                    existing_cols = {row[1] for row in result.fetchall()}
                    for col in table.columns:
                        if col.name not in existing_cols:
                            col_type = col.type.compile(engine.dialect)
                            conn.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}")
                            conn.commit()
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
                            conn.commit()
            
            # Ensure existing student and attendance records have academic_year set to 2024-2025
            conn.exec_driver_sql(
                "UPDATE student_uploads SET academic_year = '2024-2025' WHERE academic_year IS NULL OR academic_year = ''"
            )
            conn.exec_driver_sql(
                "UPDATE student_attendance SET academic_year = '2024-2025' WHERE academic_year = '2024-25' OR academic_year IS NULL OR academic_year = ''"
            )
            conn.exec_driver_sql(
                "UPDATE laboratory_utilization SET academic_year = '2024-2025' WHERE academic_year = '2024-25' OR academic_year IS NULL OR academic_year = ''"
            )
            conn.commit()
        except Exception as e:
            print("init_db migration note:", e)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

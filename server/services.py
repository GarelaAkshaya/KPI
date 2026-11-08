import hashlib
import hmac
import io
import json
import math
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional

from dotenv import load_dotenv
import pandas as pd
import jwt
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
import models

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin1234"
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY", "").strip()
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY is not configured. Add it to server/.env before starting the API.")
    return secret


def hash_feedback_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000)
    return f"pbkdf2_sha256$200000${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, digest_hex = password_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        )
        return hmac.compare_digest(derived.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def verify_access_token(token: str) -> str:
    payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
    username = payload.get("sub")
    if not username:
        raise ValueError("Token payload missing subject")
    return username


def initialize_admin_account(db: Session) -> models.AdminUser:
    username = os.getenv("ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME).strip() or DEFAULT_ADMIN_USERNAME
    password = os.getenv("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD).strip() or DEFAULT_ADMIN_PASSWORD

    admin = db.query(models.AdminUser).filter(models.AdminUser.username == username).first()
    if admin is not None:
        if not admin.password_hash:
            admin.password_hash = hash_password(password)
            db.commit()
        return admin

    user = models.AdminUser(username=username, password_hash=hash_password(password), is_active=1)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_admin(db: Session, username: str, password: str) -> Optional[models.AdminUser]:
    stored_user = db.query(models.AdminUser).filter(
        models.AdminUser.username == username,
        models.AdminUser.is_active == 1,
    ).first()
    if stored_user is None:
        return None
    if not verify_password(password, stored_user.password_hash):
        return None
    return stored_user


def parse_percentage_value(value: Any) -> Optional[float]:
    if value is None or pd.isna(value):
        return None

    text = str(value).strip()
    if text == '':
        return None

    has_percent = '%' in text
    numeric_text = text.replace('%', '').strip()
    try:
        parsed = float(numeric_text)
    except ValueError:
        return None

    if math.isnan(parsed) or math.isinf(parsed):
        return None

    if has_percent:
        return parsed

    if parsed <= 1.0:
        return parsed * 100.0

    return parsed


def normalize_academic_year(year: Optional[str]) -> Optional[str]:
    if not year:
        return None
    val = re.sub(r"\s+", "", str(year).strip().replace("–", "-").replace("—", "-").replace("/", "-"))
    if val.lower() in {"all", "allyears", "all_years"}:
        return None
    if val in {"2024-2025", "2024-25", "2024–2025", "2024/2025"}:
        return "2024-2025"
    if val in {"2025-2026", "2025-26", "2025–2026", "2025/2026"}:
        return "2025-2026"
    raise ValueError(f"Invalid Academic Year '{year}'. Allowed years are '2024-2025' and '2025-2026'.")


def normalize_semester(sem: Optional[str]) -> Optional[str]:
    if not sem or not str(sem).strip():
        return None
    val = str(sem).strip()
    if val.lower() in {"all", "all semesters", "all_semesters"}:
        return "All"
    m = re.match(r'^(?:semester\s*)?([1-8])$', val, re.IGNORECASE)
    if m:
        return f"Semester {m.group(1)}"
    return val


def normalize_student_rows(
    raw_rows: Any,
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    semester: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], bool]:
    if isinstance(raw_rows, pd.DataFrame):
        raw_rows = raw_rows.to_dict(orient="records")
    if not raw_rows:
        return [], False

    form_department = (department or "").strip()
    form_section = (section or "").strip()

    norm_year = normalize_academic_year(academic_year) or "2024-2025"
    if norm_year not in {"2024-2025", "2025-2026"}:
        raise ValueError(f"Invalid Academic Year '{academic_year}'. Only '2024-2025' and '2025-2026' are accepted.")

    norm_sem = normalize_semester(semester)

    # Check if this sheet is a subject-marks sheet with DM, DSC, COA, Python, ML
    sample_keys = {str(k).strip().lower(): k for k in raw_rows[0].keys()}
    
    subject_aliases = {
        "DM": ["dm", "discrete mathematics"],
        "DSC": ["dsc", "dynamics of social change"],
        "COA": ["coa", "computer organization and architecture", "computer organization & architecture"],
        "Python": ["python", "industry coding practice", "python programming"],
        "ML": ["ml", "machine learning"],
    }

    has_subject_columns = any(
        any(alias in sample_keys for alias in aliases)
        for aliases in subject_aliases.values()
    )

    if has_subject_columns:
        # Validate that all 5 required subjects exist
        missing_subjects = []
        resolved_subject_keys = {}
        for subj_code, aliases in subject_aliases.items():
            matched_key = next((sample_keys[alias] for alias in aliases if alias in sample_keys), None)
            if matched_key:
                resolved_subject_keys[subj_code] = matched_key
            else:
                missing_subjects.append(subj_code)

        if missing_subjects:
            raise ValueError(
                f"Missing required subject column(s): {', '.join(missing_subjects)}. "
                "The student marks file must contain columns for DM, DSC, COA, Python, and ML."
            )

        # Detect Enrollment Number, Student Name, Department, Academic Year columns
        enrollment_keys = ["enrollment number", "enrollment no", "enrollment", "student id", "studentid", "roll no", "roll number", "rollno", "id"]
        name_keys = ["student name", "studentname", "name of student", "name", "student"]
        dept_keys = ["department", "dept", "branch", "stream"]
        section_keys = ["section", "batch section", "sec", "section name"]
        year_keys = ["academic year", "academicyear", "academic_year", "year", "session"]

        normalized_records = []
        for index, row in enumerate(raw_rows):
            row_idx = index + 2  # Excel row number (1-based, header is row 1)
            row_map = {str(k).strip().lower(): (k, v) for k, v in row.items()}

            # 1. Enrollment Number
            enrollment_val = None
            for ek in enrollment_keys:
                if ek in row_map and not _is_missing(row_map[ek][1]):
                    enrollment_val = str(row_map[ek][1]).strip()
                    break

            if not enrollment_val:
                raise ValueError(f"Row {row_idx}: Enrollment Number is missing.")

            # Validate enrollment format: alphanumeric institutional format (e.g. 23STUCHH001, 24STUCHH010001)
            if not re.match(r"^[0-9A-Za-z_-]{5,20}$", enrollment_val):
                raise ValueError(
                    f"Row {row_idx}: Invalid Enrollment Number '{enrollment_val}'. "
                    "Expected valid enrollment number format (e.g. 23STUCHH001 or 24STUCHH010001)."
                )
            enrollment_number = enrollment_val.upper()

            # 2. Student Name
            name_val = None
            for nk in name_keys:
                if nk in row_map and not _is_missing(row_map[nk][1]):
                    name_val = str(row_map[nk][1]).strip()
                    break

            if not name_val:
                raise ValueError(f"Row {row_idx}: Student Name is missing.")
            student_name = name_val

            # 3. Department
            dept_val = None
            for dk in dept_keys:
                if dk in row_map and not _is_missing(row_map[dk][1]):
                    dept_val = str(row_map[dk][1]).strip()
                    break
            department_name = dept_val or form_department or "Artificial Intelligence and Data Science (AIDS)"

            # 4. Section
            section_val = None
            for sk in section_keys:
                if sk in row_map and not _is_missing(row_map[sk][1]):
                    section_val = str(row_map[sk][1]).strip()
                    break
            section_name = section_val or form_section
            if not section_name:
                raise ValueError(f"Row {row_idx}: Section is missing. Please provide a section value or enter the section in the upload form.")

            # 5. Academic Year
            file_year_val = None
            for yk in year_keys:
                if yk in row_map and not _is_missing(row_map[yk][1]):
                    file_year_val = str(row_map[yk][1]).strip()
                    break

            if file_year_val:
                norm_file_year = normalize_academic_year(file_year_val)
                if norm_file_year != norm_year:
                    raise ValueError(
                        f"Row {row_idx}: Academic Year in Excel file ('{file_year_val}') "
                        f"does not match the selected Academic Year ('{norm_year}')."
                    )

            # 5. Subject Marks: DM, DSC, COA, Python, ML
            # Subject marks must be integers from 0 to 100.
            subject_marks = {}
            for subj_code in ("DM", "DSC", "COA", "Python", "ML"):
                col_name = resolved_subject_keys[subj_code]
                raw_mark = row.get(col_name)

                if _is_missing(raw_mark) or str(raw_mark).strip() == "":
                    subject_marks[subj_code] = 0
                    continue

                try:
                    mark_float = float(str(raw_mark).strip())
                except (ValueError, TypeError):
                    raise ValueError(
                        f"Row {row_idx}: Invalid mark '{raw_mark}' for subject '{subj_code}'. "
                        "Subject marks must be integers from 0 to 100."
                    )

                if mark_float < 0 or mark_float > 100 or not mark_float.is_integer():
                    raise ValueError(
                        f"Row {row_idx}: Invalid mark '{raw_mark}' for subject '{subj_code}'. "
                        "Subject marks must be integers from 0 to 100."
                    )

                subject_marks[subj_code] = int(mark_float)

            dm = subject_marks["DM"]
            dsc = subject_marks["DSC"]
            coa = subject_marks["COA"]
            python_val = subject_marks["Python"]
            ml = subject_marks["ML"]

            # Calculate total marks out of 500 and percentage in backend
            total_marks = dm + dsc + coa + python_val + ml
            percentage = round((total_marks / 500.0) * 100.0, 2)

            normalized_records.append({
                "studentId": enrollment_number,
                "enrollment_number": enrollment_number,
                "studentName": student_name,
                "department": department_name,
                "section": section_name.upper() if section_name else None,
                "totalMarks": total_marks,
                "percentage": percentage,
                "academic_year": norm_year,
                "semester": norm_sem,
                "dm": dm,
                "dsc": dsc,
                "coa": coa,
                "python_marks": python_val,
                "ml": ml,
                "subject_marks_json": json.dumps(subject_marks),
            })

        return normalized_records, False

    # Fallback for generic / legacy marks sheets
    normalized_records = []
    has_invalid_row = False

    for row in raw_rows:
        keys_map = {str(k).strip().lower(): v for k, v in row.items()}

        student_id_val = (
            keys_map.get('enrollment number') or
            keys_map.get('enrollment no') or
            keys_map.get('student id') or 
            keys_map.get('studentid') or 
            keys_map.get('id') or 
            ''
        )
        student_name_val = (
            keys_map.get('student name') or 
            keys_map.get('studentname') or 
            keys_map.get('name') or 
            ''
        )

        student_id = str(student_id_val).strip() if not pd.isna(student_id_val) else ''
        student_name = str(student_name_val).strip() if not pd.isna(student_name_val) else ''

        if not student_id or not student_name:
            has_invalid_row = True

        total_marks_val = (
            keys_map.get('total marks (out of 600)') or 
            keys_map.get('total marks') or 
            keys_map.get('marks') or 
            0
        )
        try:
            total_marks = int(round(float(total_marks_val))) if not pd.isna(total_marks_val) else 0
        except (ValueError, TypeError):
            total_marks = 0

        pct_val = (
            keys_map.get('percentage') or 
            keys_map.get('percentage (%)') or 
            keys_map.get('percentage %') or 
            keys_map.get('pct')
        )
        percentage = parse_percentage_value(pct_val)
        if percentage is None:
            percentage = (total_marks / 600.0) * 100.0 if total_marks > 0 else 0.0

        if math.isnan(percentage) or math.isinf(percentage):
            percentage = 0.0

        percentage = round(percentage, 2)

        raw_file_year = keys_map.get('academic year') or keys_map.get('academicyear') or keys_map.get('academic_year')
        if raw_file_year and not pd.isna(raw_file_year):
            norm_file_year = normalize_academic_year(raw_file_year)
            if norm_file_year != norm_year:
                raise ValueError(
                    f"Academic Year in Excel file ('{raw_file_year}') does not match the selected Academic Year ('{norm_year}')."
                )

        normalized_records.append({
            "studentId": student_id,
            "enrollment_number": student_id,
            "studentName": student_name,
            "department": form_department or "Artificial Intelligence and Data Science (AIDS)",
            "section": (form_section or "").upper() if form_section else None,
            "totalMarks": total_marks,
            "percentage": percentage,
            "academic_year": norm_year,
            "dm": None,
            "dsc": None,
            "coa": None,
            "python_marks": None,
            "ml": None,
            "subject_marks_json": "{}",
        })

    return normalized_records, has_invalid_row


def _clean_header(value: Any) -> str:
    return str(value).strip()


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or pd.isna(value)


def _attendance_subject_value(value: Any) -> Optional[float]:
    if _is_missing(value) or str(value).strip() == '':
        return None
    parsed = parse_percentage_value(value)
    if parsed is None or parsed < 0 or parsed > 100:
        return None
    return round(parsed, 2)

def normalize_attendance_rows(
    raw_rows: Any,
    headers: Optional[List[str]] = None,
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    semester: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], bool, List[str]]:
    if isinstance(raw_rows, pd.DataFrame):
        if headers is None:
            headers = [str(c) for c in raw_rows.columns]
        raw_rows = raw_rows.to_dict(orient="records")
    elif headers is None and isinstance(raw_rows, list) and len(raw_rows) > 0:
        headers = [str(k) for k in raw_rows[0].keys()]
    elif headers is None:
        headers = []

    if not raw_rows:
        return [], False, []

    norm_year = normalize_academic_year(academic_year) or "2024-2025"
    if norm_year not in {"2024-2025", "2025-2026"}:
        raise ValueError(f"Invalid Academic Year '{academic_year}'. Only '2024-2025' and '2025-2026' are accepted.")

    norm_sem = normalize_semester(semester)

    # Subject aliases for the 5 attendance subjects
    attendance_subject_aliases = {
        "DS": ["ds", "data structures", "data structure"],
        "EG": ["eg", "engineering graphics", "engineering graphic"],
        "EVS": ["evs", "environmental science", "environmental sciences", "environmental studies"],
        "HC": ["hc", "higher calculus"],
        "PHYSICS": ["physics", "phy"],
    }

    form_department = (department or "").strip() if department is not None else ""
    form_section = (section or "").strip() if section is not None else ""

    sample_keys = {str(k).strip().lower(): k for k in headers}
    has_all_five_attendance_subjects = all(
        any(alias in sample_keys for alias in aliases)
        for aliases in attendance_subject_aliases.values()
    )

    if has_all_five_attendance_subjects:
        resolved_subject_keys = {}
        for subj_code, aliases in attendance_subject_aliases.items():
            matched_key = next((sample_keys[alias] for alias in aliases if alias in sample_keys), None)
            resolved_subject_keys[subj_code] = matched_key

        enrollment_keys = ["enrollment number", "enrollment no", "enrollment", "student id", "studentid", "roll no", "roll number", "rollno", "id"]
        name_keys = ["student name", "studentname", "name of student", "name", "student"]
        dept_keys = ["department", "dept", "branch", "stream"]
        section_keys = ["section", "batch section", "sec", "section name"]
        year_keys = ["academic year", "academicyear", "academic_year", "year", "session"]
        subject_headers = ["DS", "EG", "EVS", "HC", "PHYSICS"]

        normalized_records = []
        for index, row in enumerate(raw_rows):
            row_idx = index + 2
            row_map = {str(k).strip().lower(): (k, v) for k, v in row.items()}

            # 1. Enrollment Number
            enrollment_val = None
            for ek in enrollment_keys:
                if ek in row_map and not _is_missing(row_map[ek][1]):
                    enrollment_val = str(row_map[ek][1]).strip()
                    break

            if not enrollment_val:
                raise ValueError(f"Row {row_idx}: Enrollment Number is missing.")

            # Validate enrollment format: alphanumeric institutional format (e.g. 23STUCHH001, 24STUCHH010001)
            if not re.match(r"^[0-9A-Za-z_-]{5,20}$", enrollment_val):
                raise ValueError(
                    f"Row {row_idx}: Invalid Enrollment Number '{enrollment_val}'. "
                    "Expected valid enrollment number format (e.g. 23STUCHH001 or 24STUCHH010001)."
                )
            enrollment_number = enrollment_val.upper()

            # 2. Student Name
            name_val = None
            for nk in name_keys:
                if nk in row_map and not _is_missing(row_map[nk][1]):
                    name_val = str(row_map[nk][1]).strip()
                    break

            if not name_val:
                raise ValueError(f"Row {row_idx}: Student Name is missing.")
            student_name = name_val

            # 3. Department
            dept_val = None
            for dk in dept_keys:
                if dk in row_map and not _is_missing(row_map[dk][1]):
                    dept_val = str(row_map[dk][1]).strip()
                    break
            department_name = dept_val or form_department or "Artificial Intelligence and Data Science (AIDS)"

            # 4. Section
            section_val = None
            for sk in section_keys:
                if sk in row_map and not _is_missing(row_map[sk][1]):
                    section_val = str(row_map[sk][1]).strip()
                    break
            section_name = section_val or form_section
            if not section_name:
                raise ValueError(f"Row {row_idx}: Section is missing. Please provide a section value or enter it in the upload form.")

            # 5. Academic Year
            file_year_val = None
            for yk in year_keys:
                if yk in row_map and not _is_missing(row_map[yk][1]):
                    file_year_val = str(row_map[yk][1]).strip()
                    break

            if file_year_val:
                norm_file_year = normalize_academic_year(file_year_val)
                if norm_file_year != norm_year:
                    raise ValueError(
                        f"Row {row_idx}: Academic Year in Excel file ('{file_year_val}') "
                        f"does not match the selected Academic Year ('{norm_year}')."
                    )

            # 4. Subject Attendance Values: DS, EG, EVS, HC, PHYSICS
            # Attendance percentages must be numeric values between 0 and 100.
            subject_values = {}
            for subj_code in subject_headers:
                col_name = resolved_subject_keys[subj_code]
                raw_val = row.get(col_name)

                if _is_missing(raw_val) or str(raw_val).strip() == "":
                    raise ValueError(f"Row {row_idx}: Missing attendance value for subject '{subj_code}'.")

                val_parsed = parse_percentage_value(raw_val)
                if val_parsed is None or val_parsed < 0 or val_parsed > 100:
                    raise ValueError(
                        f"Row {row_idx}: Invalid attendance value '{raw_val}' for subject '{subj_code}'. "
                        "Attendance percentages must be numeric values between 0 and 100."
                    )

                subject_values[subj_code] = round(val_parsed, 2)

            # Calculate Average Attendance as the arithmetic mean of DS, EG, EVS, HC, and PHYSICS, rounded to two decimal places.
            calculated_avg = round(
                (
                    subject_values["DS"]
                    + subject_values["EG"]
                    + subject_values["EVS"]
                    + subject_values["HC"]
                    + subject_values["PHYSICS"]
                ) / 5.0,
                2
            )

            total_classes = 500
            attended_classes = int(round(sum(subject_values.values())))

            normalized_records.append({
                "student_id": enrollment_number,
                "enrollment_number": enrollment_number,
                "student_name": student_name,
                "department": department_name,
                "section": section_name.upper() if section_name else None,
                "academic_year": norm_year,
                "semester": norm_sem,
                "total_classes": total_classes,
                "attended_classes": attended_classes,
                "attendance_percentage": calculated_avg,
                "average_attendance": calculated_avg,
                "subjects": subject_headers,
                "subject_values": subject_values,
            })

        return normalized_records, False, subject_headers

    # Fallback parser for generic dynamic matrix sheets
    normalized_records = []
    has_invalid_row = False
    known_metadata = {
        's.no', 's.no.', 's no', 'serial no', 'serial number',
        'student id', 'studentid', 'roll no', 'roll no.', 'roll number', 'rollno',
        'enrollment number', 'enrollment no', 'enrollment', 'reg no', 'reg_no', 'registration no', 'id', 'student name',
        'studentname', 'name of student', 'name', 'student', 'department', 'dept',
        'branch', 'stream', 'academic year', 'academicyear', 'academic_year', 'year',
        'session', 'total classes', 'totalclasses', 'classes held', 'total held',
        'total sessions', 'total days', 'total conducted', 'total', 'attended classes',
        'attendedclasses', 'classes attended', 'total attended', 'attended', 'present',
        'present days', 'present classes', 'attendance percentage', 'attendance %',
        'attendance(%)', 'attendance', 'percentage', 'percentage (%)', 'percentage %',
        'att %', 'pct'
    }
    explicit_name = next((header for header in headers if header.lower() in {'student name', 'studentname', 'name of student', 'name', 'student'}), None)
    explicit_id = next((header for header in headers if header.lower() in {'enrollment number', 'enrollment no', 'enrollment', 'student id', 'studentid', 'roll no', 'roll no.', 'roll number', 'rollno', 'reg no', 'reg_no', 'registration no', 'id'}), None)
    is_subject_matrix = len([header for header in headers if header.lower() not in known_metadata]) > 0
    subject_headers = [header for header in headers if header.lower() not in known_metadata]
    if not explicit_name and not explicit_id and headers:
        explicit_name = headers[0]
        subject_headers = headers[1:]
        is_subject_matrix = True
    subject_headers = list(dict.fromkeys(subject_headers))

    for row in raw_rows:
        keys_map = {str(k).strip().lower(): v for k, v in row.items()}

        student_id_val = (
            keys_map.get('enrollment number') or 
            keys_map.get('enrollment no') or 
            keys_map.get('enrollment') or 
            keys_map.get('student id') or 
            keys_map.get('studentid') or 
            keys_map.get('roll no') or
            keys_map.get('roll no.') or
            keys_map.get('roll number') or
            keys_map.get('rollno') or
            keys_map.get('id') or 
            ''
        )
        student_name_val = (
            keys_map.get('student name') or 
            keys_map.get('studentname') or 
            keys_map.get('name of student') or 
            keys_map.get('name') or 
            keys_map.get('student') or 
            ''
        )

        student_id = str(student_id_val).strip() if not pd.isna(student_id_val) else ''
        student_name = str(student_name_val).strip() if not pd.isna(student_name_val) else ''

        if explicit_name:
            student_name = str(row.get(explicit_name, '')).strip() if not _is_missing(row.get(explicit_name)) else ''
        elif explicit_id:
            student_name = student_id
        if not student_id and student_name:
            student_id = student_name

        if not student_id:
            has_invalid_row = True
            continue

        if is_subject_matrix:
            subject_values = {}
            for subject in subject_headers:
                value = _attendance_subject_value(row.get(subject))
                if value is not None:
                    subject_values[subject] = value
            if not subject_values:
                has_invalid_row = True
                continue
            average = round(sum(subject_values.values()) / len(subject_values), 2)
            normalized_records.append({
                'student_id': student_id,
                'enrollment_number': student_id,
                'student_name': student_name,
                'department': form_department or 'Artificial Intelligence and Data Science (AIDS)',
                'section': (form_section or '').upper() if form_section else None,
                'academic_year': norm_year,
                'semester': norm_sem,
                'total_classes': len(subject_values) * 100,
                'attended_classes': int(round(sum(subject_values.values()))),
                'attendance_percentage': average,
                'average_attendance': average,
                'subjects': subject_headers,
                'subject_values': subject_values,
            })
            continue

        raw_file_year = keys_map.get('academic year') or keys_map.get('academicyear') or keys_map.get('academic_year')
        if raw_file_year and not pd.isna(raw_file_year):
            norm_file_year = normalize_academic_year(raw_file_year)
            if norm_file_year != norm_year:
                raise ValueError(
                    f"Academic Year in Excel file ('{raw_file_year}') does not match the selected Academic Year ('{norm_year}')."
                )

        pct_val = (
            keys_map.get('attendance percentage') or 
            keys_map.get('attendance %') or 
            keys_map.get('attendance(%)') or 
            keys_map.get('attendance') or 
            keys_map.get('percentage') or 
            keys_map.get('percentage (%)') or 
            keys_map.get('percentage %') or 
            keys_map.get('att %') or 
            keys_map.get('pct')
        )
        percentage = parse_percentage_value(pct_val)
        if percentage is None:
            percentage = 0.0

        percentage = round(min(max(percentage, 0.0), 100.0), 2)

        normalized_records.append({
            "student_id": student_id,
            "enrollment_number": student_id,
            "student_name": student_name,
            "department": form_department or "Artificial Intelligence and Data Science (AIDS)",
            "section": (form_section or '').upper() if form_section else None,
            "academic_year": norm_year,
            "semester": norm_sem,
            "total_classes": 100,
            "attended_classes": int(round(percentage)),
            "attendance_percentage": percentage,
            "average_attendance": percentage,
            "subjects": [],
            "subject_values": {},
        })

    return normalized_records, has_invalid_row, subject_headers


def parse_attendance_excel_file(
    file_contents: bytes,
    filename: str = '',
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    semester: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], bool, List[str]]:
    if filename.lower().endswith('.csv'):
        df = pd.read_csv(io.BytesIO(file_contents))
    else:
        df = pd.read_excel(io.BytesIO(file_contents))
    df = df.where(pd.notnull(df), None)
    if df.empty or len(df.columns) == 0:
        return [], False, []
    headers = [_clean_header(header) for header in df.columns]
    df.columns = headers
    rows = df.to_dict(orient='records')
    return normalize_attendance_rows(rows, headers, academic_year=academic_year, department=department, section=section, semester=semester)


def save_attendance_records(db: Session, records: List[Dict[str, Any]], academic_year: Optional[str] = None, semester: Optional[str] = None) -> int:
    norm_year = normalize_academic_year(academic_year) or (records[0].get('academic_year') if records else "2024-2025")
    norm_sem = normalize_semester(semester) or (records[0].get('semester') if records else None)

    existing_query = db.query(models.StudentAttendance).filter(models.StudentAttendance.academic_year == norm_year)
    if norm_sem and norm_sem != "All":
        existing_query = existing_query.filter(func.lower(func.trim(models.StudentAttendance.semester)) == norm_sem.lower())
    else:
        existing_query = existing_query.filter(models.StudentAttendance.semester.is_(None))

    existing_attendance = {
        str(a.enrollment_number or a.student_id).strip().casefold(): a
        for a in existing_query.all()
    }
    for r in records:
        enrollment = str(r.get('enrollment_number') or r['student_id']).strip().casefold()
        subjs_json = json.dumps(r.get('subjects', []))
        subj_vals_json = json.dumps(r.get('subject_values', {}))
        year = norm_year or r.get('academic_year', '2024-2025')
        sem_val = norm_sem or r.get('semester')
        section_value = r.get('section')
        if section_value is not None:
            section_value = str(section_value).strip().upper() or None
        if enrollment in existing_attendance:
            att = existing_attendance[enrollment]
            att.student_name = r['student_name']
            att.department = r.get('department', att.department)
            att.section = section_value or att.section
            att.academic_year = year
            att.semester = sem_val or att.semester
            att.total_classes = r['total_classes']
            att.attended_classes = r['attended_classes']
            att.attendance_percentage = r['attendance_percentage']
            att.average_attendance = r.get('average_attendance', r['attendance_percentage'])
            att.subjects_json = subjs_json
            att.subject_values_json = subj_vals_json
        else:
            new_att = models.StudentAttendance(
                student_id=r['student_id'],
                enrollment_number=r.get('enrollment_number', r['student_id']),
                student_name=r['student_name'],
                department=r.get('department', 'Artificial Intelligence and Data Science (AIDS)'),
                section=section_value,
                academic_year=year,
                semester=sem_val,
                total_classes=r['total_classes'],
                attended_classes=r['attended_classes'],
                attendance_percentage=r['attendance_percentage'],
                average_attendance=r.get('average_attendance', r['attendance_percentage']),
                subjects_json=subjs_json,
                subject_values_json=subj_vals_json
            )
            db.add(new_att)
            existing_attendance[enrollment] = new_att
    db.commit()
    return len(records)


def match_attendance_students(db: Session, records: List[Dict[str, Any]], academic_year: Optional[str] = None, semester: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[str]]:
    norm_year = normalize_academic_year(academic_year) or "2024-2025"
    norm_sem = normalize_semester(semester)
    query = db.query(models.StudentUpload).filter(models.StudentUpload.academic_year == norm_year)
    students = query.all()

    student_by_enrollment = {}
    student_by_name = {}
    for student in students:
        sid = str(student.studentId).strip().casefold()
        if sid:
            student_by_enrollment[sid] = student
        enum = str(getattr(student, 'enrollment_number', None) or '').strip().casefold()
        if enum:
            student_by_enrollment[enum] = student
        sname = str(student.studentName).strip().casefold()
        if sname:
            student_by_name[sname] = student

    all_students = db.query(models.StudentUpload).all()
    for student in all_students:
        sid = str(student.studentId).strip().casefold()
        if sid and sid not in student_by_enrollment:
            student_by_enrollment[sid] = student
        enum = str(getattr(student, 'enrollment_number', None) or '').strip().casefold()
        if enum and enum not in student_by_enrollment:
            student_by_enrollment[enum] = student
        sname = str(student.studentName).strip().casefold()
        if sname and sname not in student_by_name:
            student_by_name[sname] = student

    unmatched = []
    matched_records = []

    for record in records:
        enrollment_number = str(record.get('enrollment_number') or record.get('student_id') or '').strip()
        student = student_by_enrollment.get(enrollment_number.casefold())
        if not student:
            student_name = str(record.get('student_name') or '').strip()
            student = student_by_name.get(student_name.casefold())
        if not student:
            unmatched.append(enrollment_number)
            continue

        canonical_id = str(getattr(student, 'enrollment_number', None) or student.studentId).strip()
        record['student_id'] = canonical_id
        record['enrollment_number'] = canonical_id
        record['student_name'] = student.studentName
        record['department'] = record.get('department') or getattr(student, 'department', '') or 'Artificial Intelligence and Data Science (AIDS)'
        record['section'] = record.get('section') or getattr(student, 'section', '') or None
        record['academic_year'] = norm_year
        if norm_sem:
            record['semester'] = norm_sem
        matched_records.append(record)

    return matched_records, unmatched


# ============================================================================
# SEMESTER WORKBOOK SUBJECT CONFIGURATIONS & HELPERS
# ============================================================================

SEMESTER_CONFIGS = {
    "AIDS": {
        "A": {
            "2024-2025": {
                "Semester 1": [
                    "Computer Programming",
                    "Basic Electronics",
                    "English",
                    "Digital Fabrication",
                    "Chemistry",
                ],
                "Semester 2": [
                    "Data Structures",
                    "Engineering Graphics",
                    "EVS",
                    "Physics",
                    "Higher Calculus",
                ],
                "Semester 3": [
                    "AI",
                    "IoT",
                    "OOPs",
                    "DBMS",
                    "EEM",
                ],
                "Semester 4": [],  # Configurable: will accept any subjects dynamically
            }
        }
    }
}

SUBJECT_ALIASES = {
    "computer programming": ["computer programming", "cp", "programming in c", "computer programming using c", "c programming"],
    "basic electronics": ["basic electronics", "be", "electronics", "bee"],
    "english": ["english", "technical english", "communication skills", "eng"],
    "digital fabrication": ["digital fabrication", "df", "fab lab", "fabrication"],
    "chemistry": ["chemistry", "chem", "engineering chemistry"],
    "data structures": ["data structures", "ds", "dsa", "data structures & algorithms"],
    "engineering graphics": ["engineering graphics", "eg", "graphics", "cad"],
    "evs": ["evs", "environmental science", "environmental studies", "environment"],
    "physics": ["physics", "phy", "engineering physics"],
    "higher calculus": ["higher calculus", "hc", "calculus", "advanced calculus", "mathematics", "maths"],
    "ai": ["ai", "artificial intelligence", "intro to ai"],
    "iot": ["iot", "internet of things"],
    "oops": ["oops", "oop", "object oriented programming", "object oriented programming with java", "object oriented programming with c++"],
    "dbms": ["dbms", "database management systems", "database management system", "database"],
    "eem": ["eem", "engineering economics and management", "engineering economics & management", "economics"],
}


def get_configured_subjects_for_semester(department: str, section: str, academic_year: str, semester: str) -> List[str]:
    norm_year = normalize_academic_year(academic_year) or "2024-2025"
    norm_dept = canonicalize_department_name(department)
    dept_key = "AIDS" if norm_dept == "AI & Data Science" else norm_dept
    sec_key = (section or "").strip().upper()
    m = re.match(r'^([A-Z0-9]+)\s*[-_]?\s*sem', sec_key, re.IGNORECASE)
    if m:
        sec_key = m.group(1).upper()
    sem_key = (semester or "").strip()

    dept_cfg = SEMESTER_CONFIGS.get(dept_key)
    if not dept_cfg:
        return []
    sec_cfg = dept_cfg.get(sec_key)
    if not sec_cfg:
        return []
    year_cfg = sec_cfg.get(norm_year)
    if not year_cfg:
        return []
    return year_cfg.get(sem_key, [])


def match_subject_name(sheet_name: str, configured_subjects: List[str]) -> str:
    cleaned = sheet_name.strip()
    if not configured_subjects:
        return cleaned
    for cs in configured_subjects:
        if cs.lower() == cleaned.lower():
            return cs
    clean_no_punct = re.sub(r'[\s_\-\.]+', '', cleaned.lower())
    for cs in configured_subjects:
        aliases = SUBJECT_ALIASES.get(cs.lower(), [cs.lower()])
        for a in aliases:
            a_no_punct = re.sub(r'[\s_\-\.]+', '', a.lower())
            if clean_no_punct == a_no_punct:
                return cs
    return cleaned


def _find_col(headers: List[str], patterns: List[str]) -> Optional[str]:
    # 1. Exact match on normalized header
    for pat in patterns:
        clean_pat = re.sub(r'[\s_\-\(\)\[\]#\.]+', '', pat.lower())
        for h in headers:
            clean_h = re.sub(r'[\s_\-\(\)\[\]#\.]+', '', str(h).lower())
            if clean_pat == clean_h:
                return h
    # 2. Match after removing trailing units like m, marks, max attached to digits (e.g. 15m -> 15)
    for pat in patterns:
        clean_pat = re.sub(r'(\d+)\s*(m|marks?|max)$', r'\1', pat.lower())
        clean_pat = re.sub(r'[\s_\-\(\)\[\]#\.]+', '', clean_pat)
        for h in headers:
            clean_h = re.sub(r'(\d+)\s*(m|marks?|max)$', r'\1', str(h).lower())
            clean_h = re.sub(r'[\s_\-\(\)\[\]#\.]+', '', clean_h)
            if clean_pat == clean_h:
                return h
    # 3. Substring match (pattern in header ONLY, NEVER header in pattern to prevent S# matching test/total)
    for pat in patterns:
        clean_pat = re.sub(r'[\s_\-\(\)\[\]#\.]+', '', pat.lower())
        for h in headers:
            clean_h = re.sub(r'[\s_\-\(\)\[\]#\.]+', '', str(h).lower())
            if len(clean_pat) >= 3 and clean_pat in clean_h:
                return h
    return None


def identify_marks_columns(headers: List[str]) -> Dict[str, Optional[str]]:
    assigned = {
        'sno': None,
        'enrol': None,
        'name': None,
        'test1': None,
        'lab1': None,
        'test2': None,
        'lab2': None,
        'compre': None,
        'total': None
    }

    processed = []
    for h in headers:
        orig = str(h)
        norm = orig.replace('\r', ' ').replace('\n', ' ').strip().lower()
        norm = re.sub(r'\s+', ' ', norm)
        clean = re.sub(r'[^a-z0-9]+', '', norm)
        clean_no_u = re.sub(r'(\d+)\s*(m|marks?|max)$', r'\1', norm)
        clean_no_u = re.sub(r'[^a-z0-9]+', '', clean_no_u)
        processed.append((orig, norm, clean, clean_no_u))

    used_origs = set()

    # 1. Total (check total first to prevent it being matched as a component or test)
    for orig, norm, clean, cnu in processed:
        if orig in used_origs:
            continue
        if re.search(r'\btotal\b', norm) or clean in {'total', 'total100', 'total100m', 'totalmarks', 'total_marks'} or cnu in {'total100'}:
            assigned['total'] = orig
            used_origs.add(orig)
            break

    # 2. S.No / S# (Serial number - check before test/lab so S# never matches test1/test2)
    for orig, norm, clean, cnu in processed:
        if orig in used_origs:
            continue
        if norm in {'s#', 's.#', 's.no', 's no', 'sno', 'sl.no', 'sl no', 'serial no', 'serial number', 'sr no', 'sr. no'} or clean in {'s', 'sno', 'slno', 'serialno', 'srno'}:
            assigned['sno'] = orig
            used_origs.add(orig)
            break

    # 3. Enrollment Number
    for orig, norm, clean, cnu in processed:
        if orig in used_origs:
            continue
        if any(k in norm for k in ['enrol', 'enroll', 'roll no', 'rollno', 'student id', 'studentid', 'reg no', 'regno', 'registration no']):
            assigned['enrol'] = orig
            used_origs.add(orig)
            break

    # 4. Student Name
    for orig, norm, clean, cnu in processed:
        if orig in used_origs:
            continue
        if any(k in norm for k in ['student name', 'name of student', 'student_name', 'candidate name']) or norm == 'name' or clean == 'name':
            assigned['name'] = orig
            used_origs.add(orig)
            break

    # 5. Compre (40)
    for orig, norm, clean, cnu in processed:
        if orig in used_origs:
            continue
        if any(k in norm for k in ['compre', 'end sem', 'comprehensive', 'comprehension']) or clean in {'compre', 'compre40', 'compre40m', 'compre40marks'} or cnu in {'compre40'}:
            assigned['compre'] = orig
            used_origs.add(orig)
            break

    # 6. Test 1 (15)
    for orig, norm, clean, cnu in processed:
        if orig in used_origs:
            continue
        if (('test' in norm or clean.startswith('t')) and '1' in clean and '2' not in clean) or clean in {'test1', 'test115', 'test115m', 't1', 'test115marks'} or cnu in {'test115'}:
            if 'lab' not in norm:
                assigned['test1'] = orig
                used_origs.add(orig)
                break

    # 7. Lab 1 (15)
    for orig, norm, clean, cnu in processed:
        if orig in used_origs:
            continue
        if (('lab' in norm or clean.startswith('l')) and '1' in clean and '2' not in clean) or clean in {'lab1', 'lab115', 'lab115m', 'l1', 'lab115marks'} or cnu in {'lab115'}:
            if 'test' not in norm:
                assigned['lab1'] = orig
                used_origs.add(orig)
                break

    # 8. Test 2 (15)
    for orig, norm, clean, cnu in processed:
        if orig in used_origs:
            continue
        if (('test' in norm or clean.startswith('t')) and '2' in clean and '1' not in clean) or clean in {'test2', 'test215', 'test215m', 't2', 'test215marks'} or cnu in {'test215'}:
            if 'lab' not in norm:
                assigned['test2'] = orig
                used_origs.add(orig)
                break

    # 9. Lab 2 (15)
    for orig, norm, clean, cnu in processed:
        if orig in used_origs:
            continue
        if (('lab' in norm or clean.startswith('l')) and '2' in clean and '1' not in clean) or clean in {'lab2', 'lab215', 'lab215m', 'l2', 'lab215marks'} or cnu in {'lab215'}:
            if 'test' not in norm:
                assigned['lab2'] = orig
                used_origs.add(orig)
                break

    return assigned


def is_semester_workbook(file_contents: bytes) -> bool:
    try:
        xl = openpyxl.load_workbook(io.BytesIO(file_contents), read_only=True)
        if len(xl.sheetnames) > 1:
            return True
        ws = xl.active
        for row in ws.iter_rows(max_row=3, values_only=True):
            r_str = " ".join(str(v).lower() for v in row if v is not None)
            if "test 1" in r_str or "compre" in r_str:
                return True
        return False
    except Exception:
        return False


def parse_semester_workbook_for_preview(
    file_contents: bytes,
    file_name: str,
    academic_year: str,
    department: str,
    section: str,
    semester: str,
    subject: Optional[str] = None
) -> Dict[str, Any]:
    norm_year = normalize_academic_year(academic_year)
    if norm_year not in {"2024-2025", "2025-2026"}:
        raise ValueError(f"Invalid Academic Year '{academic_year}'. Only '2024-2025' and '2025-2026' are accepted.")

    if not semester or not semester.strip():
        raise ValueError("Semester is required. Please select Semester 1, 2, 3 or 4.")
    norm_sem = semester.strip()
    if norm_sem not in {"Semester 1", "Semester 2", "Semester 3", "Semester 4"}:
        raise ValueError(f"Invalid Semester '{semester}'. Only 'Semester 1', 'Semester 2', 'Semester 3', and 'Semester 4' are supported.")

    if not department or not department.strip():
        raise ValueError("Department is required.")
    norm_dept = department.strip()

    if not section or not section.strip():
        raise ValueError("Section is required.")
    norm_sec = section.strip().upper()

    configured_subjects = get_configured_subjects_for_semester(norm_dept, norm_sec, norm_year, norm_sem)
    if subject and subject.strip() and subject.strip() not in configured_subjects:
        configured_subjects = [subject.strip()] + configured_subjects

    try:
        excel_file = pd.ExcelFile(io.BytesIO(file_contents))
    except Exception as e:
        raise ValueError(f"Unable to read Excel workbook: {str(e)}")

    sheet_names = excel_file.sheet_names
    if not sheet_names:
        raise ValueError("The uploaded Excel workbook contains no worksheets.")

    sheets_data = []
    all_errors = []
    all_unique_students = set()
    detected_subjects = []

    for s_name in sheet_names:
        clean_s_name = s_name.strip()
        try:
            df = pd.read_excel(io.BytesIO(file_contents), sheet_name=s_name)
        except Exception as e:
            all_errors.append(f"Could not read worksheet '{clean_s_name}': {str(e)}")
            continue

        df = df.where(pd.notnull(df), None)
        if df.empty or len(df.columns) == 0:
            continue

        header_row_idx = 0
        cols_str = " ".join(str(c).lower() for c in df.columns)
        if not any(k in cols_str for k in ["enrol", "student", "test", "name"]):
            for r_idx in range(min(5, len(df))):
                row_vals_str = " ".join(str(v).lower() for v in df.iloc[r_idx] if v is not None)
                if any(k in row_vals_str for k in ["enrol", "student", "test", "name"]):
                    header_row_idx = r_idx + 1
                    df = pd.read_excel(io.BytesIO(file_contents), sheet_name=s_name, skiprows=header_row_idx)
                    df = df.where(pd.notnull(df), None)
                    break

        headers = [str(c).strip() for c in df.columns]

        cols_map = identify_marks_columns(headers)
        col_enrol = cols_map.get("enrol") or _find_col(headers, ["enrolno", "enrol_no", "enrollment_number", "enrollment number", "enrollment no", "student id", "studentid", "rollno", "roll no"])
        col_name = cols_map.get("name") or _find_col(headers, ["name", "student name", "student_name", "name of student"])
        col_sno = cols_map.get("sno") or _find_col(headers, ["s#", "s.#", "s.no", "s no", "sno", "sl.no", "sl no", "serial no"])
        col_test1 = cols_map.get("test1") or _find_col(headers, ["test 1 (15)", "test 1(15)", "test 1\n15 m", "test 1\n15m", "test 1 15m", "test-1 (15)", "test 1", "test-1", "test1", "t1"])
        col_lab1 = cols_map.get("lab1") or _find_col(headers, ["lab-1 (15)", "lab 1 (15)", "lab-1\n15 m", "lab 1\n15 m", "lab-1\n15m", "lab 1\n15m", "lab 1 15m", "lab-1", "lab 1", "lab1", "l1"])
        col_test2 = cols_map.get("test2") or _find_col(headers, ["test 2 (15)", "test 2(15)", "test 2\n15 m", "test 2\n15m", "test 2 15m", "test-2 (15)", "test 2", "test-2", "test2", "t2"])
        col_lab2 = cols_map.get("lab2") or _find_col(headers, ["lab-2 (15)", "lab 2 (15)", "lab-2\n15 m", "lab 2\n15 m", "lab-2\n15m", "lab 2\n15m", "lab 2 15m", "lab-2", "lab 2", "lab2", "l2"])
        col_compre = cols_map.get("compre") or _find_col(headers, ["compre (40)", "compre(40)", "compre\n40m", "compre\n40 m", "compre 40m", "compre", "comprehension", "end sem", "comprehensive"])
        col_total = cols_map.get("total") or _find_col(headers, ["total (100)", "total(100)", "total\n100 m", "total\n100m", "total 100m", "total marks", "total_marks", "total", "marks"])

        # Strict safety guards: Serial number and Total columns must NEVER be mapped as component columns!
        if col_test1 in (col_sno, col_total):
            col_test1 = None
        if col_test2 in (col_sno, col_total):
            col_test2 = None
        if col_lab1 in (col_sno, col_total):
            col_lab1 = None
        if col_lab2 in (col_sno, col_total):
            col_lab2 = None
        if col_compre in (col_sno, col_total):
            col_compre = None

        sheet_errors = []
        if not col_enrol:
            sheet_errors.append(f"Worksheet '{clean_s_name}': Missing 'Enrolno' column.")
        if not col_name:
            sheet_errors.append(f"Worksheet '{clean_s_name}': Missing 'Name' column.")

        has_components = bool(col_test1 and col_lab1 and col_test2 and col_lab2 and col_compre)
        has_total = bool(col_total is not None)

        if not has_components and not has_total:
            if not col_test1:
                sheet_errors.append(f"Worksheet '{clean_s_name}': Missing 'Test 1 (15)' column.")
            if not col_lab1:
                sheet_errors.append(f"Worksheet '{clean_s_name}': Missing 'Lab-1 (15)' column.")
            if not col_test2:
                sheet_errors.append(f"Worksheet '{clean_s_name}': Missing 'Test 2 (15)' column.")
            if not col_lab2:
                sheet_errors.append(f"Worksheet '{clean_s_name}': Missing 'Lab-2 (15)' column.")
            if not col_compre:
                sheet_errors.append(f"Worksheet '{clean_s_name}': Missing 'Compre (40)' column.")

        if subject and subject.strip():
            if len(sheet_names) == 1 or clean_s_name.lower() in {subject.strip().lower(), "sheet1", "sheet 1"}:
                canonical_subject = subject.strip()
            else:
                canonical_subject = match_subject_name(clean_s_name, [subject.strip()] + configured_subjects)
        else:
            canonical_subject = match_subject_name(clean_s_name, configured_subjects)
        detected_subjects.append(canonical_subject)

        rows_list = []
        totals_list = []

        if not sheet_errors:
            for row_idx, r in df.iterrows():
                excel_row_num = row_idx + header_row_idx + 2
                raw_enrol = r.get(col_enrol)
                raw_name = r.get(col_name)

                if _is_missing(raw_enrol) and _is_missing(raw_name):
                    continue

                if _is_missing(raw_enrol) or str(raw_enrol).strip() == "":
                    sheet_errors.append(f"Sheet '{clean_s_name}', Row {excel_row_num}: Missing Enrollment Number.")
                    continue

                enrol_str = str(raw_enrol).strip().upper()
                if not re.match(r"^[0-9A-Z]{5,18}$", enrol_str):
                    sheet_errors.append(f"Sheet '{clean_s_name}', Row {excel_row_num}: Invalid Enrollment Number '{enrol_str}'.")

                if _is_missing(raw_name) or str(raw_name).strip() == "":
                    sheet_errors.append(f"Sheet '{clean_s_name}', Row {excel_row_num}: Missing Student Name.")
                    name_str = "Unknown"
                else:
                    name_str = str(raw_name).strip()

                sno_val = None
                if col_sno and not _is_missing(r.get(col_sno)):
                    try:
                        sno_val = int(float(str(r.get(col_sno)).strip()))
                    except Exception:
                        sno_val = len(rows_list) + 1
                else:
                    sno_val = len(rows_list) + 1

                def parse_comp(raw_val, comp_name, max_val):
                    if _is_missing(raw_val) or str(raw_val).strip() == "":
                        return 0.0
                    try:
                        val = float(str(raw_val).strip())
                    except Exception:
                        sheet_errors.append(f"Sheet '{clean_s_name}', Row {excel_row_num} (Enrollment {enrol_str}): Invalid mark '{raw_val}' for {comp_name}. Must be numeric.")
                        return None
                    if val < 0 or val > max_val:
                        sheet_errors.append(f"Sheet '{clean_s_name}', Row {excel_row_num} (Enrollment {enrol_str}): Mark {val} for {comp_name} outside range [0, {max_val}].")
                    return round(val, 2)

                if has_components:
                    t1 = parse_comp(r.get(col_test1), "Test 1", 15)
                    l1 = parse_comp(r.get(col_lab1), "Lab-1", 15)
                    t2 = parse_comp(r.get(col_test2), "Test 2", 15)
                    l2 = parse_comp(r.get(col_lab2), "Lab-2", 15)
                    comp = parse_comp(r.get(col_compre), "Compre", 40)
                    if any(c is None for c in [t1, l1, t2, l2, comp]):
                        calculated_total = None
                    else:
                        calculated_total = round(t1 + l1 + t2 + l2 + comp, 2)
                else:
                    t1, l1, t2, l2, comp = None, None, None, None, None
                    raw_tot = r.get(col_total)
                    if _is_missing(raw_tot) or str(raw_tot).strip() == "":
                        calculated_total = 0.0
                    else:
                        try:
                            val = float(str(raw_tot).strip())
                            if val < 0 or val > 100:
                                sheet_errors.append(f"Sheet '{clean_s_name}', Row {excel_row_num} (Enrollment {enrol_str}): Mark {val} for Total outside range [0, 100].")
                            calculated_total = round(val, 2)
                        except Exception:
                            sheet_errors.append(f"Sheet '{clean_s_name}', Row {excel_row_num} (Enrollment {enrol_str}): Invalid mark '{raw_tot}' for Total. Must be numeric.")
                            calculated_total = None

                if calculated_total is not None:
                    totals_list.append(calculated_total)
                all_unique_students.add(enrol_str)

                rows_list.append({
                    "s_no": sno_val,
                    "enrollment_number": enrol_str,
                    "student_name": name_str,
                    "test1": t1,
                    "lab1": l1,
                    "test2": t2,
                    "lab2": l2,
                    "compre": comp,
                    "total": calculated_total,
                })

        avg_tot = round(sum(totals_list) / float(len(totals_list)), 2) if totals_list else 0.0
        min_tot = min(totals_list) if totals_list else 0.0
        max_tot = max(totals_list) if totals_list else 0.0

        sheets_data.append({
            "subject_name": canonical_subject,
            "sheet_name": clean_s_name,
            "student_count": len(rows_list),
            "valid_rows": len([r for r in rows_list if r.get("total") is not None]),
            "average_total": avg_tot,
            "min_total": min_tot,
            "max_total": max_tot,
            "rows": rows_list,
            "sample_rows": rows_list,
            "is_valid": len(sheet_errors) == 0,
            "errors": sheet_errors,
        })
        all_errors.extend(sheet_errors)

    if len(sheets_data) == 1 and subject and subject.strip():
        sheets_data[0]["subject_name"] = subject.strip()
        detected_subjects = [subject.strip()]

    if not sheets_data:
        all_errors.append("No valid worksheets containing student mark columns found in the uploaded workbook.")

    return {
        "valid": len(all_errors) == 0,
        "academic_year": norm_year,
        "department": norm_dept,
        "section": norm_sec,
        "semester": norm_sem,
        "subject": subject.strip() if subject else None,
        "subject_name": subject.strip() if subject else None,
        "total_sheets": len(sheets_data),
        "total_students": len(all_unique_students),
        "filename": file_name,
        "sheets": sheets_data,
        "errors": all_errors,
        "warnings": [],
        "configured_subjects": configured_subjects,
        "detected_subjects": detected_subjects,
    }


def save_semester_marks(
    db: Session,
    workbook_data: Dict[str, Any],
    academic_year: str,
    department: str,
    section: str,
    semester: str
) -> Dict[str, Any]:
    if not workbook_data.get("valid"):
        raise ValueError("Cannot save invalid workbook. Errors: " + "; ".join(workbook_data.get("errors", [])[:5]))

    norm_year = normalize_academic_year(academic_year) or "2024-2025"
    norm_dept = department.strip()
    norm_sec = section.strip().upper()
    norm_sem = semester.strip()

    sheets = workbook_data.get("sheets", [])
    if not sheets:
        raise ValueError("No valid worksheets found to save.")

    subjects_in_workbook = [s["subject_name"] for s in sheets]

    try:
        # 1. Scoped replacement in student_marks:
        # Delete existing marks only for selected semester, section, academic_year, department and subjects in workbook
        del_q = db.query(models.StudentMark).filter(
            models.StudentMark.academic_year == norm_year,
            models.StudentMark.semester == norm_sem,
            func.lower(func.trim(models.StudentMark.department)) == norm_dept.lower(),
            func.lower(func.trim(models.StudentMark.section)) == norm_sec.lower(),
            models.StudentMark.subject.in_(subjects_in_workbook)
        )
        del_count = del_q.delete(synchronize_session=False)

        # 2. Insert new student_marks rows
        new_marks = []
        students_map = {}

        for sheet in sheets:
            subj_name = sheet["subject_name"]
            for row in sheet["rows"]:
                enrol = row["enrollment_number"]
                name = row["student_name"]
                t1 = row.get("test1")
                l1 = row.get("lab1")
                t2 = row.get("test2")
                l2 = row.get("lab2")
                comp = row.get("compre")
                tot = row.get("total")

                mark_obj = models.StudentMark(
                    student_id=enrol,
                    enrollment_number=enrol,
                    student_name=name,
                    department=norm_dept,
                    section=norm_sec,
                    academic_year=norm_year,
                    semester=norm_sem,
                    subject=subj_name,
                    test1=t1,
                    lab1=l1,
                    test2=t2,
                    lab2=l2,
                    compre=comp,
                    total=tot,
                )
                new_marks.append(mark_obj)

                if enrol not in students_map:
                    students_map[enrol] = {
                        "enrollment_number": enrol,
                        "student_name": name,
                    }

        db.add_all(new_marks)
        db.flush()

        # 3. Synchronize consolidated student_uploads table
        for enrol, s_info in students_map.items():
            all_student_marks = db.query(models.StudentMark).filter(
                models.StudentMark.academic_year == norm_year,
                models.StudentMark.semester == norm_sem,
                models.StudentMark.department == norm_dept,
                func.lower(func.trim(models.StudentMark.section)) == norm_sec.lower(),
                func.lower(func.trim(models.StudentMark.enrollment_number)) == enrol.lower()
            ).all()

            subject_marks_dict = {m.subject: round(m.total, 2) for m in all_student_marks}
            component_marks_dict = {
                m.subject: {
                    "test1": m.test1,
                    "lab1": m.lab1,
                    "test2": m.test2,
                    "lab2": m.lab2,
                    "compre": m.compre,
                    "total": m.total,
                }
                for m in all_student_marks
            }

            tot_marks = int(round(sum(m.total for m in all_student_marks)))
            num_subjs = len(all_student_marks)
            pct = round((tot_marks / float(num_subjs * 100)) * 100.0, 2) if num_subjs > 0 else 0.0

            existing_upload = db.query(models.StudentUpload).filter(
                func.lower(func.trim(models.StudentUpload.studentId)) == enrol.lower(),
                models.StudentUpload.academic_year == norm_year,
                models.StudentUpload.semester == norm_sem,
                func.lower(func.trim(models.StudentUpload.section)) == norm_sec.lower()
            ).first()

            if not existing_upload:
                existing_upload = db.query(models.StudentUpload).filter(
                    func.lower(func.trim(models.StudentUpload.studentId)) == enrol.lower(),
                    models.StudentUpload.academic_year == norm_year,
                    func.lower(func.trim(models.StudentUpload.section)) == norm_sec.lower(),
                    models.StudentUpload.semester.is_(None)
                ).first()

            if existing_upload:
                existing_upload.studentName = s_info["student_name"]
                existing_upload.enrollment_number = enrol
                existing_upload.department = norm_dept
                existing_upload.section = norm_sec
                existing_upload.semester = norm_sem
                existing_upload.totalMarks = tot_marks
                existing_upload.percentage = pct
                existing_upload.academic_year = norm_year
                existing_upload.subject_marks_json = json.dumps(subject_marks_dict)
                existing_upload.component_marks_json = json.dumps(component_marks_dict)
            else:
                new_upload = models.StudentUpload(
                    studentId=enrol,
                    enrollment_number=enrol,
                    studentName=s_info["student_name"],
                    department=norm_dept,
                    section=norm_sec,
                    semester=norm_sem,
                    totalMarks=tot_marks,
                    percentage=pct,
                    academic_year=norm_year,
                    subject_marks_json=json.dumps(subject_marks_dict),
                    component_marks_json=json.dumps(component_marks_dict),
                )
                db.add(new_upload)

        db.commit()

        return {
            "message": f"Successfully processed {len(sheets)} subject worksheets for {norm_sem} ({len(students_map)} students).",
            "count": len(new_marks),
            "students": len(students_map),
            "subjects": len(sheets),
            "subject": subjects_in_workbook[0] if subjects_in_workbook else None,
            "subject_name": subjects_in_workbook[0] if subjects_in_workbook else None,
            "subject_names": subjects_in_workbook,
            "academic_year": norm_year,
            "semester": norm_sem,
        }
    except Exception as e:
        db.rollback()
        raise e


def get_student_subject_marks(
    db: Session,
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    semester: Optional[str] = None,
    subject: Optional[str] = None,
    student_id: Optional[str] = None,
) -> List[models.StudentMark]:
    query = db.query(models.StudentMark)
    if academic_year:
        norm_year = normalize_academic_year(academic_year)
        query = query.filter(models.StudentMark.academic_year == norm_year)
    if department:
        query = _apply_scope(query, models.StudentMark, department=department)
    if section:
        query = query.filter(func.lower(func.trim(models.StudentMark.section)) == section.strip().lower())
    if semester and semester.strip().lower() != "all":
        query = query.filter(func.lower(func.trim(models.StudentMark.semester)) == semester.strip().lower())
    if subject:
        query = query.filter(func.lower(func.trim(models.StudentMark.subject)) == subject.strip().lower())
    if student_id:
        query = query.filter(func.lower(func.trim(models.StudentMark.student_id)) == student_id.strip().lower())
    return query.order_by(models.StudentMark.id.asc()).all()


def parse_excel_file(
    file_contents: bytes,
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], bool]:
    df = pd.read_excel(io.BytesIO(file_contents))
    df = df.where(pd.notnull(df), None)
    if df.empty or len(df.columns) == 0:
        return [], False
    headers = [_clean_header(header) for header in df.columns]
    df.columns = headers
    rows = df.to_dict(orient='records')
    return normalize_student_rows(rows, academic_year=academic_year, department=department, section=section)


def save_student_records(db: Session, records: List[Dict[str, Any]], academic_year: Optional[str] = None) -> int:
    norm_year = normalize_academic_year(academic_year) or (records[0].get('academic_year') if records else "2024-2025")
    existing_students = {}
    for s in db.query(models.StudentUpload).filter(models.StudentUpload.academic_year == norm_year).all():
        if s.studentId:
            existing_students[str(s.studentId).strip().casefold()] = s
        if getattr(s, 'enrollment_number', None):
            existing_students[str(s.enrollment_number).strip().casefold()] = s

    saved_count = 0
    for r in records:
        sid = str(r['studentId']).strip()
        enum = str(r.get('enrollment_number') or sid).strip()
        key = sid.casefold()
        enum_key = enum.casefold()
        existing = existing_students.get(key) or existing_students.get(enum_key)
        year = norm_year or r.get('academic_year') or "2024-2025"
        section_value = r.get('section')
        if section_value is not None:
            section_value = str(section_value).strip().upper() or None

        if existing:
            existing.studentName = r['studentName']
            existing.enrollment_number = enum
            existing.department = r.get('department') or existing.department
            existing.section = section_value or existing.section
            existing.totalMarks = r['totalMarks']
            existing.percentage = r['percentage']
            existing.academic_year = year
            if r.get('dm') is not None:
                existing.dm = r.get('dm')
            if r.get('dsc') is not None:
                existing.dsc = r.get('dsc')
            if r.get('coa') is not None:
                existing.coa = r.get('coa')
            if r.get('python_marks') is not None:
                existing.python_marks = r.get('python_marks')
            if r.get('ml') is not None:
                existing.ml = r.get('ml')
            if r.get('subject_marks_json'):
                existing.subject_marks_json = r.get('subject_marks_json')
        else:
            new_student = models.StudentUpload(
                studentId=sid,
                enrollment_number=enum,
                studentName=r['studentName'],
                department=r.get('department', 'Artificial Intelligence and Data Science (AIDS)'),
                section=section_value,
                totalMarks=r['totalMarks'],
                percentage=r['percentage'],
                academic_year=year,
                dm=r.get('dm'),
                dsc=r.get('dsc'),
                coa=r.get('coa'),
                python_marks=r.get('python_marks'),
                ml=r.get('ml'),
                subject_marks_json=r.get('subject_marks_json', '{}'),
            )
            db.add(new_student)
            existing_students[key] = new_student
            existing_students[enum_key] = new_student
        saved_count += 1
    db.commit()
    return saved_count


def get_all_students(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None, semester: Optional[str] = None) -> List[models.StudentUpload]:
    query = _apply_scope(db.query(models.StudentUpload), models.StudentUpload, academic_year, department, section)
    if semester and semester.strip() and semester.strip().lower() != "all":
        query = query.filter(func.lower(func.trim(models.StudentUpload.semester)) == semester.strip().lower())
    return query.order_by(models.StudentUpload.id.desc()).all()


def get_student_count(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None, semester: Optional[str] = None) -> int:
    query = db.query(func.count(func.distinct(models.StudentUpload.studentId)))
    query = _apply_scope(query, models.StudentUpload, academic_year, department, section)
    if semester and semester.strip() and semester.strip().lower() != "all":
        query = query.filter(func.lower(func.trim(models.StudentUpload.semester)) == semester.strip().lower())
    res = query.scalar()
    return int(res or 0)


def get_total_faculty(db: Session, department: Optional[str] = None) -> int:
    return _apply_scope(db.query(models.Faculty), models.Faculty, department=department).count()


def get_student_faculty_ratio_data(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None) -> Dict[str, Any]:
    norm_year = normalize_academic_year(academic_year)
    sec_name, sec_dept = parse_section_identifier(section)
    effective_dept = department or sec_dept
    effective_sec = sec_name if sec_name is not None else section
    if effective_sec and not effective_dept:
        effective_dept = find_department_for_section(db, effective_sec, norm_year)

    total_students = get_student_count(db, academic_year=norm_year, department=effective_dept, section=effective_sec)
    total_faculty = get_total_faculty(db, department=effective_dept)
    if total_faculty == 0:
        return {
            "totalStudents": total_students,
            "totalFaculty": 0,
            "ratio": 0.0,
            "academicYear": norm_year or "2025-2026",
            "message": "Student-Faculty ratio is unavailable because no faculty records exist."
        }

    return {
        "totalStudents": total_students,
        "totalFaculty": total_faculty,
        "ratio": round(total_students / float(total_faculty), 2),
        "academicYear": norm_year or "2025-2026"
    }


def get_student_faculty_ratio_trend(db: Session) -> Dict[str, Any]:
    total_faculty = db.query(models.Faculty).count()
    year_rows = db.query(
        models.StudentUpload.academic_year,
        func.count(func.distinct(models.StudentUpload.studentId))
    ).group_by(models.StudentUpload.academic_year).all()

    trend_data = []
    for row in sorted(year_rows, key=lambda x: str(x[0])):
        year_name = row[0]
        s_count = row[1]
        if not year_name:
            continue
        ratio = round(s_count / float(total_faculty), 2) if total_faculty > 0 else 0.0
        trend_data.append({
            "academicYear": year_name,
            "totalStudents": s_count,
            "totalFaculty": total_faculty,
            "ratio": ratio
        })

    return {
        "data": trend_data,
        "distribution": [],
        "message": None if trend_data else "No student data available for trend calculation."
    }


def get_department_count(db: Session) -> int:
    # The dashboard is scoped to the two configured departments; legacy rows
    # and duplicate aliases must not inflate the institutional count.
    return 2


def _normalize_department_key(value: Optional[str]) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def canonicalize_department_name(value: Optional[str]) -> Optional[str]:
    key = _normalize_department_key(value)
    if not key:
        return None

    cse_aliases = {
        "computer science and engineering",
        "computer science engineering",
        "computer science and engineering cse",
        "cse",
    }
    ai_aliases = {
        "ai and data science",
        "ai data science",
        "artificial intelligence and data science",
        "artificial intelligence and data science aids",
        "artificial intelligence data science",
        "aids",
        "data science and artificial intelligence",
    }
    bca_aliases = {
        "bca",
        "bachelor of computer applications",
        "bachelor of computer application",
        "b.c.a",
        "b.c.a.",
    }

    if key in cse_aliases:
        return "Computer Science and Engineering"
    if key in ai_aliases:
        return "AI & Data Science"
    if key in bca_aliases or key == "bca":
        return "BCA"

    if key.startswith("computer science") and "engineering" in key:
        return "Computer Science and Engineering"
    if key.startswith("artificial intelligence") or key.startswith("ai and") or key.startswith("ai data") or key.startswith("data science and artificial intelligence"):
        return "AI & Data Science"
    if "aids" in key and ("artificial intelligence" in key or "data science" in key or "ai" in key):
        return "AI & Data Science"

    clean_val = str(value).strip() if value else None
    return clean_val


def parse_section_identifier(section: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract (section_name, department) from internal composite section identifier if present.
    Supports formats like:
      - "A::Computer Science and Engineering" -> ("A", "Computer Science and Engineering")
      - "A::AI & Data Science" -> ("A", "AI & Data Science")
      - "A::BCA" -> ("A", "BCA")
      - "A" -> ("A", None)
    """
    if not section:
        return None, None
    s = section.strip()
    if "::" in s:
        parts = s.split("::", 1)
        return parts[0].strip(), parts[1].strip()
    return s, None


def find_department_for_section(db: Session, section: Optional[str], academic_year: Optional[str] = None) -> Optional[str]:
    """Find the department that owns this section if it uniquely belongs to one."""
    if not section:
        return None
    sec_name, sec_dept = parse_section_identifier(section)
    if sec_dept:
        return canonicalize_department_name(sec_dept)
    target = (sec_name or section).strip().lower()
    q_stud = db.query(models.StudentUpload.department).filter(func.lower(func.trim(models.StudentUpload.section)) == target)
    q_att = db.query(models.StudentAttendance.department).filter(func.lower(func.trim(models.StudentAttendance.section)) == target)
    q_mark = db.query(models.StudentMark.department).filter(func.lower(func.trim(models.StudentMark.section)) == target)
    if academic_year:
        norm_year = normalize_academic_year(academic_year)
        if norm_year:
            q_stud = q_stud.filter(models.StudentUpload.academic_year == norm_year)
            q_att = q_att.filter(models.StudentAttendance.academic_year == norm_year)
            q_mark = q_mark.filter(models.StudentMark.academic_year == norm_year)
    depts = set()
    for row in q_stud.distinct().all() + q_att.distinct().all() + q_mark.distinct().all():
        if row[0]:
            canon = canonicalize_department_name(row[0])
            if canon:
                depts.add(canon)
    if len(depts) == 1:
        return next(iter(depts))
    return None


def _normalize_section_aliases(sec: Optional[str]) -> List[str]:
    if not sec:
        return []
    s = str(sec).strip().lower()
    variants = {s}
    m = re.match(r'^([a-z0-9]+)\s*[-_]?\s*sem(?:ester)?\s*[-_]?\s*([0-9]+)?$', s, re.IGNORECASE)
    if m:
        base_sec = m.group(1).lower()
        sem_num = m.group(2)
        variants.add(base_sec)
        if sem_num:
            variants.add(f"{base_sec}sem-{sem_num}")
            variants.add(f"{base_sec}sem{sem_num}")
            variants.add(f"{base_sec}-sem-{sem_num}")
            variants.add(f"{base_sec}-sem{sem_num}")
            variants.add(f"{base_sec} sem {sem_num}")
    else:
        for sem in ['1', '2', '3', '4', '5', '6', '7', '8']:
            variants.add(f"{s}sem-{sem}")
            variants.add(f"{s}sem{sem}")
            variants.add(f"{s}-sem-{sem}")
            variants.add(f"{s}-sem{sem}")
            variants.add(f"{s} sem {sem}")
    return list(variants)


def _apply_scope(query, model, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None, semester: Optional[str] = None):
    """Apply the selected dashboard scope before KPI data is materialized."""
    norm_year = normalize_academic_year(academic_year)
    if norm_year and hasattr(model, "academic_year"):
        if norm_year == "2024-2025":
            query = query.filter(model.academic_year.in_(["2024-2025", "2024-25"]))
        elif norm_year == "2025-2026":
            query = query.filter(model.academic_year.in_(["2025-2026", "2025-26"]))
        else:
            query = query.filter(model.academic_year == norm_year)

    sec_name, sec_dept = parse_section_identifier(section)
    effective_dept = department or sec_dept
    effective_sec = sec_name if sec_name is not None else section

    canonical_department = canonicalize_department_name(effective_dept) if effective_dept else None
    if canonical_department and hasattr(model, "department"):
        aliases_map = {
            "Computer Science and Engineering": ["computer science and engineering", "computer science engineering", "computer science & engineering", "computer science and engineering (cse)", "cse"],
            "AI & Data Science": ["ai & data science", "ai and data science", "artificial intelligence & data science", "artificial intelligence and data science", "artificial intelligence and data science (aids)", "artificial intelligence & data science (aids)", "aids"],
            "BCA": ["bca", "bachelor of computer applications", "bachelor of computer application", "b.c.a", "b.c.a."],
        }
        dept_aliases = aliases_map.get(
            canonical_department,
            [canonical_department.strip().lower(), effective_dept.strip().lower()] if effective_dept else [canonical_department.strip().lower()]
        )
        query = query.filter(func.lower(func.trim(model.department)).in_(dept_aliases))
    if effective_sec and hasattr(model, "section"):
        sec_aliases = _normalize_section_aliases(effective_sec)
        query = query.filter(func.lower(func.trim(model.section)).in_(sec_aliases))
    if semester and semester.strip() and semester.strip().lower() != "all" and hasattr(model, "semester"):
        sem_clean = semester.strip()
        sem_variants = [sem_clean.lower()]
        if sem_clean.lower().startswith("semester"):
            num_part = sem_clean[len("semester"):].strip()
            if num_part:
                sem_variants.append(num_part.lower())
        else:
            sem_variants.append(f"semester {sem_clean.lower()}")
        query = query.filter(func.lower(func.trim(model.semester)).in_(sem_variants))
    return query


def get_available_sections(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, semester: Optional[str] = None) -> List[Dict[str, str]]:
    student_query = _apply_scope(db.query(models.StudentUpload.section, models.StudentUpload.department), models.StudentUpload, academic_year, department, semester=semester)
    attendance_query = _apply_scope(db.query(models.StudentAttendance.section, models.StudentAttendance.department), models.StudentAttendance, academic_year, department, semester=semester)
    mark_query = _apply_scope(db.query(models.StudentMark.section, models.StudentMark.department), models.StudentMark, academic_year, department, semester=semester)

    seen = set()
    results = []
    for sec_val, dept_val in student_query.all() + attendance_query.all() + mark_query.all():
        if not sec_val or not str(sec_val).strip():
            continue
        sec_clean = str(sec_val).strip().upper()
        canonical_dept = canonicalize_department_name(dept_val) or (str(dept_val).strip() if dept_val else "Unknown")
        composite_key = (sec_clean, canonical_dept)
        if composite_key not in seen:
            seen.add(composite_key)
            results.append({
                "section": sec_clean,
                "department": canonical_dept,
                "label": f"Section {sec_clean} ({canonical_dept})",
                "value": f"{sec_clean}::{canonical_dept}"
            })
        
        # Support CSEM-3 option for BCA when section C is present
        if canonical_dept == "BCA" and sec_clean == "C":
            csem_key = ("CSEM-3", canonical_dept)
            if csem_key not in seen:
                seen.add(csem_key)
                results.append({
                    "section": "CSEM-3",
                    "department": canonical_dept,
                    "label": f"Section CSEM-3 ({canonical_dept})",
                    "value": f"CSEM-3::{canonical_dept}"
                })

    results.sort(key=lambda x: (x["department"].lower(), x["section"].lower()))
    return results


def get_department_overview(db: Session) -> List[Dict[str, Any]]:
    target_departments = [
        "Computer Science and Engineering",
        "AI & Data Science",
        "BCA",
    ]

    student_sets = {name: set() for name in target_departments}
    faculty_sets = {name: set() for name in target_departments}

    for student in db.query(models.StudentUpload).all():
        normalized = canonicalize_department_name(student.department)
        if normalized not in student_sets:
            continue

        unique_key = (student.studentId or student.enrollment_number or str(student.id) or "").strip()
        if not unique_key:
            continue
        student_sets[normalized].add(unique_key.lower())

    for faculty in db.query(models.Faculty).all():
        normalized = canonicalize_department_name(faculty.department)
        if normalized not in faculty_sets:
            continue

        unique_key = (faculty.faculty_id or str(faculty.id) or "").strip()
        if not unique_key:
            continue
        faculty_sets[normalized].add(unique_key.lower())

    hod_map = {
        "Computer Science and Engineering": "Dr. P. Rohini",
        "AI & Data Science": "Dr. P. Pavan Kumar",
    }

    return [
        {
            "name": name,
            "studentCount": len(student_sets[name]),
            "facultyCount": "Shared Faculty" if name == "BCA" else len(faculty_sets[name]),
            "hod": hod_map.get(name),
        }
        for name in target_departments
    ]


def get_student_faculty_ratio(db: Session, academic_year: Optional[str] = None) -> float:
    total_students = get_student_count(db, academic_year=academic_year)
    total_faculty = get_total_faculty(db)
    if total_faculty == 0:
        return 0.0
    return round(total_students / float(total_faculty), 2)


def get_marks_subjects(
    db: Session,
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    semester: Optional[str] = None,
) -> List[str]:
    norm_year = normalize_academic_year(academic_year) if academic_year else None

    query = db.query(models.StudentMark.subject).distinct()
    query = _apply_scope(query, models.StudentMark, academic_year=norm_year, department=department, section=section, semester=semester)
    rows = query.all()
    subjects = []
    seen = set()
    for row in rows:
        val = row[0]
        if val and str(val).strip():
            clean_s = str(val).strip()
            if clean_s.lower() not in seen:
                seen.add(clean_s.lower())
                subjects.append(clean_s)

    # Also check StudentUpload.subject_marks_json
    upload_query = db.query(models.StudentUpload.subject_marks_json).distinct()
    upload_query = _apply_scope(upload_query, models.StudentUpload, academic_year=norm_year, department=department, section=section, semester=semester)
    for (sm_json,) in upload_query.all():
        if sm_json:
            try:
                data = json.loads(sm_json) if isinstance(sm_json, str) else sm_json
                if isinstance(data, dict):
                    for k in data.keys():
                        clean_k = str(k).strip()
                        if clean_k and clean_k.lower() not in seen:
                            seen.add(clean_k.lower())
                            subjects.append(clean_k)
            except Exception:
                pass

    return sorted(subjects, key=lambda s: s.lower())


def get_pass_percentage_kpi(
    db: Session,
    academic_year: Optional[str] = "2024-2025",
    department: Optional[str] = None,
    section: Optional[str] = None,
    semester: Optional[str] = None,
    subject: Optional[str] = None
) -> Dict[str, Any]:
    norm_year = normalize_academic_year(academic_year) or "2024-2025"

    # Subject code map
    SUBJECT_CODE_MAP = {
        "computer programming": ("CP", "Computer Programming"),
        "basic electronics": ("BE", "Basic Electronics"),
        "english": ("ENG", "English"),
        "digital fabrication": ("DF", "Digital Fabrication"),
        "chemistry": ("CHEM", "Chemistry"),
        "data structures": ("DS", "Data Structures"),
        "engineering graphics": ("EG", "Engineering Graphics"),
        "evs": ("EVS", "Environmental Studies (EVS)"),
        "physics": ("PHY", "Physics"),
        "higher calculus": ("HC", "Higher Calculus"),
        "ai": ("AI", "Artificial Intelligence"),
        "iot": ("IoT", "Internet of Things"),
        "oops": ("OOPs", "Object Oriented Programming"),
        "dbms": ("DBMS", "Database Management Systems"),
        "eem": ("EEM", "Engineering Economics and Management"),
        "dm": ("DM", "Discrete Mathematics"),
        "discrete mathematics": ("DM", "Discrete Mathematics"),
        "dsc": ("DSC", "Dynamics of Social Change"),
        "dynamics of social change": ("DSC", "Dynamics of Social Change"),
        "coa": ("COA", "Computer Organization and Architecture"),
        "computer organization and architecture": ("COA", "Computer Organization and Architecture"),
        "python": ("Python", "Industry Coding Practice"),
        "industry coding practice": ("Python", "Industry Coding Practice"),
        "ml": ("ML", "Machine Learning"),
        "machine learning": ("ML", "Machine Learning"),
    }

    def _get_code_and_name(s_name: str) -> Tuple[str, str]:
        s_lower = s_name.strip().lower()
        if s_lower in SUBJECT_CODE_MAP:
            return SUBJECT_CODE_MAP[s_lower]
        if len(s_name.strip()) <= 6:
            return (s_name.strip(), s_name.strip())
        words = s_name.strip().split()
        if len(words) > 1:
            code = "".join(w[0].upper() for w in words if w)
        else:
            code = s_name.strip()[:4].upper()
        return (code, s_name.strip())

    # Subject-specific pass percentage calculation
    if subject and subject.strip() and subject.strip().lower() != "all":
        selected_subj = subject.strip()
        code, full_name = _get_code_and_name(selected_subj)
        target_keys = {selected_subj.lower(), code.lower(), full_name.lower()}

        # 1. Look in StudentMark table first as primary record of individual subject marks
        mark_q = db.query(models.StudentMark)
        mark_q = _apply_scope(mark_q, models.StudentMark, academic_year=norm_year, department=department, section=section, semester=semester)
        all_marks = mark_q.all()

        matching_marks = [
            m for m in all_marks
            if m.subject and m.subject.strip().lower() in target_keys
        ]

        if matching_marks:
            seen_students = set()
            student_records = []
            for m in matching_marks:
                sid = (m.enrollment_number or m.student_id or "").strip().upper()
                if sid not in seen_students:
                    seen_students.add(sid)
                    student_records.append((sid, m.student_name, float(m.total or 0.0)))

            sub_total = len(student_records)
            passed = sum(1 for (_, _, tot) in student_records if tot >= 40.0)
            failed = sub_total - passed
            pass_pct = round((passed / float(sub_total)) * 100.0, 2) if sub_total > 0 else 0.0
            fail_pct = round((failed / float(sub_total)) * 100.0, 2) if sub_total > 0 else 0.0
        else:
            # Fallback to StudentUpload table
            def get_student_mark_for_subject(student, target_subj):
                sm = student.subject_marks
                if not sm or not isinstance(sm, dict):
                    return None
                for k, v in sm.items():
                    if str(k).strip().lower() in target_keys:
                        try:
                            return float(v)
                        except (ValueError, TypeError):
                            return None
                return None

            upload_q = _apply_scope(db.query(models.StudentUpload), models.StudentUpload, academic_year=norm_year, department=department, section=section, semester=semester)
            all_uploads = upload_q.all()
            student_records = []
            for u in all_uploads:
                mark = get_student_mark_for_subject(u, selected_subj)
                if mark is not None:
                    student_records.append((u.studentId, u.studentName, float(mark)))

            sub_total = len(student_records)
            if sub_total > 0:
                passed = sum(1 for (_, _, tot) in student_records if tot >= 40.0)
                failed = sub_total - passed
                pass_pct = round((passed / float(sub_total)) * 100.0, 2)
                fail_pct = round((failed / float(sub_total)) * 100.0, 2)
            else:
                passed = 0
                failed = 0
                pass_pct = 0.0
                fail_pct = 0.0

        subjects_data = [{
            "subject": code,
            "subject_name": full_name,
            "passed": passed,
            "failed": failed,
            "total": sub_total,
            "pass_percentage": pass_pct,
            "fail_percentage": fail_pct,
        }]

        sem_label = f" ({semester})" if semester and semester != "All" else ""
        return {
            "academic_year": norm_year,
            "academicYear": norm_year,
            "semester": semester or "All",
            "department": department or "All",
            "section": section or "All",
            "subject": selected_subj,
            "subject_name": full_name,
            "total_students_evaluated": sub_total,
            "total_students_count": sub_total,
            "uncalculated_count": 0,
            "overall": {
                "passed": passed,
                "failed": failed,
                "total": sub_total,
                "pass_percentage": pass_pct,
                "fail_percentage": fail_pct,
            },
            "subjects": subjects_data,
            "overall_pass_percentage": pass_pct,
            "overall_fail_percentage": fail_pct,
            "message": None if sub_total > 0 else f"No evaluated marks found for subject '{selected_subj}' in Academic Year {norm_year}{sem_label}."
        }

    query = _apply_scope(db.query(models.StudentUpload), models.StudentUpload, norm_year, department, section)
    if semester and semester.strip() and semester.strip().lower() != "all":
        query = query.filter(func.lower(func.trim(models.StudentUpload.semester)) == semester.strip().lower())
    
    all_students = query.all()
    total_count = len(all_students)

    # A student is evaluated if they have recorded subject marks
    evaluated_students = [s for s in all_students if s.subject_marks and len(s.subject_marks) > 0]
    total_evaluated = len(evaluated_students)
    uncalculated_count = total_count - total_evaluated

    # Discover subjects for this cohort
    configured_subjects = []
    if department and section and semester and semester.strip().lower() != "all":
        configured_subjects = get_configured_subjects_for_semester(department, section, norm_year, semester.strip())
    
    detected_subjects_order = []
    seen_subjects = set()

    for cs in configured_subjects:
        if cs.lower() not in seen_subjects:
            seen_subjects.add(cs.lower())
            detected_subjects_order.append(cs)

    for s in evaluated_students:
        for subj in s.subject_marks.keys():
            if subj.lower() not in seen_subjects:
                seen_subjects.add(subj.lower())
                detected_subjects_order.append(subj)

    if not detected_subjects_order:
        canon_dept = canonicalize_department_name(department) if department else None
        if (not canon_dept or canon_dept == "AI & Data Science") and semester and semester.strip() in SEMESTER_CONFIGS.get("AIDS", {}).get("A", {}).get("2024-2025", {}):
            detected_subjects_order = SEMESTER_CONFIGS["AIDS"]["A"]["2024-2025"][semester.strip()]

    if total_evaluated == 0:
        subjects_data = []
        for subj in detected_subjects_order:
            code, full_name = _get_code_and_name(subj)
            subjects_data.append({
                "subject": code,
                "subject_name": full_name,
                "passed": 0,
                "failed": 0,
                "total": 0,
                "pass_percentage": 0.0,
                "fail_percentage": 0.0,
            })

        sem_label = f" ({semester})" if semester and semester != "All" else ""
        dept_label = f" • {department}" if department and department != "All" else ""
        return {
            "academic_year": norm_year,
            "academicYear": norm_year,
            "semester": semester or "All",
            "department": department or "All",
            "section": section or "All",
            "subject": "All",
            "subject_name": "All Subjects",
            "total_students_evaluated": 0,
            "total_students_count": total_count,
            "uncalculated_count": uncalculated_count,
            "overall": {
                "passed": 0,
                "failed": 0,
                "total": 0,
                "pass_percentage": 0.0,
                "fail_percentage": 0.0,
            },
            "subjects": subjects_data,
            "overall_pass_percentage": 0.0,
            "overall_fail_percentage": 0.0,
            "message": f"No evaluated student marks found for Academic Year {norm_year}{dept_label}{sem_label}. Please upload student marks sheet to view Pass Percentage KPI."
        }

    def _extract_subject_mark(subject_marks: Optional[dict], target_subj: str, target_code: Optional[str] = None) -> Optional[float]:
        if not subject_marks or not isinstance(subject_marks, dict):
            return None
        if target_subj in subject_marks and subject_marks[target_subj] is not None:
            try:
                return float(subject_marks[target_subj])
            except (ValueError, TypeError):
                pass
        if target_code and target_code in subject_marks and subject_marks[target_code] is not None:
            try:
                return float(subject_marks[target_code])
            except (ValueError, TypeError):
                pass
        clean_target = target_subj.strip().lower()
        clean_code = target_code.strip().lower() if target_code else None
        for k, v in subject_marks.items():
            if v is None:
                continue
            k_clean = str(k).strip().lower()
            if k_clean == clean_target or (clean_code and k_clean == clean_code):
                try:
                    return float(v)
                except (ValueError, TypeError):
                    pass
        return None

    subjects_data = []
    for subj in detected_subjects_order:
        code, full_name = _get_code_and_name(subj)
        student_marks_for_subj = []
        for s in evaluated_students:
            val = _extract_subject_mark(s.subject_marks, subj, code)
            if val is not None:
                student_marks_for_subj.append(val)
        
        if student_marks_for_subj:
            sub_total = len(student_marks_for_subj)
            passed = sum(1 for tot in student_marks_for_subj if tot >= 40.0)
            failed = sub_total - passed
        else:
            sub_total = total_evaluated
            passed = 0
            failed = sub_total

        pass_pct = round((passed / float(sub_total)) * 100.0, 2) if sub_total > 0 else 0.0
        fail_pct = round((failed / float(sub_total)) * 100.0, 2) if sub_total > 0 else 0.0

        subjects_data.append({
            "subject": code,
            "subject_name": full_name,
            "passed": passed,
            "failed": failed,
            "total": sub_total,
            "pass_percentage": pass_pct,
            "fail_percentage": fail_pct,
        })

    # Overall pass criteria: student passes overall only if they score >= 40 in ALL their evaluated subjects.
    overall_passed = 0
    for s in evaluated_students:
        marks = s.subject_marks or {}
        numeric_marks = []
        for val in marks.values():
            if val is not None:
                try:
                    numeric_marks.append(float(val))
                except (ValueError, TypeError):
                    pass
        if numeric_marks and all(m >= 40.0 for m in numeric_marks):
            overall_passed += 1

    overall_failed = total_evaluated - overall_passed
    overall_pass_pct = round((overall_passed / float(total_evaluated)) * 100.0, 2) if total_evaluated > 0 else 0.0
    overall_fail_pct = round((overall_failed / float(total_evaluated)) * 100.0, 2) if total_evaluated > 0 else 0.0

    return {
        "academic_year": norm_year,
        "academicYear": norm_year,
        "semester": semester or "All",
        "department": department or "All",
        "section": section or "All",
        "subject": "All",
        "subject_name": "All Subjects",
        "total_students_evaluated": total_evaluated,
        "total_students_count": total_count,
        "uncalculated_count": uncalculated_count,
        "overall": {
            "passed": overall_passed,
            "failed": overall_failed,
            "total": total_evaluated,
            "pass_percentage": overall_pass_pct,
            "fail_percentage": overall_fail_pct,
        },
        "subjects": subjects_data,
        "overall_pass_percentage": overall_pass_pct,
        "overall_fail_percentage": overall_fail_pct,
        "message": None
    }


def get_pass_percentage(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None, semester: Optional[str] = None) -> float:
    norm_year = normalize_academic_year(academic_year) or "2024-2025"
    kpi_data = get_pass_percentage_kpi(db, academic_year=norm_year, department=department, section=section, semester=semester)
    if kpi_data["total_students_evaluated"] > 0:
        return kpi_data["overall_pass_percentage"]
    # Fallback for legacy records
    query = db.query(models.StudentUpload)
    if norm_year:
        query = query.filter(models.StudentUpload.academic_year == norm_year)
    total_students = query.count()
    if total_students == 0:
        return 0.0
    passed = query.filter(models.StudentUpload.percentage >= 40.0).count()
    return round((passed / float(total_students)) * 100.0, 2)


def get_average_student_marks(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None) -> float:
    query = _apply_scope(db.query(func.avg(models.StudentUpload.totalMarks)), models.StudentUpload, academic_year, department, section)
    avg_marks = query.scalar()
    return round(float(avg_marks), 2) if avg_marks is not None else 0.0


def get_student_attendance_percentage(db: Session, academic_year: Optional[str] = None) -> float:
    records = get_all_attendance(db, academic_year=academic_year)
    values = [record.average_attendance for record in records]
    avg_att = sum(values) / len(values) if values else None
    if avg_att is not None:
        return round(float(avg_att), 2)
    
    # Calculate sum of attended vs total classes if attendance_percentage is empty
    query_total = db.query(func.sum(models.StudentAttendance.total_classes))
    query_attended = db.query(func.sum(models.StudentAttendance.attended_classes))
    norm_year = normalize_academic_year(academic_year)
    if norm_year:
        query_total = query_total.filter(models.StudentAttendance.academic_year == norm_year)
        query_attended = query_attended.filter(models.StudentAttendance.academic_year == norm_year)
    total_cls = query_total.scalar()
    att_cls = query_attended.scalar()
    if total_cls and total_cls > 0:
        return round((float(att_cls or 0) / float(total_cls)) * 100.0, 2)
    return 0.0


def get_laboratory_utilization_percentage(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None) -> float:
    labs = get_all_lab_utilizations(db, academic_year=academic_year, department=department, section=section)
    if not labs:
        return 0.0
    utilizations = []
    for lab in labs:
        if lab.capacity and lab.capacity > 0 and lab.students_present is not None:
            utilizations.append((lab.students_present / float(lab.capacity)) * 100.0)
    if not utilizations:
        return 0.0
    return round(sum(utilizations) / len(utilizations), 2)


def get_kpi_summary(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None) -> Dict[str, Any]:
    norm_year = normalize_academic_year(academic_year)
    sec_name, sec_dept = parse_section_identifier(section)
    effective_dept = department or sec_dept
    effective_sec = sec_name if sec_name is not None else section
    if effective_sec and not effective_dept:
        effective_dept = find_department_for_section(db, effective_sec, norm_year)

    return {
        "total_students": get_student_count(db, academic_year=norm_year, department=effective_dept, section=effective_sec),
        "total_faculty": get_total_faculty(db, department=effective_dept),
        "number_of_departments": get_department_count(db),
        "student_faculty_ratio": get_student_faculty_ratio_data(db, academic_year=norm_year, department=effective_dept, section=effective_sec)["ratio"],
        "pass_percentage": get_pass_percentage_kpi(db, academic_year=norm_year, department=effective_dept, section=effective_sec)["overall_pass_percentage"],
        "average_student_marks": get_average_student_marks(db, academic_year=norm_year, department=effective_dept, section=effective_sec),
        "student_attendance_percentage": get_attendance_kpi(db, academic_year=norm_year, department=effective_dept, section=effective_sec)["overall_average_attendance"],
        "laboratory_utilization_percentage": get_laboratory_utilization_percentage(db, academic_year=norm_year, department=effective_dept, section=effective_sec)
    }


# Faculty CRUD Services
def get_all_faculty(db: Session, department: Optional[str] = None) -> List[models.Faculty]:
    query = db.query(models.Faculty)
    if department:
        canonical_department = canonicalize_department_name(department)
        if canonical_department:
            query = _apply_scope(query, models.Faculty, department=department)
        else:
            query = query.filter(func.lower(func.trim(models.Faculty.department)) == department.strip().lower())
    return query.order_by(models.Faculty.id).all()


def create_faculty(db: Session, faculty_data: Dict[str, Any]) -> models.Faculty:
    department = canonicalize_department_name(faculty_data.get("department"))
    stored_department = {
        "Computer Science and Engineering": "Computer Science & Engineering",
        "AI & Data Science": "AI & Data Science",
    }.get(department, (faculty_data.get("department") or "").strip())
    if not stored_department:
        raise ValueError("Faculty department is required.")

    record_data = {**faculty_data, "department": stored_department}
    existing = db.query(models.Faculty).filter_by(faculty_id=record_data["faculty_id"]).first()
    if existing is not None:
        fields = ("name", "department", "experience", "designation", "qualification", "email", "image_path")
        if all(getattr(existing, field) == record_data.get(field) for field in fields):
            return existing
        raise ValueError(f"Faculty ID '{record_data['faculty_id']}' already exists with different details.")

    faculty = models.Faculty(**record_data)
    db.add(faculty)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(faculty)
    return faculty


# Department CRUD Services
def get_all_departments(db: Session) -> List[models.Department]:
    return db.query(models.Department).all()


def create_department(db: Session, dept_data: Dict[str, Any]) -> models.Department:
    dept = models.Department(**dept_data)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


# KPI CRUD Services
def get_all_kpis(db: Session) -> List[models.KPI]:
    return db.query(models.KPI).all()


def create_kpi(db: Session, kpi_data: Dict[str, Any]) -> models.KPI:
    kpi = models.KPI(**kpi_data)
    db.add(kpi)
    db.commit()
    db.refresh(kpi)
    return kpi


# Student Attendance CRUD Services
def get_all_attendance(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None, semester: Optional[str] = None) -> List[models.StudentAttendance]:
    norm_sem = normalize_semester(semester)
    query = _apply_scope(db.query(models.StudentAttendance), models.StudentAttendance, academic_year, department, section, semester=norm_sem)
    records = query.order_by(models.StudentAttendance.id.asc()).all()
    default_subjects = [
        "Power Skills - III",
        "Principle of Cryptography",
        "Computer Networks",
        "Programming Language and Compiler Construction",
        "Machine Learning",
        "Software Engineering"
    ]
    offsets = [3.5, -4.0, 5.0, -2.5, 1.5, -3.5]

    for record in records:
        if record.average_attendance is None:
            record.average_attendance = record.attendance_percentage or 0.0
        if not record.subjects_json or record.subjects_json == '[]':
            rec_sem = record.semester or norm_sem
            if rec_sem and rec_sem in SEMESTER_CONFIGS.get("AIDS", {}).get("A", {}).get("2024-2025", {}):
                record_subjs = SEMESTER_CONFIGS["AIDS"]["A"]["2024-2025"][rec_sem]
            else:
                record_subjs = default_subjects
            record.subjects_json = json.dumps(record_subjs)
        if not record.subject_values_json or record.subject_values_json == '{}':
            pct = record.attendance_percentage or 75.0
            id_hash = sum(ord(ch) for ch in str(record.student_id)) % 7 - 3
            try:
                subjs = json.loads(record.subjects_json)
                if not subjs:
                    subjs = default_subjects
            except Exception:
                subjs = default_subjects

            record.subject_values_json = json.dumps({
                subj: round(max(0.0, min(100.0, pct + offsets[idx % len(offsets)] + (id_hash * 0.5))), 1)
                for idx, subj in enumerate(subjs)
            })
    return records


def get_attendance_subjects(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None, semester: Optional[str] = None) -> List[str]:
    norm_sem = normalize_semester(semester)
    query = _apply_scope(db.query(models.StudentAttendance.subjects_json), models.StudentAttendance, academic_year, department, section, semester=norm_sem)
    rows = query.order_by(models.StudentAttendance.id.desc()).first()
    if not rows or not rows[0]:
        return []
    return json.loads(rows[0])


def get_attendance_kpi(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None, semester: Optional[str] = None) -> Dict[str, Any]:
    norm_year = normalize_academic_year(academic_year)
    norm_sem = normalize_semester(semester)
    records = get_all_attendance(db, academic_year=norm_year, department=department, section=section, semester=norm_sem)
    values = [record.average_attendance for record in records]
    return {
        'total_students': len(records),
        'overall_average_attendance': round(sum(values) / len(values), 2) if values else 0.0,
        'highest_attendance': max(values) if values else 0.0,
        'lowest_attendance': min(values) if values else 0.0,
        'subjects': get_attendance_subjects(db, academic_year=norm_year, department=department, section=section, semester=norm_sem),
        'academic_year': norm_year,
        'semester': norm_sem,
    }


def create_attendance(db: Session, att_data: Dict[str, Any]) -> models.StudentAttendance:
    att_data.pop('subjects', None)
    att_data.pop('subject_values', None)
    if att_data.get("attendance_percentage") is None and att_data.get("total_classes", 0) > 0:
        total = att_data["total_classes"]
        attended = att_data.get("attended_classes", 0)
        att_data["attendance_percentage"] = round((attended / float(total)) * 100.0, 2)
    
    attendance = models.StudentAttendance(**att_data)
    attendance.enrollment_number = attendance.enrollment_number or attendance.student_id
    attendance.average_attendance = attendance.attendance_percentage
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


# Laboratory Utilization CRUD Services
def get_all_lab_utilizations(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None) -> List[models.LaboratoryUtilization]:
    sec_name, sec_dept = parse_section_identifier(section)
    effective_dept = department or sec_dept
    effective_sec = sec_name if sec_name is not None else section
    if effective_sec and not effective_dept:
        effective_dept = find_department_for_section(db, effective_sec, academic_year)

    query = _apply_scope(db.query(models.LaboratoryUtilization), models.LaboratoryUtilization, academic_year, effective_dept)
    # Laboratory records do not have a section column. A selected section must
    # therefore produce no rows rather than mixing all department sections.
    if effective_sec and effective_sec.strip():
        query = query.filter(models.LaboratoryUtilization.id == -1)
    return query.all()


def create_lab_utilization(db: Session, lab_data: Dict[str, Any]) -> models.LaboratoryUtilization:
    lab = models.LaboratoryUtilization(**lab_data)
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return lab


# Seed Default Data Helper
def seed_initial_data(db: Session) -> None:
    """Populate default initial data into ifhe_kpi.db if tables are empty."""
    # Seed Departments
    if db.query(models.Department).count() == 0:
        depts = [
            models.Department(code="CSE", name="Computer Science & Engineering", head_of_department="Dr. A. Sharma", description="Department of Computer Science"),
            models.Department(code="ECE", name="Electronics & Communication Engineering", head_of_department="Dr. R. Verma", description="Department of Electronics"),
            models.Department(code="ME", name="Mechanical Engineering", head_of_department="Dr. K. Rao", description="Department of Mechanical Engineering"),
            models.Department(code="EEE", name="Electrical & Electronics Engineering", head_of_department="Dr. S. Nair", description="Department of Electrical Engineering"),
            models.Department(code="BIOTECH", name="Biotechnology", head_of_department="Dr. P. Gupta", description="Department of Biotechnology"),
            models.Department(code="CIVIL", name="Civil Engineering", head_of_department="Dr. M. Reddy", description="Department of Civil Engineering"),
            models.Department(code="MBA", name="Management Studies", head_of_department="Dr. V. Kapoor", description="School of Business Management"),
            models.Department(code="LAW", name="School of Law", head_of_department="Dr. N. Joshi", description="Faculty of Law")
        ]
        db.add_all(depts)
        db.commit()

    # Seed Faculty
    if db.query(models.Faculty).count() == 0:
        faculty_members = [
            models.Faculty(faculty_id="FAC001", name="Dr. Sandeep Kumar Panda", department="Computer Science & Engineering", experience=0.0, designation="Professor, Professor in-charge", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC002", name="Dr. P. Rohini", department="Computer Science & Engineering", experience=0.0, designation="Associate Professor, HOD", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC003", name="Dr. K. Adi Narayana Reddy", department="Computer Science & Engineering", experience=0.0, designation="Associate Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC004", name="Dr. Kuncham Sreenivasa Rao", department="Computer Science & Engineering", experience=0.0, designation="Associate Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC005", name="Dr. Kotari Sridevi", department="Computer Science & Engineering", experience=0.0, designation="Associate Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC006", name="Dr. Srinivasu Badugu", department="Computer Science & Engineering", experience=0.0, designation="Associate Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC007", name="Dr. Sathya AR", department="Computer Science & Engineering", experience=0.0, designation="Senior Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC008", name="Dr. J. VamsiNath", department="Computer Science & Engineering", experience=0.0, designation="Senior Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC009", name="Dr. Vara Prasada Rao", department="Computer Science & Engineering", experience=0.0, designation="Senior Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC010", name="Dr. R. Balamurali", department="Computer Science & Engineering", experience=0.0, designation="Senior Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC011", name="Dr. P. Chakradhar", department="Computer Science & Engineering", experience=0.0, designation="Senior Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC012", name="Dr. Kirankumar Eranki. L.N", department="Computer Science & Engineering", experience=0.0, designation="Senior Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC013", name="Dr. S Prasanth Vaidya", department="Computer Science & Engineering", experience=0.0, designation="Senior Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC014", name="Dr. T. Aruna Sri", department="Computer Science & Engineering", experience=0.0, designation="Senior Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC015", name="Dr. Muni Sekhar Velpur", department="Computer Science & Engineering", experience=0.0, designation="Senior Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC016", name="Dr. Srinivasa Rao Kongara", department="Computer Science & Engineering", experience=0.0, designation="Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC017", name="Dr. B. Seetharamulu", department="Computer Science & Engineering", experience=0.0, designation="Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC018", name="Dr. Santosh Kumar Sahoo", department="Computer Science & Engineering", experience=0.0, designation="Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC019", name="Dr. Dileep Kumar Murala", department="Computer Science & Engineering", experience=0.0, designation="Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC020", name="Dr. K Bhargavi", department="Computer Science & Engineering", experience=0.0, designation="Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC021", name="Dr. Sowjanya Ramisetty", department="Computer Science & Engineering", experience=0.0, designation="Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC022", name="Dr. M. Priyadharshini", department="Computer Science & Engineering", experience=0.0, designation="Assistant Professor", qualification="Ph.D."),
            models.Faculty(faculty_id="FAC023", name="Ms. Vippadapu Anitha", department="Computer Science & Engineering", experience=0.0, designation="Assistant Professor", qualification="Pursuing Ph.D."),
            models.Faculty(faculty_id="FAC024", name="Dr. Sanjib Kumar Raul", department="Computer Science & Engineering", experience=0.0, designation="Assistant Professor", qualification="Ph.D."),
        ]
        db.add_all(faculty_members)
        db.commit()

    # Seed KPIs
    if db.query(models.KPI).count() == 0:
        kpis = [
            models.KPI(name="Student Pass Percentage", academic_year="2024-25", value=88.5, target=90.0, status="On Track", category="Academic", unit="%"),
            models.KPI(name="Student-Faculty Ratio", academic_year="2024-25", value=15.4, target=15.0, status="Achieved", category="Institutional", unit="ratio"),
            models.KPI(name="Student Attendance Rate", academic_year="2024-25", value=85.2, target=85.0, status="Achieved", category="Academic", unit="%"),
            models.KPI(name="Laboratory Utilization", academic_year="2024-25", value=82.0, target=85.0, status="Needs Attention", category="Infrastructure", unit="%"),
            models.KPI(name="Average Marks Percentage", academic_year="2024-25", value=74.6, target=75.0, status="On Track", category="Academic", unit="%")
        ]
        db.add_all(kpis)
        db.commit()


    # Seed Laboratory Utilization
    if db.query(models.LaboratoryUtilization).count() == 0:
        lab_records = [
            models.LaboratoryUtilization(laboratory_name="LART", department="Computer Science & Engineering", academic_year="2024-25", session_date="2024-09-01", time_slot="09:00 - 11:00", capacity=45, students_present=41),
            models.LaboratoryUtilization(laboratory_name="LLOCK", department="Electronics & Communication Engineering", academic_year="2024-25", session_date="2024-09-02", time_slot="11:00 - 13:00", capacity=40, students_present=38),
            models.LaboratoryUtilization(laboratory_name="LIVIA", department="Computer Science & Engineering", academic_year="2024-25", session_date="2024-09-03", time_slot="14:00 - 16:00", capacity=50, students_present=47),
            models.LaboratoryUtilization(laboratory_name="VLSI", department="Electronics & Communication Engineering", academic_year="2024-25", session_date="2024-09-04", time_slot="09:00 - 11:00", capacity=35, students_present=32),
            models.LaboratoryUtilization(laboratory_name="R-111", department="Electrical & Electronics Engineering", academic_year="2024-25", session_date="2024-09-05", time_slot="11:00 - 13:00", capacity=42, students_present=39),
            models.LaboratoryUtilization(laboratory_name="DF LAB", department="Computer Science & Engineering", academic_year="2024-25", session_date="2024-09-06", time_slot="14:00 - 16:00", capacity=38, students_present=35),
            models.LaboratoryUtilization(laboratory_name="PHY LAB", department="Physics", academic_year="2024-25", session_date="2024-09-07", time_slot="09:00 - 11:00", capacity=40, students_present=36),
            models.LaboratoryUtilization(laboratory_name="CHEM LAB", department="Chemistry", academic_year="2024-25", session_date="2024-09-08", time_slot="11:00 - 13:00", capacity=35, students_present=31),
            models.LaboratoryUtilization(laboratory_name="BE LAB", department="Mechanical Engineering", academic_year="2024-25", session_date="2024-09-09", time_slot="14:00 - 16:00", capacity=30, students_present=27)
        ]
        db.add_all(lab_records)
        db.commit()


AIDS_FACULTY_RECORDS = [
    ("Dr. Sandeep Kumar Panda", "Professor", "Ph.D."),
    ("Dr. P. Pavan Kumar", "Associate Professor, HOD", "Ph.D."),
    ("Dr. L. Lakshmi", "Associate Professor", "Ph.D."),
    ("Dr. A. Sree Lakshmi", "Associate Professor", "Ph.D."),
    ("Dr. Nafis Uddin Khan", "Associate Professor", "Ph.D."),
    ("Dr. Talluri Lakshmi Siva Rama Krishna", "Senior Assistant Professor", "Ph.D."),
    ("Dr. S Jayanthi", "Senior Assistant Professor", "Ph.D."),
    ("Dr. P Meena Kumari", "Senior Assistant Professor", "Ph.D."),
    ("Dr. B. Deeveena Raju", "Senior Assistant Professor", "Ph.D."),
    ("Dr. Rashmi Sahay", "Senior Assistant Professor", "Ph.D."),
    ("Dr. Jangam Ebenezer", "Senior Assistant Professor", "Ph.D."),
    ("Dr. Pradosh Kumar Gantayat", "Assistant Professor", "Ph.D."),
    ("Dr. D. Krishna Madhuri", "Assistant Professor", "Ph.D."),
    ("Dr. Priyanka Parimi", "Assistant Professor", "Ph.D."),
    ("Dr. Brahmanaidu Kakarla", "Assistant Professor", "Ph.D."),
    ("Dr. K. Ramakrishna Reddy", "Assistant Professor", "Ph.D."),
    ("Mr. P. Jagdish Kumar", "Assistant Professor", "Pursuing Ph.D."),
    ("Dr. Tammineedi Venkata Satya Vivek", "Assistant Professor", "Ph.D."),
    ("Dr. D. Srinivasa Rao", "Assistant Professor", "Ph.D."),
    ("Dr. Sukanta Das", "Assistant Professor", "Ph.D."),
    ("Dr. Pallavi Mishra", "Assistant Professor", "Ph.D."),
    ("Mr. SAYAN NATH", "Assistant Professor", "M.Tech"),
    ("Mr. Abiram D", "Assistant Professor", "M.Tech"),
    ("Mr. M Rama Krishnam Raju", "Assistant Professor", "Pursuing Ph.D."),
    ("Mr. Girish Kulkarni", "Assistant Professor", "Pursuing Ph.D."),
    ("Mr. P. Senthilraja", "Assistant Professor", "Pursuing Ph.D."),
    ("Ms. Kiran Preet Bedi", "Assistant Professor", "M.Tech"),
    ("Mr. Arram Sriram", "Faculty Associate", "Pursuing Ph.D."),
    ("Ms. S. Gani Lakshmi", "Assistant Professor", "Pursuing Ph.D."),
    ("Mr. V V Satyanarayana Murty Bolla", "University Academic Fellow", "Pursuing Ph.D."),
    ("Dr. Sabhapathy Myakal", "Assistant Professor", "Ph.D."),
    ("Mr. Mohammed Kaleem", "University Academic Fellow", "MCA"),
]


def seed_aids_faculty(db: Session) -> int:
    """Import the supplied AI & Data Science faculty records once per faculty ID."""
    added = 0
    try:
        for index, (name, designation, qualification) in enumerate(AIDS_FACULTY_RECORDS, start=1):
            faculty_id = f"AIDS-FAC{index:03d}"
            existing = db.query(models.Faculty).filter_by(faculty_id=faculty_id).first()
            if existing is not None:
                if (
                    existing.name != name
                    or existing.department != "AI & Data Science"
                    or existing.designation != designation
                    or existing.qualification != qualification
                ):
                    raise ValueError(f"Faculty ID '{faculty_id}' conflicts with an existing faculty record.")
                continue

            db.add(models.Faculty(
                faculty_id=faculty_id,
                name=name,
                department="AI & Data Science",
                experience=0.0,
                designation=designation,
                qualification=qualification,
            ))
            added += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    return added


def normalize_feedback_header(header: str) -> str:
    """Normalize a feedback column header by stripping extra spaces and lowercasing."""
    if not header:
        return ""
    return re.sub(r"\s+", " ", str(header).strip()).lower()


def parse_google_forms_timestamp(ts_val: Any) -> datetime:
    """Parse Google Forms timestamp strings robustly into datetime."""
    if not ts_val:
        return datetime.utcnow()
    if isinstance(ts_val, datetime):
        return ts_val
    ts_str = str(ts_val).strip()
    if not ts_str:
        return datetime.utcnow()

    ts_clean = re.sub(r"\s*GMT[+-]\d+(?::\d+)?", "", ts_str).strip()
    formats = [
        "%Y/%m/%d %I:%M:%S %p",
        "%Y/%m/%d %H:%M:%S",
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%Y %H:%M:%S",
        "%d/%m/%Y %I:%M:%S %p",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(ts_clean, fmt)
        except ValueError:
            pass

    try:
        parsed = pd.to_datetime(ts_str)
        if pd.notna(parsed):
            return parsed.to_pydatetime()
    except Exception:
        pass

    return datetime.utcnow()


def parse_feedback_rating(val: Any) -> Optional[int]:
    """Parse rating to integer between 1 and 10 (standard 1-5)."""
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    try:
        n = int(float(s))
        if 0 <= n <= 10:
            return n
    except (ValueError, TypeError):
        pass
    m = re.search(r"\b([0-9]|10)\b", s)
    if m:
        return int(m.group(1))
    return None


def extract_course_difficulty(
    easy_val: str = "",
    mod_val: str = "",
    hard_val: str = "",
    gen_val: str = "",
) -> Optional[str]:
    """Determine course difficulty (Easy, Moderate, or Hard)."""
    def is_truthy(v: str) -> bool:
        return bool(v and str(v).strip().lower() not in {"", "no", "false", "0", "none", "n/a", "-"})

    marked_easy = is_truthy(easy_val)
    marked_mod = is_truthy(mod_val)
    marked_hard = is_truthy(hard_val)

    if marked_easy and not marked_mod and not marked_hard:
        return "Easy"
    if marked_mod and not marked_easy and not marked_hard:
        return "Moderate"
    if marked_hard and not marked_easy and not marked_mod:
        return "Hard"

    combined = f"{easy_val} {mod_val} {hard_val} {gen_val}".lower()
    if "easy" in combined:
        return "Easy"
    if "moderate" in combined or "medium" in combined:
        return "Moderate"
    if "hard" in combined or "difficult" in combined:
        return "Hard"

    return None


STANDARD_IMPROVEMENT_AREAS = [
    "Teaching methods and explanation of concepts",
    "More practical learning and hands-on activities",
    "More assignments and practice questions",
    "More real-world examples and case studies",
    "More interactive classroom activities",
    "No improvements needed",
]


def parse_improvement_areas(raw_value) -> list[str]:
    """Parse checkbox choices from Google Forms response."""
    if not raw_value:
        return []
    text = str(raw_value).strip()
    if not text:
        return []
    found = []
    # Google Forms separates multiple checkboxes with comma + space
    parts = [p.strip() for p in text.split(",") if p.strip()]
    for p in parts:
        matched = False
        for std in STANDARD_IMPROVEMENT_AREAS:
            if p.lower() == std.lower():
                found.append(std)
                matched = True
                break
        if not matched and p:
            found.append(p)
    return found


def load_stored_improvement_areas(val) -> list[str]:
    """Load improvement areas from JSON or string."""
    if not val:
        return []
    try:
        parsed = json.loads(val)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if item]
    except (json.JSONDecodeError, TypeError):
        pass
    return [p.strip() for p in str(val).split(",") if p.strip()]

def map_feedback_headers(raw_headers: List[Any]) -> Dict[int, str]:
    """Map raw Google Sheet column indices to logical field names."""
    field_map = {}
    for idx, raw_h in enumerate(raw_headers):
        clean_h = normalize_feedback_header(raw_h)
        if not clean_h:
            continue
        if "timestamp" in clean_h:
            field_map[idx] = "timestamp"
        elif "department" in clean_h:
            field_map[idx] = "department"
        elif "academic year" in clean_h or "academic_year" in clean_h:
            field_map[idx] = "academic_year"
        elif "semester" in clean_h:
            field_map[idx] = "semester"
        elif "subject" in clean_h:
            field_map[idx] = "subject"
        elif "teaching" in clean_h:
            field_map[idx] = "teaching_quality"
        elif "communication" in clean_h:
            field_map[idx] = "communication_skills"
        elif "doubt" in clean_h or "clarification" in clean_h:
            field_map[idx] = "student_interaction"
        elif "difficulty" in clean_h and "easy" in clean_h:
            field_map[idx] = "difficulty_easy"
        elif "difficulty" in clean_h and ("moderate" in clean_h or "medium" in clean_h):
            field_map[idx] = "difficulty_moderate"
        elif "difficulty" in clean_h and ("hard" in clean_h or "difficult" in clean_h):
            field_map[idx] = "difficulty_hard"
        elif "additional suggestions" in clean_h or "suggestions" in clean_h or "suggestion" in clean_h:
            field_map[idx] = "suggestions"
        elif "what areas" in clean_h or "areas do you think should be improved" in clean_h or "improvement" in clean_h:
            field_map[idx] = "improvement_areas"
        elif "overall learning" in clean_h or "overall satisfaction" in clean_h or clean_h.startswith("overall") or clean_h == "learning experience":
            field_map[idx] = "overall_satisfaction"
        elif "difficulty" in clean_h:
            field_map[idx] = "difficulty_general"
    return field_map


def import_google_sheet_feedback(
    db: Session,
    raw_rows: Optional[List[List[Any]]] = None,
) -> Dict[str, Any]:
    """
    Import student feedback from Google Sheets into the student_feedback table.
    Prevents duplicate submissions using google_sheet_response_hash.
    """
    if raw_rows is None:
        try:
            from google_sheets_service import fetch_google_sheet_feedback_rows
            raw_rows = fetch_google_sheet_feedback_rows()
        except Exception as exc:
            raise RuntimeError(f"Could not connect to Google Sheets: {exc}")

    if not raw_rows or len(raw_rows) <= 1:
        return {
            "status": "success",
            "imported": 0,
            "skipped": 0,
            "failed": 0,
            "total_rows": 0,
            "message": "No response rows found in Google Sheet (only header row present).",
            "errors": [],
        }

    raw_headers = raw_rows[0]
    header_map = map_feedback_headers(raw_headers)

    imported = 0
    skipped = 0
    failed = 0
    errors = []

    existing_hashes = {
        h[0]
        for h in db.query(models.StudentFeedback.google_sheet_response_hash)
        .filter(models.StudentFeedback.google_sheet_response_hash.isnot(None))
        .all()
    }

    departments = db.query(models.Department).all()

    for row_idx, row_values in enumerate(raw_rows[1:], start=2):
        try:
            row_dict = {}
            for col_idx, col_name in enumerate(raw_headers):
                val = row_values[col_idx] if col_idx < len(row_values) else ""
                field_key = header_map.get(col_idx)
                if field_key:
                    row_dict[field_key] = str(val).strip() if val is not None else ""

            if not any(row_dict.values()):
                continue

            raw_ts = row_dict.get("timestamp", "")
            raw_dept = row_dict.get("department", "")
            raw_year = row_dict.get("academic_year", "")
            raw_sem = row_dict.get("semester", "")
            raw_subj = row_dict.get("subject", "")

            norm_year = None
            if raw_year:
                try:
                    norm_year = normalize_academic_year(raw_year)
                except ValueError:
                    m = re.search(r"(20\d\d)[-–/](20\d\d|\d\d)", raw_year)
                    if m:
                        start_yr = int(m.group(1))
                        end_part = m.group(2)
                        end_yr = int(end_part) if len(end_part) == 4 else int(str(start_yr)[:2] + end_part)
                        norm_year = f"{start_yr}-{end_yr}"
                    else:
                        norm_year = raw_year
            if not norm_year:
                norm_year = "2025-2026"

            norm_sem = normalize_semester(raw_sem) if raw_sem else None
            norm_dept = canonicalize_department_name(raw_dept) if raw_dept else None
            dept_name = norm_dept or raw_dept or None

            dept_id = None
            if dept_name:
                for d in departments:
                    if d.code.lower() == dept_name.lower() or d.name.lower() == dept_name.lower():
                        dept_id = d.id
                        break

            subj_name = raw_subj.strip() if raw_subj else None

            tq = parse_feedback_rating(row_dict.get("teaching_quality"))
            cs = parse_feedback_rating(row_dict.get("communication_skills"))
            si = parse_feedback_rating(row_dict.get("student_interaction"))
            os_val = parse_feedback_rating(row_dict.get("overall_satisfaction"))

            difficulty = extract_course_difficulty(
                easy_val=row_dict.get("difficulty_easy", ""),
                mod_val=row_dict.get("difficulty_moderate", ""),
                hard_val=row_dict.get("difficulty_hard", ""),
                gen_val=row_dict.get("difficulty_general", ""),
            )

            raw_improvements = row_dict.get("improvement_areas", "")
            parsed_areas = parse_improvement_areas(raw_improvements)
            improvement_areas_json = json.dumps(parsed_areas, ensure_ascii=False) if parsed_areas else None

            raw_suggestions = row_dict.get("suggestions", "").strip() or None

            # Support both old and new form responses: require at least one useful piece of feedback or valid department & year
            if not any([os_val, tq, cs, si, subj_name, difficulty, parsed_areas, raw_suggestions, dept_name]):
                continue

            parsed_ts = parse_google_forms_timestamp(raw_ts)
            canonical_ts = parsed_ts.strftime("%Y-%m-%d %H:%M:%S") if raw_ts else ""
            canonical_areas = ",".join(sorted(parsed_areas)) if parsed_areas else (raw_improvements or "").strip()
            canonical_sugg = (raw_suggestions or "").strip()

            hash_payload = (
                f"{raw_ts}|{dept_name}|{norm_year}|{norm_sem}|{subj_name}|"
                f"{tq}|{cs}|{si}|{os_val}|{difficulty}|{raw_improvements}|{raw_suggestions}"
            )
            response_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()

            alt_payload = (
                f"{canonical_ts}|{dept_name}|{norm_year}|{norm_sem}|{subj_name}|"
                f"{tq}|{cs}|{si}|{os_val}|{difficulty}|{canonical_areas}|{canonical_sugg}"
            )
            alt_hash = hashlib.sha256(alt_payload.encode("utf-8")).hexdigest()

            if response_hash in existing_hashes or alt_hash in existing_hashes:
                skipped += 1
                continue

            feedback_record = models.StudentFeedback(
                faculty_id=None,
                department_id=dept_id,
                department=dept_name,
                academic_year=norm_year,
                semester=norm_sem,
                subject=subj_name,
                teaching_quality=tq,
                communication_skills=cs,
                student_interaction=si,
                overall_satisfaction=os_val,
                overall_rating=os_val,
                course_difficulty=difficulty,
                improvement_areas=improvement_areas_json,
                suggestions=raw_suggestions,
                comment=raw_suggestions,
                comments=raw_suggestions,
                token_id=None,
                created_at=parsed_ts,
                google_sheet_response_hash=response_hash,
            )
            db.add(feedback_record)
            existing_hashes.add(response_hash)
            existing_hashes.add(alt_hash)
            imported += 1

        except Exception as row_exc:
            failed += 1
            errors.append(f"Row {row_idx}: {str(row_exc)}")

    try:
        db.commit()
    except Exception as commit_exc:
        db.rollback()
        raise RuntimeError(f"Database error while saving imported feedback: {commit_exc}")

    total_data_rows = len(raw_rows) - 1
    return {
        "status": "success",
        "imported": imported,
        "skipped": skipped,
        "failed": failed,
        "total_rows": total_data_rows,
        "message": f"Successfully processed {total_data_rows} responses: {imported} imported, {skipped} skipped (duplicates), {failed} failed.",
        "errors": errors,
    }

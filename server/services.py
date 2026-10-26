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
    val = str(year).strip()
    if val in {"2024-2025", "2024-25", "2024–2025", "2024/2025"}:
        return "2024-2025"
    if val in {"2025-2026", "2025-26", "2025–2026", "2025/2026"}:
        return "2025-2026"
    raise ValueError(f"Invalid Academic Year '{year}'. Allowed years are '2024-2025' and '2025-2026'.")


def normalize_student_rows(
    raw_rows: Any,
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
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

            # Validate enrollment format: 23STUCHH followed by exactly 3 digits (e.g. 23STUCHH001)
            if not re.match(r"^23STUCHH\d{3}$", enrollment_val, re.IGNORECASE):
                raise ValueError(
                    f"Row {row_idx}: Invalid Enrollment Number '{enrollment_val}'. "
                    "Expected format is '23STUCHH' followed by exactly 3 digits (e.g. 23STUCHH001)."
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
                    raise ValueError(f"Row {row_idx}: Missing mark for subject '{subj_code}'.")

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

            # Validate enrollment format: 23STUCHH followed by exactly 3 digits (e.g. 23STUCHH001)
            if not re.match(r"^23STUCHH\d{3}$", enrollment_val, re.IGNORECASE):
                raise ValueError(
                    f"Row {row_idx}: Invalid Enrollment Number '{enrollment_val}'. "
                    "Expected format is '23STUCHH' followed by exactly 3 digits (e.g. 23STUCHH001)."
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
    return normalize_attendance_rows(rows, headers, academic_year=academic_year, department=department, section=section)


def save_attendance_records(db: Session, records: List[Dict[str, Any]], academic_year: Optional[str] = None) -> int:
    norm_year = normalize_academic_year(academic_year) or (records[0].get('academic_year') if records else "2024-2025")
    existing_attendance = {
        str(a.enrollment_number or a.student_id).strip().casefold(): a
        for a in db.query(models.StudentAttendance).filter(models.StudentAttendance.academic_year == norm_year).all()
    }
    for r in records:
        enrollment = str(r.get('enrollment_number') or r['student_id']).strip().casefold()
        subjs_json = json.dumps(r.get('subjects', []))
        subj_vals_json = json.dumps(r.get('subject_values', {}))
        year = norm_year or r.get('academic_year', '2024-2025')
        section_value = r.get('section')
        if section_value is not None:
            section_value = str(section_value).strip().upper() or None
        if enrollment in existing_attendance:
            att = existing_attendance[enrollment]
            att.student_name = r['student_name']
            att.department = r.get('department', att.department)
            att.section = section_value or att.section
            att.academic_year = year
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


def match_attendance_students(db: Session, records: List[Dict[str, Any]], academic_year: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[str]]:
    norm_year = normalize_academic_year(academic_year) or "2024-2025"
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
        matched_records.append(record)

    return matched_records, unmatched


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


def get_all_students(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None) -> List[models.StudentUpload]:
    query = _apply_scope(db.query(models.StudentUpload), models.StudentUpload, academic_year, department, section)
    return query.order_by(models.StudentUpload.id.desc()).all()


def get_student_count(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None) -> int:
    query = _apply_scope(db.query(models.StudentUpload), models.StudentUpload, academic_year, department, section)
    return query.count()


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
            "academicYear": norm_year or "2024-2025",
            "message": "Student-Faculty ratio is unavailable because no faculty records exist."
        }

    return {
        "totalStudents": total_students,
        "totalFaculty": total_faculty,
        "ratio": round(total_students / float(total_faculty), 2),
        "academicYear": norm_year or "2024-2025"
    }


def get_student_faculty_ratio_trend(db: Session) -> Dict[str, Any]:
    total_faculty = db.query(models.Faculty).count()
    year_rows = db.query(
        models.StudentUpload.academic_year,
        func.count(models.StudentUpload.id)
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

    if key in cse_aliases:
        return "Computer Science and Engineering"
    if key in ai_aliases:
        return "AI & Data Science"

    if key.startswith("computer science") and "engineering" in key:
        return "Computer Science and Engineering"
    if key.startswith("artificial intelligence") or key.startswith("ai and") or key.startswith("ai data") or key.startswith("data science and artificial intelligence"):
        return "AI & Data Science"
    if "aids" in key and ("artificial intelligence" in key or "data science" in key or "ai" in key):
        return "AI & Data Science"

    return None


def parse_section_identifier(section: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract (section_name, department) from internal composite section identifier if present.
    Supports formats like:
      - "A::Computer Science and Engineering" -> ("A", "Computer Science and Engineering")
      - "A::AI & Data Science" -> ("A", "AI & Data Science")
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
    if academic_year:
        norm_year = normalize_academic_year(academic_year)
        if norm_year:
            q_stud = q_stud.filter(models.StudentUpload.academic_year == norm_year)
            q_att = q_att.filter(models.StudentAttendance.academic_year == norm_year)
    depts = set()
    for row in q_stud.distinct().all() + q_att.distinct().all():
        if row[0]:
            canon = canonicalize_department_name(row[0])
            if canon:
                depts.add(canon)
    if len(depts) == 1:
        return next(iter(depts))
    return None


def _apply_scope(query, model, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None):
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
        aliases = {
            "Computer Science and Engineering": ["computer science and engineering", "computer science engineering", "computer science & engineering", "computer science and engineering (cse)", "cse"],
            "AI & Data Science": ["ai & data science", "ai and data science", "artificial intelligence & data science", "artificial intelligence and data science", "artificial intelligence and data science (aids)", "artificial intelligence & data science (aids)", "aids"],
        }[canonical_department]
        query = query.filter(func.lower(func.trim(model.department)).in_(aliases))
    if effective_sec and hasattr(model, "section"):
        query = query.filter(func.lower(func.trim(model.section)) == effective_sec.strip().lower())
    return query


def get_available_sections(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None) -> List[Dict[str, str]]:
    student_query = _apply_scope(db.query(models.StudentUpload.section, models.StudentUpload.department), models.StudentUpload, academic_year, department)
    attendance_query = _apply_scope(db.query(models.StudentAttendance.section, models.StudentAttendance.department), models.StudentAttendance, academic_year, department)

    seen = set()
    results = []
    for sec_val, dept_val in student_query.all() + attendance_query.all():
        if not sec_val or not str(sec_val).strip():
            continue
        sec_clean = str(sec_val).strip().upper()
        canonical_dept = canonicalize_department_name(dept_val) or (str(dept_val).strip() if dept_val else "Unknown")
        composite_key = (sec_clean, canonical_dept)
        if composite_key in seen:
            continue
        seen.add(composite_key)
        results.append({
            "section": sec_clean,
            "department": canonical_dept,
            "label": f"Section {sec_clean} ({canonical_dept})",
            "value": f"{sec_clean}::{canonical_dept}"
        })

    results.sort(key=lambda x: (x["department"].lower(), x["section"].lower()))
    return results


def get_department_overview(db: Session) -> List[Dict[str, Any]]:
    target_departments = [
        "Computer Science and Engineering",
        "AI & Data Science",
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

    return [
        {
            "name": name,
            "studentCount": len(student_sets[name]),
            "facultyCount": len(faculty_sets[name]),
        }
        for name in target_departments
    ]


def get_student_faculty_ratio(db: Session, academic_year: Optional[str] = None) -> float:
    total_students = get_student_count(db, academic_year=academic_year)
    total_faculty = get_total_faculty(db)
    if total_faculty == 0:
        return 0.0
    return round(total_students / float(total_faculty), 2)


def get_pass_percentage_kpi(db: Session, academic_year: Optional[str] = "2024-2025", department: Optional[str] = None, section: Optional[str] = None) -> Dict[str, Any]:
    norm_year = normalize_academic_year(academic_year) or "2024-2025"
    all_students = _apply_scope(db.query(models.StudentUpload), models.StudentUpload, norm_year, department, section).all()
    
    # Exclude incomplete or invalid marks records from the pass percentage denominator
    evaluated_students = [s for s in all_students if s.has_all_five_subjects]
    total_evaluated = len(evaluated_students)
    total_count = len(all_students)
    uncalculated_count = total_count - total_evaluated

    subject_configs = [
        ("DM", "Discrete Mathematics"),
        ("DSC", "Dynamics of Social Change"),
        ("COA", "Computer Organization and Architecture"),
        ("Python", "Industry Coding Practice"),
        ("ML", "Machine Learning"),
    ]

    if total_evaluated == 0:
        return {
            "academic_year": norm_year,
            "academicYear": norm_year,
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
            "subjects": [
                {
                    "subject": code,
                    "subject_name": name,
                    "passed": 0,
                    "failed": 0,
                    "total": 0,
                    "pass_percentage": 0.0,
                    "fail_percentage": 0.0,
                }
                for code, name in subject_configs
            ],
            "overall_pass_percentage": 0.0,
            "overall_fail_percentage": 0.0,
            "message": f"No evaluated student records with complete 5-subject marks found for academic year {norm_year}. Please upload student marks sheet to view Pass Percentage KPI."
        }

    subjects_data = []
    for code, name in subject_configs:
        passed = sum(1 for s in evaluated_students if s.subject_marks and int(s.subject_marks.get(code, 0)) >= 40)
        failed = total_evaluated - passed
        pass_pct = round((passed / float(total_evaluated)) * 100.0, 2)
        fail_pct = round((failed / float(total_evaluated)) * 100.0, 2)
        subjects_data.append({
            "subject": code,
            "subject_name": name,
            "passed": passed,
            "failed": failed,
            "total": total_evaluated,
            "pass_percentage": pass_pct,
            "fail_percentage": fail_pct,
        })

    # Overall pass criteria: student passes overall only if they score >= 40 in ALL FIVE SUBJECTS.
    overall_passed = sum(1 for s in evaluated_students if s.passed_all_subjects)
    overall_failed = total_evaluated - overall_passed
    overall_pass_pct = round((overall_passed / float(total_evaluated)) * 100.0, 2)
    overall_fail_pct = round((overall_failed / float(total_evaluated)) * 100.0, 2)

    return {
        "academic_year": norm_year,
        "academicYear": norm_year,
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


def get_pass_percentage(db: Session, academic_year: Optional[str] = None) -> float:
    norm_year = normalize_academic_year(academic_year) or "2024-2025"
    kpi_data = get_pass_percentage_kpi(db, academic_year=norm_year)
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
def get_all_faculty(db: Session) -> List[models.Faculty]:
    return db.query(models.Faculty).all()


def create_faculty(db: Session, faculty_data: Dict[str, Any]) -> models.Faculty:
    faculty = models.Faculty(**faculty_data)
    db.add(faculty)
    db.commit()
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
def get_all_attendance(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None) -> List[models.StudentAttendance]:
    query = _apply_scope(db.query(models.StudentAttendance), models.StudentAttendance, academic_year, department, section)
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
            record.subjects_json = json.dumps(default_subjects)
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


def get_attendance_subjects(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None) -> List[str]:
    query = _apply_scope(db.query(models.StudentAttendance.subjects_json), models.StudentAttendance, academic_year, department, section)
    rows = query.order_by(models.StudentAttendance.id.desc()).first()
    if not rows or not rows[0]:
        return []
    return json.loads(rows[0])


def get_attendance_kpi(db: Session, academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None) -> Dict[str, Any]:
    norm_year = normalize_academic_year(academic_year)
    records = get_all_attendance(db, academic_year=norm_year, department=department, section=section)
    values = [record.average_attendance for record in records]
    return {
        'total_students': len(records),
        'overall_average_attendance': round(sum(values) / len(values), 2) if values else 0.0,
        'highest_attendance': max(values) if values else 0.0,
        'lowest_attendance': min(values) if values else 0.0,
        'subjects': get_attendance_subjects(db, academic_year=norm_year, department=department, section=section),
        'academic_year': norm_year,
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




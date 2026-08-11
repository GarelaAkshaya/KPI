import io
import math
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
import models


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


def normalize_student_rows(raw_rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], bool]:
    normalized_records = []
    has_invalid_row = False

    for row in raw_rows:
        # Match keys case-insensitively / with fallback column names
        keys_map = {str(k).strip().lower(): v for k, v in row.items()}

        student_id_val = (
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

        normalized_records.append({
            "studentId": student_id,
            "studentName": student_name,
            "totalMarks": total_marks,
            "percentage": percentage,
        })

    return normalized_records, has_invalid_row


def parse_excel_file(file_contents: bytes) -> Tuple[List[Dict[str, Any]], bool]:
    df = pd.read_excel(io.BytesIO(file_contents))
    # Replace NaN with empty string
    df = df.where(pd.notnull(df), None)
    rows = df.to_dict(orient='records')
    return normalize_student_rows(rows)


def save_student_records(db: Session, records: List[Dict[str, Any]]) -> int:
    db_records = [
        models.StudentUpload(
            studentId=r['studentId'],
            studentName=r['studentName'],
            totalMarks=r['totalMarks'],
            percentage=r['percentage']
        )
        for r in records
    ]
    db.add_all(db_records)
    db.commit()
    return len(records)


def get_all_students(db: Session) -> List[models.StudentUpload]:
    return db.query(models.StudentUpload).order_by(models.StudentUpload.id.desc()).all()


def get_student_count(db: Session) -> int:
    return db.query(models.StudentUpload).count()


def get_total_faculty(db: Session) -> int:
    return db.query(models.Faculty).count()


def get_department_count(db: Session) -> int:
    dept_table_count = db.query(models.Department).count()
    if dept_table_count > 0:
        return dept_table_count
    
    # Fallback to distinct departments across existing tables
    faculty_depts = db.query(distinct(models.Faculty.department)).all()
    lab_depts = db.query(distinct(models.LaboratoryUtilization.department)).all()
    attendance_depts = db.query(distinct(models.StudentAttendance.department)).all()
    
    all_depts = set(
        [d[0] for d in faculty_depts if d[0]] +
        [d[0] for d in lab_depts if d[0]] +
        [d[0] for d in attendance_depts if d[0]]
    )
    return len(all_depts) if len(all_depts) > 0 else 0


def get_student_faculty_ratio(db: Session) -> float:
    total_students = get_student_count(db)
    total_faculty = get_total_faculty(db)
    if total_faculty == 0:
        return 0.0
    return round(total_students / float(total_faculty), 2)


def get_pass_percentage(db: Session) -> float:
    total_students = db.query(models.StudentUpload).count()
    if total_students == 0:
        return 0.0
    passed = db.query(models.StudentUpload).filter(models.StudentUpload.percentage >= 40.0).count()
    return round((passed / float(total_students)) * 100.0, 2)


def get_average_student_marks(db: Session) -> float:
    avg_marks = db.query(func.avg(models.StudentUpload.totalMarks)).scalar()
    return round(float(avg_marks), 2) if avg_marks is not None else 0.0


def get_student_attendance_percentage(db: Session) -> float:
    avg_att = db.query(func.avg(models.StudentAttendance.attendance_percentage)).scalar()
    if avg_att is not None:
        return round(float(avg_att), 2)
    
    # Calculate sum of attended vs total classes if attendance_percentage is empty
    total_cls = db.query(func.sum(models.StudentAttendance.total_classes)).scalar()
    att_cls = db.query(func.sum(models.StudentAttendance.attended_classes)).scalar()
    if total_cls and total_cls > 0:
        return round((float(att_cls or 0) / float(total_cls)) * 100.0, 2)
    return 0.0


def get_laboratory_utilization_percentage(db: Session) -> float:
    labs = db.query(models.LaboratoryUtilization).all()
    if not labs:
        return 0.0
    utilizations = []
    for lab in labs:
        if lab.capacity and lab.capacity > 0 and lab.students_present is not None:
            utilizations.append((lab.students_present / float(lab.capacity)) * 100.0)
    if not utilizations:
        return 0.0
    return round(sum(utilizations) / len(utilizations), 2)


def get_kpi_summary(db: Session) -> Dict[str, Any]:
    return {
        "total_students": get_student_count(db),
        "total_faculty": get_total_faculty(db),
        "number_of_departments": get_department_count(db),
        "student_faculty_ratio": get_student_faculty_ratio(db),
        "pass_percentage": get_pass_percentage(db),
        "average_student_marks": get_average_student_marks(db),
        "student_attendance_percentage": get_student_attendance_percentage(db),
        "laboratory_utilization_percentage": get_laboratory_utilization_percentage(db)
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
def get_all_attendance(db: Session) -> List[models.StudentAttendance]:
    return db.query(models.StudentAttendance).all()


def create_attendance(db: Session, att_data: Dict[str, Any]) -> models.StudentAttendance:
    if att_data.get("attendance_percentage") is None and att_data.get("total_classes", 0) > 0:
        total = att_data["total_classes"]
        attended = att_data.get("attended_classes", 0)
        att_data["attendance_percentage"] = round((attended / float(total)) * 100.0, 2)
    
    attendance = models.StudentAttendance(**att_data)
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


# Laboratory Utilization CRUD Services
def get_all_lab_utilizations(db: Session) -> List[models.LaboratoryUtilization]:
    return db.query(models.LaboratoryUtilization).all()


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
            models.Faculty(faculty_id="FAC001", name="Dr. A. Sharma", department="Computer Science & Engineering", experience=12.5, designation="Professor & HOD", email="asharma@ifhe.edu"),
            models.Faculty(faculty_id="FAC002", name="Dr. R. Verma", department="Electronics & Communication Engineering", experience=10.0, designation="Associate Professor", email="rverma@ifhe.edu"),
            models.Faculty(faculty_id="FAC003", name="Dr. K. Rao", department="Mechanical Engineering", experience=15.0, designation="Professor", email="krao@ifhe.edu"),
            models.Faculty(faculty_id="FAC004", name="Prof. S. Nair", department="Electrical & Electronics Engineering", experience=8.0, designation="Assistant Professor", email="snair@ifhe.edu"),
            models.Faculty(faculty_id="FAC005", name="Dr. P. Gupta", department="Biotechnology", experience=11.2, designation="Associate Professor", email="pgupta@ifhe.edu"),
            models.Faculty(faculty_id="FAC006", name="Prof. M. Reddy", department="Civil Engineering", experience=6.5, designation="Assistant Professor", email="mreddy@ifhe.edu"),
            models.Faculty(faculty_id="FAC007", name="Dr. V. Kapoor", department="Management Studies", experience=14.0, designation="Professor", email="vkapoor@ifhe.edu"),
            models.Faculty(faculty_id="FAC008", name="Dr. N. Joshi", department="School of Law", experience=9.0, designation="Associate Professor", email="njoshi@ifhe.edu")
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

    # Seed Student Attendance
    if db.query(models.StudentAttendance).count() == 0:
        attendance_records = [
            models.StudentAttendance(student_id="STU101", student_name="Aarav Sharma", department="Computer Science & Engineering", academic_year="2024-25", total_classes=100, attended_classes=88, attendance_percentage=88.0),
            models.StudentAttendance(student_id="STU102", student_name="Ananya Rao", department="Electronics & Communication Engineering", academic_year="2024-25", total_classes=100, attended_classes=92, attendance_percentage=92.0),
            models.StudentAttendance(student_id="STU103", student_name="Rohan Verma", department="Mechanical Engineering", academic_year="2024-25", total_classes=100, attended_classes=76, attendance_percentage=76.0),
            models.StudentAttendance(student_id="STU104", student_name="Priya Patel", department="Biotechnology", academic_year="2024-25", total_classes=100, attended_classes=85, attendance_percentage=85.0),
            models.StudentAttendance(student_id="STU105", student_name="Vikram Singh", department="Civil Engineering", academic_year="2024-25", total_classes=100, attended_classes=90, attendance_percentage=90.0)
        ]
        db.add_all(attendance_records)
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

    # Seed Sample Students if student_uploads is empty
    if db.query(models.StudentUpload).count() == 0:
        students = [
            models.StudentUpload(studentId="STU101", studentName="Aarav Sharma", totalMarks=510, percentage=85.0),
            models.StudentUpload(studentId="STU102", studentName="Ananya Rao", totalMarks=540, percentage=90.0),
            models.StudentUpload(studentId="STU103", studentName="Rohan Verma", totalMarks=432, percentage=72.0),
            models.StudentUpload(studentId="STU104", studentName="Priya Patel", totalMarks=468, percentage=78.0),
            models.StudentUpload(studentId="STU105", studentName="Vikram Singh", totalMarks=492, percentage=82.0)
        ]
        db.add_all(students)
        db.commit()


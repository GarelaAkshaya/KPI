import csv
import io
import os
import re
import secrets
import threading
import time
import math
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, File, UploadFile, Form, HTTPException, Request, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

import database
import models
import schemas
import services

VALID_ACADEMIC_YEARS = {"2024-2025", "2025-2026"}
VALID_SEMESTERS = {f"Semester {i}" for i in range(1, 9)}

# Create database tables automatically and apply any missing column migrations
database.init_db()

# Seed default initial data if tables are empty and initialize the admin account
with database.SessionLocal() as db_session:
    services.seed_initial_data(db_session)
    services.initialize_admin_account(db_session)
    services.seed_aids_faculty(db_session)

app = FastAPI(title="IFHE KPI API", version="1.0.0")
security = HTTPBearer(auto_error=False)

# Configure CORS for React frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=PlainTextResponse)
def root():
    return "IFHE KPI API"


def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(database.get_db),
) -> models.AdminUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    try:
        username = services.verify_access_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired authentication token.")

    admin = db.query(models.AdminUser).filter(models.AdminUser.username == username, models.AdminUser.is_active == 1).first()
    if admin is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials.")
    return admin


@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login_admin(payload: schemas.AdminLoginRequest, db: Session = Depends(database.get_db)):
    user = services.authenticate_admin(db, payload.username.strip(), payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    token = services.create_access_token(user.username)
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
    }


@app.get("/api/stats", response_model=schemas.StatsResponse)
def get_stats(
    academic_year: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    try:
        norm_year = services.normalize_academic_year(academic_year)
        db_student_count = services.get_student_count(db, academic_year=norm_year)
        db_faculty_count = services.get_total_faculty(db)
        db_dept_count = services.get_department_count(db)
        kpi_count = len(services.get_all_kpis(db))

        return {
            "totalStudents": db_student_count,
            "totalFaculty": db_faculty_count,
            "totalDepartments": db_dept_count,
            "activeKPIs": kpi_count if kpi_count > 0 else 5,
            "isLive": db_student_count > 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stats: {str(e)}"
        )


@app.get("/api/admin/feedback/summary", response_model=schemas.StudentFeedbackSummaryResponse)
@app.get("/api/feedback/summary", response_model=schemas.StudentFeedbackSummaryResponse)
def get_student_feedback_summary(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    semester: Optional[str] = None,
    subject: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    """Return aggregate feedback only; individual submissions are not exposed."""
    sec_name, sec_dept = services.parse_section_identifier(section)
    effective_dept = department or sec_dept
    effective_sec = sec_name if sec_name is not None else section

    # Normalize academic year if supplied and not 'all'
    norm_year = None
    if academic_year and academic_year.strip() and academic_year.strip().lower() not in {"all", "all years", "all_years"}:
        try:
            norm_year = services.normalize_academic_year(academic_year)
        except ValueError:
            norm_year = academic_year.strip()

    # Base query
    query = db.query(models.StudentFeedback)

    all_responses = db.query(models.StudentFeedback).count()
    unattributed_responses = db.query(models.StudentFeedback).filter(
        or_(
            models.StudentFeedback.academic_year.is_(None),
            func.trim(models.StudentFeedback.academic_year) == "",
        )
    ).count()

    # 1. Year filter
    if norm_year:
        query = query.filter(
            or_(
                models.StudentFeedback.academic_year == norm_year,
                models.StudentFeedback.academic_year == norm_year.replace("-", " - "),
                models.StudentFeedback.academic_year == norm_year.replace("-", "–"),
                models.StudentFeedback.academic_year == norm_year.replace("-", " – "),
                func.replace(func.replace(models.StudentFeedback.academic_year, " ", ""), "–", "-") == norm_year,
            )
        )

    # 2. Department filter
    selected_department = None
    if effective_dept and effective_dept.strip() and effective_dept.strip().lower() not in {"all", "all departments", "all_departments"}:
        selected_department = effective_dept.strip()
        dept_canon = services.canonicalize_department_name(selected_department)
        dept_conds = [
            func.lower(func.trim(models.StudentFeedback.department)) == selected_department.lower(),
        ]
        if dept_canon:
            dept_conds.append(func.lower(func.trim(models.StudentFeedback.department)) == dept_canon.lower())

        # Also match standard department abbreviations and naming variations
        sd_upper = selected_department.upper()
        if sd_upper in {"CSE", "COMPUTER SCIENCE AND ENGINEERING", "COMPUTER SCIENCE & ENGINEERING"}:
            dept_conds.extend([
                func.lower(func.trim(models.StudentFeedback.department)) == "cse",
                func.lower(func.trim(models.StudentFeedback.department)) == "computer science and engineering",
                func.lower(func.trim(models.StudentFeedback.department)) == "computer science & engineering",
            ])
        elif sd_upper in {"AIDS", "AI & DATA SCIENCE", "AI AND DATA SCIENCE", "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE"}:
            dept_conds.extend([
                func.lower(func.trim(models.StudentFeedback.department)) == "aids",
                func.lower(func.trim(models.StudentFeedback.department)) == "ai & data science",
                func.lower(func.trim(models.StudentFeedback.department)) == "ai and data science",
                func.lower(func.trim(models.StudentFeedback.department)) == "artificial intelligence and data science",
            ])
        elif sd_upper in {"BCA", "BACHELOR OF COMPUTER APPLICATIONS"}:
            dept_conds.extend([
                func.lower(func.trim(models.StudentFeedback.department)) == "bca",
                func.lower(func.trim(models.StudentFeedback.department)) == "bachelor of computer applications",
            ])

        dept_rec = db.query(models.Department).filter(
            or_(
                func.lower(func.trim(models.Department.name)) == selected_department.lower(),
                func.lower(func.trim(models.Department.code)) == selected_department.lower(),
            )
        ).first()
        if dept_rec:
            dept_conds.extend([
                models.StudentFeedback.department_id == dept_rec.id,
                func.lower(func.trim(models.StudentFeedback.department)) == dept_rec.code.lower(),
                func.lower(func.trim(models.StudentFeedback.department)) == dept_rec.name.lower(),
            ])
        query = query.filter(or_(*dept_conds))

    # 3. Semester filter
    if semester and semester.strip() and semester.strip().lower() not in {"all", "all semesters", "all_semesters"}:
        sem_clean = semester.strip()
        norm_sem = services.normalize_semester(sem_clean)
        digit_match = re.search(r"\d+", sem_clean)
        digit = digit_match.group(0) if digit_match else None
        sem_conds = [
            func.lower(func.trim(models.StudentFeedback.semester)) == sem_clean.lower(),
            func.lower(func.trim(models.StudentFeedback.semester)) == (norm_sem or "").lower(),
        ]
        if digit:
            sem_conds.extend([
                func.trim(models.StudentFeedback.semester) == digit,
                func.lower(func.trim(models.StudentFeedback.semester)) == f"semester {digit}",
                func.lower(func.trim(models.StudentFeedback.semester)) == f"sem {digit}",
            ])
        query = query.filter(or_(*sem_conds))

    # 4. Subject filter
    if subject and subject.strip() and subject.strip().lower() not in {"all", "all subjects", "all_subjects"}:
        query = query.filter(func.lower(func.trim(models.StudentFeedback.subject)) == subject.strip().lower())

    fields = (
        "teaching_quality",
        "communication_skills",
        "student_interaction",
        "overall_satisfaction",
        "course_content",
        "learning_resources",
        "faculty_support",
        "subject_knowledge",
        "overall_rating",
    )
    records = query.order_by(models.StudentFeedback.created_at.asc()).all()
    rows = [tuple(getattr(record, field) for field in fields) for record in records]
    distributions = {field: {rating: 0 for rating in range(1, 6)} for field in fields}
    totals = {field: 0 for field in fields}
    rating_counts = {field: 0 for field in fields}
    for row in rows:
        for field, rating in zip(fields, row):
            if isinstance(rating, int) and 1 <= rating <= 10:
                totals[field] += rating
                rating_counts[field] += 1
                if 1 <= rating <= 5:
                    distributions[field][rating] += 1

    averages = {
        field: round(totals[field] / rating_counts[field], 2) if rating_counts[field] else None
        for field in fields
    }

    # Course difficulty counts
    difficulty_counts = {"Easy": 0, "Moderate": 0, "Hard": 0}
    for record in records:
        diff = (record.course_difficulty or "").strip().capitalize()
        if diff in difficulty_counts:
            difficulty_counts[diff] += 1
        elif "easy" in diff.lower():
            difficulty_counts["Easy"] += 1
        elif "mod" in diff.lower():
            difficulty_counts["Moderate"] += 1
        elif "hard" in diff.lower() or "diff" in diff.lower():
            difficulty_counts["Hard"] += 1

    by_day = {}
    for record in records:
        if not record.created_at:
            continue
        day = record.created_at.date().isoformat()
        bucket = by_day.setdefault(
            day,
            {"responses": 0, **{field: 0 for field in fields}, **{f"{field}_count": 0 for field in fields}},
        )
        bucket["responses"] += 1
        for field in fields:
            rating = getattr(record, field)
            if isinstance(rating, int) and 1 <= rating <= 10:
                bucket[field] += rating
                bucket[f"{field}_count"] += 1

    timeline = [
        {"date": day, "responses": bucket["responses"], **{
            field: (
                round(bucket[field] / bucket[f"{field}_count"], 2)
                if bucket[f"{field}_count"] else None
            )
            for field in fields
        }}
        for day, bucket in sorted(by_day.items())
    ]

    # Overall Learning Experience metrics
    overall_ratings = [
        r.overall_satisfaction
        for r in records
        if isinstance(r.overall_satisfaction, int) and 1 <= r.overall_satisfaction <= 5
    ]
    avg_overall = round(sum(overall_ratings) / len(overall_ratings), 2) if overall_ratings else None
    rating_dist = {i: 0 for i in range(1, 6)}
    for r in overall_ratings:
        rating_dist[r] += 1

    # Most frequently selected improvement areas
    area_counts = {area: 0 for area in services.STANDARD_IMPROVEMENT_AREAS}
    for record in records:
        areas = services.load_stored_improvement_areas(record.improvement_areas)
        for a in areas:
            if a in area_counts:
                area_counts[a] += 1
            else:
                area_counts[a] = area_counts.get(a, 0) + 1

    total_count = len(records)
    improvement_areas_summary = [
        {
            "area": area,
            "count": count,
            "percentage": round((count / total_count) * 100, 1) if total_count else 0.0,
        }
        for area, count in sorted(area_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    # Optional student suggestions
    student_suggestions = []
    for record in records:
        text = (record.suggestions or record.comment or record.comments or "").strip()
        if text:
            student_suggestions.append({
                "id": record.id,
                "suggestion": text,
                "department": record.department,
                "semester": record.semester,
                "academic_year": record.academic_year,
                "rating": record.overall_satisfaction,
                "created_at": record.created_at.strftime("%d %b %Y, %H:%M") if record.created_at else None,
            })

    # Dynamic filter lists
    all_fb = db.query(models.StudentFeedback).all()
    available_years = sorted(list({f.academic_year for f in all_fb if f.academic_year and f.academic_year.strip()}), reverse=True)
    for yr in ["2025-2026", "2024-2025"]:
        if yr not in available_years:
            available_years.append(yr)

    dept_set = set()
    for f in all_fb:
        if f.department and f.department.strip():
            d = f.department.strip()
            if d.lower() in {"computer science and engineering", "cse"}:
                dept_set.add("CSE")
            elif d.lower() in {"ai & data science", "ai and data science", "aids"}:
                dept_set.add("AI & Data Science")
            elif d.lower() in {"bca", "bachelor of computer applications"}:
                dept_set.add("BCA")
            else:
                dept_set.add(d)
    dept_set.update(["CSE", "AI & Data Science"])
    available_depts = sorted(list(dept_set))

    sem_set = {f.semester for f in all_fb if f.semester and f.semester.strip()}
    sem_set.update(["Semester 1", "Semester 2", "Semester 3", "Semester 4"])
    available_sems = sorted(list(sem_set))

    available_subjs = sorted(list({f.subject for f in all_fb if f.subject and f.subject.strip()}))

    return {
        "academic_year": norm_year or academic_year,
        "department": selected_department,
        "total_responses": len(rows),
        "all_responses": all_responses,
        "unattributed_responses": unattributed_responses,
        "other_year_responses": max(0, all_responses - len(rows) - unattributed_responses),
        "averages": averages,
        "rating_distributions": distributions,
        "timeline": timeline,
        "difficulty_distribution": difficulty_counts,
        "available_departments": available_depts,
        "available_academic_years": available_years,
        "available_semesters": available_sems,
        "available_subjects": available_subjs,
        "average_overall_satisfaction": avg_overall,
        "rating_distribution": rating_dist,
        "improvement_areas_summary": improvement_areas_summary,
        "student_suggestions": student_suggestions,
    }


@app.post("/api/admin/feedback/import-google-sheet", response_model=schemas.GoogleSheetImportSummary)
@app.post("/api/feedback/import-google-sheet", response_model=schemas.GoogleSheetImportSummary)
def import_google_sheet_feedback_endpoint(
    db: Session = Depends(database.get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    """Admin-only endpoint to import student feedback responses from Google Sheets."""
    try:
        summary = services.import_google_sheet_feedback(db)
        return summary
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import feedback from Google Sheets: {str(exc)}",
        )


@app.get("/api/kpis/summary", response_model=schemas.KPISummaryResponse)
def get_kpi_summary(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    """Fetch all calculated KPI values for the dashboard."""
    try:
        norm_year = services.normalize_academic_year(academic_year)
        summary = services.get_kpi_summary(db, academic_year=norm_year, department=department, section=section)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate KPI summary: {str(e)}"
        )


@app.get("/api/kpis/student-faculty-ratio", response_model=schemas.StudentFacultyRatioResponse)
def get_student_faculty_ratio(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    try:
        norm_year = services.normalize_academic_year(academic_year)
        return services.get_student_faculty_ratio_data(db, academic_year=norm_year, department=department, section=section)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate student-faculty ratio: {str(e)}"
        )


@app.get("/api/kpis/student-faculty-ratio/trend", response_model=schemas.StudentFacultyRatioTrendResponse)
def get_student_faculty_ratio_trend(
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    try:
        return services.get_student_faculty_ratio_trend(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate student-faculty ratio trend: {str(e)}"
        )


@app.get("/api/kpis/pass-percentage", response_model=schemas.PassPercentageKPIResponse)
def get_pass_percentage_kpi(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    semester: Optional[str] = None,
    subject: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    try:
        norm_year = services.normalize_academic_year(academic_year) or "2024-2025"
        return services.get_pass_percentage_kpi(
            db,
            academic_year=norm_year,
            department=department,
            section=section,
            semester=semester,
            subject=subject,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate pass percentage KPI: {str(e)}"
        )


@app.get("/api/marks/subjects", response_model=List[str])
def get_marks_subjects(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    semester: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    try:
        return services.get_marks_subjects(
            db=db,
            academic_year=academic_year,
            department=department,
            section=section,
            semester=semester,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subjects: {str(e)}"
        )


@app.get("/api/filters/subjects", response_model=List[str])
def get_filters_subjects(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    semester: Optional[str] = None,
    db: Session = Depends(database.get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    return get_marks_subjects(
        academic_year=academic_year,
        department=department,
        section=section,
        semester=semester,
        db=db,
        _=admin,
    )


# Stored KPI Endpoints
@app.get("/api/kpis", response_model=List[schemas.KPISchema])
def get_kpis(db: Session = Depends(database.get_db), _: models.AdminUser = Depends(get_current_admin)):
    try:
        return services.get_all_kpis(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KPIs."
        )


@app.post("/api/kpis", response_model=schemas.KPISchema, status_code=status.HTTP_201_CREATED)
def create_kpi(kpi: schemas.KPICreate, db: Session = Depends(database.get_db), _: models.AdminUser = Depends(get_current_admin)):
    try:
        return services.create_kpi(db, kpi.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create KPI record: {str(e)}"
        )


# Faculty Endpoints
@app.get("/api/faculty", response_model=List[schemas.FacultySchema])
def get_faculty(
    department: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    try:
        return services.get_all_faculty(db, department=department)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve faculty records."
        )


@app.post("/api/faculty/import-ai-ds")
def import_ai_ds_faculty(db: Session = Depends(database.get_db), _: models.AdminUser = Depends(get_current_admin)):
    try:
        added_count = services.seed_aids_faculty(db)
        return {
            "added_count": added_count,
            "total_count": services.get_total_faculty(db, department="AI & Data Science"),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import AI & Data Science faculty: {str(e)}"
        )


@app.post("/api/faculty", response_model=schemas.FacultySchema, status_code=status.HTTP_201_CREATED)
def create_faculty(faculty: schemas.FacultyCreate, db: Session = Depends(database.get_db), _: models.AdminUser = Depends(get_current_admin)):
    try:
        return services.create_faculty(db, faculty.model_dump())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create faculty record: {str(e)}"
        )


# Department Endpoints
@app.get("/api/departments", response_model=List[schemas.DepartmentSchema])
def get_departments(db: Session = Depends(database.get_db), _: models.AdminUser = Depends(get_current_admin)):
    try:
        return services.get_all_departments(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve departments."
        )


@app.get("/api/departments/overview", response_model=List[schemas.DepartmentOverviewItem])
def get_department_overview(db: Session = Depends(database.get_db), _: models.AdminUser = Depends(get_current_admin)):
    try:
        return services.get_department_overview(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve department overview: {str(e)}"
        )


@app.get("/api/filters/sections", response_model=List[schemas.SectionFilterOption])
def get_filter_sections(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    semester: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    norm_year = None
    if academic_year:
        try:
            norm_year = services.normalize_academic_year(academic_year)
        except ValueError:
            norm_year = None
    return services.get_available_sections(db, academic_year=norm_year, department=department, semester=semester)


@app.post("/api/departments", response_model=schemas.DepartmentSchema, status_code=status.HTTP_201_CREATED)
def create_department(dept: schemas.DepartmentCreate, db: Session = Depends(database.get_db), _: models.AdminUser = Depends(get_current_admin)):
    try:
        return services.create_department(db, dept.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create department: {str(e)}"
        )


# Student Attendance Endpoints
@app.get("/api/attendance", response_model=List[schemas.StudentAttendanceSchema])
def get_attendance(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    semester: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    try:
        norm_year = services.normalize_academic_year(academic_year)
        return services.get_all_attendance(db, academic_year=norm_year, department=department, section=section, semester=semester)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve student attendance records."
        )


@app.get("/api/attendance/subjects", response_model=List[str])
def get_attendance_subjects(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    semester: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    try:
        norm_year = services.normalize_academic_year(academic_year)
        return services.get_attendance_subjects(db, academic_year=norm_year, department=department, section=section, semester=semester)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve attendance subjects: {str(e)}")


@app.get("/api/attendance/kpi")
def get_attendance_kpi(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    semester: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    try:
        norm_year = services.normalize_academic_year(academic_year)
        return services.get_attendance_kpi(db, academic_year=norm_year, department=department, section=section, semester=semester)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve attendance KPI: {str(e)}")


@app.post("/api/attendance", response_model=schemas.StudentAttendanceSchema, status_code=status.HTTP_201_CREATED)
def create_attendance(att: schemas.StudentAttendanceCreate, db: Session = Depends(database.get_db), _: models.AdminUser = Depends(get_current_admin)):
    try:
        return services.create_attendance(db, att.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create attendance record: {str(e)}"
        )


# Laboratory Utilization Endpoints
@app.get("/api/lab-utilization", response_model=List[schemas.LaboratoryUtilizationSchema])
def get_lab_utilization(academic_year: Optional[str] = None, department: Optional[str] = None, section: Optional[str] = None, db: Session = Depends(database.get_db), _: models.AdminUser = Depends(get_current_admin)):
    try:
        return services.get_all_lab_utilizations(db, academic_year=services.normalize_academic_year(academic_year), department=department, section=section)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve laboratory utilization records."
        )


@app.post("/api/lab-utilization", response_model=schemas.LaboratoryUtilizationSchema, status_code=status.HTTP_201_CREATED)
def create_lab_utilization(lab: schemas.LaboratoryUtilizationCreate, db: Session = Depends(database.get_db), _: models.AdminUser = Depends(get_current_admin)):
    try:
        return services.create_lab_utilization(db, lab.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create laboratory utilization record: {str(e)}"
        )


@app.post("/api/preview-student-marks", response_model=schemas.WorkbookPreviewResponse)
async def preview_student_marks(
    file: UploadFile = File(...),
    academic_year: Optional[str] = Form(None),
    academicYear: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    section: Optional[str] = Form(None),
    semester: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    subject_name: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    selected_year = (academic_year or academicYear or "").strip()
    selected_department = (department or "").strip()
    selected_section = (section or "").strip()
    selected_semester = (semester or "").strip()
    selected_subject = (subject or subject_name or "").strip()

    if not selected_year:
        raise HTTPException(status_code=400, detail="Academic Year is required. Please select an academic year.")
    if not selected_department:
        raise HTTPException(status_code=400, detail="Department is required.")
    if not selected_section:
        raise HTTPException(status_code=400, detail="Section is required.")
    if not selected_semester:
        raise HTTPException(status_code=400, detail="Semester is required. Please select Semester 1, 2, 3 or 4.")
    if not selected_subject:
        raise HTTPException(status_code=400, detail="Subject Name is required. Please type the subject name.")
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Please select an Excel file.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        preview_data = services.parse_semester_workbook_for_preview(
            file_contents=contents,
            file_name=file.filename,
            academic_year=selected_year,
            department=selected_department,
            section=selected_section,
            semester=selected_semester,
            subject=selected_subject,
        )
        return preview_data
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to preview workbook: {str(e)}")


@app.get("/api/semester-config")
def get_semester_config(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    norm_year = services.normalize_academic_year(academic_year) or "2024-2025"
    norm_dept = department or "Artificial Intelligence and Data Science (AIDS)"
    norm_sec = section or "A"

    return {
        "academic_year": norm_year,
        "department": norm_dept,
        "section": norm_sec,
        "semesters": {
            "Semester 1": services.get_configured_subjects_for_semester(norm_dept, norm_sec, norm_year, "Semester 1"),
            "Semester 2": services.get_configured_subjects_for_semester(norm_dept, norm_sec, norm_year, "Semester 2"),
            "Semester 3": services.get_configured_subjects_for_semester(norm_dept, norm_sec, norm_year, "Semester 3"),
            "Semester 4": services.get_configured_subjects_for_semester(norm_dept, norm_sec, norm_year, "Semester 4"),
        }
    }


@app.post("/api/upload-students", response_model=schemas.UploadResponse)
async def upload_students(
    file: UploadFile = File(...),
    academic_year: Optional[str] = Form(None),
    academicYear: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    section: Optional[str] = Form(None),
    semester: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    subject_name: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    selected_year = (academic_year or academicYear or "").strip()
    selected_department = (department or "").strip()
    selected_section = (section or "").strip()
    selected_semester = (semester or "").strip()
    selected_subject = (subject or subject_name or "").strip()

    if not selected_year:
        return JSONResponse(
            status_code=400,
            content={"message": "Academic Year is required. Please select an academic year."}
        )

    try:
        norm_year = services.normalize_academic_year(selected_year)
    except ValueError as ve:
        return JSONResponse(
            status_code=400,
            content={"message": str(ve)}
        )
    if norm_year not in VALID_ACADEMIC_YEARS:
        return JSONResponse(
            status_code=400,
            content={"message": "Invalid Academic Year. Only '2024-2025' and '2025-2026' are accepted."}
        )

    if not selected_department:
        return JSONResponse(
            status_code=400,
            content={"message": "Department is required. Please select a department."}
        )

    if not selected_section:
        return JSONResponse(
            status_code=400,
            content={"message": "Section is required. Please enter a section."}
        )

    if not selected_semester:
        return JSONResponse(
            status_code=400,
            content={"message": "Semester is required. Please select a semester."}
        )

    if not selected_subject:
        return JSONResponse(
            status_code=400,
            content={"message": "Subject Name is required. Please type the subject name."}
        )

    if not file or not file.filename:
        return JSONResponse(
            status_code=400,
            content={"message": "Please upload a file."}
        )

    try:
        contents = await file.read()
        if not contents:
            return JSONResponse(
                status_code=400,
                content={"message": "Uploaded file is empty."}
            )

        # Multi-worksheet or single-subject semester workbook upload
        if selected_semester or selected_subject or services.is_semester_workbook(contents):
            target_sem = selected_semester or "Semester 1"
            preview_data = services.parse_semester_workbook_for_preview(
                file_contents=contents,
                file_name=file.filename,
                academic_year=norm_year,
                department=selected_department,
                section=selected_section,
                semester=target_sem,
                subject=selected_subject,
            )
            if not preview_data.get("valid"):
                return JSONResponse(
                    status_code=400,
                    content={
                        "message": "Validation failed: " + "; ".join(preview_data.get("errors", [])[:5]),
                        "errors": preview_data.get("errors", [])
                    }
                )

            result = services.save_semester_marks(
                db=db,
                workbook_data=preview_data,
                academic_year=norm_year,
                department=selected_department,
                section=selected_section,
                semester=target_sem,
            )
            return {
                "message": result["message"],
                "count": result["count"],
                "students": result["students"],
                "subjects": result["subjects"],
                "subject": selected_subject,
                "subject_name": selected_subject,
                "subject_names": result["subject_names"],
                "academic_year": norm_year,
                "academicYear": norm_year,
                "semester": target_sem,
            }

        records, has_invalid_row = services.parse_excel_file(
            contents,
            academic_year=norm_year,
            department=selected_department,
            section=selected_section,
        )

        if not records:
            return JSONResponse(
                status_code=400,
                content={"message": "Excel sheet is empty or contains no valid student rows."}
            )

        if has_invalid_row:
            return JSONResponse(
                status_code=400,
                content={"message": "One or more rows are missing Enrollment Number or Student Name."}
            )

        saved_count = services.save_student_records(db, records, academic_year=norm_year)

        return {
            "message": f"Student records uploaded successfully for academic year {norm_year}.",
            "count": saved_count,
            "academic_year": norm_year,
            "academicYear": norm_year
        }
    except ValueError as ve:
        return JSONResponse(
            status_code=400,
            content={"message": str(ve)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "message": f"Failed to process the uploaded Excel file: {str(e)}",
                "error": str(e)
            }
        )


@app.post("/api/upload-attendance", response_model=schemas.UploadResponse)
async def upload_attendance(
    file: UploadFile = File(...),
    academic_year: Optional[str] = Form(None),
    academicYear: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    section: Optional[str] = Form(None),
    semester: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    selected_year = (academic_year or academicYear or "").strip()
    selected_department = (department or "").strip()
    selected_section = (section or "").strip()
    selected_semester = (semester or "").strip()

    if not selected_year:
        return JSONResponse(
            status_code=400,
            content={"message": "Academic Year is required. Please select an academic year."}
        )

    try:
        norm_year = services.normalize_academic_year(selected_year)
    except ValueError as ve:
        return JSONResponse(
            status_code=400,
            content={"message": str(ve)}
        )
    if norm_year not in VALID_ACADEMIC_YEARS:
        return JSONResponse(
            status_code=400,
            content={"message": "Invalid Academic Year. Only '2024-2025' and '2025-2026' are accepted."}
        )

    if not selected_semester:
        return JSONResponse(
            status_code=400,
            content={"message": "Semester is required. Please select a semester."}
        )

    norm_sem = services.normalize_semester(selected_semester)
    if norm_sem not in VALID_SEMESTERS:
        return JSONResponse(
            status_code=400,
            content={"message": f"Invalid Semester '{selected_semester}'. Must be one of Semester 1 to Semester 8."}
        )

    if not file or not file.filename:
        return JSONResponse(
            status_code=400,
            content={"message": "Please upload a file."}
        )

    try:
        contents = await file.read()
        if not contents:
            return JSONResponse(
                status_code=400,
                content={"message": "Uploaded file is empty."}
            )

        records, has_invalid_row, subject_names = services.parse_attendance_excel_file(
            contents,
            file.filename,
            academic_year=norm_year,
            department=selected_department,
            section=selected_section,
            semester=norm_sem,
        )

        if not records:
            return JSONResponse(
                status_code=400,
                content={"message": "Attendance Excel sheet is empty or contains no valid records."}
            )

        if has_invalid_row:
            return JSONResponse(
                status_code=400,
                content={"message": "One or more rows are missing an enrollment number."}
            )

        records, unmatched_enrollments = services.match_attendance_students(db, records, academic_year=norm_year, semester=norm_sem)
        if unmatched_enrollments:
            return JSONResponse(
                status_code=400,
                content={
                    "message": f"Attendance rows could not be matched to existing students for academic year {norm_year}. Please ensure student marks records are uploaded first.",
                    "unmatched_enrollments": unmatched_enrollments
                }
            )

        saved_count = services.save_attendance_records(db, records, academic_year=norm_year, semester=norm_sem)

        return {
            "message": f"Student attendance uploaded successfully for academic year {norm_year} ({norm_sem}).",
            "count": saved_count,
            "students": saved_count,
            "subjects": len(subject_names),
            "subject_names": subject_names,
            "average_attendance": services.get_attendance_kpi(db, academic_year=norm_year, department=selected_department, section=selected_section, semester=norm_sem)['overall_average_attendance'],
            "academic_year": norm_year,
            "academicYear": norm_year,
            "semester": norm_sem
        }
    except ValueError as ve:
        return JSONResponse(
            status_code=400,
            content={"message": str(ve)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "message": f"Failed to process the uploaded Attendance Excel file: {str(e)}",
                "error": str(e)
            }
        )


@app.get("/api/students", response_model=List[schemas.StudentUploadSchema])
def get_students(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    semester: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    try:
        norm_year = services.normalize_academic_year(academic_year)
        students = services.get_all_students(db, academic_year=norm_year, department=department, section=section, semester=semester)
        return students
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve student records."
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)

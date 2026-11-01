import csv
import io
import os
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
_feedback_rate_limit_lock = threading.Lock()
_feedback_rate_limit_events = {}

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


def _check_public_feedback_rate_limit(request: Request, action: str, limit: int, window: int = 60):
    client_ip = request.client.host if request.client else "unknown"
    key = (action, client_ip)
    now = time.monotonic()
    cutoff = now - window
    with _feedback_rate_limit_lock:
        recent = [timestamp for timestamp in _feedback_rate_limit_events.get(key, []) if timestamp > cutoff]
        if len(recent) >= limit:
            retry_after = max(1, math.ceil(window - (now - recent[0])))
            _feedback_rate_limit_events[key] = recent
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many feedback requests. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )
        recent.append(now)
        _feedback_rate_limit_events[key] = recent
        if len(_feedback_rate_limit_events) > 10000:
            for existing_key, timestamps in list(_feedback_rate_limit_events.items()):
                if not timestamps or timestamps[-1] <= cutoff:
                    del _feedback_rate_limit_events[existing_key]


def rate_limit_public_feedback_read(request: Request):
    _check_public_feedback_rate_limit(request, "read", 120)


def rate_limit_public_feedback_validate(request: Request):
    _check_public_feedback_rate_limit(request, "validate", 10)


def rate_limit_public_feedback_submit(request: Request):
    _check_public_feedback_rate_limit(request, "submit", 5)


def _active_feedback_academic_year() -> str:
    configured_year = os.getenv("ACTIVE_ACADEMIC_YEAR", "").strip()
    if configured_year:
        try:
            normalized = services.normalize_academic_year(configured_year)
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ACTIVE_ACADEMIC_YEAR is not a supported academic year.",
            ) from error
        if normalized not in VALID_ACADEMIC_YEARS:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ACTIVE_ACADEMIC_YEAR is not a supported academic year.",
            )
        return normalized
    return max(VALID_ACADEMIC_YEARS, key=lambda year: int(year[:4]))


def _normalize_feedback_year(academic_year: str) -> str:
    try:
        normalized = services.normalize_academic_year(academic_year)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid academic year.") from error
    if normalized not in VALID_ACADEMIC_YEARS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid academic year.")
    return normalized


def _department_matches_faculty(department: models.Department, faculty: models.Faculty) -> bool:
    faculty_department = (faculty.department or "").strip().casefold()
    return faculty_department in {
        (department.name or "").strip().casefold(),
        (department.code or "").strip().casefold(),
    }


def _get_public_feedback_scope(db: Session, department_id: int, faculty_id: str):
    department = db.query(models.Department).filter(models.Department.id == department_id).first()
    faculty = db.query(models.Faculty).filter(
        models.Faculty.faculty_id == faculty_id.strip()
    ).first()
    if department is None or faculty is None or not _department_matches_faculty(department, faculty):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The selected faculty and department do not match.")
    return department, faculty


@app.get(
    "/api/public/feedback/departments",
    response_model=List[schemas.PublicFeedbackDepartment],
    dependencies=[Depends(rate_limit_public_feedback_read)],
)
def get_public_feedback_departments(db: Session = Depends(database.get_db)):
    return [
        {"id": department.id, "code": department.code, "name": department.name}
        for department in db.query(models.Department).order_by(models.Department.name).all()
    ]


@app.get(
    "/api/public/feedback/faculty/",
    response_model=List[schemas.PublicFeedbackFaculty],
    dependencies=[Depends(rate_limit_public_feedback_read)],
)
def get_public_feedback_faculty(
    department_id: int = Query(..., gt=0),
    db: Session = Depends(database.get_db),
):
    department = db.query(models.Department).filter(models.Department.id == department_id).first()
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department was not found.")
    faculty = db.query(models.Faculty).order_by(models.Faculty.name).all()
    return [
        {
            "faculty_id": member.faculty_id,
            "name": member.name,
            "designation": member.designation,
            "department_id": department.id,
        }
        for member in faculty
        if _department_matches_faculty(department, member)
    ]


@app.get(
    "/api/public/feedback/academic-year",
    dependencies=[Depends(rate_limit_public_feedback_read)],
)
def get_public_feedback_academic_year():
    return {"academic_year": _active_feedback_academic_year()}


@app.post(
    "/api/public/feedback/validate-token",
    dependencies=[Depends(rate_limit_public_feedback_validate)],
)
def validate_public_feedback_token(
    request: schemas.PublicFeedbackTokenRequest,
    db: Session = Depends(database.get_db),
):
    year = _normalize_feedback_year(request.academic_year)
    _, faculty = _get_public_feedback_scope(db, request.department_id, request.faculty_id)
    token = db.query(models.AnonymousFeedbackToken).filter(
        models.AnonymousFeedbackToken.token_hash == services.hash_feedback_code(request.feedback_code),
        models.AnonymousFeedbackToken.faculty_id == faculty.faculty_id,
        models.AnonymousFeedbackToken.academic_year == year,
    ).first()
    if token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feedback code is invalid for this selection.")
    if token.used:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This feedback code has already been used.")
    return {"valid": True, "faculty_id": faculty.faculty_id, "academic_year": year}


@app.post(
    "/api/public/feedback/submit",
    response_model=schemas.StudentFeedbackSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_public_feedback_submit)],
)
def submit_public_feedback(
    request: schemas.PublicStudentFeedbackCreate,
    db: Session = Depends(database.get_db),
):
    year = _normalize_feedback_year(request.academic_year)
    department, faculty = _get_public_feedback_scope(db, request.department_id, request.faculty_id)
    token_hash = services.hash_feedback_code(request.feedback_code)
    token = db.query(models.AnonymousFeedbackToken).filter(
        models.AnonymousFeedbackToken.token_hash == token_hash,
        models.AnonymousFeedbackToken.faculty_id == faculty.faculty_id,
        models.AnonymousFeedbackToken.academic_year == year,
    ).first()
    if token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feedback code is invalid for this selection.")
    submitted_at = datetime.utcnow()
    record = models.StudentFeedback(
        faculty_id=faculty.faculty_id,
        department_id=department.id,
        department=faculty.department,
        academic_year=year,
        subject=request.subject.strip(),
        teaching_quality=request.teaching_quality,
        subject_knowledge=request.subject_knowledge,
        communication_skills=request.communication_skills,
        student_interaction=request.student_interaction,
        overall_rating=request.overall_rating,
        comments=request.comments.strip() if request.comments else None,
        token_id=token.id,
        created_at=submitted_at,
        faculty_rating=request.overall_rating,
        course_content=request.subject_knowledge,
        learning_resources=request.communication_skills,
        faculty_support=request.student_interaction,
        overall_satisfaction=max(0, min(5, round(request.overall_rating / 2))),
        comment=request.comments.strip() if request.comments else None,
    )
    try:
        updated = db.query(models.AnonymousFeedbackToken).filter(
            models.AnonymousFeedbackToken.id == token.id,
            models.AnonymousFeedbackToken.used == 0,
        ).update(
            {
                models.AnonymousFeedbackToken.used: 1,
                models.AnonymousFeedbackToken.used_at: submitted_at,
            },
            synchronize_session=False,
        )
        if updated != 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This feedback code has already been used.")
        db.add(record)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except OperationalError as error:
        db.rollback()
        if "locked" in str(error).casefold() or "busy" in str(error).casefold():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This feedback code is being redeemed.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save feedback.")
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save feedback.") from error
    return {"message": "Feedback submitted successfully."}


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


@app.post(
    "/api/feedback",
    response_model=schemas.StudentFeedbackSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_student_feedback(
    feedback: schemas.StudentFeedbackCreate,
    db: Session = Depends(database.get_db),
):
    """Consume one anonymous faculty/year token and store feedback without the token."""
    token_hash = services.hash_feedback_code(feedback.token)
    token = db.query(models.AnonymousFeedbackToken).filter(
        models.AnonymousFeedbackToken.token_hash == token_hash
    ).first()
    if token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feedback token is invalid.")
    if token.used:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This feedback token has already been used.")

    faculty = db.query(models.Faculty).filter(models.Faculty.faculty_id == token.faculty_id).first()
    if faculty is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The faculty associated with this token is unavailable.")

    department = db.query(models.Department).filter(
        or_(
            func.lower(func.trim(models.Department.name)) == faculty.department.strip().lower(),
            func.lower(func.trim(models.Department.code)) == faculty.department.strip().lower(),
        )
    ).first()
    submitted_at = datetime.utcnow()
    record = models.StudentFeedback(
        academic_year=token.academic_year,
        subject=feedback.subject.strip(),
        teaching_quality=feedback.teaching_quality,
        subject_knowledge=feedback.subject_knowledge,
        communication_skills=feedback.communication_skills,
        student_interaction=feedback.student_interaction,
        overall_rating=feedback.overall_rating,
        comments=feedback.comments,
        token_id=token.id,
        created_at=submitted_at,
        department_id=department.id if department else None,
        faculty_id=faculty.faculty_id,
        department=faculty.department,
        faculty_rating=feedback.overall_rating,
        course_content=feedback.subject_knowledge,
        learning_resources=feedback.communication_skills,
        faculty_support=feedback.student_interaction,
        overall_satisfaction=max(1, min(5, round(feedback.overall_rating / 2))),
        comment=feedback.comments,
    )
    try:
        updated = db.query(models.AnonymousFeedbackToken).filter(
            models.AnonymousFeedbackToken.id == token.id,
            models.AnonymousFeedbackToken.used == 0,
        ).update(
            {
                models.AnonymousFeedbackToken.used: 1,
                models.AnonymousFeedbackToken.used_at: submitted_at,
            },
            synchronize_session=False,
        )
        if updated != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This feedback token has already been used.",
            )
        db.add(record)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except OperationalError as error:
        db.rollback()
        if "locked" in str(error).casefold() or "busy" in str(error).casefold():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This feedback code is being redeemed. Check its status and retry if needed.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save student feedback.",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save student feedback: {str(e)}",
        )
    return {"message": "Feedback submitted successfully."}


@app.post(
    "/api/feedback/validate-code",
    response_model=schemas.FeedbackCodeValidationResponse,
)
def validate_feedback_code(
    request: schemas.FeedbackCodeValidationRequest,
    db: Session = Depends(database.get_db),
):
    """Resolve an unused token to the faculty and academic year it covers."""
    token_hash = services.hash_feedback_code(request.token)
    token = db.query(models.AnonymousFeedbackToken).filter(
        models.AnonymousFeedbackToken.token_hash == token_hash
    ).first()
    if token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feedback token is invalid.")
    if token.used:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This feedback token has already been used.")
    faculty = db.query(models.Faculty).filter(models.Faculty.faculty_id == token.faculty_id).first()
    if faculty is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The faculty associated with this code is unavailable.")
    return {
        "academic_year": token.academic_year,
        "faculty_id": faculty.faculty_id,
        "faculty_name": faculty.name,
        "department": faculty.department,
        "designation": faculty.designation,
    }


@app.post("/api/admin/feedback/tokens", response_class=StreamingResponse)
@app.post("/api/feedback/tokens/issue", response_class=StreamingResponse)
def issue_feedback_codes(
    request: schemas.FeedbackCodeIssueRequest,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    """Generate an admin-only batch of unique, single-use codes for faculty/year."""
    try:
        academic_year = services.normalize_academic_year(request.academic_year)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    if academic_year not in VALID_ACADEMIC_YEARS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A supported academic year is required.")

    faculty = db.query(models.Faculty).filter(
        models.Faculty.faculty_id == request.faculty_id.strip()
    ).first()
    if faculty is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty member was not found.")

    code_rows = []
    try:
        for _ in range(request.count):
            plaintext_token = secrets.token_urlsafe(32)
            db.add(models.AnonymousFeedbackToken(
                token_hash=services.hash_feedback_code(plaintext_token),
                faculty_id=faculty.faculty_id,
                academic_year=academic_year,
                used=0,
            ))
            code_rows.append(plaintext_token)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A token hash collision occurred. Retry issuing the batch.",
        ) from error
    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to issue feedback tokens: {str(error)}",
        )

    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(("faculty_id", "faculty_name", "department", "academic_year", "feedback_token"))
    for plaintext_token in code_rows:
        writer.writerow((
            faculty.faculty_id,
            faculty.name,
            faculty.department,
            academic_year,
            plaintext_token,
        ))
    filename = f"ifhe-feedback-tokens-{academic_year}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/admin/feedback/summary", response_model=schemas.StudentFeedbackSummaryResponse)
@app.get("/api/feedback/summary", response_model=schemas.StudentFeedbackSummaryResponse)
def get_student_feedback_summary(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    """Return aggregate feedback only; individual submissions are not exposed."""
    sec_name, sec_dept = services.parse_section_identifier(section)
    effective_dept = department or sec_dept
    effective_sec = sec_name if sec_name is not None else section
    base_query = services._apply_scope(db.query(models.StudentFeedback), models.StudentFeedback, department=effective_dept)
    norm_year = services.normalize_academic_year(academic_year)
    selected_department = effective_dept.strip() if effective_dept and effective_dept.strip() else None
    if effective_sec and effective_sec.strip():
        # Feedback records have no section field; return an empty scoped result
        # instead of accidentally mixing feedback from other sections.
        base_query = base_query.filter(models.StudentFeedback.id == -1)

    all_responses = base_query.count()
    unattributed_responses = base_query.filter(
        or_(
            models.StudentFeedback.academic_year.is_(None),
            func.trim(models.StudentFeedback.academic_year) == "",
        )
    ).count()
    query = base_query
    if norm_year:
        query = query.filter(models.StudentFeedback.academic_year == norm_year)
    selected_year_responses = query.count()

    fields = (
        "teaching_quality",
        "course_content",
        "learning_resources",
        "faculty_support",
        "overall_satisfaction",
    )
    records = query.order_by(models.StudentFeedback.created_at.asc()).all()
    rows = [tuple(getattr(record, field) for field in fields) for record in records]
    distributions = {field: {rating: 0 for rating in range(1, 6)} for field in fields}
    totals = {field: 0 for field in fields}
    rating_counts = {field: 0 for field in fields}
    for row in rows:
        for field, rating in zip(fields, row):
            if isinstance(rating, int) and 1 <= rating <= 5:
                totals[field] += rating
                rating_counts[field] += 1
                distributions[field][rating] += 1

    averages = {
        field: round(total / rating_counts[field], 2) if rating_counts[field] else None
        for field, total in totals.items()
    }
    by_day = {}
    for record in records:
        day = record.created_at.date().isoformat()
        bucket = by_day.setdefault(
            day,
            {"responses": 0, **{field: 0 for field in fields}, **{f"{field}_count": 0 for field in fields}},
        )
        bucket["responses"] += 1
        for field in fields:
            rating = getattr(record, field)
            if isinstance(rating, int) and 1 <= rating <= 5:
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
        for day, bucket in by_day.items()
    ]
    return {
        "academic_year": norm_year,
        "department": selected_department,
        "total_responses": len(rows),
        "all_responses": all_responses,
        "unattributed_responses": unattributed_responses,
        "other_year_responses": max(0, all_responses - selected_year_responses - unattributed_responses),
        "averages": averages,
        "rating_distributions": distributions,
        "timeline": timeline,
    }


@app.get("/api/admin/feedback/faculty", response_model=schemas.FacultyFeedbackSummaryResponse)
@app.get("/api/feedback/faculty", response_model=schemas.FacultyFeedbackSummaryResponse)
def get_faculty_feedback(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    """Return read-only, anonymous faculty feedback and ratings for administrators."""
    try:
        norm_year = services.normalize_academic_year(academic_year)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    selected_department = department.strip() if department and department.strip() else None
    selected_department_record = None
    if selected_department:
        selected_department_record = db.query(models.Department).filter(
            or_(
                func.lower(func.trim(models.Department.name)) == selected_department.casefold(),
                func.lower(func.trim(models.Department.code)) == selected_department.casefold(),
            )
        ).first()

    feedback_query = db.query(models.StudentFeedback)
    if norm_year:
        feedback_query = feedback_query.filter(models.StudentFeedback.academic_year == norm_year)
    if selected_department:
        department_filters = [models.StudentFeedback.department == selected_department]
        if selected_department_record:
            department_filters.extend([
                models.StudentFeedback.department_id == selected_department_record.id,
                models.StudentFeedback.department == selected_department_record.name,
                models.StudentFeedback.department == selected_department_record.code,
            ])
        feedback_query = feedback_query.filter(or_(*department_filters))
    records = feedback_query.order_by(models.StudentFeedback.created_at.desc(), models.StudentFeedback.id.desc()).all()

    unassigned_year_query = db.query(models.StudentFeedback).filter(
        or_(models.StudentFeedback.academic_year.is_(None), func.trim(models.StudentFeedback.academic_year) == "")
    )
    if selected_department:
        unassigned_year_query = unassigned_year_query.filter(
            or_(
                models.StudentFeedback.department == selected_department,
                func.trim(models.StudentFeedback.department) == "",
                *(
                    [
                        models.StudentFeedback.department_id == selected_department_record.id,
                        models.StudentFeedback.department == selected_department_record.name,
                        models.StudentFeedback.department == selected_department_record.code,
                    ]
                    if selected_department_record else []
                ),
            )
        )
    unassigned_year_records = unassigned_year_query.order_by(
        models.StudentFeedback.created_at.desc(), models.StudentFeedback.id.desc()
    ).all()

    all_faculty_records = db.query(models.Faculty).order_by(models.Faculty.department, models.Faculty.name).all()
    department_records = db.query(models.Department).all()
    faculty_department_labels = {}
    for faculty in all_faculty_records:
        faculty_department = (faculty.department or "").strip().casefold()
        department_record = next(
            (
                item for item in department_records
                if faculty_department in {
                    (item.name or "").strip().casefold(),
                    (item.code or "").strip().casefold(),
                }
            ),
            None,
        )
        faculty_department_labels[faculty.faculty_id] = (
            department_record.name if department_record else faculty.department
        )
    available_departments = sorted({
        label for label in faculty_department_labels.values() if label
    })
    faculty_records = all_faculty_records
    if selected_department:
        faculty_records = [
            faculty for faculty in faculty_records
            if (
                _department_matches_faculty(selected_department_record, faculty)
                if selected_department_record
                else faculty.department == selected_department
            )
        ]
    faculty_by_id = {faculty.faculty_id: faculty for faculty in faculty_records}

    associated = {faculty_id: [] for faculty_id in faculty_by_id}
    unassigned_faculty_records = []
    for record in records:
        if not (record.academic_year or "").strip():
            continue
        faculty = faculty_by_id.get(record.faculty_id)
        if faculty is None:
            unassigned_faculty_records.append(record)
            continue
        associated[faculty.faculty_id].append(record)

    distribution = {rating: 0 for rating in range(0, 11)}
    department_totals = {}
    faculty_results = []
    overall_rating_total = 0
    overall_rating_count = 0
    departments_with_feedback = set()
    for faculty in faculty_records:
        faculty_feedback = associated[faculty.faculty_id]
        valid_ratings = [
            (
                record.overall_rating
                if isinstance(record.overall_rating, int)
                and 0 <= record.overall_rating <= 10
                else record.faculty_rating
            )
            for record in faculty_feedback
            if (
                isinstance(record.overall_rating, int)
                and 0 <= record.overall_rating <= 10
            ) or (
                isinstance(record.faculty_rating, int)
                and 0 <= record.faculty_rating <= 10
            )
        ]
        rating_total = sum(valid_ratings)
        rating_count = len(valid_ratings)
        average = round(rating_total / rating_count, 2) if rating_count else None
        comments = [
            schemas.FacultyFeedbackComment(
                comment=record.comments if record.comments is not None else record.comment,
                faculty_rating=(
                    record.overall_rating
                    if record.overall_rating in range(0, 11)
                    else record.faculty_rating
                    if record.faculty_rating in range(0, 11)
                    else None
                ),
                teaching_quality=record.teaching_quality,
                subject_knowledge=(
                    record.subject_knowledge
                    if record.subject_knowledge is not None
                    else record.course_content
                ),
                communication_skills=(
                    record.communication_skills
                    if record.communication_skills is not None
                    else record.learning_resources
                ),
                student_interaction=(
                    record.student_interaction
                    if record.student_interaction is not None
                    else record.faculty_support
                ),
                criteria_rating_scale=(
                    10
                    if any(value is not None for value in (
                        record.subject_knowledge,
                        record.communication_skills,
                        record.student_interaction,
                    ))
                    else 5
                ),
                subject=record.subject,
                created_at=record.created_at.isoformat() if record.created_at else None,
            )
            for record in faculty_feedback
        ]
        faculty_results.append(schemas.FacultyFeedbackItem(
            faculty_id=faculty.faculty_id,
            name=faculty.name,
            department=faculty_department_labels[faculty.faculty_id],
            designation=faculty.designation,
            response_count=len(faculty_feedback),
            rating_count=rating_count,
            average_rating=average,
            feedback=comments,
        ))
        if faculty_feedback:
            departments_with_feedback.add(faculty_department_labels[faculty.faculty_id])
        for rating in valid_ratings:
            distribution[rating] += 1
        department_bucket = department_totals.setdefault(
            faculty_department_labels[faculty.faculty_id],
            {"rating_total": 0, "rating_count": 0, "response_count": 0},
        )
        department_bucket["response_count"] += len(faculty_feedback)
        department_bucket["rating_total"] += rating_total
        department_bucket["rating_count"] += rating_count
        if rating_count:
            overall_rating_total += rating_total
            overall_rating_count += rating_count

    ranked_faculty = sorted(
        (item for item in faculty_results if item.average_rating is not None),
        key=lambda item: (-item.average_rating, item.name.casefold(), item.faculty_id),
    )
    department_results = [
        schemas.FacultyDepartmentRating(
            department=name,
            response_count=values["response_count"],
            average_rating=(
                round(values["rating_total"] / values["rating_count"], 2)
                if values["rating_count"] else None
            ),
        )
        for name, values in sorted(department_totals.items())
    ]
    return schemas.FacultyFeedbackSummaryResponse(
        academic_year=norm_year,
        department=selected_department,
        total_responses=len(records),
        unassigned_year_responses=len(unassigned_year_records),
        unassigned_faculty_responses=len(unassigned_faculty_records),
        total_faculty=sum(item.response_count > 0 for item in faculty_results),
        total_departments=len(departments_with_feedback),
        overall_average_rating=(
            round(overall_rating_total / overall_rating_count, 2) if overall_rating_count else None
        ),
        highest_rated_faculty=ranked_faculty[0] if ranked_faculty else None,
        rating_distribution=distribution,
        available_departments=available_departments,
        departments=department_results,
        faculty=faculty_results,
        unassigned_year_feedback=[
            schemas.UnassignedFeedbackItem(
                academic_year=(record.academic_year or "").strip() or None,
                department=(record.department or "").strip() or None,
                comment=record.comment,
                created_at=record.created_at.isoformat() if record.created_at else None,
            )
            for record in unassigned_year_records
        ],
        unassigned_faculty_feedback=[
            schemas.UnassignedFeedbackItem(
                academic_year=(record.academic_year or "").strip() or None,
                department=(record.department or "").strip() or None,
                comment=record.comment,
                created_at=record.created_at.isoformat() if record.created_at else None,
            )
            for record in unassigned_faculty_records
        ],
    )


@app.get("/api/admin/feedback/departments")
def get_admin_feedback_departments(
    academic_year: Optional[str] = None,
    department_id: Optional[int] = Query(None, gt=0),
    db: Session = Depends(database.get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    selected_department = None
    if department_id is not None:
        selected_department = db.query(models.Department).filter(
            models.Department.id == department_id
        ).first()
        if selected_department is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department was not found.")
    summary = get_faculty_feedback(
        academic_year=academic_year,
        department=selected_department.name if selected_department else None,
        db=db,
        _=admin,
    )
    rated_departments = {item.department: item for item in summary.departments}
    department_rows = []
    departments = (
        [selected_department]
        if selected_department
        else db.query(models.Department).order_by(models.Department.name).all()
    )
    for department in departments:
        matched_rating = next(
            (
                rated for name, rated in rated_departments.items()
                if name.casefold() in {
                    department.name.casefold(),
                    department.code.casefold(),
                }
            ),
            None,
        )
        department_rows.append({
            "department_id": department.id,
            "department": department.name,
            "response_count": matched_rating.response_count if matched_rating else 0,
            "average_rating": matched_rating.average_rating if matched_rating else None,
        })
    return {
        "academic_year": summary.academic_year,
        "department_id": selected_department.id if selected_department else None,
        "departments": department_rows,
        "total_responses": summary.total_responses,
    }


@app.get("/api/admin/feedback/ratings")
def get_admin_feedback_ratings(
    academic_year: Optional[str] = None,
    department_id: Optional[int] = Query(None, gt=0),
    db: Session = Depends(database.get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    selected_department = None
    if department_id is not None:
        selected_department = db.query(models.Department).filter(
            models.Department.id == department_id
        ).first()
        if selected_department is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department was not found.")
    summary = get_faculty_feedback(
        academic_year=academic_year,
        department=selected_department.name if selected_department else None,
        db=db,
        _=admin,
    )
    return {
        "academic_year": summary.academic_year,
        "department_id": selected_department.id if selected_department else None,
        "total_responses": summary.total_responses,
        "valid_rating_count": sum(summary.rating_distribution.values()),
        "average_rating": summary.overall_average_rating,
        "rating_distribution": summary.rating_distribution,
    }


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

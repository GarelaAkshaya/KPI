from typing import List, Optional
from fastapi import FastAPI, Depends, File, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

import database
import models
import schemas
import services

VALID_ACADEMIC_YEARS = {"2024-2025", "2025-2026"}

# Create database tables automatically and apply any missing column migrations
database.init_db()

# Seed default initial data if tables are empty and initialize the admin account
with database.SessionLocal() as db_session:
    services.seed_initial_data(db_session)
    services.initialize_admin_account(db_session)

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


@app.post(
    "/api/feedback",
    response_model=schemas.StudentFeedbackSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_student_feedback(
    feedback: schemas.StudentFeedbackCreate,
    db: Session = Depends(database.get_db),
):
    """Store anonymous student feedback without student identifiers."""
    # These columns are required by the existing shared table; empty values keep
    # legacy schema compatibility without collecting academic details.
    data = {**feedback.model_dump(), "academic_year": "", "department": ""}
    record = models.StudentFeedback(**data)
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save student feedback: {str(e)}",
        )
    return {"message": "Feedback submitted successfully."}


@app.get("/api/feedback/summary", response_model=schemas.StudentFeedbackSummaryResponse)
def get_student_feedback_summary(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    """Return aggregate feedback only; individual submissions are not exposed."""
    base_query = services._apply_scope(db.query(models.StudentFeedback), models.StudentFeedback, department=department)
    norm_year = services.normalize_academic_year(academic_year)
    selected_department = department.strip() if department and department.strip() else None
    if section and section.strip():
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
    for row in rows:
        for field, rating in zip(fields, row):
            totals[field] += rating
            distributions[field][rating] += 1

    averages = {
        field: round(total / len(rows), 2) if rows else None
        for field, total in totals.items()
    }
    by_day = {}
    for record in records:
        day = record.created_at.date().isoformat()
        bucket = by_day.setdefault(day, {"responses": 0, **{field: 0 for field in fields}})
        bucket["responses"] += 1
        for field in fields:
            bucket[field] += getattr(record, field)
    timeline = [
        {"date": day, "responses": bucket["responses"], **{
            field: round(bucket[field] / bucket["responses"], 2) for field in fields
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
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    try:
        norm_year = services.normalize_academic_year(academic_year) or "2024-2025"
        return services.get_pass_percentage_kpi(db, academic_year=norm_year, department=department, section=section)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate pass percentage KPI: {str(e)}"
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
def get_faculty(db: Session = Depends(database.get_db), _: models.AdminUser = Depends(get_current_admin)):
    try:
        return services.get_all_faculty(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve faculty records."
        )


@app.post("/api/faculty", response_model=schemas.FacultySchema, status_code=status.HTTP_201_CREATED)
def create_faculty(faculty: schemas.FacultyCreate, db: Session = Depends(database.get_db), _: models.AdminUser = Depends(get_current_admin)):
    try:
        return services.create_faculty(db, faculty.model_dump())
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


@app.get("/api/filters/sections", response_model=List[str])
def get_filter_sections(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    return services.get_available_sections(db, academic_year=services.normalize_academic_year(academic_year), department=department)


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
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    try:
        norm_year = services.normalize_academic_year(academic_year)
        return services.get_all_attendance(db, academic_year=norm_year, department=department, section=section)
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
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    try:
        norm_year = services.normalize_academic_year(academic_year)
        return services.get_attendance_subjects(db, academic_year=norm_year, department=department, section=section)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve attendance subjects: {str(e)}")


@app.get("/api/attendance/kpi")
def get_attendance_kpi(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    try:
        norm_year = services.normalize_academic_year(academic_year)
        return services.get_attendance_kpi(db, academic_year=norm_year, department=department, section=section)
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


@app.post("/api/upload-students", response_model=schemas.UploadResponse)
async def upload_students(
    file: UploadFile = File(...),
    academic_year: Optional[str] = Form(None),
    academicYear: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    section: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    selected_year = (academic_year or academicYear or "").strip()
    selected_department = (department or "").strip()
    selected_section = (section or "").strip()
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
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    selected_year = (academic_year or academicYear or "").strip()
    selected_department = (department or "").strip()
    selected_section = (section or "").strip()
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

        records, unmatched_enrollments = services.match_attendance_students(db, records, academic_year=norm_year)
        if unmatched_enrollments:
            return JSONResponse(
                status_code=400,
                content={
                    "message": f"Attendance rows could not be matched to existing students for academic year {norm_year}. Please ensure student marks records are uploaded first.",
                    "unmatched_enrollments": unmatched_enrollments
                }
            )

        saved_count = services.save_attendance_records(db, records, academic_year=norm_year)

        return {
            "message": f"Student attendance uploaded successfully for academic year {norm_year}.",
            "count": saved_count,
            "students": saved_count,
            "subjects": len(subject_names),
            "subject_names": subject_names,
            "average_attendance": services.get_attendance_kpi(db, academic_year=norm_year)['overall_average_attendance'],
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
                "message": f"Failed to process the uploaded Attendance Excel file: {str(e)}",
                "error": str(e)
            }
        )


@app.get("/api/students", response_model=List[schemas.StudentUploadSchema])
def get_students(
    academic_year: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    db: Session = Depends(database.get_db),
    _: models.AdminUser = Depends(get_current_admin),
):
    try:
        norm_year = services.normalize_academic_year(academic_year)
        students = services.get_all_students(db, academic_year=norm_year, department=department, section=section)
        return students
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve student records."
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)


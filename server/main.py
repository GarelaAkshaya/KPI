from typing import List
from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

import database
import models
import schemas
import services

# Create database tables automatically
models.Base.metadata.create_all(bind=database.engine)

# Seed default initial data if tables are empty
with database.SessionLocal() as db_session:
    services.seed_initial_data(db_session)

app = FastAPI(title="IFHE KPI API", version="1.0.0")

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


@app.get("/api/stats", response_model=schemas.StatsResponse)
def get_stats(db: Session = Depends(database.get_db)):
    try:
        db_student_count = services.get_student_count(db)
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


@app.get("/api/kpis/summary", response_model=schemas.KPISummaryResponse)
def get_kpi_summary(db: Session = Depends(database.get_db)):
    """Fetch all calculated KPI values for the dashboard."""
    try:
        summary = services.get_kpi_summary(db)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate KPI summary: {str(e)}"
        )


# Stored KPI Endpoints
@app.get("/api/kpis", response_model=List[schemas.KPISchema])
def get_kpis(db: Session = Depends(database.get_db)):
    try:
        return services.get_all_kpis(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KPIs."
        )


@app.post("/api/kpis", response_model=schemas.KPISchema, status_code=status.HTTP_201_CREATED)
def create_kpi(kpi: schemas.KPICreate, db: Session = Depends(database.get_db)):
    try:
        return services.create_kpi(db, kpi.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create KPI record: {str(e)}"
        )


# Faculty Endpoints
@app.get("/api/faculty", response_model=List[schemas.FacultySchema])
def get_faculty(db: Session = Depends(database.get_db)):
    try:
        return services.get_all_faculty(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve faculty records."
        )


@app.post("/api/faculty", response_model=schemas.FacultySchema, status_code=status.HTTP_201_CREATED)
def create_faculty(faculty: schemas.FacultyCreate, db: Session = Depends(database.get_db)):
    try:
        return services.create_faculty(db, faculty.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create faculty record: {str(e)}"
        )


# Department Endpoints
@app.get("/api/departments", response_model=List[schemas.DepartmentSchema])
def get_departments(db: Session = Depends(database.get_db)):
    try:
        return services.get_all_departments(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve departments."
        )


@app.post("/api/departments", response_model=schemas.DepartmentSchema, status_code=status.HTTP_201_CREATED)
def create_department(dept: schemas.DepartmentCreate, db: Session = Depends(database.get_db)):
    try:
        return services.create_department(db, dept.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create department: {str(e)}"
        )


# Student Attendance Endpoints
@app.get("/api/attendance", response_model=List[schemas.StudentAttendanceSchema])
def get_attendance(db: Session = Depends(database.get_db)):
    try:
        return services.get_all_attendance(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve student attendance records."
        )


@app.post("/api/attendance", response_model=schemas.StudentAttendanceSchema, status_code=status.HTTP_201_CREATED)
def create_attendance(att: schemas.StudentAttendanceCreate, db: Session = Depends(database.get_db)):
    try:
        return services.create_attendance(db, att.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create attendance record: {str(e)}"
        )


# Laboratory Utilization Endpoints
@app.get("/api/lab-utilization", response_model=List[schemas.LaboratoryUtilizationSchema])
def get_lab_utilization(db: Session = Depends(database.get_db)):
    try:
        return services.get_all_lab_utilizations(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve laboratory utilization records."
        )


@app.post("/api/lab-utilization", response_model=schemas.LaboratoryUtilizationSchema, status_code=status.HTTP_201_CREATED)
def create_lab_utilization(lab: schemas.LaboratoryUtilizationCreate, db: Session = Depends(database.get_db)):
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
    db: Session = Depends(database.get_db)
):
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

        records, has_invalid_row = services.parse_excel_file(contents)

        if not records:
            return JSONResponse(
                status_code=400,
                content={"message": "Excel sheet is empty or could not be parsed."}
            )

        if has_invalid_row:
            return JSONResponse(
                status_code=400,
                content={"message": "One or more rows are missing Student ID or Student Name."}
            )

        saved_count = services.save_student_records(db, records)

        return {
            "message": "Student records uploaded successfully.",
            "count": saved_count
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Failed to process the uploaded Excel file.",
                "error": str(e)
            }
        )


@app.get("/api/students", response_model=List[schemas.StudentUploadSchema])
def get_students(db: Session = Depends(database.get_db)):
    try:
        students = services.get_all_students(db)
        return students
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve student records."
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)


from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class StudentUploadSchema(BaseModel):
    id: int
    studentId: str
    studentName: str
    totalMarks: int
    percentage: float
    enrollment_number: Optional[str] = None
    enrollmentNumber: Optional[str] = None
    department: Optional[str] = "Artificial Intelligence and Data Science (AIDS)"
    section: Optional[str] = None
    semester: Optional[str] = "Semester 1"
    academic_year: Optional[str] = "2024-2025"
    academicYear: Optional[str] = "2024-2025"
    dm: Optional[int] = None
    dsc: Optional[int] = None
    coa: Optional[int] = None
    python_marks: Optional[int] = None
    ml: Optional[int] = None
    subject_marks: Optional[dict[str, Optional[int]]] = None
    component_marks: Optional[dict[str, dict[str, Optional[float]]]] = None
    createdAt: str

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    totalStudents: int
    totalFaculty: int
    totalDepartments: int
    activeKPIs: int
    isLive: bool


class StudentFacultyRatioResponse(BaseModel):
    totalStudents: int
    totalFaculty: int
    ratio: float
    academicYear: Optional[str] = None
    academic_year: Optional[str] = None
    message: Optional[str] = None


class StudentFacultyRatioTrendResponse(BaseModel):
    data: list[dict[str, float | str]]
    distribution: list[dict[str, float | str]]
    message: Optional[str] = None


class UploadResponse(BaseModel):
    message: str
    count: int
    students: Optional[int] = None
    subjects: Optional[int] = None
    subject_names: Optional[list[str]] = None
    average_attendance: Optional[float] = None
    academic_year: Optional[str] = None
    academicYear: Optional[str] = None
    semester: Optional[str] = None


# Multi-subject Semester Workbook Schemas
class StudentMarkItem(BaseModel):
    s_no: Optional[int] = None
    enrollment_number: str
    student_name: str
    test1: Optional[float] = None
    lab1: Optional[float] = None
    test2: Optional[float] = None
    lab2: Optional[float] = None
    compre: Optional[float] = None
    total: float


class SubjectSheetPreview(BaseModel):
    subject_name: str
    sheet_name: Optional[str] = None
    student_count: int
    valid_rows: Optional[int] = None
    average_total: float
    min_total: float
    max_total: float
    rows: list[StudentMarkItem] = []
    sample_rows: Optional[list[StudentMarkItem]] = None
    is_valid: bool
    errors: list[str] = []


class WorkbookPreviewResponse(BaseModel):
    valid: bool
    academic_year: str
    department: str
    section: str
    semester: str
    total_sheets: Optional[int] = None
    total_students: int
    filename: Optional[str] = None
    sheets: list[SubjectSheetPreview]
    errors: list[str] = []
    warnings: list[str] = []
    configured_subjects: list[str] = []
    detected_subjects: list[str] = []


# Faculty Schemas
class FacultyBase(BaseModel):
    faculty_id: str
    name: str
    department: str
    experience: float = 0.0
    designation: Optional[str] = None
    qualification: Optional[str] = None
    email: Optional[str] = None
    image_path: Optional[str] = None


class FacultyCreate(FacultyBase):
    pass


class FacultySchema(FacultyBase):
    id: int

    class Config:
        from_attributes = True


# Department Schemas
class DepartmentBase(BaseModel):
    code: str
    name: str
    head_of_department: Optional[str] = None
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentSchema(DepartmentBase):
    id: int

    class Config:
        from_attributes = True


class DepartmentOverviewItem(BaseModel):
    name: str
    studentCount: int
    facultyCount: int


class SectionFilterOption(BaseModel):
    section: str
    department: str
    label: str
    value: str


# Authentication Schemas
class AdminLoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


# KPI Schemas
class KPIBase(BaseModel):
    name: str
    academic_year: str
    value: float
    target: float
    status: str
    category: Optional[str] = None
    unit: Optional[str] = None


class KPICreate(KPIBase):
    pass


class KPISchema(KPIBase):
    id: int

    class Config:
        from_attributes = True


# Student Attendance Schemas
class StudentAttendanceBase(BaseModel):
    student_id: str
    enrollment_number: Optional[str] = None
    student_name: str
    department: str
    section: Optional[str] = None
    academic_year: str
    total_classes: int = 0
    attended_classes: int = 0
    attendance_percentage: float = 0.0
    average_attendance: float = 0.0
    subjects: list[str] = []
    subject_values: dict[str, float] = {}


class StudentAttendanceCreate(StudentAttendanceBase):
    pass


class StudentAttendanceSchema(StudentAttendanceBase):
    id: int

    class Config:
        from_attributes = True


# Student Feedback Schemas
class StudentFeedbackCreate(BaseModel):
    class Config:
        extra = "ignore"

    teaching_quality: int = Field(..., ge=1, le=5)
    course_content: int = Field(..., ge=1, le=5)
    learning_resources: int = Field(..., ge=1, le=5)
    faculty_support: int = Field(..., ge=1, le=5)
    overall_satisfaction: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class StudentFeedbackSubmissionResponse(BaseModel):
    message: str


class StudentFeedbackSummaryResponse(BaseModel):
    all_responses: int
    unattributed_responses: int
    other_year_responses: int
    averages: dict[str, Optional[float]]
    rating_distributions: dict[str, dict[int, int]]
    timeline: list[dict[str, object]] = []


# Laboratory Utilization Schemas
class LaboratoryUtilizationBase(BaseModel):
    laboratory_name: str
    department: str
    academic_year: str
    session_date: str
    time_slot: Optional[str] = None
    capacity: Optional[int] = None
    students_present: Optional[int] = None


class LaboratoryUtilizationCreate(LaboratoryUtilizationBase):
    pass


class LaboratoryUtilizationSchema(LaboratoryUtilizationBase):
    id: int

    class Config:
        from_attributes = True


# Overall KPI Summary Response Schema
class KPISummaryResponse(BaseModel):
    total_students: int
    total_faculty: int
    number_of_departments: int
    student_faculty_ratio: float
    pass_percentage: float
    average_student_marks: float
    student_attendance_percentage: float
    laboratory_utilization_percentage: float

    class Config:
        from_attributes = True


# Pass Percentage KPI Schemas
class SubjectPassFail(BaseModel):
    subject: str
    subject_name: str
    passed: int
    failed: int
    total: int
    pass_percentage: float
    fail_percentage: float


class OverallPassFail(BaseModel):
    passed: int
    failed: int
    total: int
    pass_percentage: float
    fail_percentage: float


class PassPercentageKPIResponse(BaseModel):
    academic_year: str
    academicYear: str
    semester: Optional[str] = None
    total_students_evaluated: int
    total_students_count: int
    uncalculated_count: int
    overall: OverallPassFail
    subjects: list[SubjectPassFail]
    overall_pass_percentage: float
    overall_fail_percentage: float
    message: Optional[str] = None

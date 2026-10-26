from typing import Optional
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
    academic_year: Optional[str] = "2024-2025"
    academicYear: Optional[str] = "2024-2025"
    dm: Optional[int] = None
    dsc: Optional[int] = None
    coa: Optional[int] = None
    python_marks: Optional[int] = None
    ml: Optional[int] = None
    subject_marks: Optional[dict[str, Optional[int]]] = None
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


# Faculty Schemas
class FacultyBase(BaseModel):
    faculty_id: str
    name: str
    department: str
    experience: float
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


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


# KPI Storage Schemas
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
    academicYear: Optional[str] = None
    total_classes: int
    attended_classes: int
    attendance_percentage: Optional[float] = None
    average_attendance: Optional[float] = None
    subjects: Optional[list[str]] = None
    subject_values: Optional[dict[str, float]] = None


class StudentAttendanceCreate(StudentAttendanceBase):
    pass


class StudentAttendanceSchema(StudentAttendanceBase):
    id: int
    attendance_percentage: float

    class Config:
        from_attributes = True


# Student Feedback Schemas
class StudentFeedbackCreate(BaseModel):
    class Config:
        extra = "forbid"

    teaching_quality: int = Field(ge=1, le=5)
    course_content: int = Field(ge=1, le=5)
    learning_resources: int = Field(ge=1, le=5)
    faculty_support: int = Field(ge=1, le=5)
    overall_satisfaction: int = Field(ge=1, le=5)


class StudentFeedbackSubmissionResponse(BaseModel):
    message: str


class StudentFeedbackSummaryResponse(BaseModel):
    academic_year: Optional[str] = None
    department: Optional[str] = None
    total_responses: int
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
    total_students_evaluated: int
    total_students_count: int
    uncalculated_count: int
    overall: OverallPassFail
    subjects: list[SubjectPassFail]
    overall_pass_percentage: float
    overall_fail_percentage: float
    message: Optional[str] = None


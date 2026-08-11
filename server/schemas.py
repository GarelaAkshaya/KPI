from typing import Optional
from pydantic import BaseModel


class StudentUploadSchema(BaseModel):
    id: int
    studentId: str
    studentName: str
    totalMarks: int
    percentage: float
    createdAt: str

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    totalStudents: int
    totalFaculty: int
    totalDepartments: int
    activeKPIs: int
    isLive: bool


class UploadResponse(BaseModel):
    message: str
    count: int


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
    student_name: str
    department: str
    academic_year: str
    total_classes: int
    attended_classes: int
    attendance_percentage: Optional[float] = None


class StudentAttendanceCreate(StudentAttendanceBase):
    pass


class StudentAttendanceSchema(StudentAttendanceBase):
    id: int
    attendance_percentage: float

    class Config:
        from_attributes = True


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


from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base


class StudentUpload(Base):
    __tablename__ = "student_uploads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    studentId = Column(String, nullable=False)
    studentName = Column(String, nullable=False)
    totalMarks = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    createdAt = Column(String, nullable=False, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class LaboratoryUtilization(Base):
    __tablename__ = "laboratory_utilization"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    laboratory_name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    academic_year = Column(String, nullable=False)
    session_date = Column(String, nullable=False)
    time_slot = Column(String, nullable=True)
    capacity = Column(Integer, nullable=True)
    students_present = Column(Integer, nullable=True)


class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    faculty_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    experience = Column(Float, nullable=False, default=0.0)
    designation = Column(String, nullable=True)
    email = Column(String, nullable=True)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    head_of_department = Column(String, nullable=True)
    description = Column(String, nullable=True)


class KPI(Base):
    __tablename__ = "kpis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    academic_year = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    target = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    category = Column(String, nullable=True)
    unit = Column(String, nullable=True)


class StudentAttendance(Base):
    __tablename__ = "student_attendance"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String, nullable=False, index=True)
    student_name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    academic_year = Column(String, nullable=False)
    total_classes = Column(Integer, nullable=False, default=0)
    attended_classes = Column(Integer, nullable=False, default=0)
    attendance_percentage = Column(Float, nullable=False, default=0.0)


from datetime import datetime
import json
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from database import Base


class StudentUpload(Base):
    __tablename__ = "student_uploads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    studentId = Column(String, nullable=False)
    enrollment_number = Column(String, nullable=True, index=True)
    studentName = Column(String, nullable=False)
    department = Column(String, nullable=True, default="Artificial Intelligence and Data Science (AIDS)")
    section = Column(String, nullable=True, default=None)
    semester = Column(String, nullable=True, default="Semester 1", index=True)
    totalMarks = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    academic_year = Column(String, nullable=False, default="2024-2025", index=True)
    dm = Column(Integer, nullable=True)
    dsc = Column(Integer, nullable=True)
    coa = Column(Integer, nullable=True)
    python_marks = Column(Integer, nullable=True)
    ml = Column(Integer, nullable=True)
    subject_marks_json = Column(Text, nullable=True, default='{}')
    component_marks_json = Column(Text, nullable=True, default='{}')
    createdAt = Column(String, nullable=False, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    @property
    def academicYear(self):
        return self.academic_year

    @property
    def enrollmentNumber(self):
        return self.enrollment_number or self.studentId

    @property
    def subject_marks(self):
        if (
            self.dm is not None
            and self.dsc is not None
            and self.coa is not None
            and self.python_marks is not None
            and self.ml is not None
        ):
            return {
                "DM": self.dm,
                "DSC": self.dsc,
                "COA": self.coa,
                "Python": self.python_marks,
                "ML": self.ml,
            }
        if self.subject_marks_json:
            try:
                parsed = json.loads(self.subject_marks_json)
                if isinstance(parsed, dict) and len(parsed) > 0:
                    return parsed
            except Exception:
                pass
        return None

    @property
    def component_marks(self):
        if self.component_marks_json:
            try:
                parsed = json.loads(self.component_marks_json)
                if isinstance(parsed, dict) and len(parsed) > 0:
                    return parsed
            except Exception:
                pass
        return {}

    @property
    def has_all_five_subjects(self):
        marks = self.subject_marks
        if not marks:
            return False
        if all(marks.get(subj) is not None for subj in ("DM", "DSC", "COA", "Python", "ML")):
            return True
        return len(marks) >= 5

    @property
    def passed_all_subjects(self):
        marks = self.subject_marks
        if not marks:
            return False
        return all(int(marks[subj]) >= 40 for subj in marks if marks[subj] is not None)


class StudentMark(Base):
    __tablename__ = "student_marks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String, nullable=False, index=True)
    enrollment_number = Column(String, nullable=True, index=True)
    student_name = Column(String, nullable=False)
    department = Column(String, nullable=False, index=True)
    section = Column(String, nullable=True, index=True)
    academic_year = Column(String, nullable=False, index=True)
    semester = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=False, index=True)
    test1 = Column(Float, nullable=True)
    lab1 = Column(Float, nullable=True)
    test2 = Column(Float, nullable=True)
    lab2 = Column(Float, nullable=True)
    compre = Column(Float, nullable=True)
    total = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


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
    qualification = Column(String, nullable=True)
    email = Column(String, nullable=True)
    image_path = Column(String, nullable=True)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    head_of_department = Column(String, nullable=True)
    description = Column(String, nullable=True)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


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


class StudentFeedback(Base):
    __tablename__ = "student_feedback"
    __table_args__ = (
        CheckConstraint("teaching_quality IS NULL OR teaching_quality BETWEEN 0 AND 10"),
        CheckConstraint("subject_knowledge IS NULL OR subject_knowledge BETWEEN 0 AND 10"),
        CheckConstraint("communication_skills IS NULL OR communication_skills BETWEEN 0 AND 10"),
        CheckConstraint("student_interaction IS NULL OR student_interaction BETWEEN 0 AND 10"),
        CheckConstraint("overall_rating IS NULL OR overall_rating BETWEEN 0 AND 10"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    faculty_id = Column(String, ForeignKey("faculty.faculty_id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    academic_year = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=True)
    teaching_quality = Column(Integer, nullable=True)
    subject_knowledge = Column(Integer, nullable=True)
    communication_skills = Column(Integer, nullable=True)
    student_interaction = Column(Integer, nullable=True)
    overall_rating = Column(Integer, nullable=True)
    comments = Column(Text, nullable=True)
    token_id = Column(Integer, ForeignKey("anonymous_feedback_tokens.id"), nullable=True, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    department = Column(String, nullable=True, index=True)
    faculty_rating = Column(Integer, nullable=True)
    course_content = Column(Integer, nullable=True)
    learning_resources = Column(Integer, nullable=True)
    faculty_support = Column(Integer, nullable=True)
    overall_satisfaction = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    semester = Column(String, nullable=True, index=True)
    course_difficulty = Column(String, nullable=True)
    google_sheet_response_hash = Column(String, nullable=True, index=True)
    improvement_areas = Column(Text, nullable=True)
    suggestions = Column(Text, nullable=True)


class AnonymousFeedbackToken(Base):
    __tablename__ = "anonymous_feedback_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_anonymous_feedback_token_hash"),
        CheckConstraint("used IN (0, 1)"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    token_hash = Column(String, nullable=False)
    faculty_id = Column(String, ForeignKey("faculty.faculty_id"), nullable=False, index=True)
    academic_year = Column(String, nullable=False, index=True)
    used = Column(Integer, nullable=False, default=0)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class StudentAttendance(Base):
    __tablename__ = "student_attendance"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String, nullable=False, index=True)
    enrollment_number = Column(String, nullable=True, index=True)
    student_name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    section = Column(String, nullable=True, default=None)
    semester = Column(String, nullable=True, default=None, index=True)
    academic_year = Column(String, nullable=False)
    total_classes = Column(Integer, nullable=False, default=0)
    attended_classes = Column(Integer, nullable=False, default=0)
    attendance_percentage = Column(Float, nullable=False, default=0.0)
    average_attendance = Column(Float, nullable=False, default=0.0)
    subjects_json = Column(Text, nullable=False, default='[]')
    subject_values_json = Column(Text, nullable=False, default='{}')

    @property
    def subjects(self):
        return [subject for subject in json.loads(self.subjects_json or '[]') if subject.lower() not in {'s.no', 's.no.', 's no', 'serial no', 'serial number'}]

    @property
    def subject_values(self):
        ignored = {'s.no', 's.no.', 's no', 'serial no', 'serial number'}
        return {key: value for key, value in json.loads(self.subject_values_json or '{}').items() if key.lower() not in ignored}

    @property
    def academicYear(self):
        return self.academic_year

from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from database import Base


class StudentUpload(Base):
    __tablename__ = "student_uploads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    studentId = Column(String, nullable=False)
    enrollment_number = Column(String, nullable=True, index=True)
    studentName = Column(String, nullable=False)
    department = Column(String, nullable=True, default="Artificial Intelligence and Data Science (AIDS)")
    totalMarks = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    academic_year = Column(String, nullable=False, default="2024-2025", index=True)
    dm = Column(Integer, nullable=True)
    dsc = Column(Integer, nullable=True)
    coa = Column(Integer, nullable=True)
    python_marks = Column(Integer, nullable=True)
    ml = Column(Integer, nullable=True)
    subject_marks_json = Column(Text, nullable=True, default='{}')
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
    def has_all_five_subjects(self):
        marks = self.subject_marks
        if not marks:
            return False
        for subj in ("DM", "DSC", "COA", "Python", "ML"):
            if marks.get(subj) is None:
                return False
        return True

    @property
    def passed_all_subjects(self):
        marks = self.subject_marks
        if not self.has_all_five_subjects:
            return False
        return all(int(marks[subj]) >= 40 for subj in ("DM", "DSC", "COA", "Python", "ML"))


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

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    academic_year = Column(String, nullable=False, index=True)
    department = Column(String, nullable=False, index=True)
    teaching_quality = Column(Integer, nullable=False)
    course_content = Column(Integer, nullable=False)
    learning_resources = Column(Integer, nullable=False)
    faculty_support = Column(Integer, nullable=False)
    overall_satisfaction = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class StudentAttendance(Base):
    __tablename__ = "student_attendance"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String, nullable=False, index=True)
    enrollment_number = Column(String, nullable=True, index=True)
    student_name = Column(String, nullable=False)
    department = Column(String, nullable=False)
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


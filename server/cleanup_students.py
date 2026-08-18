"""
Script to remove all student data from the database
"""
from database import SessionLocal, engine
from models import StudentUpload, StudentAttendance
from sqlalchemy import text

def cleanup_student_data():
    """Delete all student data from the database"""
    db = SessionLocal()
    try:
        # Delete all records from student_uploads table
        student_uploads_count = db.query(StudentUpload).delete()
        print(f"✓ Deleted {student_uploads_count} records from student_uploads table")
        
        # Delete all records from student_attendance table
        student_attendance_count = db.query(StudentAttendance).delete()
        print(f"✓ Deleted {student_attendance_count} records from student_attendance table")
        
        # Commit the changes
        db.commit()
        print("\n✓ All student data has been successfully removed from the database")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error during cleanup: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting cleanup of student data...\n")
    cleanup_student_data()

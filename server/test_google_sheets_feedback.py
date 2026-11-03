import os
import sys
import unittest
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

test_engine = create_engine("sqlite:///:memory:")
TestSession = sessionmaker(bind=test_engine)

import database
database.init_db = lambda: None
database.SessionLocal = TestSession
database.engine = test_engine

import models
models.Base.metadata.create_all(bind=test_engine)

import services


class TestGoogleSheetsFeedbackIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = test_engine
        cls.Session = TestSession

    def setUp(self):
        self.db = self.Session()
        if not self.db.query(models.Department).first():
            self.db.add_all([
                models.Department(id=1, code="CSE", name="Computer Science & Engineering"),
                models.Department(id=2, code="BCA", name="Bachelor of Computer Applications"),
                models.Department(id=3, code="AIDS", name="AI & Data Science"),
            ])
            self.db.commit()

    def tearDown(self):
        self.db.query(models.StudentFeedback).delete()
        self.db.commit()
        self.db.close()

    def test_normalize_academic_year(self):
        self.assertEqual(services.normalize_academic_year("2025 - 2026"), "2025-2026")
        self.assertEqual(services.normalize_academic_year(" 2024 - 2025 "), "2024-2025")
        self.assertEqual(services.normalize_academic_year("2024–2025"), "2024-2025")
        self.assertEqual(services.normalize_academic_year("2025/2026"), "2025-2026")

    def test_parse_improvement_areas(self):
        text = "Teaching methods and explanation of concepts, More practical learning and hands-on activities"
        areas = services.parse_improvement_areas(text)
        self.assertEqual(len(areas), 2)
        self.assertIn("Teaching methods and explanation of concepts", areas)
        self.assertIn("More practical learning and hands-on activities", areas)

        single = services.parse_improvement_areas("No improvements needed")
        self.assertEqual(single, ["No improvements needed"])

    def test_dynamic_header_mapping_new_form_and_sheet_variants(self):
        headers = [
            "Timestamp",
            "Department ",
            "  Academic Year  ",
            "  Semester  ",
            "  Subject Name  ",
            "  Teaching Effectiveness  ",
            "  Communication Skills  ",
            "  Doubt Clarification  ",
            "  Course Difficulty Level   [Easy]",
            "  Course Difficulty Level   [Moderate]",
            "  Course Difficulty Level   [Hard]",
            "  Overall Learning Experience  ",
            "What areas do you think should be improved? ",
            "Do you have any additional suggestions to improve your learning experience?",
        ]
        mapping = services.map_feedback_headers(headers)
        self.assertEqual(mapping[0], "timestamp")
        self.assertEqual(mapping[1], "department")
        self.assertEqual(mapping[2], "academic_year")
        self.assertEqual(mapping[3], "semester")
        self.assertEqual(mapping[4], "subject")
        self.assertEqual(mapping[5], "teaching_quality")
        self.assertEqual(mapping[6], "communication_skills")
        self.assertEqual(mapping[7], "student_interaction")
        self.assertEqual(mapping[8], "difficulty_easy")
        self.assertEqual(mapping[9], "difficulty_moderate")
        self.assertEqual(mapping[10], "difficulty_hard")
        self.assertEqual(mapping[11], "overall_satisfaction")
        self.assertEqual(mapping[12], "improvement_areas")
        self.assertEqual(mapping[13], "suggestions")

    def test_import_final_and_legacy_form_structures(self):
        # 1. New Google Form response structure
        new_headers = [
            "Timestamp",
            "Department",
            "Academic Year",
            "Semester",
            "Overall Learning Experience",
            "What areas do you think should be improved?",
            "Do you have any additional suggestions to improve your learning experience?",
        ]
        new_row1 = [
            "03/11/2026 20:30:00",
            "CSE",
            "2025 - 2026",
            "3",
            "5",
            "Teaching methods and explanation of concepts, More practical learning and hands-on activities",
            "Great lab facilities, need more coding challenges.",
        ]
        new_row2 = [
            "03/11/2026 20:31:00",
            "AI & Data Science",
            "2024 - 2025",
            "1",
            "4",
            "More real-world examples and case studies",
            "More industry guest lectures please.",
        ]

        # 2. Previous spreadsheet structure (from actual sheet)
        old_headers = [
            "Timestamp",
            "Department ",
            "  Academic Year  ",
            "  Semester  ",
            "  Subject Name  ",
            "  Teaching Effectiveness  ",
            "  Communication Skills  ",
            "  Doubt Clarification  ",
            "  Course Difficulty Level   [Easy]",
            "  Course Difficulty Level   [Moderate]",
            "  Course Difficulty Level   [Hard]",
            "  Overall Learning Experience  ",
            "What areas do you think should be improved? ",
        ]
        old_row1 = [
            "03/11/2026 20:12:23",
            "AI & Data Science",
            "2025 - 2026",
            "3",
            "AI",
            "4",
            "5",
            "4",
            "Column 1",
            "Column 1",
            "Column 1",
            "4",
            "",
        ]

        # Import new format rows
        res_new = services.import_google_sheet_feedback(self.db, raw_rows=[new_headers, new_row1, new_row2])
        self.assertEqual(res_new["imported"], 2)
        self.assertEqual(res_new["skipped"], 0)
        self.assertEqual(res_new["total_rows"], 2)

        # Import old format row (Row 1 from previous response)
        res_old = services.import_google_sheet_feedback(self.db, raw_rows=[old_headers, old_row1])
        self.assertEqual(res_old["imported"], 1)
        self.assertEqual(res_old["skipped"], 0)

        # Re-importing old format row should skip duplicate
        res_old_dup = services.import_google_sheet_feedback(self.db, raw_rows=[old_headers, old_row1])
        self.assertEqual(res_old_dup["imported"], 0)
        self.assertEqual(res_old_dup["skipped"], 1)

        # Verify old row has overall_satisfaction mapped
        fb_old = self.db.query(models.StudentFeedback).filter_by(subject="AI").first()
        self.assertIsNotNone(fb_old)
        self.assertEqual(fb_old.overall_satisfaction, 4)
        self.assertEqual(fb_old.academic_year, "2025-2026")
        self.assertEqual(fb_old.semester, "Semester 3")
        self.assertEqual(fb_old.department, "AI & Data Science")

        # Verify new row 1
        fb_new = self.db.query(models.StudentFeedback).filter_by(department="Computer Science and Engineering").first()
        self.assertIsNotNone(fb_new)
        self.assertEqual(fb_new.overall_satisfaction, 5)
        self.assertEqual(fb_new.semester, "Semester 3")
        self.assertEqual(fb_new.academic_year, "2025-2026")
        self.assertIn("Teaching methods", fb_new.improvement_areas)
        self.assertIn("Great lab facilities", fb_new.suggestions)

        # Test KPI Summary output
        import main
        admin_dummy = models.AdminUser(username="admin", is_active=1)

        summary = main.get_student_feedback_summary(
            academic_year="2025-2026",
            department="All",
            semester="All",
            db=self.db,
            _=admin_dummy,
        )

        # 2 responses for 2025-2026: one 5 rating and one 4 rating -> avg 4.5
        self.assertEqual(summary["total_responses"], 2)
        self.assertEqual(summary["average_overall_satisfaction"], 4.5)
        self.assertEqual(summary["rating_distribution"][5], 1)
        self.assertEqual(summary["rating_distribution"][4], 1)

        # Check improvement areas summary ranking
        imp_summary = summary["improvement_areas_summary"]
        self.assertIsInstance(imp_summary, list)
        self.assertTrue(len(imp_summary) >= 6)
        # "Teaching methods..." was selected once
        tm_item = next(item for item in imp_summary if "Teaching methods" in item["area"])
        self.assertEqual(tm_item["count"], 1)

        # Check student suggestions list
        sugg_list = summary["student_suggestions"]
        self.assertEqual(len(sugg_list), 1)
        self.assertIn("Great lab facilities", sugg_list[0]["suggestion"])

    def test_blank_optional_fields_and_multiple_checkboxes(self):
        headers = [
            "Timestamp",
            "Department",
            "Academic Year",
            "Semester",
            "Overall Learning Experience",
            "What areas do you think should be improved?",
            "Do you have any additional suggestions to improve your learning experience?",
        ]
        # Blank suggestions and single checkbox
        row1 = ["03/11/2026 21:00:00", "CSE", "2024 - 2025", "2", "3", "No improvements needed", ""]
        # Blank improvement areas and filled suggestions
        row2 = ["03/11/2026 21:01:00", "AI & Data Science", "2024 - 2025", "1", "4", "", "Provide lab recordings."]

        res = services.import_google_sheet_feedback(self.db, raw_rows=[headers, row1, row2])
        self.assertEqual(res["imported"], 2)
        self.assertEqual(res["skipped"], 0)
        self.assertEqual(res["failed"], 0)

        # Re-import should skip both
        res_dup = services.import_google_sheet_feedback(self.db, raw_rows=[headers, row1, row2])
        self.assertEqual(res_dup["imported"], 0)
        self.assertEqual(res_dup["skipped"], 2)


if __name__ == "__main__":
    unittest.main()

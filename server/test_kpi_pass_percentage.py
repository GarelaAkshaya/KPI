import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import SessionLocal
import services
import schemas
from pydantic import TypeAdapter
from typing import List


class TestPassPercentageKPI(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_1_bca_2024_2025(self):
        """Test 1: BCA – Academic Year 2024–2025."""
        res = services.get_pass_percentage_kpi(self.db, academic_year="2024-2025", department="BCA")
        self.assertEqual(res["total_students_evaluated"], 0)
        self.assertIn("No evaluated student marks", res["message"])
        validated = schemas.PassPercentageKPIResponse.model_validate(res)
        self.assertEqual(validated.total_students_evaluated, 0)

    def test_2_bca_all_sections_2025_2026(self):
        """Test 2: BCA with All Sections (2025-2026)."""
        res = services.get_pass_percentage_kpi(self.db, academic_year="2025-2026", department="BCA", section=None, semester="All")
        self.assertEqual(res["total_students_evaluated"], 120)
        self.assertEqual(res["overall"]["passed"], 87)
        self.assertEqual(res["overall"]["failed"], 33)
        self.assertEqual(res["overall_pass_percentage"], 72.5)
        self.assertEqual(len(res["subjects"]), 1)
        self.assertEqual(res["subjects"][0]["subject"], "OOPs")
        self.assertEqual(res["subjects"][0]["passed"], 87)
        self.assertEqual(res["subjects"][0]["pass_percentage"], 72.5)
        validated = schemas.PassPercentageKPIResponse.model_validate(res)
        self.assertEqual(validated.overall_pass_percentage, 72.5)

    def test_3_bca_individual_section_csem3(self):
        """Test 3: BCA with Section CSEM-3 (2025-2026, Semester 3)."""
        res = services.get_pass_percentage_kpi(self.db, academic_year="2025-2026", department="BCA", section="CSEM-3", semester="Semester 3")
        self.assertEqual(res["total_students_evaluated"], 120)
        self.assertEqual(res["overall"]["passed"], 87)
        self.assertEqual(res["overall"]["failed"], 33)
        self.assertEqual(res["overall_pass_percentage"], 72.5)
        self.assertEqual(len(res["subjects"]), 1)
        self.assertEqual(res["subjects"][0]["subject"], "OOPs")
        validated = schemas.PassPercentageKPIResponse.model_validate(res)
        self.assertEqual(validated.total_students_evaluated, 120)

    def test_3b_bca_individual_section_c(self):
        """Test 3b: BCA with Section C (2025-2026, Semester 3)."""
        res = services.get_pass_percentage_kpi(self.db, academic_year="2025-2026", department="BCA", section="C", semester="Semester 3")
        self.assertEqual(res["total_students_evaluated"], 120)
        self.assertEqual(res["overall"]["passed"], 87)
        self.assertEqual(res["overall"]["failed"], 33)
        self.assertEqual(res["overall_pass_percentage"], 72.5)

    def test_4_bca_semesters(self):
        """Test 4: BCA with each available semester."""
        for sem in ["Semester 1", "Semester 2", "Semester 4"]:
            res = services.get_pass_percentage_kpi(self.db, academic_year="2025-2026", department="BCA", section="CSEM-3", semester=sem)
            self.assertEqual(res["total_students_evaluated"], 0)
        
        res3 = services.get_pass_percentage_kpi(self.db, academic_year="2025-2026", department="BCA", section="CSEM-3", semester="Semester 3")
        self.assertEqual(res3["total_students_evaluated"], 120)
        self.assertEqual(res3["overall_pass_percentage"], 72.5)

    def test_5_cse_and_aids_existing(self):
        """Test 5: CSE and AIDS existing results still work."""
        cse = services.get_pass_percentage_kpi(self.db, academic_year="2024-2025", department="Computer Science and Engineering", section="B", semester="Semester 1")
        self.assertEqual(cse["total_students_evaluated"], 50)
        self.assertEqual(cse["overall_pass_percentage"], 42.0)
        self.assertEqual(len(cse["subjects"]), 5)

        aids = services.get_pass_percentage_kpi(self.db, academic_year="2025-2026", department="AI & Data Science", section="A", semester="Semester 3")
        self.assertEqual(aids["total_students_evaluated"], 50)
        self.assertEqual(aids["overall_pass_percentage"], 38.0)
        self.assertEqual(len(aids["subjects"]), 5)

    def test_6_decimal_marks_preserved(self):
        """Test 6: Decimal marks returned by the backend without rounding."""
        students = services.get_all_students(self.db, department="BCA")
        self.assertEqual(len(students), 120)
        adapter = TypeAdapter(List[schemas.StudentUploadSchema])
        validated_students = adapter.validate_python(students)
        targets = {
            "24BCAHH010045": 63.2,
            "24BCAHH010044": 46.7,
            "24BCAHH010043": 56.3,
            "24BCAHH010034": 57.25,
        }
        for s in validated_students:
            if s.enrollmentNumber in targets:
                self.assertEqual(s.subject_marks["OOPs"], targets[s.enrollmentNumber])
                self.assertIsInstance(s.subject_marks["OOPs"], float)

    def test_7_section_filter_options(self):
        """Test 7: Section filter options include CSEM-3 for BCA."""
        sec_options = services.get_available_sections(self.db, academic_year="2025-2026", department="BCA", semester="Semester 3")
        sections = [o["section"] for o in sec_options]
        self.assertIn("CSEM-3", sections)
        self.assertIn("C", sections)


if __name__ == "__main__":
    unittest.main()


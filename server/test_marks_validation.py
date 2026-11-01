import unittest
import io
import math
import openpyxl
import pandas as pd
import numpy as np

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import services
import schemas


class TestMarksValidation(unittest.TestCase):
    """Test suite for Excel marks upload validation covering:
    - Blank cells
    - NaN values
    - Explicit zero marks
    - Valid marks preservation & total calculation
    - Invalid non-numeric marks
    - Marks outside permitted ranges
    """

    def test_blank_and_nan_cells_converted_to_zero(self):
        """Test that blank, empty, and NaN assessment cells convert to 0.0 without rejecting upload."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "OOPS"
        headers = ['S#', 'Enrolno', 'Name', 'Test 1\n15 M', 'Lab-1\n15 M', 'Test 2\n15 M', 'Lab-2\n15 M', 'Compre\n40M', 'Total\n100 M']
        ws.append(headers)

        # Student 1: Test 1 is None (empty cell) -> should convert to 0.0
        ws.append([1, '24BCAS001', 'Student 1', None, 14.0, 11.0, 13.0, 35.0, None])
        # Student 2: Lab-1 is empty string "" -> should convert to 0.0
        ws.append([2, '24BCAS002', 'Student 2', 12.0, '', 11.0, 13.0, 35.0, None])
        # Student 3: Test 2 is whitespace "   " -> should convert to 0.0
        ws.append([3, '24BCAS003', 'Student 3', 12.0, 14.0, '   ', 13.0, 35.0, None])
        # Student 4: Lab-2 is NaN -> should convert to 0.0
        ws.append([4, '24BCAS004', 'Student 4', 12.0, 14.0, 11.0, float('nan'), 35.0, None])
        # Student 5: Compre is None -> should convert to 0.0
        ws.append([5, '24BCAS005', 'Student 5', 12.0, 14.0, 11.0, 13.0, None, None])

        buf = io.BytesIO()
        wb.save(buf)
        contents = buf.getvalue()

        preview = services.parse_semester_workbook_for_preview(
            file_contents=contents,
            file_name="test_blank_nan.xlsx",
            academic_year="2024-2025",
            department="BCA",
            section="A",
            semester="Semester 1",
            subject="OOPS",
        )

        self.assertTrue(preview["valid"], f"Expected upload preview to be valid, errors: {preview.get('errors')}")
        self.assertEqual(len(preview["errors"]), 0)
        sheet = preview["sheets"][0]
        self.assertEqual(sheet["valid_rows"], 5)
        self.assertEqual(sheet["student_count"], 5)

        # Student 1: Test 1 was None -> 0.0. Total = 0.0 + 14.0 + 11.0 + 13.0 + 35.0 = 73.0
        s1 = sheet["rows"][0]
        self.assertEqual(s1["test1"], 0.0)
        self.assertEqual(s1["lab1"], 14.0)
        self.assertEqual(s1["total"], 73.0)

        # Student 2: Lab-1 was "" -> 0.0. Total = 12.0 + 0.0 + 11.0 + 13.0 + 35.0 = 71.0
        s2 = sheet["rows"][1]
        self.assertEqual(s2["test1"], 12.0)
        self.assertEqual(s2["lab1"], 0.0)
        self.assertEqual(s2["total"], 71.0)

        # Student 3: Test 2 was "   " -> 0.0. Total = 12.0 + 14.0 + 0.0 + 13.0 + 35.0 = 74.0
        s3 = sheet["rows"][2]
        self.assertEqual(s3["test2"], 0.0)
        self.assertEqual(s3["total"], 74.0)

        # Student 4: Lab-2 was NaN -> 0.0. Total = 12.0 + 14.0 + 11.0 + 0.0 + 35.0 = 72.0
        s4 = sheet["rows"][3]
        self.assertEqual(s4["lab2"], 0.0)
        self.assertEqual(s4["total"], 72.0)

        # Student 5: Compre was None -> 0.0. Total = 12.0 + 14.0 + 11.0 + 13.0 + 0.0 = 50.0
        s5 = sheet["rows"][4]
        self.assertEqual(s5["compre"], 0.0)
        self.assertEqual(s5["total"], 50.0)

    def test_explicit_zero_marks_preserved(self):
        """Test that explicit numeric 0, 0.0, and string '0' are correctly parsed as 0.0."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "OOPS"
        headers = ['S#', 'Enrolno', 'Name', 'Test 1 (15)', 'Lab-1 (15)', 'Test 2 (15)', 'Lab-2 (15)', 'Compre (40)', 'Total (100)']
        ws.append(headers)

        ws.append([1, '24BCAS001', 'Student 1', 0, 0.0, '0', 10.0, 30.0, None])

        buf = io.BytesIO()
        wb.save(buf)
        contents = buf.getvalue()

        preview = services.parse_semester_workbook_for_preview(
            file_contents=contents,
            file_name="test_explicit_zero.xlsx",
            academic_year="2024-2025",
            department="BCA",
            section="A",
            semester="Semester 1",
            subject="OOPS",
        )

        self.assertTrue(preview["valid"])
        row = preview["sheets"][0]["rows"][0]
        self.assertEqual(row["test1"], 0.0)
        self.assertEqual(row["lab1"], 0.0)
        self.assertEqual(row["test2"], 0.0)
        self.assertEqual(row["lab2"], 10.0)
        self.assertEqual(row["compre"], 30.0)
        self.assertEqual(row["total"], 40.0)

    def test_all_components_blank_converts_to_zero_total(self):
        """Test that a student with all assessment components blank gets 0.0 total."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "OOPS"
        headers = ['S#', 'Enrolno', 'Name', 'Test 1 (15)', 'Lab-1 (15)', 'Test 2 (15)', 'Lab-2 (15)', 'Compre (40)', 'Total (100)']
        ws.append(headers)

        ws.append([1, '24BCAS001', 'Student 1', None, None, None, None, None, None])

        buf = io.BytesIO()
        wb.save(buf)
        contents = buf.getvalue()

        preview = services.parse_semester_workbook_for_preview(
            file_contents=contents,
            file_name="test_all_blank.xlsx",
            academic_year="2024-2025",
            department="BCA",
            section="A",
            semester="Semester 1",
            subject="OOPS",
        )

        self.assertTrue(preview["valid"])
        row = preview["sheets"][0]["rows"][0]
        self.assertEqual(row["test1"], 0.0)
        self.assertEqual(row["lab1"], 0.0)
        self.assertEqual(row["test2"], 0.0)
        self.assertEqual(row["lab2"], 0.0)
        self.assertEqual(row["compre"], 0.0)
        self.assertEqual(row["total"], 0.0)

    def test_invalid_non_numeric_marks_rejected(self):
        """Test that non-numeric values (e.g. 'AB', 'Absent') are rejected with validation errors."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "OOPS"
        headers = ['S#', 'Enrolno', 'Name', 'Test 1 (15)', 'Lab-1 (15)', 'Test 2 (15)', 'Lab-2 (15)', 'Compre (40)', 'Total (100)']
        ws.append(headers)

        ws.append([1, '24BCAS001', 'Student 1', 'AB', 12.0, 10.0, 12.0, 30.0, None])

        buf = io.BytesIO()
        wb.save(buf)
        contents = buf.getvalue()

        preview = services.parse_semester_workbook_for_preview(
            file_contents=contents,
            file_name="test_non_numeric.xlsx",
            academic_year="2024-2025",
            department="BCA",
            section="A",
            semester="Semester 1",
            subject="OOPS",
        )

        self.assertFalse(preview["valid"])
        self.assertTrue(any("Invalid mark 'AB' for Test 1. Must be numeric" in err for err in preview["errors"]))

    def test_marks_outside_permitted_ranges_rejected(self):
        """Test that marks exceeding component maximums (15 for tests/labs, 40 for compre) are rejected."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "OOPS"
        headers = ['S#', 'Enrolno', 'Name', 'Test 1 (15)', 'Lab-1 (15)', 'Test 2 (15)', 'Lab-2 (15)', 'Compre (40)', 'Total (100)']
        ws.append(headers)

        # Student 1: Test 1 = 18 (> 15)
        ws.append([1, '24BCAS001', 'Student 1', 18.0, 12.0, 10.0, 12.0, 30.0, None])
        # Student 2: Compre = 45 (> 40)
        ws.append([2, '24BCAS002', 'Student 2', 12.0, 12.0, 10.0, 12.0, 45.0, None])
        # Student 3: Lab-1 = -2 (< 0)
        ws.append([3, '24BCAS003', 'Student 3', 12.0, -2.0, 10.0, 12.0, 30.0, None])

        buf = io.BytesIO()
        wb.save(buf)
        contents = buf.getvalue()

        preview = services.parse_semester_workbook_for_preview(
            file_contents=contents,
            file_name="test_range_error.xlsx",
            academic_year="2024-2025",
            department="BCA",
            section="A",
            semester="Semester 1",
            subject="OOPS",
        )

        self.assertFalse(preview["valid"])
        err_str = " ".join(preview["errors"])
        self.assertIn("Mark 18.0 for Test 1 outside range [0, 15]", err_str)
        self.assertIn("Mark 45.0 for Compre outside range [0, 40]", err_str)
        self.assertIn("Mark -2.0 for Lab-1 outside range [0, 15]", err_str)

    def test_120_students_with_mixed_blanks_and_valid_marks(self):
        """Test 120-student BCA dataset where multiple students have blanks; upload must succeed and compute exact totals."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "OOPS"
        headers = ['S#', 'Enrolno', 'Name', 'Test 1\n15 M', 'Lab-1\n15 M', 'Test 2\n15 M', 'Lab-2\n15 M', 'Compre\n40M', 'Total\n100 M']
        ws.append(headers)

        expected_totals = []
        for i in range(1, 121):
            enrol = f"24BCAS{i:03d}"
            name = f"Student {i}"
            # Some students have blank cells in different components
            t1 = None if i % 10 == 1 else 12.0
            l1 = '' if i % 10 == 2 else 14.0
            t2 = float('nan') if i % 10 == 3 else 11.0
            l2 = None if i % 10 == 4 else 13.0
            comp = None if i % 10 == 5 else 35.0

            # Expected sum with blanks treated as 0.0
            c_t1 = 0.0 if t1 is None else 12.0
            c_l1 = 0.0 if l1 == '' else 14.0
            c_t2 = 0.0 if math.isnan(t2) else 11.0
            c_l2 = 0.0 if l2 is None else 13.0
            c_comp = 0.0 if comp is None else 35.0
            expected_tot = round(c_t1 + c_l1 + c_t2 + c_l2 + c_comp, 2)
            expected_totals.append(expected_tot)

            ws.append([i, enrol, name, t1, l1, t2, l2, comp, None])

        buf = io.BytesIO()
        wb.save(buf)
        contents = buf.getvalue()

        preview = services.parse_semester_workbook_for_preview(
            file_contents=contents,
            file_name="bca_oops_120_mixed_blanks.xlsx",
            academic_year="2024-2025",
            department="BCA",
            section="A",
            semester="Semester 1",
            subject="OOPS",
        )

        self.assertTrue(preview["valid"], f"Validation failed with errors: {preview.get('errors')}")
        self.assertEqual(len(preview["errors"]), 0)
        self.assertEqual(preview["total_students"], 120)

        sheet = preview["sheets"][0]
        self.assertEqual(sheet["valid_rows"], 120)
        for i, row in enumerate(sheet["rows"]):
            self.assertEqual(row["total"], expected_totals[i], f"Mismatch for student {i+1}")

        expected_avg = round(sum(expected_totals) / len(expected_totals), 2)
        self.assertEqual(sheet["average_total"], expected_avg)

    def test_legacy_normalize_student_rows_blanks(self):
        """Test that legacy 5-subject files convert blank/NaN cells to 0."""
        raw_rows = [
            {
                "Enrollment Number": "23STUCHH001",
                "Student Name": "Student One",
                "Department": "AIDS",
                "Section": "A",
                "DM": 80,
                "DSC": None,  # Blank -> 0
                "COA": 75,
                "Python": "",  # Empty string -> 0
                "ML": float('nan'),  # NaN -> 0
            }
        ]
        records, has_invalid = services.normalize_student_rows(
            raw_rows=raw_rows,
            academic_year="2024-2025",
            department="Artificial Intelligence and Data Science (AIDS)",
            section="A",
        )
        self.assertFalse(has_invalid)
        self.assertEqual(len(records), 1)
        r = records[0]
        self.assertEqual(r["dm"], 80)
        self.assertEqual(r["dsc"], 0)
        self.assertEqual(r["coa"], 75)
        self.assertEqual(r["python_marks"], 0)
        self.assertEqual(r["ml"], 0)
        self.assertEqual(r["totalMarks"], 155)  # 80 + 0 + 75 + 0 + 0 = 155
        self.assertEqual(r["percentage"], 31.0)  # 155 / 500 * 100 = 31.0

    def test_exact_decimal_preservation(self):
        """Test that fractional non-empty marks (e.g. 11.5, 13.75) are preserved without truncation."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "OOPS"
        headers = ['S#', 'Enrolno', 'Name', 'Test 1 (15)', 'Lab-1 (15)', 'Test 2 (15)', 'Lab-2 (15)', 'Compre (40)', 'Total (100)']
        ws.append(headers)
        ws.append([1, '24BCAS001', 'Student 1', 11.5, 13.25, None, 14.75, 33.5, None])

        buf = io.BytesIO()
        wb.save(buf)
        contents = buf.getvalue()

        preview = services.parse_semester_workbook_for_preview(
            file_contents=contents,
            file_name="test_decimal.xlsx",
            academic_year="2024-2025",
            department="BCA",
            section="A",
            semester="Semester 1",
            subject="OOPS",
        )
        self.assertTrue(preview["valid"])
        row = preview["sheets"][0]["rows"][0]
        self.assertEqual(row["test1"], 11.5)
        self.assertEqual(row["lab1"], 13.25)
        self.assertEqual(row["test2"], 0.0)  # Blank converted to 0.0
        self.assertEqual(row["lab2"], 14.75)
        self.assertEqual(row["compre"], 33.5)
        # 11.5 + 13.25 + 0.0 + 14.75 + 33.5 = 73.0
        self.assertEqual(row["total"], 73.0)

    def test_single_column_total_blank_converts_to_zero(self):
        """Test that single-column Total format converts blank total to 0.0."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "OOPS"
        headers = ['S#', 'Enrolno', 'Name', 'Total (100)']
        ws.append(headers)
        ws.append([1, '24BCAS001', 'Student 1', None])
        ws.append([2, '24BCAS002', 'Student 2', 65.5])

        buf = io.BytesIO()
        wb.save(buf)
        contents = buf.getvalue()

        preview = services.parse_semester_workbook_for_preview(
            file_contents=contents,
            file_name="test_total_only.xlsx",
            academic_year="2024-2025",
            department="BCA",
            section="A",
            semester="Semester 1",
            subject="OOPS",
        )
        self.assertTrue(preview["valid"])
        rows = preview["sheets"][0]["rows"]
        self.assertEqual(rows[0]["total"], 0.0)
        self.assertEqual(rows[1]["total"], 65.5)

    def test_student_upload_schema_accepts_decimal_marks(self):
        """Test that StudentUploadSchema correctly validates decimal marks without int_from_float errors."""
        test_payload = {
            "id": 1,
            "studentId": "24BCAHH010045",
            "enrollmentNumber": "24BCAHH010045",
            "studentName": "PUNYAVANTULA DHARANEEDHAR",
            "department": "BCA",
            "section": "C",
            "semester": "Semester 3",
            "academicYear": "2025-2026",
            "totalMarks": 63.2,
            "percentage": 63.2,
            "subject_marks": {
                "OOPs": 63.2
            },
            "createdAt": "2026-11-01 12:00:00"
        }

        # Should validate without raising ValidationError (e.g. int_from_float)
        validated = schemas.StudentUploadSchema.model_validate(test_payload)
        self.assertEqual(validated.subject_marks["OOPs"], 63.2)
        self.assertEqual(validated.totalMarks, 63.2)
        self.assertIsInstance(validated.subject_marks["OOPs"], float)

    def test_student_upload_schema_exact_target_decimal_values(self):
        """Test exact target decimal values: 63.2, 46.7, 56.3, and 57.25."""
        target_values = [63.2, 46.7, 56.3, 57.25]
        for val in target_values:
            payload = {
                "id": 100,
                "studentId": "TEST_STUDENT",
                "studentName": "Test Student",
                "totalMarks": int(round(val)),
                "percentage": float(val),
                "subject_marks": {
                    "OOPs": val
                },
                "createdAt": "2026-11-01 12:00:00"
            }
            validated = schemas.StudentUploadSchema.model_validate(payload)
            self.assertEqual(validated.subject_marks["OOPs"], val)
            self.assertEqual(validated.model_dump()["subject_marks"]["OOPs"], val)

    def test_student_upload_schema_integer_and_null_marks_preserved(self):
        """Test that integer marks and None marks are preserved accurately."""
        payload = {
            "id": 200,
            "studentId": "24STUCHH010050",
            "studentName": "John Doe",
            "department": "Artificial Intelligence and Data Science (AIDS)",
            "totalMarks": 303,
            "percentage": 60.6,
            "dm": 65,
            "dsc": 58,
            "coa": 80,
            "python_marks": 34,
            "ml": 66,
            "subject_marks": {
                "AI": 65,
                "IoT": 58,
                "OOPs": 80,
                "DBMS": None
            },
            "createdAt": "2026-11-01 12:00:00"
        }
        validated = schemas.StudentUploadSchema.model_validate(payload)
        self.assertEqual(validated.totalMarks, 303)
        self.assertIsInstance(validated.totalMarks, int)
        self.assertEqual(validated.subject_marks["AI"], 65)
        self.assertIsNone(validated.subject_marks["DBMS"])


if __name__ == "__main__":
    unittest.main()

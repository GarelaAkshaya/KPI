import database, models, services


def test_repeating_sections_across_departments():
    db = next(database.get_db())

    # Create dummy records with repeating section 'TEST_SEC' across two departments
    dept1 = "Computer Science and Engineering"
    dept2 = "AI & Data Science"
    sec_name = "TEST_SEC"

    # Clean up any previous test records
    db.query(models.StudentUpload).filter(models.StudentUpload.studentId.in_(["TEST_CSE_01", "TEST_AIDS_01"])).delete()
    db.query(models.StudentAttendance).filter(models.StudentAttendance.student_id.in_(["TEST_CSE_01", "TEST_AIDS_01"])).delete()
    db.commit()

    # Insert student for CSE, section TEST_SEC
    student_cse = models.StudentUpload(
        studentId="TEST_CSE_01",
        studentName="CSE Student",
        totalMarks=450,
        percentage=90.0,
        department=dept1,
        section=sec_name,
        academic_year="2024-2025",
        dm=90, dsc=90, coa=90, python_marks=90, ml=90,
    )
    # Insert student for AIDS, section TEST_SEC
    student_aids = models.StudentUpload(
        studentId="TEST_AIDS_01",
        studentName="AIDS Student",
        totalMarks=200,
        percentage=40.0,
        department=dept2,
        section=sec_name,
        academic_year="2024-2025",
        dm=40, dsc=40, coa=40, python_marks=40, ml=40,
    )
    db.add_all([student_cse, student_aids])
    db.commit()

    try:
        # 1. Verify get_available_sections returns BOTH sections separately identified
        sections = services.get_available_sections(db, academic_year="2024-2025")
        matching = [s for s in sections if s["section"] == sec_name]
        assert len(matching) == 2, f"Expected 2 sections for {sec_name}, got {len(matching)}: {matching}"

        cse_option = next(s for s in matching if s["department"] == dept1)
        aids_option = next(s for s in matching if s["department"] == dept2)

        assert cse_option["value"] == f"{sec_name}::{dept1}"
        assert aids_option["value"] == f"{sec_name}::{dept2}"
        assert dept1 in cse_option["label"]
        assert dept2 in aids_option["label"]
        print("[PASS] Available sections distinguishes repeating section names across departments")

        # 2. Verify _apply_scope with CSE option returns ONLY CSE student
        cse_students = services._apply_scope(db.query(models.StudentUpload), models.StudentUpload, "2024-2025", section=cse_option["value"]).all()
        assert len(cse_students) == 1
        assert cse_students[0].studentId == "TEST_CSE_01"
        assert cse_students[0].percentage == 90.0
        print("[PASS] Scoping by CSE section returns only CSE data")

        # 3. Verify _apply_scope with AIDS option returns ONLY AIDS student
        aids_students = services._apply_scope(db.query(models.StudentUpload), models.StudentUpload, "2024-2025", section=aids_option["value"]).all()
        assert len(aids_students) == 1
        assert aids_students[0].studentId == "TEST_AIDS_01"
        assert aids_students[0].percentage == 40.0
        print("[PASS] Scoping by AIDS section returns only AIDS data")

        # 4. Verify Pass Percentage for CSE section vs AIDS section
        kpi_cse = services.get_pass_percentage_kpi(db, academic_year="2024-2025", section=cse_option["value"])
        assert kpi_cse["total_students_evaluated"] == 1
        assert kpi_cse["overall"]["passed"] == 1

        kpi_aids = services.get_pass_percentage_kpi(db, academic_year="2024-2025", section=aids_option["value"])
        assert kpi_aids["total_students_evaluated"] == 1
        print("[PASS] Pass Percentage KPI correctly scoped by internal section+department")

        # 5. Verify Student-Faculty Ratio for CSE section vs AIDS section
        ratio_cse = services.get_student_faculty_ratio_data(db, academic_year="2024-2025", section=cse_option["value"])
        assert ratio_cse["totalStudents"] == 1
        assert ratio_cse["totalFaculty"] == 24  # CSE has 24 faculty in DB
        assert ratio_cse["ratio"] == 0.04

        ratio_aids = services.get_student_faculty_ratio_data(db, academic_year="2024-2025", section=aids_option["value"])
        assert ratio_aids["totalStudents"] == 1
        assert ratio_aids["totalFaculty"] == 32  # AI & Data Science has 32 faculty in DB
        assert ratio_aids["ratio"] == 0.03
        print("[PASS] Student-Faculty Ratio correctly resolves department faculty for selected section")

    finally:
        # Cleanup
        db.query(models.StudentUpload).filter(models.StudentUpload.studentId.in_(["TEST_CSE_01", "TEST_AIDS_01"])).delete()
        db.commit()
        print("[PASS] Test cleanup completed")


if __name__ == "__main__":
    test_repeating_sections_across_departments()
    print("\nALL REPEATING SECTION TESTS PASSED SUCCESSFULLY!")

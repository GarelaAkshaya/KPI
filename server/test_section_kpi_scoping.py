import database, models, services


def test_section_parsing():
    sec, dept = services.parse_section_identifier("A::Computer Science and Engineering")
    assert sec == "A"
    assert dept == "Computer Science and Engineering"

    sec2, dept2 = services.parse_section_identifier("B::AI & Data Science")
    assert sec2 == "B"
    assert dept2 == "AI & Data Science"

    sec3, dept3 = services.parse_section_identifier("A")
    assert sec3 == "A"
    assert dept3 is None

    sec4, dept4 = services.parse_section_identifier("")
    assert sec4 is None
    assert dept4 is None

    sec5, dept5 = services.parse_section_identifier(None)
    assert sec5 is None
    assert dept5 is None
    print("test_section_parsing passed")


def test_scope_and_kpi():
    db = next(database.get_db())

    # Test get_available_sections returns properly formatted items
    sections = services.get_available_sections(db, academic_year="2024-2025")
    assert isinstance(sections, list)
    for s in sections:
        assert "section" in s
        assert "department" in s
        assert "label" in s
        assert "value" in s
        assert s["value"] == f"{s['section']}::{s['department']}"

    # Test ratio when no section is selected
    ratio_all = services.get_student_faculty_ratio_data(db, academic_year="2024-2025", department=None, section=None)
    assert ratio_all["totalStudents"] > 0
    assert ratio_all["totalFaculty"] > 0
    assert ratio_all["ratio"] > 0

    # Test ratio with composite section
    ratio_scoped = services.get_student_faculty_ratio_data(db, academic_year="2024-2025", section="A::AI & Data Science")
    assert "ratio" in ratio_scoped

    # Test pass percentage with composite section
    pass_scoped = services.get_pass_percentage_kpi(db, academic_year="2024-2025", section="A::AI & Data Science")
    assert "overall_pass_percentage" in pass_scoped

    # Test KPI summary
    summary = services.get_kpi_summary(db, academic_year="2024-2025")
    assert "student_faculty_ratio" in summary
    assert "pass_percentage" in summary

    print("test_scope_and_kpi passed")


if __name__ == "__main__":
    test_section_parsing()
    test_scope_and_kpi()
    print("ALL TESTS PASSED!")

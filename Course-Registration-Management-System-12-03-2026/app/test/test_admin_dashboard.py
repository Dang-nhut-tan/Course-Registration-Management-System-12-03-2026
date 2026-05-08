from datetime import datetime

from app import db
from app.admin import build_admin_dashboard
from app.model import ClassSection, Course, Faculty
from app.test.test_base import test_app, test_session


def test_dashboard_uses_latest_semester(test_app, test_session):
    faculty = Faculty(id=1, name="Khoa CNTT")
    course_2024 = Course(id=1, name="Mon 2024", credits=3, faculty_id=1)
    course_2025 = Course(id=2, name="Mon 2025", credits=3, faculty_id=1)
    section_2024 = ClassSection(
        id=1,
        course_id=1,
        semester="2024-2",
        max_students=50,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 5, 1),
    )
    section_2025 = ClassSection(
        id=2,
        course_id=2,
        semester="2025-1",
        max_students=50,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 5, 1),
    )

    test_session.add_all([faculty, course_2024, course_2025, section_2024, section_2025])
    test_session.commit()

    with test_app.test_request_context("/admin/"):
        dashboard = build_admin_dashboard()

    assert dashboard["semester"] == "2025-1"
    assert dashboard["stats"][1]["value"] == 1
    assert dashboard["stats"][2]["value"] == 1

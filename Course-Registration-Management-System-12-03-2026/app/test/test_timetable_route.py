from datetime import date
from unittest.mock import patch

from app.test.test_base import test_app, test_client


def test_timetable_redirects_to_login_when_not_logged_in(test_app, test_client):
    from app import index as index_routes

    test_app.add_url_rule("/timetable", "timetable", index_routes.timetable)

    response = test_client.get("/timetable")

    assert response.status_code == 302
    assert response.location.endswith("/")


def test_timetable_renders_for_logged_in_student(test_app, test_client):
    from app import index as index_routes

    test_app.add_url_rule("/timetable", "timetable", index_routes.timetable)
    context = {
        "schedules": [],
        "schedule_rows": [],
        "unscheduled_sections": [],
        "week_days": [],
        "week": 2,
        "semester_no": 1,
        "max_week": 10,
        "can_previous_week": True,
        "can_next_week": True,
        "term_start": date(2026, 6, 1),
        "term_end": date(2026, 9, 30),
    }

    with test_client.session_transaction() as session:
        session["student_code"] = "2354050113"
        session["student_name"] = "Test Student"

    with patch.object(index_routes.utils, "get_student_timetable", return_value=context):
        with patch.object(index_routes, "render_template", return_value="timetable page"):
            response = test_client.get("/timetable?week=2")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "timetable page"

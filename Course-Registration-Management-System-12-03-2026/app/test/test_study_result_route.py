from unittest.mock import patch

from pathlib import Path

from flask import Flask, render_template

from app.test.test_base import test_app, test_client


def test_study_result_redirects_to_login_when_not_logged_in(test_app, test_client):
    from app import index as index_routes

    test_app.add_url_rule("/study-result", "study_result", index_routes.study_result)##############

    response = test_client.get("/study-result")

    assert response.status_code == 302
    assert response.location.endswith("/")


def test_study_result_renders_for_logged_in_student(test_app, test_client):
    from app import index as index_routes

    test_app.add_url_rule("/study-result", "study_result", index_routes.study_result)

    with test_client.session_transaction() as session:
        session["student_code"] = "2354050999"
        session["student_name"] = "Test Student"

    with patch.object(index_routes.utils, "build_study_result_context", return_value=[]):
        with patch.object(index_routes, "render_template", return_value="study result page"):
            response = test_client.get("/study-result")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "study result page"


def test_study_result_template_renders_course_rows(test_app):
    template_app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parents[1] / "templates"),
        static_folder=str(Path(__file__).resolve().parents[1] / "static"),
    )

    @template_app.route("/index")
    def index():
        return ""

    @template_app.route("/timetable")
    def timetable():
        return ""

    @template_app.route("/study-result")
    def study_result():
        return ""

    @template_app.route("/logout")
    def logout():
        return ""

    semester_results = [
        {
            "semester": "2026-1",
            "courses": [
                {
                    "course": type("Course", (), {"id": 1, "name": "Test Course", "credits": 3})(),
                    "section": type("Section", (), {"name": "LHP 1"})(),
                    "midterm_score": 8.0,
                    "final_score": 9.0,
                    "total_score": 8.6,
                    "scale_4_score": 4.0,
                    "letter_score": "A",
                    "result": "PASS",
                }
            ],
            "summary": {
                "semester_average_10": 8.6,
                "semester_average_4": 4.0,
                "semester_credits": 3,
                "cumulative_average_4": 4.0,
                "cumulative_credits": 3,
                "classification": "Xuất sắc",
            },
        }
    ]

    with template_app.test_request_context("/study-result"):
        html = render_template(
            "study-result.html",
            student_code="2354050113",
            student_name="Test Student",
            semester_results=semester_results,
        )

    assert "Test Course" in html
    assert "Xuất sắc" in html

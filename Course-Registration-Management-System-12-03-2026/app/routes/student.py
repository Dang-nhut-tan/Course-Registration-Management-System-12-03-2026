"""Student-facing page routes."""

from flask import Blueprint, redirect, render_template, request, session, url_for

from app import utils
from app.services.registration_page import build_registration_page_context


student_bp = Blueprint("student", __name__)


def _student_code_or_redirect():
    student_code = session.get("student_code")
    if not student_code:
        return None, redirect(url_for("login"))
    return student_code, None


@student_bp.route("/index")
def registration():
    student_code, response = _student_code_or_redirect()
    if response:
        return response

    context = build_registration_page_context(
        student_code,
        request.args,
        student_name=session.get("student_name"),
    )
    return render_template("index.html", **context)


@student_bp.route("/timetable")
def timetable():
    student_code, response = _student_code_or_redirect()
    if response:
        return response

    week = request.args.get("week", 1, type=int)
    context = utils.get_student_timetable(student_code, week)

    return render_template(
        "timetable.html",
        student_code=student_code,
        student_name=session.get("student_name"),
        schedules=context["schedules"],
        schedule_rows=context["schedule_rows"],
        unscheduled_sections=context["unscheduled_sections"],
        week_days=context["week_days"],
        week=context["week"],
        semester=f"Kỳ {context['semester_no']}",
        max_week=context["max_week"],
        can_previous_week=context["can_previous_week"],
        can_next_week=context["can_next_week"],
        term_start=context["term_start"],
        term_end=context["term_end"],
    )


@student_bp.route("/study-result")
@student_bp.route("/grades")
def study_result():
    student_code, response = _student_code_or_redirect()
    if response:
        return response

    return render_template(
        "study-result.html",
        student_code=student_code,
        student_name=session.get("student_name"),
        semester_results=utils.build_study_result_context(student_code),
    )

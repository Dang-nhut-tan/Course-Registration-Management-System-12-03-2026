from flask import redirect, render_template, request, session, url_for
from flask_login import login_user
from app import app
from app import utils
from app import admin
from app import api as api_routes
from app.model import UserRole
from datetime import datetime, timedelta


@app.route("/", methods=["GET", "POST"])
def login():
    err_msg = ""

    if request.method == "POST":
        role = request.form.get("login_role")
        username = request.form.get("student_code")
        password = request.form.get("password")
        remember = request.form.get("remember") == "on"

        user = None
        if role == "admin":
            user = utils.check_login_admin(username=username, password=password)
        else:
            user = utils.check_login_student(student_code=username, password=password)

        if user:
            login_user(user, remember=remember)

            if user.role == UserRole.STUDENT:
                session["student_code"] = user.student_code
                session["student_name"] = user.student.name if user.student else ""
                return redirect(url_for("index"))

            elif user.role == UserRole.ADMIN:
                return redirect(url_for('course.index_view'))

        err_msg = "MSSV hoặc mật khẩu không chính xác"

    if err_msg:
        err_msg = "MSSV hoặc mật khẩu không chính xác"

    return render_template("login.html", err_msg=err_msg)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/forgot-password")
def forgot_password():
    return render_template("forgot-password.html")


@app.route("/index")
def index():
    student_code = session.get("student_code")
    if not student_code:
        return redirect(url_for("login"))

    course_query = (request.args.get("course_query") or "").strip()
    faculty_id = request.args.get("faculty")
    training_program_semester = request.args.get("training_program_semester")
    page = request.args.get("page", default=1, type=int) or 1
    per_page = 4
    has_manual_training_program_filter = bool(training_program_semester)
    default_training_program_semester = str(
        utils.get_default_training_program_semester(student_code) or ""
    )
    current_training_program_semester = str(
        utils.get_current_training_program_semester(student_code) or ""
    )
    effective_training_program_semester = (
        training_program_semester or default_training_program_semester
    )
    student, student_class, major_id = utils.get_student_context(student_code)
    selected_faculty_id = faculty_id or ""

    all_sections = utils.get_sections(
        student_code,
        course_query or None,
        selected_faculty_id or None,
        effective_training_program_semester or None,
    )
    filters = utils.get_filter_data(
        student_code,
        selected_faculty_id or None,
        effective_training_program_semester or None,
    )
    registered_courses = utils.get_registered_courses(student_code)
    registered_credits = utils.get_registered_credits(student_code)
    credit_limit = utils.get_credit_limit_per_semester(student_code)
    minimum_registered_credits = utils.get_minimum_credits_to_enforce(student_code)
    registered_section_ids = [enrollment.class_section_id for enrollment in registered_courses]
    total_sections = len(all_sections)
    total_pages = max((total_sections + per_page - 1) // per_page, 1)
    page = min(max(page, 1), total_pages)
    sections = all_sections[(page - 1) * per_page:page * per_page]
    count_section_ids = []
    for section in sections:
        count_section_ids.append(section.id)
        if section.linked_section_id:
            count_section_ids.append(section.linked_section_id)

    section_registered_counts = utils.get_registered_counts(count_section_ids)
    section_capacity_limits = {}
    for section in sections:
        section_capacity_limits[section.id] = utils.get_section_capacity_limit(section)
        if section.linked_section:
            section_capacity_limits[section.linked_section.id] = utils.get_section_capacity_limit(
                section.linked_section
            )

    return render_template(
        "index.html",
        sections=sections,
        total_sections=total_sections,
        page=page,
        total_pages=total_pages,
        courses=filters["courses"],
        faculties=filters["faculties"],
        selected_course_query=course_query,
        selected_faculty_id=selected_faculty_id,
        selected_training_program_semester=training_program_semester or "",
        default_training_program_semester=default_training_program_semester,
        current_training_program_semester=current_training_program_semester,
        has_manual_training_program_filter=has_manual_training_program_filter,
        training_program_semesters=filters["training_program_semesters"],
        student_code=student_code,
        student_name=session.get("student_name"),
        student_class=student_class,
        registered_courses=registered_courses,
        registered_credits=registered_credits,
        credit_limit=credit_limit,
        minimum_registered_credits=minimum_registered_credits,
        registered_section_ids=registered_section_ids,
        section_registered_counts=section_registered_counts,
        section_capacity_limits=section_capacity_limits,
        message=request.args.get("msg", ""),
        message_type=request.args.get("msg_type", "")
    )

@app.route("/timetable")
def timetable():
    student_code = session.get("student_code")
    if not student_code:
        return redirect(url_for("login"))

    week = request.args.get("week", 1, type=int)
    context = utils.get_student_timetable(student_code, week)

    semester = f"Kỳ {context['semester_no']}"

    return render_template(
        "timetable.html",
        student_code=student_code,
        student_name=session.get("student_name"),
        schedules=context['schedules'],
        week_days=context['week_days'],
        week=context['week'],
        semester=semester,
        max_week=context["max_week"],
        can_previous_week=context["can_previous_week"],
        can_next_week=context["can_next_week"],
        term_start=context["term_start"],
        term_end=context["term_end"],
    )

@app.route("/study-result")
@app.route("/grades")#########
def study_result():
    student_code = session.get("student_code")
    if not student_code:
        return redirect(url_for("login"))

    semester_results = utils.build_study_result_context(student_code)

    return render_template(
        "study-result.html",
        student_code=student_code,
        student_name=session.get("student_name"),
        semester_results=semester_results,
    )

if __name__ == "__main__":
    app.run(debug=True)

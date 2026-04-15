from flask import redirect, render_template, request, session, url_for

from app import app
from app import utils
from app.admin import admin


@app.route("/", methods=["GET", "POST"])
def login():
    err_msg = ""

    if request.method == "POST":
        student_code = request.form.get("student_code")
        password = request.form.get("password")
        remember = request.form.get("remember") == "on"
        user = utils.check_login_student(student_code=student_code, password=password)

        if user:
            session.permanent = remember
            session["student_code"] = user.student_code
            session["student_name"] = user.student.name if user.student else ""
            return redirect(url_for("index"))

        err_msg = "MSSV hoặc mật khẩu không chính xác"

    return render_template("login.html", err_msg=err_msg)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/forgot-password")
def forgot_password():
    return render_template("forgot-password.html")


@app.route("/register-course", methods=["POST"])
def register_course():
    student_code = session.get("student_code")
    if not student_code:
        return redirect(url_for("login"))

    class_section_id = request.form.get("class_section_id", type=int)
    success, message = utils.register_section(student_code, class_section_id)
    return redirect(
        url_for(
            "index",
            course=request.form.get("course"),
            faculty=request.form.get("faculty"),
            msg=message,
            msg_type="success" if success else "error",
        )
    )


@app.route("/cancel-course", methods=["POST"])
def cancel_course():
    student_code = session.get("student_code")
    if not student_code:
        return redirect(url_for("login"))

    enrollment_id = request.form.get("enrollment_id", type=int)
    success, message = utils.cancel_registered_course(student_code, enrollment_id)
    return redirect(
        url_for(
            "index",
            course=request.form.get("course"),
            faculty=request.form.get("faculty"),
            training_program_semester=request.form.get("training_program_semester"),
            msg=message,
            msg_type="success" if success else "error",
        )
    )


@app.route("/index")
def index():
    student_code = session.get("student_code")
    if not student_code:
        return redirect(url_for("login"))

    course_id = request.args.get("course")
    faculty_id = request.args.get("faculty")
    training_program_semester = request.args.get("training_program_semester")
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
    _, student_class, _ = utils.get_student_context(student_code)
    default_faculty_id = utils.get_student_faculty_id(student_code)
    selected_faculty_id = faculty_id or (str(default_faculty_id) if default_faculty_id else "")

    sections = utils.get_sections(
        student_code,
        course_id,
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
    registered_section_ids = [enrollment.class_section_id for enrollment in registered_courses]

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
        courses=filters["courses"],
        faculties=filters["faculties"],
        selected_course_id=course_id or "",
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
        registered_section_ids=registered_section_ids,
        section_registered_counts=section_registered_counts,
        section_capacity_limits=section_capacity_limits,
        message=request.args.get("msg", ""),
        message_type=request.args.get("msg_type", "")
    )


if __name__ == "__main__":
    app.run(debug=True)

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

    sections = utils.get_sections(course_id, faculty_id)
    filters = utils.get_filter_data()
    registered_courses = utils.get_registered_courses(student_code, course_id, faculty_id)
    registered_credits = utils.get_registered_credits(student_code)
    registered_section_ids = [
        enrollment.class_section_id
        for enrollment in registered_courses
        if enrollment.status and enrollment.status.value == "registered"
    ]
    section_registered_counts = utils.get_registered_counts([section.id for section in sections])

    return render_template(
        "index.html",
        sections=sections,
        courses=filters["courses"],
        faculties=filters["faculties"],
        student_code=student_code,
        student_name=session.get("student_name"),
        registered_courses=registered_courses,
        registered_credits=registered_credits,
        registered_section_ids=registered_section_ids,
        section_registered_counts=section_registered_counts,
        message=request.args.get("msg", ""),
        message_type=request.args.get("msg_type", ""),
    )


if __name__ == "__main__":
    app.run(debug=True)

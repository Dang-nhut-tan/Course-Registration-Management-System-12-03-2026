"""Authentication routes."""

from flask import Blueprint, redirect, render_template, request, session, url_for
from flask_login import login_user

from app import utils
from app.model import UserRole


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET", "POST"])
def login():
    err_msg = ""

    if request.method == "POST":
        role = request.form.get("login_role")
        username = request.form.get("student_code")
        password = request.form.get("password")
        remember = request.form.get("remember") == "on"

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

            if user.role == UserRole.ADMIN:
                return redirect(url_for("course.index_view"))

        err_msg = "MSSV hoặc mật khẩu không chính xác"

    return render_template("login.html", err_msg=err_msg)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@auth_bp.route("/forgot-password")
def forgot_password():
    return render_template("forgot-password.html")

from flask import render_template, url_for
from flask_login import login_user

from app import app, utils
from app.routes import auth as auth_routes
from app.routes import student as student_routes


def login():
    auth_routes.url_for = url_for
    auth_routes.render_template = render_template
    auth_routes.login_user = login_user
    return auth_routes.login()


def logout():
    auth_routes.url_for = url_for
    return auth_routes.logout()


def forgot_password():
    auth_routes.render_template = render_template
    return auth_routes.forgot_password()


def index():
    student_routes.url_for = url_for
    student_routes.render_template = render_template
    return student_routes.registration()


def timetable():
    student_routes.url_for = url_for
    student_routes.render_template = render_template
    return student_routes.timetable()


def study_result():
    student_routes.url_for = url_for
    student_routes.render_template = render_template
    return student_routes.study_result()


if __name__ == "__main__":
    app.run(debug=True)

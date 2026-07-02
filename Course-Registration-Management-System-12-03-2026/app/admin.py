"""Flask-Admin setup and backward-compatible view exports."""

import os

from flask_admin import Admin

from app import db
from app.admin_views.base import AdminAccessIndexView, BaseView
from app.admin_views.catalog import (
    CampusView,
    CoursePrerequisiteView,
    CourseView,
    FacultyView,
    RoomView,
    TeacherCourseView,
    TeacherView,
)
from app.admin_views.class_section import ClassSectionView, ScheduleView
from app.admin_views.grades import GradeView
from app.model import (
    Campus,
    ClassSection,
    Course,
    CoursePrerequisite,
    Faculty,
    Grade,
    Room,
    Teacher,
    TeacherCourse,
)


IndexView = AdminAccessIndexView
admin = None


def init_admin(flask_app):
    """Attach Flask-Admin and its model views to an application."""
    global admin
    admin = Admin(
        app=flask_app,
        name="Quản trị đăng ký môn học",
        index_view=AdminAccessIndexView(),
        translations_path=os.path.join(flask_app.root_path, "translations"),
    )

    admin.add_view(CourseView(Course, db.session, name="Môn học"))
    admin.add_view(ClassSectionView(ClassSection, db.session, name="Lớp học phần"))
    admin.add_view(GradeView(Grade, db.session, name="Điểm"))
    admin.add_view(RoomView(Room, db.session, name="Phòng học"))
    admin.add_view(TeacherView(Teacher, db.session, name="Giảng viên"))
    admin.add_view(
        TeacherCourseView(TeacherCourse, db.session, name="Phân công giảng dạy")
    )
    admin.add_view(FacultyView(Faculty, db.session, name="Khoa"))
    admin.add_view(
        CoursePrerequisiteView(CoursePrerequisite, db.session, name="Môn tiên quyết")
    )
    admin.add_view(CampusView(Campus, db.session, name="Cơ sở"))
    return admin

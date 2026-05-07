import typing as t
from flask_admin._types import T_SQLALCHEMY_MODEL
from flask import flash, redirect, url_for, request
from wtforms import Form
from flask_login import current_user
from app import app, db
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from app.model import Course, ClassSection, Enrollment, Schedule, Room, UserRole, Campus, Teacher, CoursePrerequisite, CourseMajor
from app.utils import check_room_conflict

class IndexView(AdminIndexView):
    def is_visible(self):
        return False

admin = Admin(app=app, name="Course Registration Administration", index_view=IndexView())

class BaseView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))

class ClassSectionView(BaseView):
    form_args = {
        'max_students': {
            'render_kw': {
                'min': '1'
            }
        }
    }

    def delete_model(self, model):
        has_enrollment = db.session.query(Enrollment).filter_by(class_section_id = model.id).count() > 0

        if has_enrollment:
            flash(message="Không thể xóa lớp học này vì đã có sinh viên đăng ký!", category="error")
            return False

        return  super(ClassSectionView, self).delete_model(model)

    def create_model(self, form):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            flash(message="Chỉ Admin mới được phép tạo lớp học!",category="error")
            return False

        if form.max_students.data > 50:
            flash(message="Số sinh viên tối đa không được vượt quá 50!",category="error")
            return False

        return super(ClassSectionView, self).create_model(form)

WEEKDAYS_MAP = {
    2: "Thứ 2",
    3: "Thứ 3",
    4: "Thứ 4",
    5: "Thứ 5",
    6: "Thứ 6",
    7: "Thứ 7"
}

class ScheduleView(BaseView):
    column_formatters = {
        'day_of_week': lambda v, c, m, p: WEEKDAYS_MAP.get(m.day_of_week, m.day_of_week)
    }

    form_args = {
        'day_of_week': {
            'render_kw': {
                'min': '2',
                'max': '7'
            }
        }
    }

    def create_model(self, form):
        day = form.day.data
        start_time = form.start_time.data
        end_time = form.end_time.data
        room_id = form.class_section.data.room_id

        if check_room_conflict(day, start_time, end_time, room_id):
            flash(message="Lịch học bị trùng phòng!",category="error")
            return False

        return super(ScheduleView, self).create_model(form)


class CourseView(BaseView):
    form_args = {
        'credits': {
            'render_kw': {
                'min': '1',
                'max': '6'
            }
        }
    }

    def delete_model(self, model):
        try:
            class_section = db.session.query(ClassSection).filter_by(course_id=model.id).count() > 0
            if class_section:
                flash(f"Lỗi: Môn '{model.name}' đã có lớp học phần, không thể xóa!", "error")
                return False

            major = db.session.query(CourseMajor).filter_by(course_id=model.id).count() > 0
            if major:
                flash(f"Lỗi: Môn '{model.name}' đang thuộc chương trình đào tạo của một ngành!", "error")
                return False

            course_prerequisite = db.session.query(CoursePrerequisite).filter(
                (CoursePrerequisite.course_id == model.id) |
                (CoursePrerequisite.prerequisite_id == model.id)
            ).count() > 0
            if course_prerequisite:
                flash(f"Lỗi: Môn '{model.name}' đang là môn tiên quyết của môn khác!", "error")
                return False

            return super(CourseView, self).delete_model(model)

        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi hệ thống: {str(e)}", "error")
            return False

admin.add_view(CourseView(Course, db.session))
admin.add_view(ClassSectionView(ClassSection, db.session))
admin.add_view(ScheduleView(Schedule, db.session))
admin.add_view(BaseView(Room, db.session))
admin.add_view(BaseView(Teacher, db.session))
admin.add_view(BaseView(CoursePrerequisite, db.session))
admin.add_view(BaseView(Campus, db.session))
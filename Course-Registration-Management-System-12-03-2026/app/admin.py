import typing as t
from flask_admin._types import T_SQLALCHEMY_MODEL
from flask import flash
from wtforms import Form
from flask_login import current_user
from app import app, db
#from index import app
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app.model import Course, ClassSection, Enrollment, Schedule, Room
from app.utils import check_room_conflict

admin = Admin(app=app, name="Course Registration Administration")

class ClassSectionView(ModelView):
    def delete_model(self, model):
        has_enrollment = db.session.query(Enrollment).filter_by(class_section_id = model.id).count() > 0

        if has_enrollment:
            flash(message="Không thể xóa lớp học này vì đã có sinh viên đăng ký!", category="error")
            return False

        return  super(ClassSectionView, self).delete_model(model)

    def create_model(self, form):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash(message="Chỉ Admin mới được phép tạo lớp học!",category="error")
            return False

        if form.max_students.data > 50:
            flash(message="Số sinh viên tối đa không được vượt quá 50!",category="error")
            return False

        return super(ClassSectionView, self).create_model(form)


class ScheduleView(ModelView):
    def create_model(self, form):
        day = form.day.data
        start_time = form.start_time.data
        end_time = form.end_time.data
        room_id = form.class_section.data.room_id

        if check_room_conflict(day, start_time, end_time, room_id):
            flash(message="Lịch học bị trùng phòng!",category="error")
            return False

        return super(ScheduleView, self).create_model(form)


admin.add_view(ModelView(Course, db.session))
admin.add_view(ClassSectionView(ClassSection, db.session))
admin.add_view(ScheduleView(Schedule, db.session))
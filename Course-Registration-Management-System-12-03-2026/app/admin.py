import typing as t
from flask_admin._types import T_SQLALCHEMY_MODEL
from flask import flash
from wtforms import Form
from flask_login import current_user
from app import app, db
#from index import app
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app.model import Course, ClassSection, Enrollment, Schedule, Room, UserRole, Campus, Teacher, CoursePrerequisite
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
    7: "Thứ 7",
    8: "Chủ nhật"
}

class ScheduleView(ModelView):
    column_list = [
        'day_of_week',
        'start_time',
        'end_time',
        'class_section.course.id',
        'class_section.course.name',
        'class_section'
    ]

    column_labels = {
        'day_of_week': 'Thứ',
        'start_time': 'Giờ bắt đầu',
        'end_time': 'Giờ kết thúc',
        'class_section.course.id': 'Mã môn học',
        'class_section.course.name': 'Tên môn học',
        'class_section': 'Lớp học phần'
    }

    column_formatters = {
        'day_of_week': lambda v, c, m, p: WEEKDAYS_MAP.get(m.day_of_week, m.day_of_week)
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


class CourseView(ModelView):
    column_list = ['id', 'name', 'credits', 'faculty']

    column_labels = {
        'id': 'Mã môn học',
        'name': 'Tên môn học',
        'credits': 'Số tín chỉ',
        'faculty': 'Khoa'
    }
    form_columns = ['id', 'name', 'credits', 'faculty']

admin.add_view(CourseView(Course, db.session))
admin.add_view(ClassSectionView(ClassSection, db.session))
admin.add_view(ScheduleView(Schedule, db.session))
admin.add_view(ModelView(Room, db.session))
admin.add_view(ModelView(Teacher, db.session))
admin.add_view(ModelView(CoursePrerequisite, db.session))
admin.add_view(ModelView(Campus, db.session))
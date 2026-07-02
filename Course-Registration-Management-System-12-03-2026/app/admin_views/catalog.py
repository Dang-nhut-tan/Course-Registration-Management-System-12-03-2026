"""Admin views for catalog."""

from flask import flash
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app import db
from app.admin_views.base import BaseView
from app.model import (Campus, ClassSection, Course, CourseMajor,
    CoursePrerequisite, Room, TeacherCourse)


class CourseView(BaseView):
    form_columns = ("faculty", "name", "credits", "is_shared")
    column_labels = {
        "faculty": "Khoa",
        "name": "Tên môn học",
        "credits": "Số tín chỉ",
        "is_shared": "Môn dùng chung",
    }
    form_args = {
        'credits': {
            'render_kw': {
                'min': '1',
                'max': '6'
            }
        }
    }

    def is_duplicate_course_name(self, form, model=None):
        name = (form.name.data or "").strip() if form.name.data else ""
        faculty = form.faculty.data
        if not name or not faculty:
            return False

        query = Course.query.filter(
            func.lower(Course.name) == name.lower(),
            Course.faculty_id == faculty.id,
        )
        if model and model.id:
            query = query.filter(Course.id != model.id)

        return query.first() is not None

    def create_model(self, form):
        if not form.faculty.data:
            flash("Vui lòng chọn khoa cho môn học.", "error")
            return False

        if self.is_duplicate_course_name(form):
            flash("Không thể tạo môn học vì tên môn đã tồn tại trong khoa này.", "error")
            return False

        return super(CourseView, self).create_model(form)

    def update_model(self, form, model):
        if not form.faculty.data:
            flash("Vui lòng chọn khoa cho môn học.", "error")
            return False

        if self.is_duplicate_course_name(form, model):
            flash("Không thể cập nhật vì tên môn đã tồn tại trong khoa này.", "error")
            return False

        return super(CourseView, self).update_model(form, model)

    def delete_model(self, model):
        try:
            class_section = db.session.query(ClassSection).filter_by(course_id=model.id).count() > 0
            if class_section:
                flash(f"Không thể xóa môn '{model.name}' vì đã có lớp học phần.", "error")
                return False

            major = db.session.query(CourseMajor).filter_by(course_id=model.id).count() > 0
            if major:
                flash(f"Không thể xóa môn '{model.name}' vì môn này thuộc chương trình đào tạo.", "error")
                return False

            course_prerequisite = db.session.query(CoursePrerequisite).filter(
                (CoursePrerequisite.course_id == model.id) |
                (CoursePrerequisite.prerequisite_id == model.id)
            ).count() > 0
            if course_prerequisite:
                flash(f"Không thể xóa môn '{model.name}' vì môn này đang được dùng làm môn tiên quyết.", "error")
                return False

            return super(CourseView, self).delete_model(model)

        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi hệ thống: {str(e)}", "error")
            return False


class CoursePrerequisiteView(BaseView):
    column_list = ("course", "prerequisite")
    column_labels = {
        "course": "Môn học",
        "prerequisite": "Môn tiên quyết",
    }

    def is_invalid_prerequisite(self, form, model=None):
        course = form.course.data
        prerequisite = form.prerequisite.data
        if not course or not prerequisite:
            return False

        if course.id == prerequisite.id:
            flash("Môn học không được là môn tiên quyết của chính nó.", "error")
            return True

        query = CoursePrerequisite.query.filter_by(
            course_id=course.id,
            prerequisite_id=prerequisite.id,
        )
        if model:
            query = query.filter(
                (CoursePrerequisite.course_id != model.course_id) |
                (CoursePrerequisite.prerequisite_id != model.prerequisite_id)
            )

        if query.first():
            flash("Quan hệ môn tiên quyết này đã tồn tại.", "error")
            return True

        return False

    def create_model(self, form):
        if self.is_invalid_prerequisite(form):
            return False

        return super(CoursePrerequisiteView, self).create_model(form)

    def update_model(self, form, model):
        if self.is_invalid_prerequisite(form, model):
            return False

        return super(CoursePrerequisiteView, self).update_model(form, model)


class TeacherCourseView(BaseView):
    column_list = ("teacher", "course")
    column_labels = {
        "teacher": "Giảng viên",
        "course": "Môn học",
    }
    form_columns = ("teacher", "course")

    def is_duplicate_teacher_course(self, form, model=None):
        teacher = form.teacher.data
        course = form.course.data
        if not teacher or not course:
            return False

        query = TeacherCourse.query.filter_by(
            teacher_id=teacher.id,
            course_id=course.id,
        )
        if model:
            query = query.filter(
                (TeacherCourse.teacher_id != model.teacher_id) |
                (TeacherCourse.course_id != model.course_id)
            )

        if query.first():
            flash("Giáo viên này đã được gán cho môn học đã chọn.", "error")
            return True

        return False

    def create_model(self, form):
        if self.is_duplicate_teacher_course(form):
            return False

        return super(TeacherCourseView, self).create_model(form)

    def update_model(self, form, model):
        if self.is_duplicate_teacher_course(form, model):
            return False

        return super(TeacherCourseView, self).update_model(form, model)


class TeacherView(BaseView):
    column_display_pk = True
    column_list = ("id", "name")
    form_columns = ("name",)
    column_labels = {
        "id": "Mã giảng viên",
        "name": "Tên giảng viên",
    }

    def delete_model(self, model):
        try:
            has_class_section = ClassSection.query.filter_by(teacher_id=model.id).count() > 0
            if has_class_section:
                flash("Không thể xóa giáo viên vì giáo viên này đang được gán cho lớp học phần.", "error")
                return False

            return super(TeacherView, self).delete_model(model)

        except IntegrityError:
            db.session.rollback()
            flash("Không thể xóa giáo viên vì dữ liệu đang được sử dụng ở bảng khác.", "error")
            return False

        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi hệ thống khi xóa giáo viên: {str(e)}", "error")
            return False


class RoomView(BaseView):
    column_filters = ("campus",)
    form_choices = {
        "room_type": [
            ("theory", "Lý thuyết"),
            ("practice", "Thực hành"),
        ]
    }
    column_labels = {
        "name": "Tên phòng",
        "room_type": "Loại phòng",
        "capacity": "Sức chứa",
        "campus": "Cơ sở",
    }

    def has_required_room_data(self, form):
        if not form.name.data or not str(form.name.data).strip():
            flash("Vui lòng nhập tên phòng.", "error")
            return False

        if not form.room_type.data:
            flash("Vui lòng chọn loại phòng.", "error")
            return False

        if not form.capacity.data:
            flash("Vui lòng nhập sức chứa phòng.", "error")
            return False

        if not form.campus.data:
            flash("Vui lòng chọn cơ sở.", "error")
            return False

        return True

    def is_duplicate_room(self, form, model=None):
        room = Room.query.filter(
            Room.name == form.name.data,
            Room.campus == form.campus.data,
        ).first()

        if room and (not model or room.id != model.id):
            flash("Phòng này đã tồn tại trong cơ sở đã chọn.", "error")
            return True

        return False

    def create_model(self, form):
        if not self.has_required_room_data(form):
            return False

        if self.is_duplicate_room(form):
            return False

        return super(RoomView, self).create_model(form)

    def update_model(self, form, model):
        if not self.has_required_room_data(form):
            return False

        if self.is_duplicate_room(form, model):
            return False

        return super(RoomView, self).update_model(form, model)

    def delete_model(self, model):
        has_active_class_section = db.session.query(ClassSection).filter(
            ClassSection.room_id == model.id,
        ).count() > 0

        if has_active_class_section:
            flash("Không thể xóa phòng vì phòng này đang được dùng cho lớp học phần.", "error")
            return False

        return super(RoomView, self).delete_model(model)


class CampusView(BaseView):
    form_excluded_columns = ("rooms",)
    column_labels = {
        "name": "Tên cơ sở",
        "address": "Địa chỉ",
    }

    def is_duplicate_campus_name(self, form, model=None):
        name = (form.name.data or "").strip() if form.name.data else ""
        if not name:
            return False

        query = Campus.query.filter(func.lower(Campus.name) == name.lower())
        if model and model.id:
            query = query.filter(Campus.id != model.id)

        return query.first() is not None

    def create_model(self, form):
        if self.is_duplicate_campus_name(form):
            flash("Không thể tạo cơ sở vì tên cơ sở đã tồn tại.", "error")
            return False

        return super(CampusView, self).create_model(form)

    def update_model(self, form, model):
        if self.is_duplicate_campus_name(form, model):
            flash("Không thể cập nhật vì tên cơ sở đã tồn tại.", "error")
            return False

        return super(CampusView, self).update_model(form, model)

    def delete_model(self, model):
        has_room = Room.query.filter_by(campus_id=model.id).count() > 0
        if has_room:
            flash("Không thể xóa cơ sở vì cơ sở này đang có phòng học.", "error")
            return False

        return super(CampusView, self).delete_model(model)


class FacultyView(BaseView):
    column_list = ("name", "registration_start_date", "registration_deadline")
    column_labels = {
        "name": "Khoa",
        "registration_start_date": "Ngày bắt đầu đăng ký",
        "registration_deadline": "Hạn đăng ký",
    }
    form_excluded_columns = ("majors",)

    def validate_registration_dates(self, form):
        start_date = form.registration_start_date.data
        deadline = form.registration_deadline.data
        if start_date and deadline and start_date > deadline:
            flash("Ngày bắt đầu đăng ký phải trước hoặc bằng hạn đăng ký.", "error")
            return False
        return True

    def create_model(self, form):
        if not self.validate_registration_dates(form):
            return False
        return super(FacultyView, self).create_model(form)

    def update_model(self, form, model):
        if not self.validate_registration_dates(form):
            return False
        return super(FacultyView, self).update_model(form, model)

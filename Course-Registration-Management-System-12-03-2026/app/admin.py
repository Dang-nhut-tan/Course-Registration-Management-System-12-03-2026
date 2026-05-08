import typing as t
from flask_admin._types import T_SQLALCHEMY_MODEL
from flask import flash, redirect, url_for, request
from wtforms import Form
from flask_login import current_user
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app import app, db
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from app.model import Course, ClassSection, ClassSectionType, Enrollment, EnrollmentStatus, Schedule, Room, UserRole, Campus, Teacher, CoursePrerequisite, CourseMajor, Faculty, Student
from app.utils import check_room_conflict, check_teacher_conflict

class IndexView(AdminIndexView):
    def is_visible(self):
        return False

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))

    @expose("/")
    def index(self):
        if not self.is_accessible():
            return self.inaccessible_callback("index")

        return self.render("admin/dashboard.html", dashboard=build_admin_dashboard())


def build_admin_dashboard():
    semester_rows = db.session.query(ClassSection.semester).distinct().order_by(ClassSection.semester.desc()).all()
    semester_values = [row[0] for row in semester_rows if row[0] and "-" in row[0]]
    current_semester = semester_values[0] if semester_values else ""
    sections = ClassSection.query.filter_by(semester=current_semester).all() if current_semester else []

    section_ids = [section.id for section in sections]
    enrollments = Enrollment.query.filter(
        Enrollment.status == EnrollmentStatus.REGISTERED,
        Enrollment.class_section_id.in_(section_ids),
    ).all() if section_ids else []

    registered_counts = {}
    for enrollment in enrollments:
        registered_counts[enrollment.class_section_id] = registered_counts.get(enrollment.class_section_id, 0) + 1

    underfilled_room_ids = set()
    for section in sections:
        room_capacity = section.room.capacity if section.room and section.room.capacity else section.max_students
        capacity = min(section.max_students or 0, room_capacity or 0)
        if section.room_id and capacity and registered_counts.get(section.id, 0) < capacity:
            underfilled_room_ids.add(section.room_id)

    registered_students = db.session.query(Enrollment.student_code).filter(
        Enrollment.status == EnrollmentStatus.REGISTERED,
        Enrollment.class_section_id.in_(section_ids),
    ).distinct().count()
    open_courses = db.session.query(ClassSection.course_id).filter(
        ClassSection.id.in_(section_ids),
    ).distinct().count() if section_ids else 0
    used_room_ids = {section.room_id for section in sections if section.room_id}
    empty_rooms = Room.query.filter(~Room.id.in_(list(used_room_ids))).count() if used_room_ids else Room.query.count()
    recent_activities = [
        {
            "time": enrollment.registered_at.strftime("%H:%M") if enrollment.registered_at else "--:--",
            "action": f"Sinh viên {enrollment.student_code} đã đăng ký Môn học {enrollment.class_section.course_id}",
        }
        for enrollment in Enrollment.query.filter(
            Enrollment.class_section_id.in_(section_ids),
        ).order_by(Enrollment.registered_at.desc()).limit(5).all()
    ]
    if not recent_activities:
        recent_activities.append({"time": "--:--", "action": "Chưa có hoạt động gần đây"})

    chart_rows = db.session.query(
        Faculty.id,
        func.count(Enrollment.id),
    ).join(Course, Course.faculty_id == Faculty.id).join(
        ClassSection, ClassSection.course_id == Course.id
    ).join(
        Enrollment, Enrollment.class_section_id == ClassSection.id
    ).filter(
        Enrollment.status == EnrollmentStatus.REGISTERED,
        ClassSection.id.in_(section_ids),
    ).group_by(Faculty.id).order_by(func.count(Enrollment.id).desc()).all()
    max_chart_value = max([count for _, count in chart_rows], default=1)

    return {
        "semester": current_semester or "Không có kỳ phù hợp",
        "stats": [
            {"label": "Tổng sinh viên", "value": Student.query.count()},
            {"label": "Môn học đang mở", "value": open_courses},
            {"label": "Lớp học phần mở", "value": len(sections)},
            {"label": "Sinh viên đã đăng ký", "value": registered_students},
        ],
        "room_stats": [
            {"label": "Số phòng trống", "value": empty_rooms},
            {"label": "Số phòng chưa đầy", "value": len(underfilled_room_ids)},
            {"label": "Số lượng sinh viên", "value": registered_students},
        ],
        "activities": recent_activities,
        "chart": [
            {
                "label": f"Khoa {faculty_id}",
                "count": count,
                "width": int((count / max_chart_value) * 100),
            }
            for faculty_id, count in chart_rows
        ],
    }

admin = Admin(app=app, name="Course Registration Administration", index_view=IndexView())

class BaseView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))

    def delete_model(self, model):
        try:
            return super(BaseView, self).delete_model(model)
        except IntegrityError:
            db.session.rollback()
            flash("Không thể xóa dữ liệu này vì đang được sử dụng ở bảng khác.", "error")
            return False
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi hệ thống khi xóa dữ liệu: {str(e)}", "error")
            return False

class ClassSectionView(BaseView):
    form_excluded_columns = ("name",)
    form_args = {
        'max_students': {
            'render_kw': {
                'min': '1'
            }
        }
    }

    def get_form_field(self, form, field_name):
        fields = getattr(form, "_fields", None)
        if isinstance(fields, dict):
            return fields.get(field_name)

        return form.__dict__.get(field_name)

    def get_form_data(self, form, field_name):
        field = self.get_form_field(form, field_name)
        return getattr(field, "data", None)

    def update_section_name(self, form, model):
        student_class = self.get_form_data(form, "student_class")
        course = self.get_form_data(form, "course")

        if student_class:
            model.name = student_class.code
        elif course:
            model.name = course.name
        else:
            model.name = None

    def on_model_change(self, form, model, is_created):
        self.update_section_name(form, model)
        return super(ClassSectionView, self).on_model_change(form, model, is_created)

    def auto_link_practice_section(self, form, model=None):
        linked_section_field = self.get_form_field(form, "linked_section")
        if not linked_section_field or isinstance(linked_section_field.data, ClassSection):
            return

        section_type = self.get_form_data(form, "section_type")
        if section_type in (ClassSectionType.PRACTICE, "practice"):
            return

        course = self.get_form_data(form, "course")
        student_class = self.get_form_data(form, "student_class")
        semester = self.get_form_data(form, "semester")
        if not course:
            return

        query = ClassSection.query.filter(
            ClassSection.course_id == course.id,
            ClassSection.section_type == ClassSectionType.PRACTICE,
        )

        if student_class:
            query = query.filter(ClassSection.student_class_id == student_class.id)
        if semester:
            query = query.filter(ClassSection.semester == semester)
        if model:
            query = query.filter(ClassSection.id != model.id)

        linked_ids = db.session.query(ClassSection.linked_section_id).filter(
            ClassSection.linked_section_id.isnot(None)
        )
        if model:
            linked_ids = linked_ids.filter(ClassSection.id != model.id)
        linked_ids = {linked_id for linked_id, in linked_ids}

        practice_sections = query.order_by(ClassSection.id).all()
        fallback_section = None
        for practice_section in practice_sections:
            if practice_section.id in linked_ids:
                continue

            registered_count = Enrollment.query.filter(
                Enrollment.class_section_id == practice_section.id,
                Enrollment.status == EnrollmentStatus.REGISTERED,
            ).count()
            if registered_count >= practice_section.max_students:
                continue

            if practice_section.room and practice_section.room.room_type == "practice":
                linked_section_field.data = practice_section
                return

            if not fallback_section:
                fallback_section = practice_section

        if fallback_section:
            linked_section_field.data = fallback_section

    def is_valid_linked_section(self, form, model=None):
        linked_section = getattr(getattr(form, "linked_section", None), "data", None)
        if not isinstance(linked_section, ClassSection):
            return True

        course = getattr(getattr(form, "course", None), "data", None)
        student_class = getattr(getattr(form, "student_class", None), "data", None)

        if model and linked_section.id == model.id:
            flash("Lớp học phần không được liên kết với chính nó.", "error")
            return False

        if linked_section.section_type != ClassSectionType.PRACTICE:
            flash("Lớp liên kết phải là lớp thực hành.", "error")
            return False

        if course and linked_section.course_id != course.id:
            flash("Lớp thực hành liên kết phải cùng môn học.", "error")
            return False

        if student_class and linked_section.student_class_id != student_class.id:
            flash("Lớp thực hành liên kết phải cùng lớp sinh viên.", "error")
            return False

        return True

    def delete_model(self, model):
        has_enrollment = db.session.query(Enrollment).filter_by(class_section_id = model.id).count() > 0

        if has_enrollment:
            flash(message="Không thể xóa lớp học phần vì đã có sinh viên đăng ký.", category="error")
            return False

        return  super(ClassSectionView, self).delete_model(model)

    def create_model(self, form):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            flash(message="Chỉ quản trị viên mới được tạo lớp học phần.",category="error")
            return False

        if form.max_students.data > 50:
            flash(message="Số sinh viên tối đa không được vượt quá 50.",category="error")
            return False

        self.auto_link_practice_section(form)

        if not self.is_valid_linked_section(form):
            return False

        return super(ClassSectionView, self).create_model(form)

    def update_model(self, form, model):
        self.auto_link_practice_section(form, model)

        if not self.is_valid_linked_section(form, model):
            return False

        return super(ClassSectionView, self).update_model(form, model)

WEEKDAYS_MAP = {
    2: "Monday",
    3: "Tuesday",
    4: "Wednesday",
    5: "Thursday",
    6: "Friday",
    7: "Saturday"
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
        day = form.day_of_week.data
        start_time = form.start_time.data
        end_time = form.end_time.data
        class_section = form.class_section.data
        room_id = class_section.room_id
        teacher_id = class_section.teacher_id

        if check_room_conflict(day, start_time, end_time, room_id):
            flash(message="Lịch học bị trùng phòng.",category="error")
            return False

        if check_teacher_conflict(day, start_time, end_time, teacher_id):
            flash(message="Lịch học bị trùng giáo viên.", category="error")
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

    def create_model(self, form):
        if not form.faculty.data:
            flash("Vui lòng chọn khoa cho môn học.", "error")
            return False

        return super(CourseView, self).create_model(form)

    def update_model(self, form, model):
        if not form.faculty.data:
            flash("Vui lòng chọn khoa cho môn học.", "error")
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
        "course": "Course",
        "prerequisite": "Prerequisite",
    }

class TeacherView(BaseView):
    column_display_pk = True
    column_list = ("id", "name")
    column_labels = {
        "id": "Teacher ID",
        "name": "Name",
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
    form_choices = {
        "room_type": [
            ("theory", "Theory"),
            ("practice", "Practice"),
        ]
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

    def delete_model(self, model):
        has_room = Room.query.filter_by(campus_id=model.id).count() > 0
        if has_room:
            flash("Không thể xóa cơ sở vì cơ sở này đang có phòng học.", "error")
            return False

        return super(CampusView, self).delete_model(model)

admin.add_view(CourseView(Course, db.session))
admin.add_view(ClassSectionView(ClassSection, db.session))
admin.add_view(ScheduleView(Schedule, db.session))
admin.add_view(RoomView(Room, db.session))
admin.add_view(TeacherView(Teacher, db.session))
admin.add_view(CoursePrerequisiteView(CoursePrerequisite, db.session))
admin.add_view(CampusView(Campus, db.session))


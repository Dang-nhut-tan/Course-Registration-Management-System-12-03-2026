import re
import typing as t
from flask_admin._types import T_SQLALCHEMY_MODEL
from flask import flash, redirect, url_for, request
from wtforms import Form, SelectField
from flask_login import current_user
from datetime import datetime, time
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app import app, db
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from app.model import Course, ClassSection, ClassSectionType, Enrollment, EnrollmentStatus, Schedule, Room, UserRole, Campus, Teacher, TeacherCourse, CoursePrerequisite, CourseMajor, Faculty, Student, StudentClass
from app.utils import check_room_conflict, check_teacher_conflict

DEFAULT_START_TIME = time(7, 30)
DEFAULT_END_TIME = time(12, 0)
SCHEDULE_TIME_CHOICES = [
    ("07:30", "07:30"),
    ("09:30", "09:30"),
    ("12:00", "12:00"),
    ("13:00", "13:00"),
    ("15:00", "15:00"),
    ("17:30", "17:30"),
]


def get_semester_choices():
    current_year = datetime.now().year
    choices = []
    for year in range(current_year - 1, current_year + 2):
        choices.append((f"{year}-1", f"{year}-1"))
        choices.append((f"{year}-2", f"{year}-2"))
    return choices

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
    form_excluded_columns = ("name", "schedules", "enrollments")
    create_template = "admin/classsection_create.html"
    edit_template = "admin/classsection_edit.html"
    form_extra_fields = {
        "semester": SelectField(
            "Semester",
            choices=get_semester_choices,
        ),
        "schedule_day": SelectField(
            "Schedule Day",
            choices=[
                ("", "-- Chọn thứ --"),
                ("2", "Thứ 2"),
                ("3", "Thứ 3"),
                ("4", "Thứ 4"),
                ("5", "Thứ 5"),
                ("6", "Thứ 6"),
                ("7", "Thứ 7"),
            ],
        ),
        "schedule_start_time": SelectField(
            "Start Time",
            choices=SCHEDULE_TIME_CHOICES,
            default="07:30",
        ),
        "schedule_end_time": SelectField(
            "End Time",
            choices=SCHEDULE_TIME_CHOICES,
            default="12:00",
        ),
    }
    column_labels = {
        "course": "Course",
        "student_class": "Student Class",
        "teacher": "Teacher",
        "room": "Room",
        "linked_section": "Linked Section",
        "name": "Name",
        "semester": "Semester",
        "max_students": "Max Students",
        "start_date": "Start Date",
        "end_date": "End Date",
        "registration_start_date": "Registration Start Date",
        "registration_deadline": "Registration Deadline",
        "section_type": "Section Type",
        "schedules": "Schedules",
    }
    column_formatters = {
        "schedules": lambda v, c, m, p: format_section_schedules(m.schedules),
    }
    form_args = {
        'max_students': {
            'render_kw': {
                'min': '1'
            }
        },
        'teacher': {
            'description': 'Auto-filled when left blank.'
        },
        'room': {
            'description': 'Auto-filled when left blank.'
        },
        'linked_section': {
            'description': 'Auto-filled for theory sections when left blank.'
        }
    }

    def get_filter_data_for_form(self):
        teacher_course_rows = TeacherCourse.query.all()
        teacher_course_map = {}
        for row in teacher_course_rows:
            teacher_course_map.setdefault(str(row.course_id), []).append(str(row.teacher_id))

        linked_section_ids = {
            str(linked_id)
            for linked_id, in db.session.query(ClassSection.linked_section_id).filter(
                ClassSection.linked_section_id.isnot(None)
            )
        }
        schedules = Schedule.query.join(ClassSection).all()
        busy_rows = [
            {
                "semester": schedule.class_section.semester,
                "day": schedule.day_of_week,
                "teacher_id": str(schedule.class_section.teacher_id) if schedule.class_section.teacher_id else "",
                "room_id": str(schedule.class_section.room_id) if schedule.class_section.room_id else "",
                "start": schedule.start_time.strftime("%H:%M"),
                "end": schedule.end_time.strftime("%H:%M"),
            }
            for schedule in schedules
        ]

        return {
            "courses": [
                {"id": str(course.id), "faculty_id": str(course.faculty_id)}
                for course in Course.query.all()
            ],
            "teachers": [
                {"id": str(teacher.id), "name": teacher.name, "faculty_id": str(teacher.faculty_id or "")}
                for teacher in Teacher.query.all()
            ],
            "rooms": [
                {"id": str(room.id), "name": str(room), "room_type": room.room_type or ""}
                for room in Room.query.all()
            ],
            "practice_sections": [
                {
                    "id": str(section.id),
                    "course_id": str(section.course_id or ""),
                    "student_class_id": str(section.student_class_id or ""),
                    "semester": section.semester or "",
                    "name": str(section),
                    "room_type": section.room.room_type if section.room else "",
                    "is_linked": str(section.id) in linked_section_ids,
                }
                for section in ClassSection.query.filter(
                    ClassSection.section_type == ClassSectionType.PRACTICE
                ).order_by(ClassSection.id).all()
            ],
            "teacher_courses": teacher_course_map,
            "busy": busy_rows,
        }

    def get_form_field(self, form, field_name):
        fields = getattr(form, "_fields", None)
        if isinstance(fields, dict):
            return fields.get(field_name)

        return form.__dict__.get(field_name)

    def get_form_data(self, form, field_name):
        field = self.get_form_field(form, field_name)
        return getattr(field, "data", None)

    def get_course_from_form(self, form):
        course = self.get_form_data(form, "course")
        if isinstance(course, Course):
            return course
        return None

    def get_semester_from_form(self, form):
        return self.get_form_data(form, "semester")

    def get_schedule_day_from_form(self, form):
        day = self.get_form_data(form, "schedule_day")
        try:
            day = int(day)
        except (TypeError, ValueError):
            return None

        return day if 2 <= day <= 7 else None

    def parse_schedule_time(self, value, default_time):
        if not value:
            return default_time

        if isinstance(value, time):
            return value

        try:
            return datetime.strptime(str(value), "%H:%M").time()
        except (TypeError, ValueError):
            return default_time

    def get_schedule_start_time_from_form(self, form):
        return self.parse_schedule_time(
            self.get_form_data(form, "schedule_start_time"),
            DEFAULT_START_TIME,
        )

    def get_schedule_end_time_from_form(self, form):
        return self.parse_schedule_time(
            self.get_form_data(form, "schedule_end_time"),
            DEFAULT_END_TIME,
        )

    def get_section_type_from_form(self, form):
        section_type = self.get_form_data(form, "section_type")
        if section_type == "practice":
            return ClassSectionType.PRACTICE
        if section_type == "theory":
            return ClassSectionType.THEORY
        return section_type or ClassSectionType.THEORY

    def find_available_teacher(self, form, model=None):
        course = self.get_course_from_form(form)
        semester = self.get_semester_from_form(form)
        day = self.get_schedule_day_from_form(form)
        start_time = self.get_schedule_start_time_from_form(form)
        end_time = self.get_schedule_end_time_from_form(form)
        if not course:
            return None

        teacher_ids = [
            teacher_id
            for teacher_id, in db.session.query(TeacherCourse.teacher_id).filter_by(course_id=course.id).all()
        ]
        query = Teacher.query
        if teacher_ids:
            query = query.filter(Teacher.id.in_(teacher_ids))
        elif course.faculty_id:
            query = query.filter(Teacher.faculty_id == course.faculty_id)

        if day:
            used_teacher_ids = db.session.query(ClassSection.teacher_id).join(Schedule).filter(
                ClassSection.semester == semester,
                ClassSection.teacher_id.isnot(None),
                Schedule.day_of_week == day,
                Schedule.start_time < end_time,
                Schedule.end_time > start_time,
            )
            if model and model.id:
                used_teacher_ids = used_teacher_ids.filter(ClassSection.id != model.id)
        else:
            used_teacher_ids = db.session.query(ClassSection.teacher_id).filter(
                ClassSection.semester == semester,
                ClassSection.teacher_id.isnot(None),
            )
            if model and model.id:
                used_teacher_ids = used_teacher_ids.filter(ClassSection.id != model.id)

        return query.filter(~Teacher.id.in_(used_teacher_ids)).order_by(Teacher.id).first()

    def find_available_room(self, form, model=None):
        semester = self.get_semester_from_form(form)
        day = self.get_schedule_day_from_form(form)
        start_time = self.get_schedule_start_time_from_form(form)
        end_time = self.get_schedule_end_time_from_form(form)
        section_type = self.get_section_type_from_form(form)
        room_type = "practice" if section_type == ClassSectionType.PRACTICE else "theory"

        if day:
            used_room_ids = db.session.query(ClassSection.room_id).join(Schedule).filter(
                ClassSection.semester == semester,
                ClassSection.room_id.isnot(None),
                Schedule.day_of_week == day,
                Schedule.start_time < end_time,
                Schedule.end_time > start_time,
            )
            if model and model.id:
                used_room_ids = used_room_ids.filter(ClassSection.id != model.id)
        else:
            used_room_ids = db.session.query(ClassSection.room_id).filter(
                ClassSection.semester == semester,
                ClassSection.room_id.isnot(None),
            )
            if model and model.id:
                used_room_ids = used_room_ids.filter(ClassSection.id != model.id)

        room = Room.query.filter(
            Room.room_type == room_type,
            ~Room.id.in_(used_room_ids),
        ).order_by(Room.id).first()
        if room:
            return room

        return Room.query.filter(Room.room_type == room_type).order_by(Room.id).first()

    def has_teacher_busy(self, teacher_id, semester, day, start_time, end_time, model=None):
        query = db.session.query(Schedule).join(ClassSection).filter(
            ClassSection.semester == semester,
            ClassSection.teacher_id == teacher_id,
            Schedule.day_of_week == day,
            Schedule.start_time < end_time,
            Schedule.end_time > start_time,
        )
        if model and model.id:
            query = query.filter(ClassSection.id != model.id)
        return query.first() is not None

    def has_room_busy(self, room_id, semester, day, start_time, end_time, model=None):
        query = db.session.query(Schedule).join(ClassSection).filter(
            ClassSection.semester == semester,
            ClassSection.room_id == room_id,
            Schedule.day_of_week == day,
            Schedule.start_time < end_time,
            Schedule.end_time > start_time,
        )
        if model and model.id:
            query = query.filter(ClassSection.id != model.id)
        return query.first() is not None

    def find_practice_section(self, form, model=None):
        course = self.get_course_from_form(form)
        student_class = self.get_form_data(form, "student_class")
        semester = self.get_semester_from_form(form)
        section_type = self.get_section_type_from_form(form)
        if not course or section_type == ClassSectionType.PRACTICE:
            return None

        query = ClassSection.query.filter(
            ClassSection.course_id == course.id,
            ClassSection.section_type == ClassSectionType.PRACTICE,
            ClassSection.semester == semester,
        )
        if student_class:
            query = query.filter(ClassSection.student_class_id == student_class.id)
        if model and model.id:
            query = query.filter(ClassSection.id != model.id)

        linked_ids = db.session.query(ClassSection.linked_section_id).filter(
            ClassSection.linked_section_id.isnot(None)
        )
        if model and model.id:
            linked_ids = linked_ids.filter(ClassSection.id != model.id)
        linked_ids = {linked_id for linked_id, in linked_ids}

        fallback_section = None
        for practice_section in query.order_by(ClassSection.id).all():
            if practice_section.id in linked_ids:
                continue

            registered_count = Enrollment.query.filter(
                Enrollment.class_section_id == practice_section.id,
                Enrollment.status == EnrollmentStatus.REGISTERED,
            ).count()
            if registered_count >= practice_section.max_students:
                continue

            if practice_section.room and practice_section.room.room_type == "practice":
                return practice_section

            if not fallback_section:
                fallback_section = practice_section

        return fallback_section

    def can_auto_fill_class_section(self, form, model=None):
        if self.get_course_from_form(form) is None:
            return True

        if not self.get_form_data(form, "teacher") and not self.find_available_teacher(form, model):
            flash("Không tìm thấy giáo viên phù hợp còn trống cho môn học và kỳ này.", "error")
            return False

        if not self.get_form_data(form, "room") and not self.find_available_room(form, model):
            flash("Không tìm thấy phòng phù hợp còn trống cho kỳ này.", "error")
            return False

        selected_teacher = self.get_form_data(form, "teacher")
        selected_room = self.get_form_data(form, "room")
        day = self.get_schedule_day_from_form(form)
        semester = self.get_semester_from_form(form)
        start_time = self.get_schedule_start_time_from_form(form)
        end_time = self.get_schedule_end_time_from_form(form)
        if day and selected_teacher and self.has_teacher_busy(selected_teacher.id, semester, day, start_time, end_time, model):
            flash("Giáo viên đã bận vào thứ đã chọn.", "error")
            return False

        if day and selected_room and self.has_room_busy(selected_room.id, semester, day, start_time, end_time, model):
            flash("Phòng đã bận vào thứ đã chọn.", "error")
            return False

        return True

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
        teacher = self.get_form_data(form, "teacher") or self.find_available_teacher(form, model)
        room = self.get_form_data(form, "room") or self.find_available_room(form, model)
        practice_section = self.get_form_data(form, "linked_section") or self.find_practice_section(form, model)

        if teacher:
            model.teacher = teacher
        if room:
            model.room = room
        if practice_section:
            model.linked_section = practice_section

        return super(ClassSectionView, self).on_model_change(form, model, is_created)

    def after_model_change(self, form, model, is_created):
        day = self.get_schedule_day_from_form(form)
        if day:
            schedule = Schedule.query.filter_by(class_section_id=model.id).first()
            if not schedule:
                schedule = Schedule(class_section_id=model.id)
                db.session.add(schedule)

            schedule.day_of_week = day
            schedule.start_time = self.get_schedule_start_time_from_form(form)
            schedule.end_time = self.get_schedule_end_time_from_form(form)
            db.session.commit()

        return super(ClassSectionView, self).after_model_change(form, model, is_created)

    def auto_link_practice_section(self, form, model=None):
        linked_section_field = self.get_form_field(form, "linked_section")
        if not linked_section_field or isinstance(linked_section_field.data, ClassSection):
            return
        linked_section_field.data = self.find_practice_section(form, model)

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

    def is_valid_semester(self, semester):
        if not isinstance(semester, str):
            return False
        return re.match(r"^\d{4}-[12]$", semester.strip()) is not None

    def get_max_students_from_form(self, form):
        try:
            return int(self.get_form_data(form, "max_students"))
        except (TypeError, ValueError):
            return None

    def is_valid_selected_teacher(self, form):
        teacher = self.get_form_data(form, "teacher")
        course = self.get_course_from_form(form)
        if not teacher or not course:
            return True

        teaches_course = TeacherCourse.query.filter_by(
            teacher_id=teacher.id,
            course_id=course.id,
        ).first()
        if teaches_course:
            return True

        return teacher.faculty_id == course.faculty_id

    def is_valid_selected_room(self, form):
        room = self.get_form_data(form, "room")
        if not room:
            return True

        section_type = self.get_section_type_from_form(form)
        expected_room_type = "practice" if section_type == ClassSectionType.PRACTICE else "theory"
        return room.room_type == expected_room_type

    def validate_class_section_form(self, form):
        if self.get_form_field(form, "course") and not self.get_form_data(form, "course"):
            flash("Vui lòng chọn môn học.", "error")
            return False

        if self.get_form_field(form, "student_class") and not self.get_form_data(form, "student_class"):
            flash("Vui lòng chọn lớp sinh viên.", "error")
            return False

        if self.get_form_field(form, "semester") and not self.is_valid_semester(self.get_semester_from_form(form)):
            flash("Kỳ học không hợp lệ. Vui lòng chọn đúng dạng năm-kỳ, ví dụ 2026-1.", "error")
            return False

        if self.get_form_field(form, "schedule_day") and not self.get_schedule_day_from_form(form):
            flash("Vui lòng chọn thứ học.", "error")
            return False

        schedule_start_time = self.get_schedule_start_time_from_form(form)
        schedule_end_time = self.get_schedule_end_time_from_form(form)
        if schedule_start_time >= schedule_end_time:
            flash("Giờ bắt đầu học phải nhỏ hơn giờ kết thúc học.", "error")
            return False

        max_students = self.get_max_students_from_form(form)
        if max_students is not None and not 1 <= max_students <= 50:
            flash("Số sinh viên tối đa phải từ 1 đến 50.", "error")
            return False

        start_date = self.get_form_data(form, "start_date")
        end_date = self.get_form_data(form, "end_date")
        registration_start_date = self.get_form_data(form, "registration_start_date")
        registration_deadline = self.get_form_data(form, "registration_deadline")
        if start_date and end_date and start_date >= end_date:
            flash("Ngày bắt đầu phải nhỏ hơn ngày kết thúc.", "error")
            return False

        if registration_start_date and registration_deadline and registration_start_date > registration_deadline:
            flash("Ngày bắt đầu đăng ký phải trước hoặc bằng hạn đăng ký.", "error")
            return False

        if registration_deadline and start_date and registration_deadline > start_date:
            flash("Hạn đăng ký phải trước hoặc bằng ngày bắt đầu.", "error")
            return False

        if not self.is_valid_selected_teacher(form):
            flash("Giáo viên không phù hợp với môn học đã chọn.", "error")
            return False

        if not self.is_valid_selected_room(form):
            flash("Phòng học không phù hợp với loại lớp học phần.", "error")
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

        if not self.validate_class_section_form(form):
            return False

        if not self.can_auto_fill_class_section(form):
            return False

        if not self.is_valid_linked_section(form):
            return False

        return super(ClassSectionView, self).create_model(form)

    def update_model(self, form, model):
        if not self.validate_class_section_form(form):
            return False

        if not self.can_auto_fill_class_section(form, model):
            return False

        if not self.is_valid_linked_section(form, model):
            return False

        return super(ClassSectionView, self).update_model(form, model)

WEEKDAYS_MAP = {
    2: "Thứ 2",
    3: "Thứ 3",
    4: "Thứ 4",
    5: "Thứ 5",
    6: "Thứ 6",
    7: "Thứ 7",
    8: "Chủ nhật",
}


def format_section_schedules(schedules):
    if not schedules:
        return "-"

    return ", ".join(
        f"{WEEKDAYS_MAP.get(schedule.day_of_week, schedule.day_of_week)} "
        f"({schedule.start_time.strftime('%H:%M')} - {schedule.end_time.strftime('%H:%M')})"
        for schedule in sorted(schedules, key=lambda item: (item.day_of_week, item.start_time))
    )

class ScheduleView(BaseView):
    column_formatters = {
        'day_of_week': lambda v, c, m, p: WEEKDAYS_MAP.get(m.day_of_week, m.day_of_week)
    }
    column_labels = {
        "class_section": "Class Section",
        "day_of_week": "Day",
        "start_time": "Start Time",
        "end_time": "End Time",
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

        if class_section:
            existing_schedule = db.session.query(Schedule).filter_by(
                class_section_id=class_section.id
            ).first()

            if existing_schedule:
                flash(message=f"Lớp học phần '{class_section}' đã có lịch học tồn tại!", category="error")
                return False

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
        "course": "Course",
        "prerequisite": "Prerequisite",
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
    column_filters = ("campus",)
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

admin.add_view(CourseView(Course, db.session))
admin.add_view(ClassSectionView(ClassSection, db.session))
admin.add_view(ScheduleView(Schedule, db.session))
admin.add_view(RoomView(Room, db.session))
admin.add_view(TeacherView(Teacher, db.session))
admin.add_view(CoursePrerequisiteView(CoursePrerequisite, db.session))
admin.add_view(CampusView(Campus, db.session))


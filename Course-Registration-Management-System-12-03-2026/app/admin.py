import re
import typing as t
from flask_admin._types import T_SQLALCHEMY_MODEL
from flask import flash, has_request_context, redirect, url_for, request
from wtforms import Form, SelectField
from flask_login import current_user
from datetime import datetime, time
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app import app, db
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.filters import BaseFilter
from app.model import Course, ClassSection, ClassSectionType, Enrollment, EnrollmentStatus, Grade, Schedule, Room, UserRole, Campus, Teacher, TeacherCourse, CoursePrerequisite, CourseMajor, Faculty, Student, StudentClass
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


def get_current_semester_value():
    today = datetime.now()
    semester_no = 1 if today.month <= 6 else 2
    return f"{today.year}-{semester_no}"


def get_semester_choices():
    current_semester = get_current_semester_value()
    choices = [(current_semester, current_semester)]

    existing_semesters = [
        semester
        for semester, in db.session.query(ClassSection.semester).distinct().all()
        if semester
    ]
    nearby_semesters = []
    current_year = datetime.now().year
    for year in range(current_year - 1, current_year + 2):
        nearby_semesters.extend([f"{year}-1", f"{year}-2"])

    for semester in sorted({*existing_semesters, *nearby_semesters}, reverse=True):
        if semester != current_semester:
            choices.append((semester, semester))

    return choices

class AdminAccessIndexView (AdminIndexView):
    def is_visible(self):
        return False

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))

admin = Admin(app=app, name="Course Registration Administration", index_view=AdminAccessIndexView())

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
            default=get_current_semester_value,
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
                {
                    "id": str(room.id),
                    "name": str(room),
                    "room_type": room.room_type or "",
                    "campus_id": str(room.campus_id or ""),
                }
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
                    "campus_id": str(section.room.campus_id) if section.room else "",
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

    def get_teacher_candidates(self, course):
        if not course:
            return [], []

        teacher_ids = [
            teacher_id
            for teacher_id, in db.session.query(TeacherCourse.teacher_id).filter_by(course_id=course.id).all()
        ]
        query = Teacher.query
        if teacher_ids:
            query = query.filter(Teacher.id.in_(teacher_ids))
        elif course.faculty_id:
            query = query.filter(Teacher.faculty_id == course.faculty_id)

        return query.order_by(Teacher.id).all(), teacher_ids

    def get_room_type_from_form(self, form):
        return "practice" if self.get_section_type_from_form(form) == ClassSectionType.PRACTICE else "theory"

    def get_section_room(self, form, model=None):
        return self.get_form_data(form, "room") or getattr(model, "room", None)

    def find_available_teacher(self, form, model=None):
        course = self.get_course_from_form(form)
        semester = self.get_semester_from_form(form)
        day = self.get_schedule_day_from_form(form)
        start_time = self.get_schedule_start_time_from_form(form)
        end_time = self.get_schedule_end_time_from_form(form)
        candidates, _ = self.get_teacher_candidates(course)
        return next(
            (
                teacher
                for teacher in candidates
                if not day or not self.has_teacher_busy(teacher.id, semester, day, start_time, end_time, model)
            ),
            None,
        )

    def get_teacher_unavailable_reason(self, form, model=None):
        course = self.get_course_from_form(form)
        semester = self.get_semester_from_form(form)
        day = self.get_schedule_day_from_form(form)
        start_time = self.get_schedule_start_time_from_form(form)
        end_time = self.get_schedule_end_time_from_form(form)
        if not course:
            return "Vui lòng chọn môn học trước khi hệ thống tự chọn giáo viên."

        candidates, teacher_ids = self.get_teacher_candidates(course)
        if not candidates and teacher_ids:
            return f"Môn {course.name} có phân công Teacher Course nhưng không tìm thấy giáo viên tương ứng."
        if not candidates:
            return f"Không có giáo viên phù hợp cho môn {course.name}; hãy thêm Teacher Course hoặc giáo viên cùng khoa."
        if not day:
            return f"Không thể kiểm tra giáo viên trống cho môn {course.name} vì chưa chọn thứ học."

        busy_teachers = [
            teacher
            for teacher in candidates
            if self.has_teacher_busy(teacher.id, semester, day, start_time, end_time, model)
        ]
        if len(busy_teachers) == len(candidates):
            names = ", ".join(teacher.name for teacher in busy_teachers)
            return (
                f"Tất cả giáo viên phù hợp cho môn {course.name} đều bận vào thứ {day} "
                f"({start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}): {names}."
            )

        return f"Không tìm thấy giáo viên phù hợp còn trống cho môn {course.name}."

    def find_available_room(self, form, model=None):
        semester = self.get_semester_from_form(form)
        day = self.get_schedule_day_from_form(form)
        start_time = self.get_schedule_start_time_from_form(form)
        end_time = self.get_schedule_end_time_from_form(form)
        rooms = Room.query.filter(Room.room_type == self.get_room_type_from_form(form)).order_by(Room.id).all()
        return next(
            (
                room
                for room in rooms
                if not day or not self.has_room_busy(room.id, semester, day, start_time, end_time, model)
            ),
            None,
        )

    def get_room_unavailable_reason(self, form, model=None):
        semester = self.get_semester_from_form(form)
        day = self.get_schedule_day_from_form(form)
        start_time = self.get_schedule_start_time_from_form(form)
        end_time = self.get_schedule_end_time_from_form(form)
        room_type = self.get_room_type_from_form(form)
        room_label = "thực hành" if room_type == "practice" else "lý thuyết"

        rooms = Room.query.filter(Room.room_type == room_type).order_by(Room.id).all()
        if not rooms:
            return f"Không có phòng {room_label} trong hệ thống."
        if not day:
            return f"Không thể kiểm tra phòng {room_label} trống vì chưa chọn thứ học."

        busy_rooms = [
            room
            for room in rooms
            if self.has_room_busy(room.id, semester, day, start_time, end_time, model)
        ]
        if len(busy_rooms) == len(rooms):
            names = ", ".join(str(room) for room in busy_rooms)
            return (
                f"Tất cả phòng {room_label} đều bận vào thứ {day} "
                f"({start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}): {names}."
            )

        return f"Không tìm thấy phòng {room_label} còn trống cho kỳ {semester}."

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

    def get_practice_schedule_slots(self, form):
        theory_day = self.get_schedule_day_from_form(form)
        theory_start = self.get_schedule_start_time_from_form(form)
        theory_end = self.get_schedule_end_time_from_form(form)
        if theory_day and theory_start < time(12, 0) and theory_end <= time(12, 0):
            return [(theory_day, time(13, 0), time(17, 30))]
        if theory_day and theory_start >= time(12, 0):
            return [(theory_day, time(7, 30), time(12, 0))]
        return []

    def find_practice_section(self, form, model=None):
        course = self.get_course_from_form(form)
        student_class = self.get_form_data(form, "student_class")
        semester = self.get_semester_from_form(form)
        section_type = self.get_section_type_from_form(form)
        theory_room = self.get_section_room(form, model)
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

        for practice_section in query.order_by(ClassSection.id).all():
            if practice_section.id in linked_ids:
                continue
            if (
                theory_room
                and practice_section.room
                and practice_section.room.campus_id != theory_room.campus_id
            ):
                continue

            registered_count = Enrollment.query.filter(
                Enrollment.class_section_id == practice_section.id,
                Enrollment.status == EnrollmentStatus.REGISTERED,
            ).count()
            if registered_count >= practice_section.max_students:
                continue

            return practice_section

        return None

    def ensure_practice_section(self, form, model):
        if self.get_section_type_from_form(form) == ClassSectionType.PRACTICE:
            return
        if model.linked_section_id:
            return

        practice_section = self.find_practice_section(form, model)
        if practice_section:
            model.linked_section = practice_section
            db.session.commit()
            return

        course = self.get_course_from_form(form)
        semester = self.get_semester_from_form(form)
        theory_room = self.get_section_room(form, model)
        resources = None
        if course and semester and theory_room:
            teachers, _ = self.get_teacher_candidates(course)
            rooms = Room.query.filter_by(
                room_type="practice",
                campus_id=theory_room.campus_id,
            ).order_by(Room.id).all()
            for day, start_time, end_time in self.get_practice_schedule_slots(form):
                room = next(
                    (
                        item
                        for item in rooms
                        if not self.has_room_busy(item.id, semester, day, start_time, end_time, model)
                    ),
                    None,
                )
                teacher = next(
                    (
                        item
                        for item in teachers
                        if not self.has_teacher_busy(item.id, semester, day, start_time, end_time, model)
                    ),
                    None,
                )
                if room and teacher:
                    resources = teacher, room, day, start_time, end_time
                    break
        if not resources:
            if has_request_context():
                flash("Không tìm thấy phòng thực hành cùng cơ sở và giáo viên còn trống để tự tạo lớp thực hành.", "warning")
            return

        teacher, room, day, start_time, end_time = resources
        practice_section = ClassSection(
            name=model.name,
            course_id=model.course_id,
            student_class_id=model.student_class_id,
            teacher_id=teacher.id,
            room_id=room.id,
            semester=model.semester,
            max_students=model.max_students,
            start_date=model.start_date,
            end_date=model.end_date,
            section_type=ClassSectionType.PRACTICE,
        )
        db.session.add(practice_section)
        db.session.flush()
        db.session.add(
            Schedule(
                class_section_id=practice_section.id,
                day_of_week=day,
                start_time=start_time,
                end_time=end_time,
            )
        )
        model.linked_section = practice_section
        db.session.commit()

    def can_auto_fill_class_section(self, form, model=None):
        if self.get_course_from_form(form) is None:
            return True

        if not self.get_form_data(form, "teacher") and not self.find_available_teacher(form, model):
            flash(self.get_teacher_unavailable_reason(form, model), "error")
            return False

        if not self.get_form_data(form, "room") and not self.find_available_room(form, model):
            flash(self.get_room_unavailable_reason(form, model), "error")
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

        self.ensure_practice_section(form, model)

        return super(ClassSectionView, self).after_model_change(form, model, is_created)

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

        room = self.get_form_data(form, "room")
        if room and linked_section.room and linked_section.room.campus_id != room.campus_id:
            flash("Phòng thực hành liên kết phải cùng cơ sở với phòng lý thuyết.", "error")
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
        if start_date and end_date and start_date >= end_date:
            flash("Ngày bắt đầu phải nhỏ hơn ngày kết thúc.", "error")
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

        if check_room_conflict(day, start_time, end_time, room_id):
            flash(message="Lịch học bị trùng phòng.",category="error")
            return False

        if check_teacher_conflict(day, start_time, end_time, teacher_id):
            flash(message="Lịch học bị trùng giáo viên.", category="error")
            return False

        return super(ScheduleView, self).create_model(form)


class CourseView(BaseView):
    form_columns = ("faculty", "name", "credits", "is_shared")
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

class TeacherCourseView(BaseView):
    column_list = ("teacher", "course")
    column_labels = {
        "teacher": "Teacher",
        "course": "Course",
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

class GradeCourseFilter(BaseFilter):
    def apply(self, query, value):
        return query.filter(
            Grade.enrollment.has(
                Enrollment.class_section.has(
                    ClassSection.course.has(Course.name.ilike(f"%{value}%"))
                )
            )
        )

    def operation(self):
        return "contains"


class GradeClassSectionFilter(BaseFilter):
    def apply(self, query, value):
        return query.filter(
            Grade.enrollment.has(
                Enrollment.class_section.has(ClassSection.name.ilike(f"%{value}%"))
            )
        )

    def operation(self):
        return "contains"


class GradeStudentFilter(BaseFilter):
    def apply(self, query, value):
        return query.filter(
            Grade.enrollment.has(Enrollment.student.has(Student.name.ilike(f"%{value}%")))
        )

    def operation(self):
        return "contains"


class GradeStudentCodeFilter(BaseFilter):
    def apply(self, query, value):
        return query.filter(
            Grade.enrollment.has(Enrollment.student_code.ilike(f"%{value}%"))
        )

    def operation(self):
        return "contains"


class GradeView(BaseView):
    column_list = (
        "student_name",
        "student_code",
        "course_name",
        "class_section_name",
        "midterm_score",
        "final_score",
        "graded_at",
    )
    form_columns = ("enrollment", "midterm_score", "final_score", "graded_at")
    column_filters = (
        GradeCourseFilter("Course"),
        GradeClassSectionFilter("Class section"),
        GradeStudentFilter("Student"),
        GradeStudentCodeFilter("Student code"),
    )
    column_labels = {
        "student_name": "Student",
        "student_code": "Student code",
        "course_name": "Course",
        "class_section_name": "Class section",
        "midterm_score": "Midterm score",
        "final_score": "Final score",
        "graded_at": "Graded at",
        "enrollment": "Enrollment",
    }
    form_args = {
        "enrollment": {
            "label": "Enrollment",
            "description": "Student code - student name | course | class section | semester",
        },
        "midterm_score": {"label": "Midterm score"},
        "final_score": {"label": "Final score"},
        "graded_at": {"label": "Graded at"},
    }

    def _get_enrollment(self, model):
        return model.enrollment if model and model.enrollment else None

    def _get_section(self, model):
        enrollment = self._get_enrollment(model)
        return enrollment.class_section if enrollment and enrollment.class_section else None

    def _get_course(self, model):
        section = self._get_section(model)
        return section.course if section and section.course else None

    def _get_student(self, model):
        enrollment = self._get_enrollment(model)
        return enrollment.student if enrollment and enrollment.student else None

    def _student_name_formatter(self, context, model, name):
        student = self._get_student(model)
        return student.name if student else "-"

    def _student_code_formatter(self, context, model, name):
        enrollment = self._get_enrollment(model)
        return enrollment.student_code if enrollment else "-"

    def _course_name_formatter(self, context, model, name):
        course = self._get_course(model)
        return course.name if course else "-"

    def _class_section_name_formatter(self, context, model, name):
        section = self._get_section(model)
        return section.name if section and section.name else "-"

    def _graded_at_formatter(self, context, model, name):
        return model.graded_at.strftime("%Y-%m-%d %H:%M:%S") if model.graded_at else "-"

    def get_query(self):
        return (
            super()
            .get_query()
            .join(Enrollment, Grade.enrollment_id == Enrollment.id)
            .join(ClassSection, Enrollment.class_section_id == ClassSection.id)
            .join(Course, ClassSection.course_id == Course.id)
            .join(Student, Enrollment.student_code == Student.student_code)
        )

    def get_count_query(self):
        return (
            super()
            .get_count_query()
            .join(Enrollment, Grade.enrollment_id == Enrollment.id)
            .join(ClassSection, Enrollment.class_section_id == ClassSection.id)
            .join(Course, ClassSection.course_id == Course.id)
            .join(Student, Enrollment.student_code == Student.student_code)
        )

    def create_form(self, obj=None):
        form = super().create_form(obj)
        if hasattr(form, "graded_at") and not form.graded_at.data:
            form.graded_at.data = datetime.now()
        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        if hasattr(form, "graded_at") and not form.graded_at.data:
            form.graded_at.data = datetime.now()
        return form

    def on_model_change(self, form, model, is_created):
        if not model.graded_at:
            model.graded_at = datetime.now()
        return super().on_model_change(form, model, is_created)

    column_formatters = {
        "student_name": _student_name_formatter,
        "student_code": _student_code_formatter,
        "course_name": _course_name_formatter,
        "class_section_name": _class_section_name_formatter,
        "graded_at": _graded_at_formatter,
    }

admin.add_view(CourseView(Course, db.session))
admin.add_view(ClassSectionView(ClassSection, db.session))
admin.add_view(ScheduleView(Schedule, db.session))
admin.add_view(GradeView(Grade, db.session))
admin.add_view(RoomView(Room, db.session))
admin.add_view(TeacherView(Teacher, db.session))
admin.add_view(TeacherCourseView(TeacherCourse, db.session))
admin.add_view(FacultyView(Faculty, db.session))
admin.add_view(CoursePrerequisiteView(CoursePrerequisite, db.session))
admin.add_view(CampusView(Campus, db.session))


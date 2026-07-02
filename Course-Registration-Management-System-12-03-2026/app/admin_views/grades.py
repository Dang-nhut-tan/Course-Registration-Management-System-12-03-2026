"""Admin views for grades."""

from datetime import datetime

from flask_admin.model.filters import BaseFilter

from app.admin_views.base import BaseView
from app.model import ClassSection, Course, Enrollment, Grade, Student


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
        return "chứa"


class GradeClassSectionFilter(BaseFilter):
    def apply(self, query, value):
        return query.filter(
            Grade.enrollment.has(
                Enrollment.class_section.has(ClassSection.name.ilike(f"%{value}%"))
            )
        )

    def operation(self):
        return "chứa"


class GradeStudentFilter(BaseFilter):
    def apply(self, query, value):
        return query.filter(
            Grade.enrollment.has(Enrollment.student.has(Student.name.ilike(f"%{value}%")))
        )

    def operation(self):
        return "chứa"


class GradeStudentCodeFilter(BaseFilter):
    def apply(self, query, value):
        return query.filter(
            Grade.enrollment.has(Enrollment.student_code.ilike(f"%{value}%"))
        )

    def operation(self):
        return "chứa"


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
        GradeCourseFilter("Môn học"),
        GradeClassSectionFilter("Lớp học phần"),
        GradeStudentFilter("Sinh viên"),
        GradeStudentCodeFilter("Mã sinh viên"),
    )
    column_labels = {
        "student_name": "Sinh viên",
        "student_code": "Mã sinh viên",
        "course_name": "Môn học",
        "class_section_name": "Lớp học phần",
        "midterm_score": "Điểm giữa kỳ",
        "final_score": "Điểm cuối kỳ",
        "graded_at": "Thời gian nhập điểm",
        "enrollment": "Đăng ký môn học",
    }
    form_args = {
        "enrollment": {
            "label": "Đăng ký môn học",
            "description": "Mã sinh viên - tên sinh viên | môn học | lớp học phần | học kỳ",
        },
        "midterm_score": {"label": "Điểm giữa kỳ"},
        "final_score": {"label": "Điểm cuối kỳ"},
        "graded_at": {"label": "Thời gian nhập điểm"},
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

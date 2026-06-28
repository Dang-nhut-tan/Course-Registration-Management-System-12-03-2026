"""REST API endpoints and their database operations."""

from datetime import datetime, time, timedelta
from enum import Enum

from flask import Blueprint, jsonify, request, session
from flask_login import current_user
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app import app, db, utils
from app.model import (Campus, ClassSection, Course, CourseMajor,
                       CoursePrerequisite, Enrollment, EnrollmentStatus,
                       Faculty, Grade, Room, Student, Teacher, TeacherCourse,
                       ClassSectionType, UserRole)


class ApiError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


RESOURCE_CONFIG = {
    "campuses": (Campus, {"name", "address"}),
    "rooms": (Room, {"name", "room_type", "capacity", "campus_id"}),
    "faculties": (Faculty, {"name", "registration_start_date", "registration_deadline"}),
    "courses": (Course, {"name", "credits", "is_shared", "faculty_id"}),
    "teachers": (Teacher, {"name", "faculty_id"}),
    "teacher-courses": (TeacherCourse, {"teacher_id", "course_id"}),
    "course-prerequisites": (CoursePrerequisite, {"course_id", "prerequisite_id"}),
    "class-sections": (ClassSection, {
        "name", "course_id", "student_class_id", "teacher_id", "room_id",
        "semester", "max_students", "start_date", "end_date", "section_type",
        "linked_section_id",
    }),
    "grades": (Grade, {"enrollment_id", "midterm_score", "final_score", "graded_at"}),
}


def create_record(model, database_session=None):
    database_session = database_session or db.session
    try:
        database_session.add(model)
        database_session.commit()
        return model
    except Exception:
        database_session.rollback()
        raise


def update_record(model, database_session=None):
    database_session = database_session or db.session
    try:
        database_session.add(model)
        database_session.commit()
        return model
    except Exception:
        database_session.rollback()
        raise


def delete_record(model, database_session=None):
    database_session = database_session or db.session
    try:
        database_session.delete(model)
        database_session.commit()
    except Exception:
        database_session.rollback()
        raise


def _resource(resource):
    config = RESOURCE_CONFIG.get(resource)
    if not config:
        raise ApiError("Tài nguyên API không tồn tại.", 404)
    return config


def _find_model(model_class, identifier):
    mapper = inspect(model_class)
    parts = identifier.split(":")
    if len(parts) != len(mapper.primary_key):
        raise ApiError("Định danh tài nguyên không hợp lệ.")
    values = []
    for part, column in zip(parts, mapper.primary_key):
        try:
            values.append(column.type.python_type(part))
        except (TypeError, ValueError):
            raise ApiError("Định danh tài nguyên không hợp lệ.") from None
    identity = values[0] if len(values) == 1 else tuple(values)
    model = db.session.get(model_class, identity)
    if model is None:
        raise ApiError("Không tìm thấy dữ liệu.", 404)
    return model


def _coerce(column, value):
    if value is None:
        return None
    enum_class = getattr(column.type, "enum_class", None)
    if enum_class:
        try:
            return enum_class(value)
        except ValueError:
            raise ApiError(f"Giá trị '{column.key}' không hợp lệ.") from None
    python_type = column.type.python_type
    try:
        if python_type is datetime:
            return datetime.fromisoformat(value)
        if python_type is time:
            return time.fromisoformat(value)
        if python_type is bool and isinstance(value, str):
            return value.lower() in {"true", "1", "yes"}
        return python_type(value)
    except (TypeError, ValueError):
        raise ApiError(f"Giá trị '{column.key}' không hợp lệ.") from None


def _apply_payload(model, fields, payload):
    if not isinstance(payload, dict):
        raise ApiError("Nội dung JSON phải là một object.")
    unknown = set(payload) - fields
    if unknown:
        raise ApiError(f"Trường không được phép: {', '.join(sorted(unknown))}.")
    columns = {column.key: column for column in inspect(type(model)).columns}
    for key, value in payload.items():
        setattr(model, key, _coerce(columns[key], value))


def _validate(resource, model):
    if resource == "courses" and (not model.name or not model.credits or not 1 <= model.credits <= 6):
        raise ApiError("Tên môn học là bắt buộc và số tín chỉ phải từ 1 đến 6.")
    if resource == "rooms" and (not model.name or model.room_type not in {"theory", "practice"} or not model.capacity):
        raise ApiError("Thông tin phòng học không hợp lệ.")
    if resource == "class-sections":
        if not model.semester or not model.max_students or not 1 <= model.max_students <= 50:
            raise ApiError("Học kỳ và sĩ số từ 1 đến 50 là bắt buộc.")
        if model.start_date and model.end_date and model.start_date >= model.end_date:
            raise ApiError("Ngày bắt đầu phải trước ngày kết thúc.")
    if resource == "faculties" and (model.registration_start_date and model.registration_deadline and model.registration_start_date > model.registration_deadline):
        raise ApiError("Ngày bắt đầu đăng ký phải trước hạn đăng ký.")
    if resource == "course-prerequisites" and model.course_id == model.prerequisite_id:
        raise ApiError("Môn học không thể là môn tiên quyết của chính nó.")


def _validate_delete(resource, model):
    if resource == "class-sections" and Enrollment.query.filter_by(class_section_id=model.id).first():
        raise ApiError("Không thể xóa lớp học phần đã có sinh viên đăng ký.", 409)
    if resource == "courses":
        is_used = (
            ClassSection.query.filter_by(course_id=model.id).first()
            or CourseMajor.query.filter_by(course_id=model.id).first()
            or CoursePrerequisite.query.filter(
                (CoursePrerequisite.course_id == model.id)
                | (CoursePrerequisite.prerequisite_id == model.id)
            ).first()
        )
        if is_used:
            raise ApiError("Không thể xóa môn học đang được sử dụng.", 409)
    if resource == "rooms" and ClassSection.query.filter_by(room_id=model.id).first():
        raise ApiError("Không thể xóa phòng đang được dùng cho lớp học phần.", 409)
    if resource == "campuses" and Room.query.filter_by(campus_id=model.id).first():
        raise ApiError("Không thể xóa cơ sở đang có phòng học.", 409)
    if resource == "teachers" and ClassSection.query.filter_by(teacher_id=model.id).first():
        raise ApiError("Không thể xóa giáo viên đang được gán cho lớp học phần.", 409)


def serialize(model):
    result = {}
    for column in inspect(type(model)).columns:
        value = getattr(model, column.key)
        if isinstance(value, Enum):
            value = value.value
        elif isinstance(value, (datetime, time)):
            value = value.isoformat()
        result[column.key] = value
    return result


def list_resources(resource):
    model_class, _ = _resource(resource)
    return [serialize(item) for item in db.session.query(model_class).all()]


def get_resource(resource, identifier):
    model_class, _ = _resource(resource)
    return serialize(_find_model(model_class, identifier))


def create_resource(resource, payload):
    model_class, fields = _resource(resource)
    model = model_class()
    _apply_payload(model, fields, payload)
    _validate(resource, model)
    try:
        create_record(model)
    except IntegrityError as exc:
        raise ApiError("Dữ liệu bị trùng hoặc tham chiếu không hợp lệ.", 409) from exc
    return serialize(model)


def update_resource(resource, identifier, payload):
    model_class, fields = _resource(resource)
    model = _find_model(model_class, identifier)
    _apply_payload(model, fields, payload)
    _validate(resource, model)
    try:
        update_record(model)
    except IntegrityError as exc:
        raise ApiError("Dữ liệu bị trùng hoặc tham chiếu không hợp lệ.", 409) from exc
    return serialize(model)


def delete_resource(resource, identifier):
    model_class, _ = _resource(resource)
    model = _find_model(model_class, identifier)
    _validate_delete(resource, model)
    try:
        delete_record(model)
    except IntegrityError as exc:
        raise ApiError("Không thể xóa vì dữ liệu đang được sử dụng.", 409) from exc


def register_enrollment(student_code, class_section_id):
    try:
        locked_student = Student.query.filter(
            Student.student_code == student_code
        ).with_for_update().first()
        if not locked_student:
            return False, "Không tìm thấy sinh viên."

        section = ClassSection.query.filter(
            ClassSection.id == class_section_id
        ).with_for_update().first()
        if not section:
            return False, "Không tìm thấy lớp học phần."

        block_reason = utils.get_section_registration_block_reason(student_code, section)
        if block_reason:
            return False, block_reason

        related_section_ids = [section.id]
        if section.linked_section_id:
            related_section_ids.append(section.linked_section_id)

        locked_sections = ClassSection.query.filter(
            ClassSection.id.in_(related_section_ids)
        ).order_by(ClassSection.id).with_for_update().all()
        locked_section_map = {item.id: item for item in locked_sections}
        section = locked_section_map.get(class_section_id)
        related_sections = [section]
        if section and section.linked_section_id:
            practice_section = locked_section_map.get(section.linked_section_id)
            if practice_section:
                related_sections.append(practice_section)

        same_course = utils.has_registered_same_course(student_code, related_sections)
        if same_course:
            return False, f"Môn {same_course.class_section.course.name} đã được đăng ký rồi."

        conflict = utils.get_schedule_conflict(student_code, related_sections)
        if conflict:
            conflict_section, day_of_week, start_time, end_time = conflict
            return False, (
                f"Trùng lịch học với môn {conflict_section.course.name} vào thứ "
                f"{day_of_week} ({start_time.strftime('%H:%M')} - "
                f"{end_time.strftime('%H:%M')})."
            )

        enrollments = []
        registration_time = datetime.now()
        for related_section in related_sections:
            enrollment = Enrollment.query.filter(
                Enrollment.student_code == student_code,
                Enrollment.class_section_id == related_section.id,
            ).first()
            if enrollment and enrollment.status == EnrollmentStatus.REGISTERED:
                return False, "Môn này đã được đăng ký rồi."

            registered_count = Enrollment.query.filter(
                Enrollment.class_section_id == related_section.id,
                Enrollment.status == EnrollmentStatus.REGISTERED,
            ).count()
            if registered_count >= utils.get_section_capacity_limit(related_section):
                if related_section.section_type == ClassSectionType.PRACTICE:
                    return False, "Lớp thực hành tương ứng đã hết chỗ."
                return False, "Lớp học phần đã hết chỗ."
            enrollments.append(enrollment)

        current_credits = utils.get_registered_credits(student_code)
        section_credits = section.course.credits or 0
        credit_limit = utils.get_credit_limit_per_semester(student_code)
        if current_credits + section_credits > credit_limit:
            return False, f"Tổng số tín chỉ trong một kỳ không được vượt quá {credit_limit}."

        for related_section, enrollment in zip(related_sections, enrollments):
            if enrollment:
                enrollment.status = EnrollmentStatus.REGISTERED
                enrollment.registered_at = registration_time
            else:
                db.session.add(Enrollment(
                    student_code=student_code,
                    class_section_id=related_section.id,
                    status=EnrollmentStatus.REGISTERED,
                    registered_at=registration_time,
                ))

        db.session.commit()
        if section.linked_section_id:
            return True, "Đăng ký thành công và đã tự động gắn lớp thực hành tương ứng."
        return True, "Đăng ký môn học thành công."
    except Exception:
        db.session.rollback()
        raise


def cancel_enrollment(student_code, enrollment_id):
    enrollment = Enrollment.query.filter(Enrollment.id == enrollment_id).first()
    if not enrollment:
        return False, "Không tìm thấy môn đã đăng ký."
    if enrollment.student_code != student_code:
        return False, "Bạn không có quyền hủy môn học của sinh viên khác."
    if enrollment.status == EnrollmentStatus.CANCELED:
        return False, "Môn học này đã được hủy trước đó."

    cancel_limit = enrollment.class_section.start_date + timedelta(weeks=2)
    if datetime.now() > cancel_limit:
        return False, "Đã quá hạn hủy môn."
    if enrollment.grade and enrollment.grade.midterm_score is not None:
        return False, "Không thể hủy môn vì đã có điểm giữa kỳ."

    minimum_credits = utils.get_minimum_credits_to_enforce(student_code)
    canceled_credits = (
        enrollment.class_section.course.credits or 0
        if enrollment.class_section.section_type == ClassSectionType.THEORY else 0
    )
    credits_after_cancel = max(
        utils.get_registered_credits(student_code) - canceled_credits, 0
    )
    if minimum_credits and credits_after_cancel < minimum_credits:
        return False, (
            f"Không thể hủy vì số tín chỉ sau khi hủy nhỏ hơn {minimum_credits}."
        )

    enrollment.status = EnrollmentStatus.CANCELED
    linked_section = enrollment.class_section.linked_section
    if linked_section:
        linked_enrollment = Enrollment.query.filter(
            Enrollment.student_code == student_code,
            Enrollment.class_section_id == linked_section.id,
            Enrollment.status == EnrollmentStatus.REGISTERED,
        ).first()
        if linked_enrollment:
            linked_enrollment.status = EnrollmentStatus.CANCELED

    db.session.commit()
    return True, "Hủy môn học thành công."


api = Blueprint("api", __name__, url_prefix="/api")


def _error(message, status):
    return jsonify({"success": False, "message": message}), status


def _require_admin():
    if not current_user.is_authenticated:
        raise ApiError("Bạn chưa đăng nhập.", 401)
    if current_user.role != UserRole.ADMIN:
        raise ApiError("Bạn không có quyền quản trị.", 403)


@api.errorhandler(ApiError)
def handle_api_error(error):
    return _error(error.message, error.status_code)


@api.route("/admin/<resource>", methods=["GET", "POST"])
def resource_collection(resource):
    _require_admin()
    if request.method == "GET":
        return jsonify({"success": True, "data": list_resources(resource)})
    data = create_resource(resource, request.get_json(silent=True))
    return jsonify({"success": True, "data": data}), 201


@api.route("/admin/<resource>/<path:identifier>", methods=["GET", "PUT", "PATCH", "DELETE"])
def resource_item(resource, identifier):
    _require_admin()
    if request.method == "GET":
        data = get_resource(resource, identifier)
    elif request.method in {"PUT", "PATCH"}:
        data = update_resource(resource, identifier, request.get_json(silent=True))
    else:
        delete_resource(resource, identifier)
        return "", 204
    return jsonify({"success": True, "data": data})


@api.post("/enrollments")
def register_course_api():
    student_code = session.get("student_code")
    if not student_code:
        return _error("Bạn chưa đăng nhập.", 401)
    payload = request.get_json(silent=True) or {}
    class_section_id = payload.get("class_section_id")
    if not isinstance(class_section_id, int):
        return _error("class_section_id không hợp lệ.", 400)
    success, message = register_enrollment(student_code, class_section_id)
    return jsonify({"success": success, "message": message}), 201 if success else 409


@api.delete("/enrollments/<int:enrollment_id>")
def cancel_course_api(enrollment_id):
    student_code = session.get("student_code")
    if not student_code:
        return _error("Bạn chưa đăng nhập.", 401)
    success, message = cancel_enrollment(student_code, enrollment_id)
    return jsonify({"success": success, "message": message}), 200 if success else 409


if "api" not in app.blueprints:
    app.register_blueprint(api)

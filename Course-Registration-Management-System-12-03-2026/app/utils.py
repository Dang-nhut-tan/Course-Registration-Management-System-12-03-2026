import hashlib

from app import db
from app.model import ClassSection,Course, CourseMajor,CoursePrerequisite,Enrollment,EnrollmentStatus,Faculty, Student,User


def check_login_student(student_code, password):
    if student_code and password:
        password = hashlib.md5(password.strip().encode("utf-8")).hexdigest()
        return User.query.filter(
            User.password == password,
            User.student_code == student_code.strip(),
        ).first()

    return None


def get_sections(course_id=None, faculty_id=None):
    query = ClassSection.query

    if course_id:
        query = query.filter(ClassSection.course_id == int(course_id))
    if faculty_id:
        query = query.join(Course).filter(Course.faculty_id == int(faculty_id))

    return query.all()


def get_registered_courses(student_code, course_id=None, faculty_id=None):
    query = Enrollment.query.filter(Enrollment.student_code == student_code)

    if course_id:
        query = query.join(ClassSection).filter(ClassSection.course_id == int(course_id))

    if faculty_id:
        query = query.join(ClassSection).join(Course).filter(Course.faculty_id == int(faculty_id))

    return query.all()


def get_registered_credits(student_code):
    enrollments = Enrollment.query.join(
        ClassSection, Enrollment.class_section_id == ClassSection.id
    ).join(
        Course, ClassSection.course_id == Course.id
    ).filter(
        Enrollment.student_code == student_code,
        Enrollment.status == EnrollmentStatus.REGISTERED,
    ).all()

    return sum(enrollment.class_section.course.credits or 0 for enrollment in enrollments)


def get_registered_counts(section_ids):
    if not section_ids:
        return {}

    enrollments = Enrollment.query.filter(
        Enrollment.class_section_id.in_(section_ids),
        Enrollment.status == EnrollmentStatus.REGISTERED,
    ).all()

    counts = {}
    for enrollment in enrollments:
        counts[enrollment.class_section_id] = counts.get(enrollment.class_section_id, 0) + 1

    return counts


def check_prerequisite_courses(student_code, course_id):
    prerequisite_rows = CoursePrerequisite.query.filter(
        CoursePrerequisite.course_id == course_id
    ).all()

    if not prerequisite_rows:
        return True, []

    prerequisite_ids = [row.prerequisite_id for row in prerequisite_rows]
    completed_ids = db.session.query(ClassSection.course_id).join(
        Enrollment, Enrollment.class_section_id == ClassSection.id
    ).filter(
        Enrollment.student_code == student_code,
        Enrollment.status == EnrollmentStatus.REGISTERED,
        ClassSection.course_id.in_(prerequisite_ids),
    ).distinct().all()

    completed_ids = {completed_id for completed_id, in completed_ids}
    missing_ids = [required_id for required_id in prerequisite_ids if required_id not in completed_ids]

    if not missing_ids:
        return True, []

    missing_courses = Course.query.filter(Course.id.in_(missing_ids)).all()
    return False, [course.name for course in missing_courses]


def register_section(student_code, class_section_id):
    section = ClassSection.query.get(class_section_id)
    if not section:
        return False, "Không tìm thấy lớp học phần."
    if not is_course_allowed(student_code,section.course):
        return False, "Môn học không thuộc ngành của bạn "

    is_valid, missing_courses = check_prerequisite_courses(student_code, section.course_id)
    if not is_valid:
        return False, "Bạn chưa học môn tiên quyết: " + ", ".join(missing_courses) + "."

    enrollment = Enrollment.query.filter(
        Enrollment.student_code == student_code,
        Enrollment.class_section_id == class_section_id,
    ).first()

    if enrollment and enrollment.status == EnrollmentStatus.REGISTERED:
        return False, "Môn này đã được đăng ký rồi."

    registered_count = Enrollment.query.filter(
        Enrollment.class_section_id == class_section_id,
        Enrollment.status == EnrollmentStatus.REGISTERED,
    ).count()

    if registered_count >= section.max_students:
        return False, "Lớp học phần đã hết chỗ."

    current_credits = get_registered_credits(student_code)
    section_credits = section.course.credits or 0
    if current_credits + section_credits > 25:
        return False, "Tổng số tín chỉ không được vượt quá 25."

    if enrollment:
        enrollment.status = EnrollmentStatus.REGISTERED
    else:
        enrollment = Enrollment(
            student_code=student_code,
            class_section_id=class_section_id,
            status=EnrollmentStatus.REGISTERED,
        )
        db.session.add(enrollment)

    db.session.commit()
    return True, "Đăng ký môn học thành công."


def cancel_registered_course(student_code, enrollment_id):
    enrollment = Enrollment.query.filter(
        Enrollment.id == enrollment_id,
        Enrollment.student_code == student_code,
    ).first()

    if not enrollment:
        return False, "Không tìm thấy môn đã đăng ký."

    if enrollment.status == EnrollmentStatus.CANCELED:
        return False, "Môn học này đã được hủy trước đó."

    enrollment.status = EnrollmentStatus.CANCELED
    db.session.commit()
    return True, "Hủy môn học thành công."

def is_course_allowed(student_code, course):
    student = Student.query.filter_by(student_code=student_code).first()
    major_id=student.major_id
    if course.is_shared:
        return True;
    return CourseMajor.query.filter_by(
        course_id=course.id,
        major_id=major_id
    ).first() is not None


def get_filter_data():
    return {
        "courses": db.session.query(Course).all(),
        "faculties": db.session.query(Faculty).all(),
    }

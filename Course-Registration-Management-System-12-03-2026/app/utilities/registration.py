from datetime import datetime

from sqlalchemy import String, or_

from app import db
from app.exceptions import ApplicationError
from app.model import (
    ClassSection, ClassSectionType, Course, CoursePrerequisite, Enrollment,
    EnrollmentStatus, Faculty, TrainingProgramCourse,
)

from app.utilities.curriculum import (
    get_allowed_course_ids, get_available_training_program_semesters,
    get_current_open_semester,
    get_current_training_program_semester,
    get_student_program_course_ids, get_student_training_program,
    is_course_registrable_for_student, is_current_open_section,
)

MIN_CREDITS_PER_SEMESTER = 12


def validate_section_registration(student_code, section):
    if not section:
        raise ApplicationError("Không tìm thấy lớp học phần.", 404)
    if section.section_type != ClassSectionType.THEORY:
        raise ApplicationError("Vui lòng chọn lớp lý thuyết để đăng ký.", 409)
    if not is_current_open_section(student_code, section):
        raise ApplicationError("Không thuộc học kỳ hiện tại.", 409)
    if not is_course_registrable_for_student(student_code, section.course):
        raise ApplicationError("Không thuộc ngành của bạn.", 409)

    registration_start_date = get_section_registration_start_date(section)
    registration_deadline = get_section_registration_deadline(section)
    now = datetime.now()
    if registration_start_date and now < registration_start_date:
        raise ApplicationError("Chưa tới ngày bắt đầu đăng ký môn học.", 409)
    if registration_deadline and now > registration_deadline:
        raise ApplicationError("Đã quá hạn đăng ký môn học.", 409)

    missing_courses = get_missing_prerequisite_courses(student_code, section.course_id)
    if missing_courses:
        raise ApplicationError(
            "Thiếu tiên quyết: " + ", ".join(missing_courses),
            409,
        )

    credit_limit = get_credit_limit_per_semester(student_code)
    current_credits = get_registered_credits(student_code)
    section_credits = section.course.credits or 0
    if current_credits + section_credits > credit_limit:
        raise ApplicationError(
            f"Vượt giới hạn {credit_limit} tín chỉ trong 1 kỳ.",
            409,
        )


def get_section_registration_start_date(section):
    faculty = section.course.faculty if section and section.course else None
    if faculty and faculty.registration_start_date:
        return faculty.registration_start_date
    return None


def get_section_registration_deadline(section):
    faculty = section.course.faculty if section and section.course else None
    if faculty and faculty.registration_deadline:
        return faculty.registration_deadline
    return None


def is_section_open_for_registration(section, now=None):
    now = now or datetime.now()
    start_date = get_section_registration_start_date(section)
    deadline = get_section_registration_deadline(section)
    if start_date and now < start_date:
        return False
    if deadline and now > deadline:
        return False
    return True


def get_sections(student_code, course_query=None, faculty_id=None, training_program_semester=None):
    query = ClassSection.query.filter(
        ClassSection.section_type == ClassSectionType.THEORY,
    )
    current_open_semester = get_current_open_semester(student_code)
    allowed_course_ids = (
        get_student_program_course_ids(student_code)
        if course_query
        else get_allowed_course_ids(student_code, training_program_semester)
    )

    if not allowed_course_ids:
        return []

    query = query.filter(ClassSection.course_id.in_(allowed_course_ids))
    if current_open_semester:
        query = query.filter(ClassSection.semester == current_open_semester)
    should_join_course = bool(course_query or faculty_id)
    if should_join_course:
        query = query.join(Course)
    if course_query:
        query = query.filter(or_(
            Course.name.ilike(f"%{course_query}%"),
            Course.id.cast(String).ilike(f"%{course_query}%"),
        ))
    if faculty_id and not course_query:
        query = query.filter(Course.faculty_id == int(faculty_id))

    return [
        section
        for section in query.all()
        if is_section_open_for_registration(section)
    ]


def get_open_filter_options(student_code, training_program_semester=None):
    allowed_course_ids = get_student_program_course_ids(student_code)
    current_open_semester = get_current_open_semester(student_code)

    if not allowed_course_ids:
        return [], []

    open_sections = ClassSection.query.filter(
        ClassSection.section_type == ClassSectionType.THEORY,
        ClassSection.course_id.in_(allowed_course_ids),
    ).all()

    open_course_ids = list({
        section.course_id
        for section in open_sections
        if is_section_open_for_registration(section)
        and (not current_open_semester or section.semester == current_open_semester)
    })
    if not open_course_ids:
        return [], []

    courses = Course.query.filter(Course.id.in_(open_course_ids)).order_by(Course.name).all()
    faculties = db.session.query(Faculty).join(
        Course, Course.faculty_id == Faculty.id
    ).filter(
        Course.id.in_(open_course_ids)
    ).distinct().order_by(Faculty.name).all()
    return courses, faculties


def get_registered_courses(student_code):
    current_open_semester = get_current_open_semester(student_code)
    if not current_open_semester:
        return []

    return Enrollment.query.join(ClassSection).filter(
        Enrollment.student_code == student_code,
        ClassSection.section_type == ClassSectionType.THEORY,
        Enrollment.status == EnrollmentStatus.REGISTERED,
        ClassSection.semester == current_open_semester,
        ClassSection.end_date >= datetime.now(),
    ).all()


def get_registered_credits(student_code):
    enrollments = get_registered_courses(student_code)
    return sum(enrollment.class_section.course.credits or 0 for enrollment in enrollments)


def get_credit_limit_per_semester(student_code):
    training_program = get_student_training_program(student_code)
    if training_program and training_program.max_credits_per_semester is not None:
        return training_program.max_credits_per_semester
    return 25


def get_current_training_program_credit_load(student_code):
    training_program = get_student_training_program(student_code)
    current_semester = get_current_training_program_semester(student_code)

    if not training_program or not current_semester:
        return None

    credit_rows = db.session.query(Course.credits).join(
        TrainingProgramCourse,
        TrainingProgramCourse.course_id == Course.id,
    ).filter(
        TrainingProgramCourse.training_program_id == training_program.id,
        TrainingProgramCourse.semester_no == current_semester,
    ).all()

    return sum(credits or 0 for credits, in credit_rows)


def get_minimum_credits_to_enforce(student_code):
    current_credit_load = get_current_training_program_credit_load(student_code)

    # Học kỳ cuối có tổng số tín chỉ theo CTĐT <= 12 thì không áp mức tối thiểu 12 tín.
    if current_credit_load is not None and current_credit_load <= MIN_CREDITS_PER_SEMESTER:
        return 0

    return MIN_CREDITS_PER_SEMESTER


def get_registered_counts(section_ids):
    if not section_ids:
        return {}

    enrollments = Enrollment.query.filter(
        Enrollment.class_section_id.in_(section_ids),
        Enrollment.status == EnrollmentStatus.REGISTERED
    ).all()

    counts = {}
    for enrollment in enrollments:
        counts[enrollment.class_section_id] = counts.get(enrollment.class_section_id, 0) + 1

    return counts


def get_section_capacity_limit(section):
    limits = []

    if section.max_students is not None:
        limits.append(section.max_students)

    if section.room and section.room.capacity is not None:
        limits.append(section.room.capacity)

    if not limits:
        return 0

    return min(limits)


def get_missing_prerequisite_courses(student_code, course_id):
    prerequisite_rows = CoursePrerequisite.query.filter(
        CoursePrerequisite.course_id == course_id
    ).all()

    if not prerequisite_rows:
        return []

    prerequisite_ids = [row.prerequisite_id for row in prerequisite_rows]
    completed_ids = db.session.query(ClassSection.course_id).join(
        Enrollment, Enrollment.class_section_id == ClassSection.id
    ).filter(
        Enrollment.student_code == student_code,
        Enrollment.status == EnrollmentStatus.REGISTERED,
        ClassSection.end_date.isnot(None),
        ClassSection.end_date < datetime.now(),
        ClassSection.course_id.in_(prerequisite_ids),
    ).distinct().all()

    completed_ids = {completed_id for completed_id, in completed_ids}
    missing_ids = [required_id for required_id in prerequisite_ids if required_id not in completed_ids]

    if not missing_ids:
        return []

    missing_courses = Course.query.filter(Course.id.in_(missing_ids)).all()
    return [course.name for course in missing_courses]


def schedules_overlap(schedule_a, schedule_b):
    return (
        schedule_a.day_of_week == schedule_b.day_of_week
        and schedule_a.start_time < schedule_b.end_time
        and schedule_b.start_time < schedule_a.end_time
    )


def get_schedule_conflict(student_code, candidate_sections):
    registered_sections = db.session.query(ClassSection).join(
        Enrollment, Enrollment.class_section_id == ClassSection.id
    ).filter(
        Enrollment.student_code == student_code,
        Enrollment.status == EnrollmentStatus.REGISTERED
    )

    training_program = get_student_training_program(student_code)
    current_semester = get_current_training_program_semester(student_code)
    if training_program and current_semester:
        registered_sections = registered_sections.join(
            TrainingProgramCourse,
            TrainingProgramCourse.course_id == ClassSection.course_id,
        ).filter(
            TrainingProgramCourse.training_program_id == training_program.id,
            TrainingProgramCourse.semester_no == current_semester,
        )

    registered_sections = registered_sections.all()

    for candidate_section in candidate_sections:
        for registered_section in registered_sections:
            if registered_section.id == candidate_section.id:
                continue

            for candidate_schedule in candidate_section.schedules:
                for registered_schedule in registered_section.schedules:
                    if schedules_overlap(candidate_schedule, registered_schedule):
                        return (
                            registered_section,
                            candidate_schedule.day_of_week,
                            candidate_schedule.start_time,
                            candidate_schedule.end_time
                        )

    return None


def has_registered_same_course(student_code, candidate_sections):
    candidate_course_ids = {section.course_id for section in candidate_sections if section}
    candidate_semesters = {section.semester for section in candidate_sections if section and section.semester}
    if not candidate_course_ids:
        return None

    query = db.session.query(Enrollment).join(
        ClassSection, Enrollment.class_section_id == ClassSection.id
    ).filter(
        Enrollment.student_code == student_code,
        Enrollment.status == EnrollmentStatus.REGISTERED,
        ClassSection.course_id.in_(candidate_course_ids),
        ClassSection.end_date >= datetime.now(),
    )
    if candidate_semesters:
        query = query.filter(ClassSection.semester.in_(candidate_semesters))

    return query.first()


def get_filter_data(student_code, faculty_id=None, training_program_semester=None):
    courses, faculties = get_open_filter_options(student_code, training_program_semester)

    return {
        "courses": courses,
        "faculties": Faculty.query.order_by(Faculty.name).all(),
        "training_program_semesters": get_available_training_program_semesters(student_code),
    }

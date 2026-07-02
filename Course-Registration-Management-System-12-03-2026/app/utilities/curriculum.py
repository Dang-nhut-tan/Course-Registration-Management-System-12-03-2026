from datetime import datetime

from app import db
from app.model import (
    ClassSection, ClassSectionType, Course, CourseMajor, Major, Student,
    TrainingProgram, TrainingProgramCourse,
)


def get_student_context(student_code):
    student = Student.query.filter_by(student_code=student_code).first()
    if not student:
        return None, "", None

    student_class = student.student_class
    class_code = student_class.code if student_class else ""
    major_id = student_class.major_id if student_class else student.major_id
    return student, class_code, major_id


def get_student_training_program(student_code):
    student = Student.query.filter_by(student_code=student_code).first()
    if not student or not student.class_id:
        return None

    student_class = student.student_class
    if not student_class:
        return None

    return TrainingProgram.query.filter_by(
        major_id=student_class.major_id,
        school_year=student_class.school_year,
    ).first()


def get_available_training_program_semesters(student_code):
    training_program = get_student_training_program(student_code)
    if not training_program:
        return list(range(1, 12))

    semesters = [
        semester_no
        for semester_no, in db.session.query(TrainingProgramCourse.semester_no).filter(
            TrainingProgramCourse.training_program_id == training_program.id
        ).distinct().order_by(TrainingProgramCourse.semester_no).all()
    ]
    return semesters or list(range(1, 12))


def get_default_training_program_semester(student_code):
    semesters = get_available_training_program_semesters(student_code)
    if not semesters:
        return None

    student, student_class_code, major_id = get_student_context(student_code)
    if not student or not student.student_class or not student.student_class.school_year:
        return semesters[0]

    try:
        school_year = int(student.student_class.school_year)
    except (TypeError, ValueError):
        return semesters[0]

    today = datetime.now()
    current_year = today.year
    current_month = today.month

    # Quy ước:
    # - tháng 8-12: học kỳ 1 của năm học mới
    # - tháng 1-7: học kỳ 2 của năm học đang diễn ra
    if current_month >= 8:
        computed_semester = (current_year - school_year) * 2 + 1
    else:
        computed_semester = (current_year - school_year - 1) * 2 + 2

    if computed_semester < semesters[0]:
        return semesters[0]

    if computed_semester > semesters[-1]:
        return semesters[-1]

    eligible_semesters = [semester_no for semester_no in semesters if semester_no <= computed_semester]
    return eligible_semesters[-1] if eligible_semesters else semesters[0]


def get_allowed_course_ids(student_code, training_program_semester=None):
    training_program = get_student_training_program(student_code)
    if training_program:
        query = TrainingProgramCourse.query.filter_by(training_program_id=training_program.id)
        if training_program_semester:
            query = query.filter(TrainingProgramCourse.semester_no == int(training_program_semester))
        return [item.course_id for item in query.all()]

    student_id, class_id, major_id = get_student_context(student_code)
    if major_id is None:
        return []

    major_course_ids = [
        item.course_id
        for item in CourseMajor.query.filter_by(major_id=major_id).all()
    ]
    shared_course_ids = [
        course_id
        for course_id, in db.session.query(Course.id).filter(Course.is_shared.is_(True)).all()
    ]
    return list({*major_course_ids, *shared_course_ids})


def get_student_program_course_ids(student_code):
    training_program = get_student_training_program(student_code)
    if training_program:
        course_ids = [
            item.course_id
            for item in TrainingProgramCourse.query.filter_by(
                training_program_id=training_program.id
            ).all()
        ]
        shared_course_ids = [
            course_id
            for course_id, in db.session.query(Course.id).filter(Course.is_shared.is_(True)).all()
        ]
        return list({*course_ids, *shared_course_ids})

    return get_allowed_course_ids(student_code)


def is_current_training_program_semester(student_code, training_program_semester=None):
    current_semester = get_current_training_program_semester(student_code)
    if not current_semester:
        return False
    return str(training_program_semester or current_semester) == str(current_semester)


def get_current_open_semester(student_code):
    training_program = get_student_training_program(student_code)
    current_semester = get_current_training_program_semester(student_code)

    if training_program and current_semester:
        mapped_semester = db.session.query(ClassSection.semester).join(
            TrainingProgramCourse,
            TrainingProgramCourse.course_id == ClassSection.course_id,
        ).filter(
            TrainingProgramCourse.training_program_id == training_program.id,
            TrainingProgramCourse.semester_no == current_semester,
            ClassSection.section_type == ClassSectionType.THEORY,
            ClassSection.semester.isnot(None),
        ).order_by(ClassSection.start_date.desc()).first()
        if mapped_semester:
            return mapped_semester[0]

    latest_semester = db.session.query(ClassSection.semester).filter(
        ClassSection.section_type == ClassSectionType.THEORY,
        ClassSection.semester.isnot(None),
    ).order_by(ClassSection.start_date.desc()).first()
    return latest_semester[0] if latest_semester else None


def is_current_open_section(student_code, section):
    current_open_semester = get_current_open_semester(student_code)
    return (
        section is not None
        and current_open_semester is not None
        and section.semester == current_open_semester
    )


def is_course_in_student_major(student_code, course):
    student, student_class_code, major_id = get_student_context(student_code)
    if not course or major_id is None:
        return False
    training_program = get_student_training_program(student_code)
    if training_program and TrainingProgramCourse.query.filter_by(
        training_program_id=training_program.id,
        course_id=course.id,
    ).first():
        return True
    if course.is_shared:
        return True
    return CourseMajor.query.filter_by(
        course_id=course.id,
        major_id=major_id,
    ).first() is not None


def is_course_in_current_training_program_semester(student_code, course_id):
    current_semester = get_current_training_program_semester(student_code)
    training_program = get_student_training_program(student_code)

    if training_program and current_semester:
        return TrainingProgramCourse.query.filter_by(
            training_program_id=training_program.id,
            course_id=course_id,
            semester_no=current_semester,
        ).first() is not None

    return course_id in get_allowed_course_ids(student_code)


def is_course_registrable_for_student(student_code, course):
    if not course:
        return False
    if course.is_shared:
        return True
    return course.id in get_student_program_course_ids(student_code)


def get_student_faculty_id(student_code):
    student, student_class_code, major_id = get_student_context(student_code)
    if not student:
        return None
    if student.student_class and student.student_class.major:
        return student.student_class.major.faculty_id
    if student.major_id:
        major = Major.query.get(student.major_id)
        if major:
            return major.faculty_id
    return None


def get_current_training_program_semester(student_code):
    return get_default_training_program_semester(student_code)


def is_course_allowed(student_code, course):
    student, student_class_code, major_id = get_student_context(student_code)
    if student and student.class_id:
        training_program = get_student_training_program(student_code)
        if training_program:
            return TrainingProgramCourse.query.filter_by(
                training_program_id=training_program.id,
                course_id=course.id,
            ).first() is not None

    if major_id is None:
        return False
    if course.is_shared:
        return True
    return CourseMajor.query.filter_by(
        course_id=course.id,
        major_id=major_id
    ).first() is not None

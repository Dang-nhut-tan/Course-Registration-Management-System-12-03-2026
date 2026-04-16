import hashlib

from app import app, db
from flask_login import LoginManager
from datetime import datetime, timedelta
from app.model import ClassSection, ClassSectionType, Course, CourseMajor, CoursePrerequisite, Enrollment, EnrollmentStatus, Faculty, Major, Schedule, Student, StudentClassSection, TrainingProgram, TrainingProgramCourse, User

def check_login_student(student_code, password):
    if student_code and password:
        password = hashlib.md5(password.strip().encode("utf-8")).hexdigest()
        return User.query.filter(
            User.password == password,
            User.student_code == student_code.strip(),
        ).first()

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def check_room_conflict(day, start_time, end_time, room_id):
    query = db.session.query(Schedule).join(ClassSection).filter(
        Schedule.day_of_week==day,
        Schedule.start_time < end_time,
        Schedule.end_time > start_time,
        ClassSection.room_id == room_id
    )
    if query.first():
        return True
    return False

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

    student, _, _ = get_student_context(student_code)
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


def get_student_faculty_id(student_code):
    student, _, _ = get_student_context(student_code)
    if not student:
        return None
    if student.student_class and student.student_class.major:
        return student.student_class.major.faculty_id
    if student.major_id:
        major = Major.query.get(student.major_id)
        if major:
            return major.faculty_id
    return None


def get_sections(student_code, course_id=None, faculty_id=None, training_program_semester=None):
    query = ClassSection.query.filter(ClassSection.section_type == ClassSectionType.THEORY)
    allowed_course_ids = get_allowed_course_ids(student_code, training_program_semester)

    if not allowed_course_ids:
        return []

    query = query.filter(ClassSection.course_id.in_(allowed_course_ids))

    if course_id:
        query = query.filter(ClassSection.course_id == int(course_id))
    if faculty_id:
        query = query.join(Course).filter(Course.faculty_id == int(faculty_id))

    return query.all()


def get_open_filter_options(student_code, training_program_semester=None):
    allowed_course_ids = get_allowed_course_ids(student_code, training_program_semester)
    if not allowed_course_ids:
        return [], []

    open_sections_query = db.session.query(ClassSection.course_id).filter(
        ClassSection.section_type == ClassSectionType.THEORY,
        ClassSection.course_id.in_(allowed_course_ids),
    ).distinct()

    open_course_ids = [course_id for course_id, in open_sections_query.all()]
    if not open_course_ids:
        return [], []

    courses = Course.query.filter(Course.id.in_(open_course_ids)).order_by(Course.name).all()
    faculties = db.session.query(Faculty).join(
        Course, Course.faculty_id == Faculty.id
    ).filter(
        Course.id.in_(open_course_ids)
    ).distinct().order_by(Faculty.name).all()
    return courses, faculties


def get_current_training_program_semester(student_code):
    return get_default_training_program_semester(student_code)


def get_registered_courses(student_code):
    query = Enrollment.query.join(ClassSection).filter(
        Enrollment.student_code == student_code,
        ClassSection.section_type == ClassSectionType.THEORY,
        Enrollment.status == EnrollmentStatus.REGISTERED,
    )

    training_program = get_student_training_program(student_code)
    current_semester = get_current_training_program_semester(student_code)
    if training_program and current_semester:
        query = query.join(
            TrainingProgramCourse,
            TrainingProgramCourse.course_id == ClassSection.course_id,
        ).filter(
            TrainingProgramCourse.training_program_id == training_program.id,
            TrainingProgramCourse.semester_no == current_semester,
        )

    return query.all()


def get_registered_credits(student_code):
    enrollments = Enrollment.query.join(
        ClassSection, Enrollment.class_section_id == ClassSection.id
    ).join(
        Course, ClassSection.course_id == Course.id
    ).filter(
        Enrollment.student_code == student_code,
        Enrollment.status == EnrollmentStatus.REGISTERED,
        ClassSection.section_type == ClassSectionType.THEORY,
    )

    training_program = get_student_training_program(student_code)
    current_semester = get_current_training_program_semester(student_code)
    if training_program and current_semester:
        enrollments = enrollments.join(
            TrainingProgramCourse,
            TrainingProgramCourse.course_id == ClassSection.course_id,
        ).filter(
            TrainingProgramCourse.training_program_id == training_program.id,
            TrainingProgramCourse.semester_no == current_semester,
        )

    enrollments = enrollments.all()

    return sum(enrollment.class_section.course.credits or 0 for enrollment in enrollments)


def get_credit_limit_per_semester(student_code):
    training_program = get_student_training_program(student_code)
    if training_program and training_program.max_credits_per_semester is not None:
        return training_program.max_credits_per_semester
    return 25


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
    ).all()

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
    if not candidate_course_ids:
        return None

    return db.session.query(Enrollment).join(
        ClassSection, Enrollment.class_section_id == ClassSection.id
    ).filter(
        Enrollment.student_code == student_code,
        Enrollment.status == EnrollmentStatus.REGISTERED,
        ClassSection.course_id.in_(candidate_course_ids),
    ).first()


def register_section(student_code, class_section_id):
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
        if section.section_type != ClassSectionType.THEORY:
            return False, "Vui lòng chọn lớp lý thuyết để đăng ký."
        if not is_course_allowed(student_code, section.course):
            return False, "Môn học không thuộc chương trình đào tạo của lớp bạn."

        is_valid, missing_courses = check_prerequisite_courses(student_code, section.course_id)
        if not is_valid:
            return False, "Bạn chưa học môn tiên quyết: " + ", ".join(missing_courses) + "."

        related_section_ids = [section.id]
        if section.linked_section_id:
            related_section_ids.append(section.linked_section_id)

        locked_sections = ClassSection.query.filter(
            ClassSection.id.in_(related_section_ids)
        ).order_by(ClassSection.id).with_for_update().all()
        locked_section_map = {locked_section.id: locked_section for locked_section in locked_sections}

        section = locked_section_map.get(class_section_id)
        related_sections = [section]
        if section and section.linked_section_id:
            practice_section = locked_section_map.get(section.linked_section_id)
            if practice_section:
                related_sections.append(practice_section)

        same_course_enrollment = has_registered_same_course(student_code, related_sections)
        if same_course_enrollment:
            return False, f"Môn {same_course_enrollment.class_section.course.name} đã được đăng ký rồi."

        conflict = get_schedule_conflict(student_code, related_sections)
        if conflict:
            conflict_section, day_of_week, start_time, end_time = conflict
            return (
                False,
                "Trùng lịch học với môn "
                f"{conflict_section.course.name} vào thứ {day_of_week} "
                f"({start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}).",
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

            if registered_count >= get_section_capacity_limit(related_section):
                if related_section.section_type == ClassSectionType.PRACTICE:
                    return False, "Lớp thực hành tương ứng đã hết chỗ."
                return False, "Lớp học phần đã hết chỗ."

            enrollments.append(enrollment)

        current_credits = get_registered_credits(student_code)
        section_credits = section.course.credits or 0
        credit_limit = get_credit_limit_per_semester(student_code)
        if current_credits + section_credits > credit_limit:
            return False, f"Tổng số tín chỉ trong 1 kỳ không được vượt quá {credit_limit}."

        for related_section, enrollment in zip(related_sections, enrollments):
            if enrollment:
                enrollment.status = EnrollmentStatus.REGISTERED
                enrollment.registered_at = registration_time
                continue

            db.session.add(
                Enrollment(
                    student_code=student_code,
                    class_section_id=related_section.id,
                    status=EnrollmentStatus.REGISTERED,
                    registered_at=registration_time,
                )
            )

        db.session.commit()
        if section.linked_section_id:
            return True, "Đăng ký môn học thành công. Hệ thống đã tự động gán lớp thực hành tương ứng."
        return True, "Đăng ký môn học thành công."
    except Exception:
        db.session.rollback()
        raise


def cancel_registered_course(student_code, enrollment_id):
    enrollment = Enrollment.query.filter(
        Enrollment.id == enrollment_id,
        #Enrollment.student_code == student_code,
    ).first()

    if not enrollment:
        return False, "Không tìm thấy môn đã đăng ký."

    if enrollment.student_code != student_code:
        return False, "Bạn không có quyền hủy môn học cua sinh viên khác."

    if enrollment.status == EnrollmentStatus.CANCELED:
        return False, "Môn học này đã được hủy trước đó."

    start_date = enrollment.class_section.start_date
    cancel_limit = start_date + timedelta(weeks=2)
    if datetime.now() > cancel_limit:
        return False, "Đã quá hạn hủy môn."

    info = StudentClassSection.query.filter(
        StudentClassSection.student_code == enrollment.student_code,
        StudentClassSection.class_section_id == enrollment.class_section_id
    ).first()

    if info and info.score_midterm is not None:
        return False, "Không thể hủy vì đã có điểm giữa kỳ."

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


def is_course_allowed(student_code, course):
    student, _, major_id = get_student_context(student_code)
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


def get_filter_data(student_code, faculty_id=None, training_program_semester=None):
    courses, faculties = get_open_filter_options(student_code, training_program_semester)
    if faculty_id:
        courses = [course for course in courses if course.faculty_id == int(faculty_id)]

    return {
        "courses": courses,
        "faculties": faculties,
        "training_program_semesters": get_available_training_program_semesters(student_code),
    }

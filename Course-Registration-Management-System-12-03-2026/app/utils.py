import hashlib

from app import app, db
from flask_login import LoginManager
from datetime import datetime, timedelta
from sqlalchemy import String, or_
from app.model import ClassSection, ClassSectionType, Course, CourseMajor, CoursePrerequisite, Enrollment, EnrollmentStatus, Faculty, Major, Schedule, Student, TrainingProgram, TrainingProgramCourse, User, UserRole

MIN_CREDITS_PER_SEMESTER = 12

def check_login_student(student_code, password):
    if student_code and password:
        password = hashlib.md5(password.strip().encode("utf-8")).hexdigest()
        return User.query.filter(
            User.password == password,
            User.student_code == student_code.strip(),
        ).first()

def check_login_admin(username, password):
    if username and password:
        password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()
        return User.query.filter(User.username == username.strip(),
                                 User.password == password,
                                 User.role == UserRole.ADMIN).first()
    return None

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
        ClassSection.room_id == room_id,
        ClassSection.end_date >= datetime.now(),
    )
    if query.first():
        return True
    return False

def check_teacher_conflict(day, start_time, end_time, teacher_id):
    query = db.session.query(Schedule).join(ClassSection).filter(
        Schedule.day_of_week == day,
        Schedule.start_time < end_time,
        Schedule.end_time > start_time,
        ClassSection.teacher_id == teacher_id,
        ClassSection.end_date >= datetime.now(),
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


def get_section_registration_block_reason(student_code, section):
    if not section:
        return "Không tìm thấy lớp học phần."
    if section.section_type != ClassSectionType.THEORY:
        return "Vui lòng chọn lớp lý thuyết để đăng ký."
    if not is_current_open_section(student_code, section):
        return "Không thuộc học kỳ hiện tại."
    if not is_course_registrable_for_student(student_code, section.course):
        return "Không thuộc ngành của bạn."

    registration_start_date = get_section_registration_start_date(section)
    registration_deadline = get_section_registration_deadline(section)
    now = datetime.now()
    if registration_start_date and now < registration_start_date:
        return "Chưa tới ngày bắt đầu đăng ký môn học."
    if registration_deadline and now > registration_deadline:
        return "Đã quá hạn đăng ký môn học."

    is_valid, missing_courses = check_prerequisite_courses(student_code, section.course_id)
    if not is_valid:
        return "Thiếu tiên quyết: " + ", ".join(missing_courses)

    credit_limit = get_credit_limit_per_semester(student_code)
    current_credits = get_registered_credits(student_code)
    section_credits = section.course.credits or 0
    if current_credits + section_credits > credit_limit:
        return f"Vượt giới hạn {credit_limit} tín chỉ trong 1 kỳ."

    return None


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


def get_current_training_program_semester(student_code):
    return get_default_training_program_semester(student_code)


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


def calculate_total_score(midterm_score, final_score):
    if midterm_score is None or final_score is None:
        return None
    return round((midterm_score * 0.4) + (final_score * 0.6), 1)


def convert_score_to_scale_4(total_score):
    if total_score is None:
        return None
    if total_score >= 8.5:
        return 4.0
    if total_score >= 7.0:
        return 3.0
    if total_score >= 5.5:
        return 2.0
    if total_score >= 4.0:
        return 1.0
    return 0


def convert_score_to_letter(total_score):
    if total_score is None:
        return None
    if total_score >= 8.5:
        return "A"
    if total_score >= 7.0:
        return "B"
    if total_score >= 5.5:
        return "C"
    if total_score >= 4.0:
        return "D"
    return "F"


def get_pass_fail_result(total_score):
    if total_score is None:
        return None
    return "PASS" if total_score >= 4.0 else "FAIL"


def build_grade_result(enrollment):
    section = enrollment.class_section
    grade = enrollment.grade
    midterm_score = grade.midterm_score if grade else None
    final_score = grade.final_score if grade else None
    total_score = calculate_total_score(midterm_score, final_score)

    return {
        "enrollment": enrollment,
        "section": section,
        "course": section.course,
        "grade": grade,
        "midterm_score": midterm_score,
        "final_score": final_score,
        "total_score": total_score,
        "scale_4_score": convert_score_to_scale_4(total_score),
        "letter_score": convert_score_to_letter(total_score),
        "result": get_pass_fail_result(total_score),
    }


def get_student_grade_results(student_code):
    enrollments = Enrollment.query.join(ClassSection).filter(
        Enrollment.student_code == student_code,
        ClassSection.section_type == ClassSectionType.THEORY,
    ).order_by(ClassSection.semester.desc(), ClassSection.id).all()

    return [build_grade_result(enrollment) for enrollment in enrollments]


def calculate_weighted_average(items, score_key):
    total_points = 0
    total_credits = 0
    for item in items:
        score = item.get(score_key)
        credits = item["course"].credits or 0
        if score is None or credits <= 0:
            continue
        total_points += score * credits
        total_credits += credits

    if total_credits == 0:
        return None
    return round(total_points / total_credits, 2)


def classify_average(scale_4_score):
    if scale_4_score is None:
        return "-"
    if scale_4_score >= 3.6:
        return "Xuất sắc"
    if scale_4_score >= 3.2:
        return "Giỏi"
    if scale_4_score >= 2.5:
        return "Khá"
    if scale_4_score >= 2.0:
        return "Trung bình"
    return "Yếu"


def get_passed_credits(items):
    return sum(
        item["course"].credits or 0
        for item in items
        if item.get("total_score") is not None and item["total_score"] >= 4.0
    )


def get_completed_credits(items):
    return sum(
        item["course"].credits or 0
        for item in items
        if item.get("total_score") is not None
    )


def semester_sort_key(semester):
    try:
        year, term = str(semester).split("-", 1)
        return int(year), int(term)
    except (TypeError, ValueError):
        return 0, 0


def build_study_result_context(student_code):
    grade_results = get_student_grade_results(student_code)
    grouped = {}
    for item in grade_results:
        grouped.setdefault(item["section"].semester, []).append(item)

    semester_rows = []
    cumulative_items = []
    for semester in sorted(grouped, key=semester_sort_key):
        items = grouped[semester]
        cumulative_items.extend(items)

        semester_average_10 = calculate_weighted_average(items, "total_score")
        semester_average_4 = calculate_weighted_average(items, "scale_4_score")
        cumulative_average_4 = calculate_weighted_average(cumulative_items, "scale_4_score")

        semester_rows.append(
            {
                "semester": semester,
                "courses": items,
                "summary": {
                    "semester_average_10": semester_average_10,
                    "semester_average_4": semester_average_4,
                    "semester_credits": get_passed_credits(items),
                    "cumulative_average_4": cumulative_average_4,
                    "cumulative_credits": get_passed_credits(cumulative_items),
                    "classification": classify_average(semester_average_4),
                },
            }
        )

    return list(reversed(semester_rows))


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
        ClassSection.end_date.isnot(None),
        ClassSection.end_date < datetime.now(),
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
        block_reason = get_section_registration_block_reason(student_code, section)
        if block_reason:
            return False, block_reason

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
            return True, "Đăng ký môn học thành công. Hệ thống đã tự động gắn lớp thực hành tương ứng."
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
        return False, "Bạn không có quyền hủy môn học của sinh viên khác."

    if enrollment.status == EnrollmentStatus.CANCELED:
        return False, "Môn học này đã được hủy trước đó."

    start_date = enrollment.class_section.start_date
    cancel_limit = start_date + timedelta(weeks=2)
    if datetime.now() > cancel_limit:
        return False, "Đã quá hạn hủy môn."

    if enrollment.grade and enrollment.grade.midterm_score is not None:
        return False, "Không thể hủy môn vì đã có điểm giữa kỳ"

    minimum_credits = get_minimum_credits_to_enforce(student_code)
    canceled_credits = (
        enrollment.class_section.course.credits or 0
        if enrollment.class_section.section_type == ClassSectionType.THEORY
        else 0
    )
    credits_after_cancel = max(get_registered_credits(student_code) - canceled_credits, 0)
    if minimum_credits and credits_after_cancel < minimum_credits:
        return False, f"Không thể hủy vì nếu hủy sẽ có số tín chỉ nhỏ hơn {minimum_credits}."

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


def get_filter_data(student_code, faculty_id=None, training_program_semester=None):
    courses, faculties = get_open_filter_options(student_code, training_program_semester)

    return {
        "courses": courses,
        "faculties": Faculty.query.order_by(Faculty.name).all(),
        "training_program_semesters": get_available_training_program_semesters(student_code),
    }

def get_student_timetable(student_code, requested_week=1):
    semester_no = get_current_training_program_semester(student_code)

    training_program = get_student_training_program(student_code)

    if not training_program:
        return {
            "schedules": [],
            "semester_no": "N/A",
            "semester_raw": "N/A",
            "week_days": [],
            "week": 1,
            "max_week": 1,
            "can_previous_week": False,
            "can_next_week": False,
            "term_start": None,
            "term_end": None,
        }

    schedules = db.session.query(Schedule) \
        .join(ClassSection, Schedule.class_section_id == ClassSection.id) \
        .join(Enrollment, Enrollment.class_section_id == ClassSection.id) \
        .join(TrainingProgramCourse, TrainingProgramCourse.course_id == ClassSection.course_id) \
        .filter(
        Enrollment.student_code == student_code,
        Enrollment.status == EnrollmentStatus.REGISTERED,
        TrainingProgramCourse.training_program_id == training_program.id,
        TrainingProgramCourse.semester_no == semester_no
    ).order_by(ClassSection.start_date, Schedule.day_of_week, Schedule.start_time).all()

    raw_semester = "2026-1"
    if schedules:
        raw_semester = schedules[0].class_section.semester

    if schedules:
        term_start = min(schedule.class_section.start_date.date() for schedule in schedules)
        term_end = max(schedule.class_section.end_date.date() for schedule in schedules)
    else:
        term_start = datetime.now().date()
        term_end = term_start

    max_week = max(((term_end - term_start).days // 7) + 1, 1)
    current_week = min(max(requested_week or 1, 1), max_week)

    week_start_date = term_start + timedelta(days=(current_week - 1) * 7)
    week_days = [{'thu': i + 2 if i < 6 else 8, 'date': week_start_date + timedelta(days=i)} for i in range(7)]
    week_dates_by_day = {day["thu"]: day["date"] for day in week_days}

    active_schedules = []
    for schedule in schedules:
        class_date = week_dates_by_day.get(schedule.day_of_week)
        section_start = schedule.class_section.start_date.date()
        section_end = schedule.class_section.end_date.date()
        if class_date and section_start <= class_date <= section_end:
            active_schedules.append(schedule)

    return {
        "schedules": active_schedules,
        "semester_no": semester_no,
        "semester_raw": raw_semester,
        "week_days": week_days,
        "week": current_week,
        "max_week": max_week,
        "can_previous_week": current_week > 1,
        "can_next_week": current_week < max_week,
        "term_start": term_start,
        "term_end": term_end,
    }

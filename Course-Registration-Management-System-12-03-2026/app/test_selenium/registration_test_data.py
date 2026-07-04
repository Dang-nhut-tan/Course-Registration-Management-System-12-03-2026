import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from app import app, db
from app.model import (
    Campus,
    ClassSection,
    Course,
    CoursePrerequisite,
    Enrollment,
    EnrollmentStatus,
    Faculty,
    Major,
    Room,
    Schedule,
    Student,
    StudentClass,
    TrainingProgram,
    TrainingProgramCourse,
    User,
    UserRole,
)


@dataclass(frozen=True)
class RegistrationScenario:
    student_code: str
    course_name: str
    prerequisite_name: str | None = None


def _active_program_semester(now):
    # A class beginning this academic year is always in semester 1 or 2,
    # independent of the calendar year in which the test is executed.
    return 1 if now.month >= 8 else 2


def _school_year_for_active_semester(now):
    return now.year if now.month >= 8 else now.year - 1


def _password_hash(password):
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def create_registration_scenario(
    prefix,
    *,
    baseline_credits=0,
    target_enrolled=False,
    cancel_deadline_passed=False,
    target_section_count=1,
    target_capacity=50,
    registration_deadline_passed=False,
    missing_prerequisite=False,
):
    """Create isolated Selenium data whose dates are relative to test runtime."""
    if baseline_credits % 3:
        raise ValueError("baseline_credits must be divisible by 3")

    now = datetime.now()
    token = uuid.uuid4().hex[:10]
    student_code = f"SEL{token}".upper()
    course_name = f"{prefix} {token}"
    program_semester = _active_program_semester(now)
    semester = f"SEL-{now:%Y%m}-{token}"

    with app.app_context():
        faculty = Faculty(
            name=f"SEL Faculty {token}",
            registration_start_date=now - timedelta(days=2),
            registration_deadline=(
                now - timedelta(days=1)
                if registration_deadline_passed
                else now + timedelta(days=30)
            ),
        )
        db.session.add(faculty)
        db.session.flush()

        major = Major(name=f"SEL Major {token}", faculty_id=faculty.id)
        db.session.add(major)
        db.session.flush()

        student_class = StudentClass(
            code=f"SC{token}",
            name=f"SEL Class {token}",
            school_year=str(_school_year_for_active_semester(now)),
            major_id=major.id,
        )
        db.session.add(student_class)
        db.session.flush()

        student = Student(
            student_code=student_code,
            name=f"SEL Student {token}",
            birth_year=2005,
            major_id=major.id,
            class_id=student_class.id,
        )
        user = User(
            student_code=student_code,
            password=_password_hash("123456"),
            role=UserRole.STUDENT,
        )
        db.session.add_all([student, user])

        campus = Campus(name=f"SEL Campus {token}")
        db.session.add(campus)
        db.session.flush()

        room = Room(
            name=f"SEL Room {token}",
            room_type="theory",
            capacity=50,
            campus_id=campus.id,
        )
        db.session.add(room)
        db.session.flush()

        program = TrainingProgram(
            name=f"SEL Program {token}",
            major_id=major.id,
            school_year=student_class.school_year,
            max_credits_per_semester=25,
        )
        db.session.add(program)
        db.session.flush()

        target_course = Course(name=course_name, credits=3, faculty_id=faculty.id)
        db.session.add(target_course)
        db.session.flush()
        db.session.add(
            TrainingProgramCourse(
                training_program_id=program.id,
                course_id=target_course.id,
                semester_no=program_semester,
            )
        )

        prerequisite_name = None
        if missing_prerequisite:
            prerequisite_name = f"SEL Prerequisite {token}"
            prerequisite = Course(
                name=prerequisite_name,
                credits=3,
                faculty_id=faculty.id,
            )
            db.session.add(prerequisite)
            db.session.flush()
            db.session.add_all(
                [
                    TrainingProgramCourse(
                        training_program_id=program.id,
                        course_id=prerequisite.id,
                        semester_no=program_semester,
                    ),
                    CoursePrerequisite(
                        course_id=target_course.id,
                        prerequisite_id=prerequisite.id,
                    ),
                ]
            )

        # The extra mapped course keeps the minimum-credit scenario's curriculum
        # load above 12, avoiding the final-semester exemption.
        curriculum_only_course = Course(
            name=f"SEL Curriculum Only {token}",
            credits=3,
            faculty_id=faculty.id,
        )
        db.session.add(curriculum_only_course)
        db.session.flush()
        db.session.add(
            TrainingProgramCourse(
                training_program_id=program.id,
                course_id=curriculum_only_course.id,
                semester_no=program_semester,
            )
        )

        current_week_start = now - timedelta(days=now.weekday())
        target_start = current_week_start - timedelta(
            days=21 if cancel_deadline_passed else 0
        )
        target_sections = []
        for index in range(target_section_count):
            section = ClassSection(
                name=f"SEL Target {index + 1} {token}",
                course_id=target_course.id,
                student_class_id=student_class.id,
                room_id=room.id,
                semester=semester,
                max_students=target_capacity,
                start_date=target_start,
                end_date=now + timedelta(days=90),
            )
            db.session.add(section)
            db.session.flush()
            db.session.add(
                Schedule(
                    class_section_id=section.id,
                    day_of_week=2 + index,
                    start_time=datetime.strptime("07:30", "%H:%M").time(),
                    end_time=datetime.strptime("09:30", "%H:%M").time(),
                )
            )
            target_sections.append(section)

        if target_enrolled:
            db.session.add(
                Enrollment(
                    student_code=student_code,
                    class_section_id=target_sections[0].id,
                    status=EnrollmentStatus.REGISTERED,
                    registered_at=now,
                )
            )

        for index in range(baseline_credits // 3):
            course = Course(
                name=f"SEL Baseline {index + 1} {token}",
                credits=3,
                faculty_id=faculty.id,
            )
            db.session.add(course)
            db.session.flush()
            db.session.add(
                TrainingProgramCourse(
                    training_program_id=program.id,
                    course_id=course.id,
                    semester_no=program_semester,
                )
            )
            section = ClassSection(
                name=f"SEL Baseline Section {index + 1} {token}",
                course_id=course.id,
                student_class_id=student_class.id,
                room_id=room.id,
                semester=semester,
                max_students=50,
                start_date=current_week_start,
                end_date=now + timedelta(days=90),
            )
            db.session.add(section)
            db.session.flush()
            db.session.add_all(
                [
                    Schedule(
                        class_section_id=section.id,
                        day_of_week=3 + index,
                        start_time=datetime.strptime("13:00", "%H:%M").time(),
                        end_time=datetime.strptime("15:00", "%H:%M").time(),
                    ),
                    Enrollment(
                        student_code=student_code,
                        class_section_id=section.id,
                        status=EnrollmentStatus.REGISTERED,
                        registered_at=now,
                    ),
                ]
            )

        db.session.commit()

    return RegistrationScenario(
        student_code=student_code,
        course_name=course_name,
        prerequisite_name=prerequisite_name,
    )

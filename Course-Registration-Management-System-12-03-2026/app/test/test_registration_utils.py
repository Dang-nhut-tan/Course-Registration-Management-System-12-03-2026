from datetime import datetime, time, timedelta

import pytest

from app import api, db
from app import utils
from app.model import ClassSection,Course,CoursePrerequisite,Enrollment,EnrollmentStatus,Faculty,Major,Schedule,Student,StudentClass,TrainingProgram,TrainingProgramCourse
from app.test.test_base import test_app, test_session


CURRENT_TRAINING_PROGRAM_SEMESTER = 6


def seed_student_context(test_session, student_code="2354050999"):
    faculty = Faculty(id=1, name="CNTT")
    major = Major(id=1, name="HTTT", faculty_id=1)
    student_class = StudentClass(
        id=1,
        code="DH23IT01",
        name="DH23IT01",
        school_year="2023",
        major_id=1,
    )
    student = Student(
        student_code=student_code,
        name="Test Student",
        birth_year=2005,
        major_id=1,
        class_id=1,
    )
    training_program = TrainingProgram(
        id=1,
        name="CTDT HTTT K2023",
        major_id=1,
        school_year="2023",
        max_credits_per_semester=25,
    )

    test_session.add_all([faculty, major, student_class, student, training_program])
    test_session.commit()


def add_course_with_section(
    test_session,
    course_id,
    section_id,
    credits=3,
    semester_no=CURRENT_TRAINING_PROGRAM_SEMESTER,
    start_offset_days=-5,
    end_offset_days=30,
    add_to_training_program=True,
    faculty_id=1,
    is_shared=False,
):
    course = Course(
        id=course_id,
        name=f"Course {course_id}",
        credits=credits,
        faculty_id=faculty_id,
        is_shared=is_shared,
    )
    section = ClassSection(
        id=section_id,
        name=f"LHP {section_id}",
        course_id=course_id,
        semester="2026-1",
        max_students=50,
        start_date=datetime.now() + timedelta(days=start_offset_days),
        end_date=datetime.now() + timedelta(days=end_offset_days),
    )
    records = [course, section]
    if add_to_training_program:
        records.append(
            TrainingProgramCourse(
                training_program_id=1,
                course_id=course_id,
                semester_no=semester_no,
            )
        )

    test_session.add_all(records)
    test_session.commit()

    return course, section


def test_prerequisite_requires_completed_course(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        prerequisite_course, prerequisite_section = add_course_with_section(
            test_session,
            course_id=1,
            section_id=1,
            end_offset_days=10,
        )
        add_course_with_section(test_session, course_id=2, section_id=2)
        test_session.add(CoursePrerequisite(course_id=2, prerequisite_id=1))
        test_session.add(
            Enrollment(
                id=1,
                student_code="2354050999",
                class_section_id=prerequisite_section.id,
                status=EnrollmentStatus.REGISTERED,
            )
        )
        test_session.commit()

        with pytest.raises(api.ApiError):
            api.register_enrollment("2354050999", 2)


def test_register_section_blocks_after_faculty_registration_deadline(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        course, section = add_course_with_section(test_session, course_id=1, section_id=1)
        faculty = db.session.get(Faculty, 1)
        faculty.registration_deadline = datetime.now() - timedelta(days=1)
        test_session.commit()

        with pytest.raises(api.ApiError) as error:
            api.register_enrollment("2354050999", section.id)

        assert "quá hạn đăng ký" in error.value.message
        assert Enrollment.query.filter_by(
            student_code="2354050999",
            class_section_id=section.id,
        ).count() == 0


def test_register_section_blocks_before_faculty_registration_start_date(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        course, section = add_course_with_section(test_session, course_id=1, section_id=1)
        faculty = db.session.get(Faculty, 1)
        faculty.registration_start_date = datetime.now() + timedelta(days=1)
        faculty.registration_deadline = datetime.now() + timedelta(days=7)
        test_session.commit()

        with pytest.raises(api.ApiError) as error:
            api.register_enrollment("2354050999", section.id)

        assert "Chưa tới ngày" in error.value.message
        assert Enrollment.query.filter_by(
            student_code="2354050999",
            class_section_id=section.id,
        ).count() == 0


def test_get_sections_hides_before_faculty_registration_start_date(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        course, section = add_course_with_section(test_session, course_id=1, section_id=1)
        faculty = db.session.get(Faculty, 1)
        faculty.registration_start_date = datetime.now() + timedelta(days=1)
        faculty.registration_deadline = datetime.now() + timedelta(days=7)
        test_session.commit()

        sections = utils.get_sections("2354050999")

        assert section not in sections


def test_get_sections_hides_extra_class_section_outside_current_training_program_semester(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        add_course_with_section(test_session, course_id=1, section_id=1)
        extra_course, extra_section = add_course_with_section(
            test_session,
            course_id=2,
            section_id=2,
            add_to_training_program=False,
        )

        sections = utils.get_sections("2354050999")
        courses, faculties = utils.get_open_filter_options("2354050999")

        assert extra_section not in sections
        assert extra_course not in courses


def test_get_sections_filters_by_course_text_and_faculty(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        add_course_with_section(test_session, course_id=1, section_id=1)
        add_course_with_section(test_session, course_id=2, section_id=2)

        sections = utils.get_sections("2354050999", course_query="Course 2", faculty_id=1)

        assert [section.id for section in sections] == [2]


def test_course_search_can_show_shared_course_from_other_faculty(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        other_faculty = Faculty(id=2, name="Kinh tế")
        test_session.add(other_faculty)
        shared_course, shared_section = add_course_with_section(
            test_session,
            course_id=2,
            section_id=2,
            add_to_training_program=False,
            faculty_id=2,
            is_shared=True,
        )

        sections = utils.get_sections(
            "2354050999",
            course_query="Course 2",
            faculty_id=1,
        )
        result = api.register_enrollment("2354050999", shared_section.id)

        assert [section.id for section in sections] == [shared_section.id]
        assert result.linked_section_registered is False


def test_register_section_blocks_extra_class_section_outside_current_training_program_semester(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        add_course_with_section(test_session, course_id=1, section_id=1)
        extra_course, extra_section = add_course_with_section(
            test_session,
            course_id=2,
            section_id=2,
            add_to_training_program=False,
        )

        with pytest.raises(api.ApiError) as error:
            api.register_enrollment("2354050999", extra_section.id)

        assert error.value.message == "Không thuộc ngành của bạn."
        assert Enrollment.query.filter_by(
            student_code="2354050999",
            class_section_id=extra_section.id,
            status=EnrollmentStatus.REGISTERED,
        ).count() == 0


def test_section_registration_block_reason_blocks_over_credit_limit(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)

        for course_id in range(1, 10):
            add_course_with_section(test_session, course_id=course_id, section_id=course_id, credits=3)

        candidate_course, candidate_section = add_course_with_section(
            test_session,
            course_id=10,
            section_id=10,
            credits=3,
        )
        for enrollment_id, section_id in enumerate(range(1, 9), start=1):
            test_session.add(
                Enrollment(
                    id=enrollment_id,
                    student_code="2354050999",
                    class_section_id=section_id,
                    status=EnrollmentStatus.REGISTERED,
                )
            )
        test_session.commit()

        with pytest.raises(api.ApiError) as validation_error:
            utils.validate_section_registration("2354050999", candidate_section)
        with pytest.raises(api.ApiError) as error:
            api.register_enrollment("2354050999", candidate_section.id)

        assert validation_error.value.message == "Vượt giới hạn 25 tín chỉ trong 1 kỳ."#######
        assert error.value.message == "Vượt giới hạn 25 tín chỉ trong 1 kỳ."


def test_registered_courses_includes_current_open_semester_enrollment(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        add_course_with_section(test_session, course_id=1, section_id=1)
        extra_course, extra_section = add_course_with_section(
            test_session,
            course_id=2,
            section_id=2,
            add_to_training_program=False,
        )
        test_session.add(
            Enrollment(
                student_code="2354050999",
                class_section_id=extra_section.id,
                status=EnrollmentStatus.REGISTERED,
            )
        )
        test_session.commit()

        registered_courses = utils.get_registered_courses("2354050999")

        assert [enrollment.class_section_id for enrollment in registered_courses] == [extra_section.id]


def test_registered_courses_hides_ended_and_previous_semester_enrollments(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        current_course, current_section = add_course_with_section(
            test_session,
            course_id=1,
            section_id=1,
        )
        ended_course, ended_section = add_course_with_section(
            test_session,
            course_id=2,
            section_id=2,
            end_offset_days=-1,
        )
        previous_course, previous_section = add_course_with_section(
            test_session,
            course_id=3,
            section_id=3,
            semester_no=1,
        )
        previous_section.semester = "2025-1"
        test_session.add_all([
            Enrollment(
                id=1,
                student_code="2354050999",
                class_section_id=current_section.id,
                status=EnrollmentStatus.REGISTERED,
            ),
            Enrollment(
                id=2,
                student_code="2354050999",
                class_section_id=ended_section.id,
                status=EnrollmentStatus.REGISTERED,
            ),
            Enrollment(
                id=3,
                student_code="2354050999",
                class_section_id=previous_section.id,
                status=EnrollmentStatus.REGISTERED,
            ),
        ])
        test_session.commit()

        registered_courses = utils.get_registered_courses("2354050999")

        assert [enrollment.class_section_id for enrollment in registered_courses] == [current_section.id]


def test_register_section_ignores_ended_same_course_enrollment(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        course, current_section = add_course_with_section(
            test_session,
            course_id=1,
            section_id=1,
        )
        ended_section = ClassSection(
            id=2,
            name="Old section",
            course_id=course.id,
            semester="2025-2",
            max_students=50,
            start_date=datetime.now() - timedelta(days=90),
            end_date=datetime.now() - timedelta(days=1),
        )
        test_session.add_all([
            ended_section,
            Enrollment(
                student_code="2354050999",
                class_section_id=ended_section.id,
                status=EnrollmentStatus.REGISTERED,
            ),
        ])
        test_session.commit()

        result = api.register_enrollment("2354050999", current_section.id)

        assert result.linked_section_registered is False
        assert Enrollment.query.filter_by(
            student_code="2354050999",
            class_section_id=current_section.id,
            status=EnrollmentStatus.REGISTERED,
        ).count() == 1


def test_register_section_uses_faculty_registration_deadline(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        course, section = add_course_with_section(test_session, course_id=1, section_id=1)
        faculty = db.session.get(Faculty, 1)
        faculty.registration_deadline = datetime.now() - timedelta(days=1)
        test_session.commit()

        with pytest.raises(api.ApiError) as error:
            api.register_enrollment("2354050999", section.id)

        assert "quá hạn đăng ký" in error.value.message


def test_cancel_course_blocks_when_falling_below_minimum_credits(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)

        for course_id in range(1, 6):
            add_course_with_section(test_session, course_id=course_id, section_id=course_id)

        for enrollment_id, section_id in enumerate(range(1, 5), start=1):
            test_session.add(
                Enrollment(
                    id=enrollment_id,
                    student_code="2354050999",
                    class_section_id=section_id,
                    status=EnrollmentStatus.REGISTERED,
                )
            )
        test_session.commit()

        with pytest.raises(api.ApiError) as error:
            api.cancel_enrollment("2354050999", 1)

        assert "12" in error.value.message


def test_cancel_course_allows_below_minimum_for_graduation_semester(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)

        for course_id in range(1, 4):
            add_course_with_section(test_session, course_id=course_id, section_id=course_id)

        for enrollment_id, section_id in enumerate(range(1, 4), start=1):
            test_session.add(
                Enrollment(
                    id=enrollment_id,
                    student_code="2354050999",
                    class_section_id=section_id,
                    status=EnrollmentStatus.REGISTERED,
                )
            )
        test_session.commit()

        result = api.cancel_enrollment("2354050999", 1)
        canceled_enrollment = db.session.get(Enrollment, 1)

        assert result is canceled_enrollment
        assert canceled_enrollment.status == EnrollmentStatus.CANCELED


def test_schedule_conflict_ignores_registered_course_outside_current_semester(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        old_course, old_section = add_course_with_section(
            test_session,
            course_id=1,
            section_id=1,
            semester_no=1,
        )
        current_course, current_section = add_course_with_section(
            test_session,
            course_id=2,
            section_id=2,
            semester_no=CURRENT_TRAINING_PROGRAM_SEMESTER,
        )
        test_session.add_all([
            Schedule(class_section_id=old_section.id, day_of_week=7, start_time=time(7, 0), end_time=time(11, 30)),
            Schedule(class_section_id=current_section.id, day_of_week=7, start_time=time(7, 0), end_time=time(11, 30)),
            Enrollment(
                student_code="2354050999",
                class_section_id=old_section.id,
                status=EnrollmentStatus.REGISTERED,
            ),
        ])
        test_session.commit()

        conflict = utils.get_schedule_conflict("2354050999", [current_section])

        assert conflict is None

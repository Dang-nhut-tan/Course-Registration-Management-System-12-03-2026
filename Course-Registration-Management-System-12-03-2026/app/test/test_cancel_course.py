from datetime import datetime, timedelta

import pytest

from app import api, db
from app.api import ApiError
from app.model import ClassSection, ClassSectionType, Enrollment, EnrollmentStatus, Grade
from app.test.test_base import test_app, test_session
from app.test.test_registration_utils import add_course_with_section, seed_student_context


@pytest.fixture
def setup_data(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)

        for i in range(1, 6):
            add_course_with_section(test_session, course_id=i, section_id=i)
            enrollment = Enrollment(
                id=i,
                student_code="2354050999",
                class_section_id=i,
                status=EnrollmentStatus.REGISTERED,
            )
            test_session.add(enrollment)

        test_session.commit()
        return db.session.get(Enrollment, 1)


def test_cancel_by_owner(setup_data, test_app, test_session):
    with test_app.app_context():
        test_session.add(setup_data)
        result = api.cancel_enrollment("2354050999", setup_data.id)

        assert result is setup_data
        assert setup_data.status == EnrollmentStatus.CANCELED


def test_cancel_by_other_student(setup_data, test_app, test_session):
    with test_app.app_context():
        test_session.add(setup_data)
        with pytest.raises(ApiError) as error:
            api.cancel_enrollment("2354050112", setup_data.id)

        assert error.value.status_code == 403
        assert setup_data.status == EnrollmentStatus.REGISTERED


def test_cancel_within_two_weeks(setup_data, test_app, test_session):
    with test_app.app_context():
        test_session.add(setup_data)
        section = db.session.get(ClassSection, 1)
        section.start_date = datetime.now() - timedelta(weeks=1)
        test_session.commit()

        result = api.cancel_enrollment("2354050999", setup_data.id)

        assert result is setup_data


def test_cancel_after_two_weeks_fails(setup_data, test_app, test_session):
    with test_app.app_context():
        test_session.add(setup_data)
        section = db.session.get(ClassSection, 1)
        section.start_date = datetime.now() - timedelta(weeks=3)###########
        test_session.commit()

        with pytest.raises(ApiError) as error:
            api.cancel_enrollment("2354050999", setup_data.id)

        assert error.value.status_code == 409

# thánh tuần 2>tuần 4
        #tuần 0
def test_cancel_no_midterm_score(setup_data, test_app, test_session):
    with test_app.app_context():
        test_session.add(setup_data)
        result = api.cancel_enrollment("2354050999", setup_data.id)

        assert result is setup_data


def test_cancel_with_midterm_score(setup_data, test_app, test_session):
    with test_app.app_context():
        test_session.add(setup_data)
        grade = Grade(enrollment=setup_data, midterm_score=8.0)
        test_session.add(grade)
        test_session.commit()

        with pytest.raises(ApiError) as error:
            api.cancel_enrollment("2354050999", setup_data.id)

        assert error.value.status_code == 409
        assert setup_data.status == EnrollmentStatus.REGISTERED


def test_cancel_registered_course_cancels_linked_practice_section(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        course, theory_section = add_course_with_section(test_session, course_id=1, section_id=1)
        practice_section = ClassSection(
            id=2,
            name="LHP 1 practice",
            course_id=course.id,
            semester=theory_section.semester,
            max_students=50,
            start_date=theory_section.start_date,
            end_date=theory_section.end_date,
            section_type=ClassSectionType.PRACTICE,
        )
        test_session.add(practice_section)
        test_session.flush()

        theory_section.linked_section_id = practice_section.id
        theory_enrollment = Enrollment(
            id=1,
            student_code="2354050999",
            class_section_id=theory_section.id,
            status=EnrollmentStatus.REGISTERED,
        )
        practice_enrollment = Enrollment(
            id=2,
            student_code="2354050999",
            class_section_id=practice_section.id,
            status=EnrollmentStatus.REGISTERED,
        )
        test_session.add_all([theory_enrollment, practice_enrollment])
        test_session.commit()

        result = api.cancel_enrollment("2354050999", theory_enrollment.id)

        assert result is theory_enrollment
        assert theory_enrollment.status == EnrollmentStatus.CANCELED
        assert practice_enrollment.status == EnrollmentStatus.CANCELED

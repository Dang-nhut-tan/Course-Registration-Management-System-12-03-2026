from datetime import datetime, timedelta
import pytest
from app import db, utils
from app.model import ClassSection, ClassSectionType, Enrollment, EnrollmentStatus, StudentClassSection
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
        actual_cancel, message= utils.cancel_registered_course("2354050999", setup_data.id)
        assert actual_cancel is True
        assert setup_data.status == EnrollmentStatus.CANCELED


def test_cancel_by_other_student(setup_data, test_app, test_session):
    with test_app.app_context():
        test_session.add(setup_data)
        actual_cancel, message = utils.cancel_registered_course("2354050112", setup_data.id)
        assert actual_cancel is False
        assert setup_data.status == EnrollmentStatus.REGISTERED


def test_cancel_within_two_weeks(setup_data, test_app, test_session):
    with test_app.app_context():
        test_session.add(setup_data)
        section = db.session.get(ClassSection, 1)
        section.start_date = datetime.now() - timedelta(weeks=1)
        test_session.commit()

        actual_cancel, message = utils.cancel_registered_course("2354050999", setup_data.id)
        assert actual_cancel is True


def test_cancel_after_two_weeks_fails(setup_data, test_app, test_session):
    with test_app.app_context():
        test_session.add(setup_data)
        section = db.session.get(ClassSection, 1)
        section.start_date = datetime.now() - timedelta(weeks=3)
        test_session.commit()

        actual_cancel, message = utils.cancel_registered_course("2354050999", setup_data.id)
        assert actual_cancel is False


def test_cancel_no_midterm_score(setup_data, test_app, test_session):
    with test_app.app_context():
        test_session.add(setup_data)
        actual_cancel, message = utils.cancel_registered_course("2354050999", setup_data.id)
        assert actual_cancel is True


def test_cancel_with_midterm_score(setup_data, test_app, test_session):
    with test_app.app_context():
        test_session.add(setup_data)
        score = StudentClassSection(
            student_code="2354050999",
            class_section_id=1,
            score_midterm=8.0
        )
        test_session.add(score)
        test_session.commit()

        actual_cancel, message = utils.cancel_registered_course("2354050999", setup_data.id)
        assert actual_cancel is False

from datetime import datetime, timedelta

from app import db, utils
from app.model import ClassSection, ClassSectionType, Enrollment, EnrollmentStatus, StudentClassSection
from app.test.test_base import test_app, test_session
from app.test.test_registration_utils import add_course_with_section, seed_student_context


def test_cancel_registered_course_success(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        add_course_with_section(test_session, course_id=1, section_id=1)

        enrollment = Enrollment(
            id=1,
            student_code="2354050999",
            class_section_id=1,
            status=EnrollmentStatus.REGISTERED,
        )
        test_session.add(enrollment)
        test_session.commit()

        success, message = utils.cancel_registered_course("2354050999", enrollment.id)
        canceled_enrollment = db.session.get(Enrollment, enrollment.id)

        assert success is True
        assert canceled_enrollment.status == EnrollmentStatus.CANCELED


def test_cancel_registered_course_not_found(test_session, test_app):
    with test_app.app_context():
        success, message = utils.cancel_registered_course("2354050999", 999)

        assert success is False


def test_cancel_registered_course_wrong_student(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        add_course_with_section(test_session, course_id=1, section_id=1)

        enrollment = Enrollment(
            id=1,
            student_code="2354050999",
            class_section_id=1,
            status=EnrollmentStatus.REGISTERED,
        )
        test_session.add(enrollment)
        test_session.commit()

        success, message = utils.cancel_registered_course("2354050000", enrollment.id)

        assert success is False
        assert enrollment.status == EnrollmentStatus.REGISTERED


def test_cancel_registered_course_already_canceled(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        add_course_with_section(test_session, course_id=1, section_id=1)

        enrollment = Enrollment(
            id=1,
            student_code="2354050999",
            class_section_id=1,
            status=EnrollmentStatus.CANCELED,
        )
        test_session.add(enrollment)
        test_session.commit()

        success, message = utils.cancel_registered_course("2354050999", enrollment.id)

        assert success is False
        assert enrollment.status == EnrollmentStatus.CANCELED


def test_cancel_registered_course_after_deadline(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        add_course_with_section(
            test_session,
            course_id=1,
            section_id=1,
            start_offset_days=-30,
        )

        enrollment = Enrollment(
            id=1,
            student_code="2354050999",
            class_section_id=1,
            status=EnrollmentStatus.REGISTERED,
        )
        test_session.add(enrollment)
        test_session.commit()

        success, message = utils.cancel_registered_course("2354050999", enrollment.id)

        assert success is False
        assert enrollment.status == EnrollmentStatus.REGISTERED


def test_cancel_registered_course_on_deadline_boundary(test_session, test_app, monkeypatch):
    with test_app.app_context():
        seed_student_context(test_session)
        add_course_with_section(test_session, course_id=1, section_id=1)

        fixed_now = datetime(2026, 5, 4, 8, 0, 0)
        section = db.session.get(ClassSection, 1)
        section.start_date = fixed_now - timedelta(weeks=2)

        class FixedDateTime(datetime):
            @classmethod
            def now(cls):
                return fixed_now

        monkeypatch.setattr(utils, "datetime", FixedDateTime)

        enrollment = Enrollment(
            id=1,
            student_code="2354050999",
            class_section_id=1,
            status=EnrollmentStatus.REGISTERED,
        )
        test_session.add(enrollment)
        test_session.commit()

        success, message = utils.cancel_registered_course("2354050999", enrollment.id)

        assert success is True
        assert enrollment.status == EnrollmentStatus.CANCELED


def test_cancel_registered_course_after_deadline_boundary(test_session, test_app, monkeypatch):
    with test_app.app_context():
        seed_student_context(test_session)
        add_course_with_section(test_session, course_id=1, section_id=1)

        fixed_now = datetime(2026, 5, 4, 8, 0, 0)
        section = db.session.get(ClassSection, 1)
        section.start_date = fixed_now - timedelta(weeks=2, seconds=1)

        class FixedDateTime(datetime):
            @classmethod
            def now(cls):
                return fixed_now

        monkeypatch.setattr(utils, "datetime", FixedDateTime)

        enrollment = Enrollment(
            id=1,
            student_code="2354050999",
            class_section_id=1,
            status=EnrollmentStatus.REGISTERED,
        )
        test_session.add(enrollment)
        test_session.commit()

        success, message = utils.cancel_registered_course("2354050999", enrollment.id)

        assert success is False
        assert enrollment.status == EnrollmentStatus.REGISTERED


def test_cancel_registered_course_has_midterm_score(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        add_course_with_section(test_session, course_id=1, section_id=1)

        enrollment = Enrollment(
            id=1,
            student_code="2354050999",
            class_section_id=1,
            status=EnrollmentStatus.REGISTERED,
        )
        score = StudentClassSection(
            student_code="2354050999",
            class_section_id=1,
            score_midterm=8.0,
        )
        test_session.add_all([enrollment, score])
        test_session.commit()

        success, message = utils.cancel_registered_course("2354050999", enrollment.id)

        assert success is False
        assert enrollment.status == EnrollmentStatus.REGISTERED


def test_cancel_registered_course_cancels_linked_practice_section(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)
        add_course_with_section(test_session, course_id=1, section_id=1)

        theory_section = db.session.get(ClassSection, 1)
        practice_section = ClassSection(
            id=2,
            name="LHP TH 2",
            course_id=1,
            semester="2026-1",
            max_students=50,
            start_date=datetime.now() - timedelta(days=5),
            end_date=datetime.now() + timedelta(days=30),
            registration_deadline=datetime.now() + timedelta(days=7),
            section_type=ClassSectionType.PRACTICE,
        )
        theory_section.linked_section_id = practice_section.id

        theory_enrollment = Enrollment(
            id=1,
            student_code="2354050999",
            class_section_id=1,
            status=EnrollmentStatus.REGISTERED,
        )
        practice_enrollment = Enrollment(
            id=2,
            student_code="2354050999",
            class_section_id=2,
            status=EnrollmentStatus.REGISTERED,
        )
        test_session.add_all([practice_section, theory_enrollment, practice_enrollment])
        test_session.commit()

        success, message = utils.cancel_registered_course("2354050999", theory_enrollment.id)

        assert success is True
        assert theory_enrollment.status == EnrollmentStatus.CANCELED
        assert practice_enrollment.status == EnrollmentStatus.CANCELED


def test_cancel_registered_course_allows_credits_equal_minimum_after_cancel(test_session, test_app):
    with test_app.app_context():
        seed_student_context(test_session)

        for course_id in range(1, 6):
            add_course_with_section(test_session, course_id=course_id, section_id=course_id)

        for enrollment_id, section_id in enumerate(range(1, 6), start=1):
            test_session.add(
                Enrollment(
                    id=enrollment_id,
                    student_code="2354050999",
                    class_section_id=section_id,
                    status=EnrollmentStatus.REGISTERED,
                )
            )
        test_session.commit()

        success, message = utils.cancel_registered_course("2354050999", 1)
        canceled_enrollment = db.session.get(Enrollment, 1)

        assert success is True
        assert utils.get_registered_credits("2354050999") == 12
        assert canceled_enrollment.status == EnrollmentStatus.CANCELED


def test_cancel_registered_course_blocks_credits_below_minimum_after_cancel(test_session, test_app):
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

        success, message = utils.cancel_registered_course("2354050999", 1)
        enrollment = db.session.get(Enrollment, 1)

        assert success is False
        assert utils.get_registered_credits("2354050999") == 12
        assert enrollment.status == EnrollmentStatus.REGISTERED

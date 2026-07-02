from datetime import datetime, time
from types import SimpleNamespace

from flask import render_template

from app import db, utils
from app.index import app
from app.model import ClassSectionType, Enrollment, EnrollmentStatus, Schedule
from app.test.test_base import test_app, test_session
from app.test.test_registration_utils import add_course_with_section, seed_student_context


def test_build_timetable_rows_keeps_multiple_classes_in_same_day_session():
    morning_first = SimpleNamespace(
        day_of_week=2, start_time=time(7, 30), end_time=time(9, 30)
    )
    morning_second = SimpleNamespace(
        day_of_week=2, start_time=time(9, 30), end_time=time(12, 0)
    )

    rows = utils.build_timetable_rows([morning_first, morning_second])

    assert len(rows) == 2
    assert rows[0]["by_day"][2] == [morning_first]
    assert rows[1]["by_day"][2] == [morning_second]


def test_timetable_template_renders_every_schedule_name():
    def make_schedule(name, start_time, end_time):
        section = SimpleNamespace(
            section_type=ClassSectionType.THEORY,
            course=SimpleNamespace(name=name),
            name="LHP",
            room=SimpleNamespace(name="A101"),
            teacher=SimpleNamespace(name="Giảng viên"),
        )
        return SimpleNamespace(
            class_section=section,
            day_of_week=2,
            start_time=start_time,
            end_time=end_time,
        )

    schedules = [
        make_schedule("Môn buổi sáng 1", time(7, 30), time(9, 30)),
        make_schedule("Môn buổi sáng 2", time(9, 30), time(12, 0)),
    ]
    week_days = [
        {"thu": day, "date": SimpleNamespace(strftime=lambda _format: "01/06")}
        for day in range(2, 9)
    ]

    with app.test_request_context("/timetable"):
        html = render_template(
            "timetable.html",
            student_code="SV001",
            student_name="Test",
            semester="Kỳ 1",
            schedule_rows=utils.build_timetable_rows(schedules),
            unscheduled_sections=[],
            week_days=week_days,
            week=1,
            can_previous_week=False,
            can_next_week=False,
            term_start=None,
            term_end=None,
        )

    assert "Môn buổi sáng 1" in html
    assert "Môn buổi sáng 2" in html


def test_timetable_includes_registered_shared_course_outside_program_mapping(
    test_app, test_session
):
    with test_app.app_context():
        seed_student_context(test_session)
        add_course_with_section(test_session, course_id=1, section_id=1)
        _, shared_section = add_course_with_section(
            test_session,
            course_id=2,
            section_id=2,
            add_to_training_program=False,
            is_shared=True,
            # Keep the fixture on Monday of the current week so week 1 always
            # contains its Monday schedule, regardless of the test run date.
            start_offset_days=-datetime.now().weekday(),
        )
        schedule = Schedule(
            class_section_id=shared_section.id,
            day_of_week=2,
            start_time=time(9, 30),
            end_time=time(12, 0),
        )
        test_session.add(schedule)
        test_session.add(Enrollment(
            student_code="2354050999",
            class_section_id=shared_section.id,
            status=EnrollmentStatus.REGISTERED,
        ))
        test_session.commit()

        context = utils.get_student_timetable("2354050999", requested_week=1)

        assert [item.id for item in context["schedules"]] == [schedule.id]
        assert context["schedule_rows"][0]["by_day"][2] == [schedule]


def test_timetable_reports_registered_section_without_schedule(test_app, test_session):
    with test_app.app_context():
        seed_student_context(test_session)
        _, section = add_course_with_section(
            test_session, course_id=1, section_id=1
        )
        test_session.add(Enrollment(
            student_code="2354050999",
            class_section_id=section.id,
            status=EnrollmentStatus.REGISTERED,
        ))
        test_session.commit()

        context = utils.get_student_timetable("2354050999", requested_week=1)

        assert context["schedules"] == []
        assert context["schedule_rows"] == []
        assert context["unscheduled_sections"] == [section]


def test_timetable_week_always_starts_on_monday(test_app, test_session):
    with test_app.app_context():
        seed_student_context(test_session)
        _, section = add_course_with_section(
            test_session, course_id=1, section_id=1, start_offset_days=0
        )
        test_session.add(Enrollment(
            student_code="2354050999",
            class_section_id=section.id,
            status=EnrollmentStatus.REGISTERED,
        ))
        test_session.commit()

        context = utils.get_student_timetable("2354050999", requested_week=1)

        assert context["week_days"][0]["date"].weekday() == 0
        assert context["week_days"][-1]["date"].weekday() == 6

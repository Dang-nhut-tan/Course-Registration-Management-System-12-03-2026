from app.utils import check_room_conflict, check_teacher_conflict
import pytest
from app.model import ClassSection, Schedule, Room, Teacher
from app.test.test_base import test_app, test_session
from datetime import datetime, time, timedelta

@pytest.fixture
def sample_schedule(test_session):
    room = Room(id=1, name="A101", campus_id=1)
    teacher = Teacher(id=1, name="Teacher A")
    cs = ClassSection(
        id=10,
        semester="2024-1",
        room_id=room.id,
        teacher_id=teacher.id,
        section_type='theory',
        max_students=50,
        start_date=datetime.now() - timedelta(days=10),
        end_date=datetime.now() + timedelta(days=10),
    )
    sch = Schedule(
        day_of_week= 2,
        start_time=time(7, 0),
        end_time=time(9, 30),
        class_section_id=cs.id
    )
    test_session.add_all([room, teacher, cs, sch])
    test_session.commit()
    return sch

def test_room_no_conflict(test_app, test_session, sample_schedule):
    with test_app.app_context():
        is_conflict = check_room_conflict(
            day= 2,
            start_time=time(13, 0),
            end_time=time(16, 30),
            room_id=1
        )
        assert is_conflict is False

def test_room_conflict(test_app, test_session, sample_schedule):
    with test_app.app_context():
        is_conflict = check_room_conflict(
            day= 2,
            start_time=time(7, 0),
            end_time=time(9, 30),
            room_id=1
        )
        assert is_conflict is True

def test_ended_section_releases_room_and_teacher(test_app, test_session):
    with test_app.app_context():
        room = Room(id=2, name="A102", campus_id=1)
        teacher = Teacher(id=2, name="Teacher B")
        ended_section = ClassSection(
            id=20,
            semester="2024-1",
            room_id=room.id,
            teacher_id=teacher.id,
            section_type='theory',
            max_students=50,
            start_date=datetime.now() - timedelta(days=40),
            end_date=datetime.now() - timedelta(days=1),
        )
        schedule = Schedule(
            day_of_week=2,
            start_time=time(7, 0),
            end_time=time(9, 30),
            class_section_id=ended_section.id,
        )
        test_session.add_all([room, teacher, ended_section, schedule])
        test_session.commit()

        room_conflict = check_room_conflict(2, time(7, 0), time(9, 30), room.id)
        teacher_conflict = check_teacher_conflict(2, time(7, 0), time(9, 30), teacher.id)

        assert room_conflict is False
        assert teacher_conflict is False

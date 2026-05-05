from app.utils import check_room_conflict
import pytest
from app.model import ClassSection, Schedule, Room
from app.test.test_base import test_app, test_session
from datetime import time

@pytest.fixture
def sample_schedule(test_session):
    room = Room(id=1, name="A101", campus_id=1)
    cs = ClassSection(id=10, semester="2024-1", room_id=room.id, section_type= 'theory')
    sch = Schedule(
        day_of_week= 2,
        start_time=time(7, 0),
        end_time=time(9, 30),
        class_section_id=cs.id
    )
    test_session.add_all([room, cs, sch])
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

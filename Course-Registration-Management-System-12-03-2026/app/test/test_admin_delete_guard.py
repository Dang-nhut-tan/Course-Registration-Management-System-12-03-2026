from datetime import datetime

from app import db
from app.admin import CampusView, RoomView
from app.model import Campus, ClassSection, Room
from app.test.test_base import test_app, test_session


def test_delete_room_used_by_class_section_returns_false(test_app, test_session):
    campus = Campus(id=1, name="Co so 1")
    room = Room(id=1, name="A101", room_type="theory", capacity=50, campus_id=1)
    section = ClassSection(
        id=1,
        room_id=1,
        semester="2025-1",
        max_students=50,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 5, 1),
    )
    test_session.add_all([campus, room, section])
    test_session.commit()

    view = RoomView(Room, db.session)
    with test_app.test_request_context():
        result = view.delete_model(room)

    assert result is False
    assert db.session.get(Room, 1) is not None


def test_delete_campus_with_rooms_returns_false(test_app, test_session):
    campus = Campus(id=1, name="Co so 1")
    room = Room(id=1, name="A101", room_type="theory", capacity=50, campus_id=1)
    test_session.add_all([campus, room])
    test_session.commit()

    view = CampusView(Campus, db.session)
    with test_app.test_request_context():
        result = view.delete_model(campus)

    assert result is False
    assert db.session.get(Campus, 1) is not None

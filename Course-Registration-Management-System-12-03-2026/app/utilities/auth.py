import hashlib
from datetime import datetime

from app.extensions import db, login_manager
from app.model import ClassSection, Schedule, User, UserRole


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


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


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

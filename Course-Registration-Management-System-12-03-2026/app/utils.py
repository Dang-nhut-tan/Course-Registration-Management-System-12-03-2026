from app.model import Student, User, Schedule
import hashlib
from app import app, db
from flask_login import LoginManager
from app.model import User, Student, ClassSection

def check_login_student(student_code, password):
    if student_code and password:
        password=str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
        return User.query.filter(User.password.__eq__(password),User.student_code.__eq__(student_code.strip())).first()

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def check_room_conflict(day, start_time, end_time, room_id):
    query = db.session.query(Schedule).join(ClassSection).filter(
        Schedule.day_of_week==day,
        Schedule.start_time < end_time,
        Schedule.end_time > start_time,
        ClassSection.room_id == room_id
    )
    if query.first():
        return True
    return False
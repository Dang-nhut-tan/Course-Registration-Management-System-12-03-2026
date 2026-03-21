from app.model import Student, User
import hashlib


def check_login_student(student_code, password):
    if student_code and password:
        password=str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
        return User.query.filter(User.password.__eq__(password),User.student_code.__eq__(student_code.strip())).first()


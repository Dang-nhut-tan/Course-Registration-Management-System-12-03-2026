from app.model import ClassSection, Course, Enrollment, Student, User,Faculty
import hashlib
from app import db


def check_login_student(student_code, password):
    if student_code and password:
        password=str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
        return User.query.filter(User.password.__eq__(password),User.student_code.__eq__(student_code.strip())).first()

def get_sections(course_id=None, faculty_id=None):
    query = ClassSection.query
    if course_id:
        query = query.filter(ClassSection.course_id == course_id)
    if faculty_id:
        query = query.join(Course).filter(Course.faculty_id == faculty_id)
    return query.all()

def get_registered_courses(student_code):
    enrollments = Enrollment.query.filter(
        Enrollment.student_code == student_code
    ).all()
    return enrollments

def get_filter_data():
    courses = db.session.query(Course).all()
    faculties = db.session.query(Faculty).all()

    return {
        "courses": courses,
        "faculties": faculties
    }
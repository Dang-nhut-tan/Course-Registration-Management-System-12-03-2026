from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Enum, Time
from sqlalchemy.orm import relationship
from app import db, app
from enum import Enum as PyEnum


# ================= BASE =================
class BaseModel(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)

    def __str__(self):
        return getattr(self, 'name', str(self.id))


# ================= ENUM =================
class UserRole(PyEnum):
    ADMIN = "admin"
    STUDENT = "student"

class EnrollmentStatus(PyEnum):
    REGISTERED = "registered"
    CANCELED = "canceled"


# ================= USER =================
class User(BaseModel):
    __tablename__ = 'users'

    username = Column(String(100), unique=True, nullable=True)  # admin dùng
    password = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)

    role = Column(Enum(UserRole), default=UserRole.STUDENT)

    student_id = Column(Integer, ForeignKey('students.id'), nullable=True)
    student = relationship('Student', backref='user', uselist=False)


# ================= CAMPUS =================
class Campus(BaseModel):
    __tablename__ = 'campuses'

    name = Column(String(255), nullable=False)
    address = Column(String(500))

    rooms = relationship('Room', backref='campus', lazy=True)


# ================= ROOM =================
class Room(BaseModel):
    __tablename__ = 'rooms'

    name = Column(String(100))
    room_type = Column(String(50))
    capacity = Column(Integer)

    campus_id = Column(Integer, ForeignKey('campuses.id'), nullable=False)


# ================= FACULTY =================
class Faculty(BaseModel):
    __tablename__ = 'faculties'

    name = Column(String(255))
    majors = relationship('Major', backref='faculty', lazy=True)


# ================= MAJOR =================
class Major(BaseModel):
    __tablename__ = 'majors'

    name = Column(String(255))
    faculty_id = Column(Integer, ForeignKey('faculties.id'), nullable=False)


# ================= COURSE =================
class Course(BaseModel):
    __tablename__ = 'courses'

    name = Column(String(255))
    credits = Column(Integer)
    is_shared = Column(Boolean, default=False)

    faculty_id = Column(Integer, ForeignKey('faculties.id'))


# ================= COURSE-MAJOR =================
class CourseMajor(db.Model):
    __tablename__ = 'course_major'

    course_id = Column(Integer, ForeignKey('courses.id'), primary_key=True)
    major_id = Column(Integer, ForeignKey('majors.id'), primary_key=True)


# ================= PREREQUISITE =================
class CoursePrerequisite(db.Model):
    __tablename__ = 'course_prerequisite'

    course_id = Column(Integer, ForeignKey('courses.id'), primary_key=True)
    prerequisite_id = Column(Integer, ForeignKey('courses.id'), primary_key=True)


# ================= TEACHER =================
class Teacher(BaseModel):
    __tablename__ = 'teachers'

    name = Column(String(255))
    faculty_id = Column(Integer, ForeignKey('faculties.id'))


# ================= TEACHER-COURSE =================
class TeacherCourse(db.Model):
    __tablename__ = 'teacher_course'

    teacher_id = Column(Integer, ForeignKey('teachers.id'), primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), primary_key=True)


# ================= STUDENT =================
class Student(BaseModel):
    __tablename__ = 'students'

    student_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255))
    birth_year = Column(Integer)
    hometown = Column(String(255))
    religion = Column(String(100))
    identity_number = Column(String(50), unique=True)

    major_id = Column(Integer, ForeignKey('majors.id'), nullable=False)


# ================= CLASS SECTION =================
class ClassSection(BaseModel):
    __tablename__ = 'class_sections'

    course_id = Column(Integer, ForeignKey('courses.id'))
    teacher_id = Column(Integer, ForeignKey('teachers.id'))
    room_id = Column(Integer, ForeignKey('rooms.id'))

    semester = Column(String(50))
    max_students = Column(Integer)

    start_date = Column(DateTime)
    end_date = Column(DateTime)
    registration_deadline = Column(DateTime)

    schedules = relationship('Schedule', backref='class_section', lazy=True)
    enrollments = relationship('Enrollment', backref='class_section', lazy=True)


# ================= SCHEDULE =================
class Schedule(BaseModel):
    __tablename__ = 'schedules'

    class_section_id = Column(Integer, ForeignKey('class_sections.id'))

    day_of_week = Column(Integer)
    start_time = Column(Time)
    end_time = Column(Time)


# ================= ENROLLMENT =================
class Enrollment(BaseModel):
    __tablename__ = 'enrollments'

    student_id = Column(Integer, ForeignKey('students.id'))
    class_section_id = Column(Integer, ForeignKey('class_sections.id'))
    status = Column(Enum(EnrollmentStatus))

    student = relationship('Student', backref='enrollments')


# ================= CREATE DB =================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
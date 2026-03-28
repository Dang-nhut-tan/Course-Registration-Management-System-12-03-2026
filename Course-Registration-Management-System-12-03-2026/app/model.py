from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Enum, Time
from sqlalchemy.orm import relationship
from app import db, app
from enum import Enum as PyEnum
import hashlib
from datetime import datetime
from flask_login import UserMixin

class BaseModel(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)

    def __str__(self):
        return getattr(self, 'name', str(self.id))


class UserRole(PyEnum):
    ADMIN = "admin"
    STUDENT = "student"

class EnrollmentStatus(PyEnum):
    REGISTERED = "registered"
    CANCELED = "canceled"


class User(BaseModel,UserMixin):
    __tablename__ = 'users'

    username = Column(String(100), unique=True, nullable=True)  # admin dùng
    password = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)

    role = Column(Enum(UserRole), default=UserRole.STUDENT)

    student_code = Column(String(50), ForeignKey('students.student_code'))
    student = relationship('Student', backref='user', uselist=False)


class Campus(BaseModel):
    __tablename__ = 'campuses'

    name = Column(String(255), nullable=False)
    address = Column(String(500))

    rooms = relationship('Room', backref='campus', lazy=True)



class Room(BaseModel):
    __tablename__ = 'rooms'

    name = Column(String(100))
    room_type = Column(String(50))
    capacity = Column(Integer)

    campus_id = Column(Integer, ForeignKey('campuses.id'), nullable=False)

class Faculty(BaseModel):
    __tablename__ = 'faculties'

    name = Column(String(255))
    majors = relationship('Major', backref='faculty', lazy=True)


class Major(BaseModel):
    __tablename__ = 'majors'

    name = Column(String(255))
    faculty_id = Column(Integer, ForeignKey('faculties.id'), nullable=False)


class Course(BaseModel):
    __tablename__ = 'courses'

    name = Column(String(255))
    credits = Column(Integer)
    is_shared = Column(Boolean, default=False)

    faculty_id = Column(Integer, ForeignKey('faculties.id'))


class CourseMajor(db.Model):
    __tablename__ = 'course_major'

    course_id = Column(Integer, ForeignKey('courses.id'), primary_key=True)
    major_id = Column(Integer, ForeignKey('majors.id'), primary_key=True)

class CoursePrerequisite(db.Model):
    __tablename__ = 'course_prerequisite'

    course_id = Column(Integer, ForeignKey('courses.id'), primary_key=True)
    prerequisite_id = Column(Integer, ForeignKey('courses.id'), primary_key=True)


class Teacher(BaseModel):
    __tablename__ = 'teachers'

    name = Column(String(255))
    faculty_id = Column(Integer, ForeignKey('faculties.id'))


class TeacherCourse(db.Model):
    __tablename__ = 'teacher_course'

    teacher_id = Column(Integer, ForeignKey('teachers.id'), primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), primary_key=True)


class Student(db.Model):
    __tablename__ = 'students'

    student_code = Column(String(50),primary_key=True, unique=True, nullable=False)
    name = Column(String(255))
    birth_year = Column(Integer)
    hometown = Column(String(255))
    religion = Column(String(100))
    identity_number = Column(String(50), unique=True)

    major_id = Column(Integer, ForeignKey('majors.id'), nullable=False)

class ClassSection(BaseModel):
    __tablename__ = 'class_sections'

    course_id = Column(Integer, ForeignKey('courses.id'))
    teacher_id = Column(Integer, ForeignKey('teachers.id'))
    room_id = Column(Integer, ForeignKey('rooms.id'))

    course = relationship('Course')
    teacher = relationship('Teacher')
    room = relationship('Room')


    semester = Column(String(50))
    max_students = Column(Integer)

    start_date = Column(DateTime)
    end_date = Column(DateTime)
    registration_deadline = Column(DateTime)

    schedules = relationship('Schedule', backref='class_section', lazy=True)
    enrollments = relationship('Enrollment', backref='class_section', lazy=True)


class Schedule(BaseModel):
    __tablename__ = 'schedules'

    class_section_id = Column(Integer, ForeignKey('class_sections.id'))

    day_of_week = Column(Integer)
    start_time = Column(Time)
    end_time = Column(Time)


class Enrollment(BaseModel):
    __tablename__ = 'enrollments'

    student_code = Column(String(50), ForeignKey('students.student_code'))
    class_section_id = Column(Integer, ForeignKey('class_sections.id'))
    status = Column(Enum(EnrollmentStatus))

    student = relationship('Student', backref='enrollments')

sample_data = {
  "faculties": [
    { "id": 1, "name": "CNTT" }
  ],

  "majors": [
    { "id": 1, "name": "HTTQL", "faculty_id": 1 }
  ],

  "students": [
    {
      "student_code": "2354050113",
      "name": "Nguyen Van A",
      "birth_year": 2003,
      "major_id": 1
    }
  ],

  "users": [
    {
      "id": 1,
      "username": "admin",
      "password": "admin123",
      "role": "admin"
    },
    {
      "id": 2,
      "student_code": "2354050113",
      "password": "123456",
      "role": "student"
    }
  ],

  "courses": [
    {
      "id": 1,
      "name": "Kiểm thử phần mềm",
      "credits": 3,
      "faculty_id": 1
    },
    {
      "id": 2,
      "name": "Cấu trúc dữ liệu và giải thuật",
      "credits": 4,
      "faculty_id": 1
    }
  ],

  "course_prerequisites": [
    {
      "course_id": 2,
      "prerequisite_id": 1
    }
  ],

  "teachers": [
    {
      "id": 1,
      "name": "Thay B",
      "faculty_id": 1
    }
  ],

  "rooms": [
    {
      "id": 1,
      "name": "A101",
      "capacity": 50,
      "campus_id": 1
    }
  ],

  "campuses": [
    {
      "id": 1,
      "name": "Co so 1",
      "address": "TPHCM"
    }
  ],

  "class_sections": [
    {
      "id": 1,
      "course_id": 1,
      "teacher_id": 1,
      "room_id": 1,
      "semester": "2025-1",
      "max_students": 50,
      "start_date": "2025-09-01",
      "end_date": "2025-12-01",
      "registration_deadline": "2025-08-25"
    }
  ],

  "schedules": [
    {
      "id": 1,
      "class_section_id": 1,
      "day_of_week": 2,
      "start_time": "07:00",
      "end_time": "09:00"
    }
  ],

  "enrollments": [
    {
      "id": 1,
      "student_code": "2354050113",
      "class_section_id": 1,
      "status": "registered"
    }
  ]
}




def seed_data():
    db.drop_all()
    db.create_all()

    for f in sample_data["faculties"]:
        db.session.add(Faculty(
            id=f["id"],
            name=f["name"]
        ))
    db.session.commit()


    for m in sample_data["majors"]:
        db.session.add(Major(
            id=m["id"],
            name=m["name"],
            faculty_id=m["faculty_id"]
        ))
    db.session.commit()

    for s in sample_data["students"]:
        db.session.add(Student(
            student_code=s["student_code"],
            name=s["name"],
            birth_year=s["birth_year"],
            major_id=s["major_id"]
        ))
    db.session.commit()

    for u in sample_data["users"]:
        role = UserRole(u["role"])

        user = User(
            id=u["id"],
            username=u.get("username"),
            password=hashlib.md5(u['password'].strip().encode('utf-8')).hexdigest(),
            role=role
        )

        if role == UserRole.STUDENT:
            user.student_code = u["student_code"]

        db.session.add(user)
    db.session.commit()

    for c in sample_data["campuses"]:
        db.session.add(Campus(
            id=c["id"],
            name=c["name"],
            address=c["address"]
        ))
    db.session.commit()

    for r in sample_data["rooms"]:
        db.session.add(Room(
            id=r["id"],
            name=r["name"],
            capacity=r["capacity"],
            campus_id=r["campus_id"]
        ))
    db.session.commit()


    for c in sample_data["courses"]:
        db.session.add(Course(
            id=c["id"],
            name=c["name"],
            credits=c["credits"],
            faculty_id=c["faculty_id"]
        ))
    db.session.commit()


    for cp in sample_data.get("course_prerequisites", []):
        db.session.add(CoursePrerequisite(
            course_id=cp["course_id"],
            prerequisite_id=cp["prerequisite_id"]
        ))
    db.session.commit()

    for t in sample_data["teachers"]:
        db.session.add(Teacher(
            id=t["id"],
            name=t["name"],
            faculty_id=t["faculty_id"]
        ))
    db.session.commit()

    for cs in sample_data["class_sections"]:
        db.session.add(ClassSection(
            id=cs["id"],
            course_id=cs["course_id"],
            teacher_id=cs["teacher_id"],
            room_id=cs["room_id"],
            semester=cs["semester"],
            max_students=cs["max_students"],
            start_date=datetime.fromisoformat(cs["start_date"]),
            end_date=datetime.fromisoformat(cs["end_date"]),
            registration_deadline=datetime.fromisoformat(cs["registration_deadline"])
        ))
    db.session.commit()

    for s in sample_data["schedules"]:
        db.session.add(Schedule(
            id=s["id"],
            class_section_id=s["class_section_id"],
            day_of_week=s["day_of_week"],
            start_time=datetime.strptime(s["start_time"], "%H:%M").time(),
            end_time=datetime.strptime(s["end_time"], "%H:%M").time()
        ))
    db.session.commit()

    for e in sample_data["enrollments"]:
        db.session.add(Enrollment(
            id=e["id"],
            student_code=e["student_code"],
            class_section_id=e["class_section_id"],
            status=EnrollmentStatus(e["status"])
        ))
    db.session.commit()

    print(" Seed full data thành công!")
if __name__ == '__main__':
    with app.app_context():
        seed_data()
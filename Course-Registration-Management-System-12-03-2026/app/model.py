from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Enum, Time
from sqlalchemy.orm import relationship
<<<<<<< HEAD
from app import db, app
from enum import Enum as PyEnum
import hashlib
from datetime import datetime
from flask_login import UserMixin

=======
from app import app, db
from enum import Enum as PyEnum
import hashlib
from datetime import datetime
>>>>>>> feature/admin

class BaseModel(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)

    def __str__(self):
        return getattr(self, 'name', str(self.id))


class UserRole(PyEnum):
    ADMIN = "admin"
    STUDENT = "student"

<<<<<<< HEAD

=======
>>>>>>> feature/admin
class EnrollmentStatus(PyEnum):
    REGISTERED = "registered"
    CANCELED = "canceled"


<<<<<<< HEAD
class User(BaseModel, UserMixin):
=======
class User(BaseModel):
>>>>>>> feature/admin
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


<<<<<<< HEAD
=======

>>>>>>> feature/admin
class Room(BaseModel):
    __tablename__ = 'rooms'

    name = Column(String(100))
    room_type = Column(String(50))
    capacity = Column(Integer)

    campus_id = Column(Integer, ForeignKey('campuses.id'), nullable=False)

<<<<<<< HEAD

=======
>>>>>>> feature/admin
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

<<<<<<< HEAD

=======
>>>>>>> feature/admin
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

<<<<<<< HEAD
    student_code = Column(String(50), primary_key=True, unique=True, nullable=False)
=======
    student_code = Column(String(50),primary_key=True, unique=True, nullable=False)
>>>>>>> feature/admin
    name = Column(String(255))
    birth_year = Column(Integer)
    hometown = Column(String(255))
    religion = Column(String(100))
    identity_number = Column(String(50), unique=True)

    major_id = Column(Integer, ForeignKey('majors.id'), nullable=False)

<<<<<<< HEAD

=======
>>>>>>> feature/admin
class ClassSection(BaseModel):
    __tablename__ = 'class_sections'

    course_id = Column(Integer, ForeignKey('courses.id'))
    teacher_id = Column(Integer, ForeignKey('teachers.id'))
    room_id = Column(Integer, ForeignKey('rooms.id'))

<<<<<<< HEAD
    course = relationship('Course')
    teacher = relationship('Teacher')
    room = relationship('Room')

=======
>>>>>>> feature/admin
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

<<<<<<< HEAD

sample_data = {
  "faculties": [
    {"id": 1, "name": "CNTT"},
    {"id": 2, "name": "Kinh tế"},
    {"id": 3, "name": "Quản trị kinh doanh"}
  ],

  "majors": [
    {"id": 1, "name": "HTTQL", "faculty_id": 1},
    {"id": 2, "name": "Khoa học máy tính", "faculty_id": 1},
    {"id": 3, "name": "Tài chính - Ngân hàng", "faculty_id": 2},
    {"id": 4, "name": "Marketing", "faculty_id": 3}
=======
sample_data = {
  "faculties": [
    { "id": 1, "name": "CNTT" }
  ],

  "majors": [
    { "id": 1, "name": "HTTQL", "faculty_id": 1 }
>>>>>>> feature/admin
  ],

  "students": [
    {
      "student_code": "2354050113",
      "name": "Nguyen Van A",
      "birth_year": 2003,
      "major_id": 1
    },
    {
<<<<<<< HEAD
      "student_code": "2354050114",
      "name": "Tran Thi B",
      "birth_year": 2003,
      "major_id": 3
    },
    {
      "student_code": "2354050115",
      "name": "Le Van C",
      "birth_year": 2002,
      "major_id": 4
=======
      "student_code": "2354050118",
      "name": "Le Thi B",
      "birth_year": 2003,
      "major_id": 1
>>>>>>> feature/admin
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
    },
    {
      "id": 3,
<<<<<<< HEAD
      "student_code": "2354050114",
      "password": "123456",
      "role": "student"
    },
    {
      "id": 4,
      "student_code": "2354050115",
      "password": "123456",
=======
      "student_code": "2354050118",
      "password": "12345",
>>>>>>> feature/admin
      "role": "student"
    }
  ],

  "courses": [
<<<<<<< HEAD
    {"id": 1, "name": "Kiểm thử phần mềm", "credits": 3, "faculty_id": 1, "is_shared": False},
    {"id": 2, "name": "Cấu trúc dữ liệu và giải thuật", "credits": 4, "faculty_id": 1, "is_shared": False},
    {"id": 3, "name": "Cơ sở dữ liệu", "credits": 3, "faculty_id": 1, "is_shared": False},
    {"id": 4, "name": "Phân tích thiết kế hệ thống", "credits": 3, "faculty_id": 1, "is_shared": False},
    {"id": 5, "name": "Lập trình Web", "credits": 4, "faculty_id": 1, "is_shared": False},
    {"id": 6, "name": "Mạng máy tính", "credits": 3, "faculty_id": 1, "is_shared": False},
    {"id": 7, "name": "Nguyên lý kế toán", "credits": 3, "faculty_id": 2, "is_shared": False},
    {"id": 8, "name": "Tài chính doanh nghiệp", "credits": 3, "faculty_id": 2, "is_shared": False},
    {"id": 9, "name": "Marketing căn bản", "credits": 3, "faculty_id": 3, "is_shared": False},
    {"id": 10, "name": "Tin học đại cương", "credits": 2, "faculty_id": 1, "is_shared": True}
  ],

  "course_prerequisites": [
    {"course_id": 2, "prerequisite_id": 1},
    {"course_id": 4, "prerequisite_id": 3},
    {"course_id": 8, "prerequisite_id": 7}
  ],

  "teachers": [
    {"id": 1, "name": "Thầy B", "faculty_id": 1},
    {"id": 2, "name": "Cô C", "faculty_id": 1},
    {"id": 3, "name": "Thầy D", "faculty_id": 1},
    {"id": 4, "name": "Thầy K", "faculty_id": 2},
    {"id": 5, "name": "Cô M", "faculty_id": 3}
  ],

  "rooms": [
    {"id": 1, "name": "A101", "capacity": 50, "campus_id": 1},
    {"id": 2, "name": "A102", "capacity": 45, "campus_id": 1},
    {"id": 3, "name": "B201", "capacity": 50, "campus_id": 1}
  ],

  "campuses": [
    {"id": 1, "name": "Cơ sở 1", "address": "TPHCM"}
=======
    {
      "id": 1,
      "name": "Lap trinh Python",
      "credits": 3,
      "faculty_id": 1
    },
    {
      "id": 2,
      "name": "Cau truc du lieu",
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
    },
    {
      "id": 2,
      "name": "B101",
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
>>>>>>> feature/admin
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
    },
    {
      "id": 2,
      "course_id": 2,
<<<<<<< HEAD
      "teacher_id": 2,
      "room_id": 2,
      "semester": "2025-1",
      "max_students": 45,
      "start_date": "2025-09-03",
      "end_date": "2025-12-05",
      "registration_deadline": "2025-08-25"
    },
    {
      "id": 3,
      "course_id": 3,
      "teacher_id": 1,
      "room_id": 3,
      "semester": "2025-1",
      "max_students": 60,
      "start_date": "2025-09-04",
      "end_date": "2025-12-10",
      "registration_deadline": "2025-08-25"
    },
    {
      "id": 4,
      "course_id": 4,
      "teacher_id": 3,
      "room_id": 1,
      "semester": "2025-1",
      "max_students": 40,
      "start_date": "2025-09-05",
      "end_date": "2025-12-12",
      "registration_deadline": "2025-08-25"
    },
    {
      "id": 5,
      "course_id": 5,
      "teacher_id": 2,
      "room_id": 2,
      "semester": "2025-1",
      "max_students": 35,
      "start_date": "2025-09-06",
      "end_date": "2025-12-15",
      "registration_deadline": "2025-08-25"
    },
    {
      "id": 6,
      "course_id": 6,
      "teacher_id": 3,
      "room_id": 3,
      "semester": "2025-1",
      "max_students": 55,
      "start_date": "2025-09-07",
      "end_date": "2025-12-18",
      "registration_deadline": "2025-08-25"
    },
    {
      "id": 7,
      "course_id": 7,
      "teacher_id": 4,
      "room_id": 1,
      "semester": "2025-1",
      "max_students": 50,
      "start_date": "2025-09-08",
      "end_date": "2025-12-19",
      "registration_deadline": "2025-08-25"
    },
    {
      "id": 8,
      "course_id": 8,
      "teacher_id": 4,
      "room_id": 2,
      "semester": "2025-1",
      "max_students": 45,
      "start_date": "2025-09-09",
      "end_date": "2025-12-20",
      "registration_deadline": "2025-08-25"
    },
    {
      "id": 9,
      "course_id": 9,
      "teacher_id": 5,
      "room_id": 3,
      "semester": "2025-1",
      "max_students": 40,
      "start_date": "2025-09-10",
      "end_date": "2025-12-21",
=======
      "teacher_id": 1,
      "room_id": 2,
      "semester": "2025-1",
      "max_students": 50,
      "start_date": "2025-09-01",
      "end_date": "2025-12-01",
>>>>>>> feature/admin
      "registration_deadline": "2025-08-25"
    }
  ],

  "schedules": [
<<<<<<< HEAD
    # CNTT
    {"id": 1, "class_section_id": 1, "day_of_week": 2, "start_time": "07:00", "end_time": "11:30"},
    {"id": 2, "class_section_id": 2, "day_of_week": 3, "start_time": "07:00", "end_time": "11:30"},
    {"id": 3, "class_section_id": 3, "day_of_week": 4, "start_time": "13:00", "end_time": "17:30"},
    {"id": 4, "class_section_id": 4, "day_of_week": 5, "start_time": "07:00", "end_time": "11:30"},
    {"id": 5, "class_section_id": 5, "day_of_week": 6, "start_time": "13:00", "end_time": "17:30"},
    {"id": 6, "class_section_id": 6, "day_of_week": 7, "start_time": "07:00", "end_time": "11:30"},

    # Kinh tế
    {"id": 7, "class_section_id": 7, "day_of_week": 2, "start_time": "13:00", "end_time": "17:30"},
    {"id": 8, "class_section_id": 8, "day_of_week": 4, "start_time": "07:00", "end_time": "11:30"},

    # QTKD
    {"id": 9, "class_section_id": 9, "day_of_week": 6, "start_time": "13:00", "end_time": "17:30"}
  ],

  "enrollments": [
    {"id": 1, "student_code": "2354050113", "class_section_id": 1, "status": "registered"},
    {"id": 2, "student_code": "2354050113", "class_section_id": 3, "status": "registered"},
    {"id": 3, "student_code": "2354050113", "class_section_id": 5, "status": "canceled"},
    {"id": 4, "student_code": "2354050114", "class_section_id": 7, "status": "registered"},
    {"id": 5, "student_code": "2354050115", "class_section_id": 9, "status": "registered"}
=======
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
    },
    {
      "id": 2,
      "student_code": "2354050118",
      "class_section_id": 2,
      "status": "registered"
    }
>>>>>>> feature/admin
  ]
}


<<<<<<< HEAD
=======


>>>>>>> feature/admin
def seed_data():
    db.drop_all()
    db.create_all()

    for f in sample_data["faculties"]:
        db.session.add(Faculty(
            id=f["id"],
            name=f["name"]
        ))
    db.session.commit()

<<<<<<< HEAD
=======

>>>>>>> feature/admin
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

<<<<<<< HEAD
=======

>>>>>>> feature/admin
    for c in sample_data["courses"]:
        db.session.add(Course(
            id=c["id"],
            name=c["name"],
            credits=c["credits"],
<<<<<<< HEAD
            faculty_id=c["faculty_id"],
            is_shared=c.get("is_shared", False)
        ))
    db.session.commit()

=======
            faculty_id=c["faculty_id"]
        ))
    db.session.commit()


>>>>>>> feature/admin
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

<<<<<<< HEAD
    print("Seed full data thành công!")


if __name__ == '__main__':
    with app.app_context():
        seed_data()
=======
    print(" Seed full data thành công!")
if __name__ == '__main__':
    with app.app_context():
        seed_data()
>>>>>>> feature/admin

from flask_sqlalchemy import SQLAlchemy
from app import db,app

class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    def __str__(self):
        return self.name

class Campus(BaseModel):
    __tablename__ = 'campuses'

    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(500))

    rooms = db.relationship('Room', backref='campus', lazy=True)


class Room(BaseModel):
    __tablename__ = 'rooms'

    name = db.Column(db.String(100))
    room_type = db.Column(db.String(50))
    capacity = db.Column(db.Integer)

    campus_id = db.Column(db.Integer, db.ForeignKey('campuses.id'), nullable=False)


class Faculty(BaseModel):
    __tablename__ = 'faculties'
    name = db.Column(db.String(255))
    majors = db.relationship('Major', backref='faculty', lazy=True)


class Major(BaseModel):
    __tablename__ = 'majors'
    name = db.Column(db.String(255))
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculties.id'), nullable=False)


class Course(BaseModel):
    __tablename__ = 'courses'

    name = db.Column(db.String(255))
    credits = db.Column(db.Integer)
    is_shared = db.Column(db.Boolean, default=False)

    faculty_id = db.Column(db.Integer, db.ForeignKey('faculties.id'))

class CourseMajor(db.Model):
    __tablename__ = 'course_major'

    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), primary_key=True)
    major_id = db.Column(db.Integer, db.ForeignKey('majors.id'), primary_key=True)


class CoursePrerequisite(db.Model):
    __tablename__ = 'course_prerequisite'

    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), primary_key=True)
    prerequisite_id = db.Column(db.Integer, db.ForeignKey('courses.id'), primary_key=True)


class Teacher(BaseModel):
    __tablename__ = 'teachers'

    name = db.Column(db.String(255))

    faculty_id = db.Column(db.Integer, db.ForeignKey('faculties.id'))


class TeacherCourse(db.Model):
    __tablename__ = 'teacher_course'

    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), primary_key=True)


class Student(BaseModel):
    __tablename__ = 'students'
    student_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255))
    birth_year = db.Column(db.Integer)
    hometown = db.Column(db.String(255))
    religion = db.Column(db.String(100))
    identity_number = db.Column(db.String(50), unique=True)
    major_id = db.Column(db.Integer, db.ForeignKey('majors.id'), nullable=False)



class ClassSection(BaseModel):
    __tablename__ = 'class_sections'

    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))

    semester = db.Column(db.String(50))
    max_students = db.Column(db.Integer)

    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    registration_deadline = db.Column(db.Date)


class Schedule(BaseModel):
    __tablename__ = 'schedules'

    class_section_id = db.Column(db.Integer, db.ForeignKey('class_sections.id'))

    day_of_week = db.Column(db.Integer)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)


class Enrollment(BaseModel):
    __tablename__ = 'enrollments'
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    class_section_id = db.Column(db.Integer, db.ForeignKey('class_sections.id'))
    status = db.Column(db.String(50))

if __name__=='__main__':
    with app.app_context():
        db.create_all()
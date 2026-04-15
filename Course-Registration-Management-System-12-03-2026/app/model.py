import os
import sys
from enum import Enum as PyEnum

from flask_login import UserMixin
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import relationship
from app import app

from app import db


class BaseModel(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)

    def __str__(self):
        return getattr(self, "name", str(self.id))


class UserRole(PyEnum):
    ADMIN = "admin"
    STUDENT = "student"


class EnrollmentStatus(PyEnum):
    REGISTERED = "registered"
    CANCELED = "canceled"


class ClassSectionType(PyEnum):
    THEORY = "theory"
    PRACTICE = "practice"


class User(BaseModel, UserMixin):
    __tablename__ = "users"

    username = Column(String(100), unique=True, nullable=True)
    password = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.STUDENT)

    student_code = Column(String(50), ForeignKey("students.student_code"))
    student = relationship("Student", backref="user", uselist=False)


class Campus(BaseModel):
    __tablename__ = "campuses"

    name = Column(String(255), nullable=False)
    address = Column(String(500))

    rooms = relationship("Room", backref="campus", lazy=True)


class Room(BaseModel):
    __tablename__ = "rooms"

    name = Column(String(100))
    room_type = Column(String(50))
    capacity = Column(Integer)
    campus_id = Column(Integer, ForeignKey("campuses.id"), nullable=False)


class Faculty(BaseModel):
    __tablename__ = "faculties"

    name = Column(String(255))
    majors = relationship("Major", backref="faculty", lazy=True)


class Major(BaseModel):
    __tablename__ = "majors"

    name = Column(String(255))
    faculty_id = Column(Integer, ForeignKey("faculties.id"), nullable=False)


class StudentClass(BaseModel):
    __tablename__ = "student_classes"

    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255))
    school_year = Column(String(20))
    major_id = Column(Integer, ForeignKey("majors.id"), nullable=False)

    major = relationship("Major", backref="student_classes")


class TrainingProgram(BaseModel):
    __tablename__ = "training_programs"
    __table_args__ = (
        UniqueConstraint("major_id", "school_year", name="uq_training_program_major_year"),
    )

    name = Column(String(255), nullable=False)
    major_id = Column(Integer, ForeignKey("majors.id"), nullable=False)
    school_year = Column(String(20), nullable=False)
    max_credits_per_semester = Column(Integer, nullable=False, default=25)

    major = relationship("Major", backref="training_programs")
    training_program_courses = relationship(
        "TrainingProgramCourse",
        back_populates="training_program",
        cascade="all, delete-orphan",
        lazy=True,
    )


class TrainingProgramCourse(db.Model):
    __tablename__ = "training_program_course"

    training_program_id = Column(Integer, ForeignKey("training_programs.id"), primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), primary_key=True)
    semester_no = Column(Integer, nullable=False, default=1)

    training_program = relationship("TrainingProgram", back_populates="training_program_courses")
    course = relationship("Course")


class Course(BaseModel):
    __tablename__ = "courses"

    name = Column(String(255))
    credits = Column(Integer)
    is_shared = Column(Boolean, default=False)
    faculty_id = Column(Integer, ForeignKey("faculties.id"))


class CourseMajor(db.Model):
    __tablename__ = "course_major"

    course_id = Column(Integer, ForeignKey("courses.id"), primary_key=True)
    major_id = Column(Integer, ForeignKey("majors.id"), primary_key=True)


class CoursePrerequisite(db.Model):
    __tablename__ = "course_prerequisite"

    course_id = Column(Integer, ForeignKey("courses.id"), primary_key=True)
    prerequisite_id = Column(Integer, ForeignKey("courses.id"), primary_key=True)


class Teacher(BaseModel):
    __tablename__ = "teachers"

    name = Column(String(255))
    faculty_id = Column(Integer, ForeignKey("faculties.id"))


class TeacherCourse(db.Model):
    __tablename__ = "teacher_course"

    teacher_id = Column(Integer, ForeignKey("teachers.id"), primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), primary_key=True)


class Student(db.Model):
    __tablename__ = "students"

    student_code = Column(String(50), primary_key=True, unique=True, nullable=False)
    name = Column(String(255))
    birth_year = Column(Integer)
    hometown = Column(String(255))
    religion = Column(String(100))
    identity_number = Column(String(50), unique=True)
    major_id = Column(Integer, ForeignKey("majors.id"), nullable=True)
    class_id = Column(Integer, ForeignKey("student_classes.id"), nullable=True)

    student_class = relationship("StudentClass", backref="students")


class ClassSection(BaseModel):
    __tablename__ = "class_sections"

    name = Column(String(255))
    course_id = Column(Integer, ForeignKey("courses.id"))
    student_class_id = Column(Integer, ForeignKey("student_classes.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))

    course = relationship("Course")
    student_class = relationship("StudentClass")
    teacher = relationship("Teacher")
    room = relationship("Room")

    semester = Column(String(50))
    max_students = Column(Integer)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    registration_deadline = Column(DateTime)
    section_type = Column(Enum(ClassSectionType), default=ClassSectionType.THEORY, nullable=False)
    linked_section_id = Column(Integer, ForeignKey("class_sections.id"))

    schedules = relationship("Schedule", backref="class_section", lazy=True)
    enrollments = relationship("Enrollment", backref="class_section", lazy=True)
    linked_section = relationship("ClassSection", remote_side="ClassSection.id", uselist=False)


class Schedule(BaseModel):
    __tablename__ = "schedules"

    class_section_id = Column(Integer, ForeignKey("class_sections.id"))
    day_of_week = Column(Integer)
    start_time = Column(Time)
    end_time = Column(Time)


class Enrollment(BaseModel):
    __tablename__ = "enrollments"

    student_code = Column(String(50), ForeignKey("students.student_code"))
    class_section_id = Column(Integer, ForeignKey("class_sections.id"))
    status = Column(Enum(EnrollmentStatus))
    registered_at = Column(DateTime, nullable=True)

    student = relationship("Student", backref="enrollments")


def get_sample_data():
    from app.seed_data import sample_data

    return sample_data


def seed_data():
    from app.seed_data import seed_data as run_seed_data

    return run_seed_data()


if __name__ == "__main__":


    sys.modules.setdefault("app.model", sys.modules[__name__])

    with app.app_context():
        seed_data()

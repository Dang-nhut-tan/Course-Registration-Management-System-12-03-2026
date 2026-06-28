from selenium.webdriver.common.by import By

from app.test_selenium.pages.adminBasePage import AdminBasePage


class ClassSectionPage(AdminBasePage):
    LIST_URL = "classsection/"
    CREATE_URL = "classsection/new/"

    COURSE_SELECT = (By.ID, "course")
    STUDENT_CLASS_SELECT = (By.ID, "student_class")
    ROOM_SELECT = (By.ID, "room")
    SECTION_TYPE_SELECT = (By.ID, "section_type")
    SCHEDULE_DAY_SELECT = (By.ID, "schedule_day")
    SCHEDULE_START_TIME_SELECT = (By.ID, "schedule_start_time")
    SCHEDULE_END_TIME_SELECT = (By.ID, "schedule_end_time")
    TEACHER_SELECT = (By.ID, "teacher")

    MAX_STUDENTS_INPUT = (By.ID, "max_students")
    START_DATE_INPUT = (By.ID, "start_date")
    END_DATE_INPUT = (By.ID, "end_date")

    def open_list(self):
        self.open_list_path(self.LIST_URL)

    def open_create(self):
        self.open_admin_path(self.CREATE_URL)


    def select_course(self, course_name):
        self.select_text_contains(
            *self.COURSE_SELECT,
            course_name,
        )

    def select_teacher(self, teacher_name):
        self.select_text_contains(
            *self.TEACHER_SELECT,
            teacher_name,
        )

    def select_student_class(self, index=1):
        self.select_index(
            *self.STUDENT_CLASS_SELECT,
            index,
        )

    def select_room(self, room_name):
        self.select_text_contains(
            *self.ROOM_SELECT,
            room_name,
        )

    def select_section_type(self, section_type="theory"):
        self.select_value(
            *self.SECTION_TYPE_SELECT,
            section_type,
        )

    def select_schedule_day(self, day="2"):
        self.select_value(
            *self.SCHEDULE_DAY_SELECT,
            day,
        )

    def select_start_time(self, start_time="07:30"):
        self.select_value(
            *self.SCHEDULE_START_TIME_SELECT,
            start_time,
        )

    def select_end_time(self, end_time="12:00"):
        self.select_value(
            *self.SCHEDULE_END_TIME_SELECT,
            end_time,
        )

    def set_max_students(self, max_students="40"):
        self.clear_and_type(
            *self.MAX_STUDENTS_INPUT,
            max_students,
        )

    def set_start_date(self, start_date_value):
        self.set_value(
            *self.START_DATE_INPUT,
            start_date_value,
        )

    def set_end_date(self, end_date_value):
        self.set_value(
            *self.END_DATE_INPUT,
            end_date_value,
        )

    # FULL FORM

    def fill_classsection_form(
        self,
        course_name,
        room_name,
        teacher_name=None,
        student_class_index=1,
        section_type="theory",
        schedule_day="2",
        start_time="07:30",
        end_time="12:00",
        max_students="40",
        start_date_value="2026-08-01 00:00:00",
        end_date_value="2026-12-31 00:00:00",
    ):
        self.open_create()

        self.select_course(course_name)

        if teacher_name:
            self.select_teacher(teacher_name)

        self.select_student_class(student_class_index)

        self.select_room(room_name)

        self.select_section_type(section_type)

        self.select_schedule_day(schedule_day)

        self.select_start_time(start_time)

        self.select_end_time(end_time)

        self.set_max_students(max_students)

        self.set_start_date(start_date_value)

        self.set_end_date(end_date_value)


    # CRUD
    def create_classsection(
        self,
        course_name,
        room_name,
        **kwargs,
    ):
        self.fill_classsection_form(
            course_name,
            room_name,
            **kwargs,
        )

        self.submit()

    def edit_max_students(
        self,
        course_name,
        max_students,
        schedule_day="2",
        start_time="07:30",
        end_time="12:00",
    ):
        self.open_list()

        self.click_edit_for_row_containing(course_name)

        self.select_schedule_day(schedule_day)

        self.select_start_time(start_time)

        self.select_end_time(end_time)

        self.set_max_students(max_students)

        self.submit()

    def delete_classsection(self, course_name):
        self.open_list()

        self.delete_row_containing(course_name)

    # ASSERT
    def create_failed(self):
        return (
            self.SUCCESS_MESSAGE not in self.driver.page_source
            and "/admin/classsection/new/" in self.driver.current_url
        )

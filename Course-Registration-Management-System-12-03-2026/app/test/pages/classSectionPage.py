from selenium.webdriver.common.by import By

from app.test.pages.adminBasePage import AdminBasePage


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
    MAX_STUDENTS_INPUT = (By.ID, "max_students")
    START_DATE_INPUT = (By.ID, "start_date")
    END_DATE_INPUT = (By.ID, "end_date")

    def open_list(self):
        self.open_list_path(self.LIST_URL)

    def open_create(self):
        self.open_admin_path(self.CREATE_URL)

    def fill_classsection_form(
        self,
        course_name,
        room_name,
        max_students="40",
        start_time="07:30",
        end_time="12:00",
        start_date_value="2026-08-01 00:00:00",
        end_date_value="2026-12-31 00:00:00",
    ):
        self.open_create()
        self.select_text_contains(*self.COURSE_SELECT, course_name)
        self.select_index(*self.STUDENT_CLASS_SELECT, 1)
        self.select_text_contains(*self.ROOM_SELECT, room_name)
        self.select_value(*self.SECTION_TYPE_SELECT, "theory")
        self.select_value(*self.SCHEDULE_DAY_SELECT, "2")
        self.select_value(*self.SCHEDULE_START_TIME_SELECT, start_time)
        self.select_value(*self.SCHEDULE_END_TIME_SELECT, end_time)
        self.clear_and_type(*self.MAX_STUDENTS_INPUT, max_students)
        self.set_value(*self.START_DATE_INPUT, start_date_value)
        self.set_value(*self.END_DATE_INPUT, end_date_value)

    def create_classsection(self, course_name, room_name, **kwargs):
        self.fill_classsection_form(course_name, room_name, **kwargs)
        self.submit()

    def create_failed(self):
        return (
            self.SUCCESS_MESSAGE not in self.driver.page_source
            and "/admin/classsection/new/" in self.driver.current_url
        )

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
        self.select_value(*self.SCHEDULE_DAY_SELECT, schedule_day)
        self.select_value(*self.SCHEDULE_START_TIME_SELECT, start_time)
        self.select_value(*self.SCHEDULE_END_TIME_SELECT, end_time)
        self.clear_and_type(*self.MAX_STUDENTS_INPUT, max_students)
        self.submit()

    def delete_classsection(self, course_name):
        self.open_list()
        self.delete_row_containing(course_name)

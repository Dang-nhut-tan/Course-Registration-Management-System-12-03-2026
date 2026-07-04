from app.test_selenium.pages.basePage import BasePage


class StudentAcademicPage(BasePage):
    """Student timetable and grade views."""

    def open_timetable(self):
        self.open_path("timetable")

    def open_grades(self):
        self.open_path("grades")

    def has_course(self, course_name):
        return self.contains_text(course_name)

    def does_not_have_course(self, course_name):
        return self.does_not_contain_text(course_name)

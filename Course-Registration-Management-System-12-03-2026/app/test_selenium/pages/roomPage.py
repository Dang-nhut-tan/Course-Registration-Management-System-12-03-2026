from selenium.webdriver.common.by import By

from app.test_selenium.pages.adminBasePage import AdminBasePage


class RoomPage(AdminBasePage):
    LIST_URL = "room/"
    CREATE_URL = "room/new/"

    NAME_INPUT = (By.ID, "name")
    ROOM_TYPE_SELECT = (By.ID, "room_type")
    CAPACITY_INPUT = (By.ID, "capacity")
    CAMPUS_SELECT = (By.ID, "campus")

    def open_list(self):
        self.open_list_path(self.LIST_URL)

    def open_create(self):
        self.open_admin_path(self.CREATE_URL)

    def campus_count(self):
        self.open_create()
        return len(self.find(*self.CAMPUS_SELECT).find_elements(By.TAG_NAME, "option"))

    def create_room(self, name, room_type="theory", capacity="40", campus_index=1):
        self.open_create()
        self.fill_room_form(name, room_type, capacity, campus_index)
        self.submit()

    def fill_room_form(self, name, room_type="theory", capacity="40", campus_index=1):
        self.typing(*self.NAME_INPUT, name)
        self.select_value(*self.ROOM_TYPE_SELECT, room_type)
        self.clear_and_type(*self.CAPACITY_INPUT, capacity)
        self.select_index(*self.CAMPUS_SELECT, campus_index)

    def edit_room_name(self, current_name, new_name):
        self.open_list()
        self.click_edit_for_row_containing(current_name)
        self.clear_and_type(*self.NAME_INPUT, new_name)
        self.submit()

    def delete_room(self, name):
        self.open_list()
        self.delete_row_containing(name)

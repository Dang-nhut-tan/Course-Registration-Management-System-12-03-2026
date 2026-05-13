import time

from app.test.pages.loginPage import LoginPage
from app.test.pages.roomPage import RoomPage
from app.test.test_base import driver, test_app


def test_admin_create_room_in_all_campuses(driver):
    login = LoginPage(driver=driver)
    login.open_page()
    login.login("admin", "admin123", role="admin")
    time.sleep(1)

    room_page = RoomPage(driver)
    campus_count = room_page.campus_count()

    for index in range(1, campus_count):
        room_name = f"SEL{index}{int(time.time())}"
        edited_room_name = f"{room_name}E"

        room_page.create_room(room_name, campus_index=index)
        time.sleep(1)

        assert room_page.has_created_message()

        room_page.edit_room_name(room_name, edited_room_name)
        time.sleep(1)

        assert room_page.has_saved_message()

        room_page.delete_room(edited_room_name)
        time.sleep(1)

        assert room_page.has_deleted_message()

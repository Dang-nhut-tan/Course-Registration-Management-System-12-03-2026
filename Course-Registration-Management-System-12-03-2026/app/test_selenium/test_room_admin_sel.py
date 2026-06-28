import time
from app.test_selenium.pages.roomPage import RoomPage
from app.test.test_base import driver

DELETE_ROOM_FAILED_MESSAGE = "Không thể xóa phòng vì phòng này đang được dùng cho lớp học phần."


def test_admin_create_room_in_all_campuses(driver):
    room_page = RoomPage(driver)
    room_page.admin_login()

    time.sleep(1)

    room_page = RoomPage(driver=driver)
    campus_count = room_page.campus_count()

    for index in range(1, campus_count):
        room_name = f"SEL{index}{int(time.time())}"
        edited_room_name = f"{room_name}E"

        # CREATE ROOM
        room_page.create_room(room_name, campus_index=index)
        time.sleep(1)

        assert room_page.has_created_message()

        # EDIT ROOM
        room_page.edit_room_name(room_name, edited_room_name)
        time.sleep(1)

        assert room_page.has_saved_message()

        # DELETE ROOM
        room_page.delete_room(edited_room_name)
        time.sleep(1)

        assert room_page.has_deleted_message()


def test_admin_cannot_delete_room_used_by_classsection(driver):
    room_name = "A101"

    room_page = RoomPage(driver)
    room_page.admin_login()

    # OPEN ROOM PAGE
    room_page.open_list()
    time.sleep(2)

    # DELETE ROOM
    room_page.delete_room(room_name)
    time.sleep(2)

    # ASSERT DELETE FAILED MESSAGE
    assert (
        DELETE_ROOM_FAILED_MESSAGE
        in driver.page_source
    )

    # ASSERT ROOM STILL EXISTS
    assert (room_name in driver.page_source)

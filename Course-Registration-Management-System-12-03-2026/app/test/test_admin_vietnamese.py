from flask import g

from app import app
from app.admin import (
    ClassSectionView,
    CourseView,
    GradeView,
    RoomView,
    admin,
)
from app.model import ClassSection, Course, Grade, Room
from app.test.test_base import test_app, test_session
from flask_admin.babel import gettext


def test_flask_admin_builtin_actions_are_vietnamese():
    expected = {
        "Create": "Tạo",
        "Edit": "Chỉnh sửa",
        "Delete": "Xóa",
        "Save": "Lưu",
        "Cancel": "Hủy bỏ",
        "Search": "Tìm",
        "Reset": "Đặt lại",
        "List": "Danh sách",
    }

    with app.test_request_context("/admin/course/"):
        g._admin_view = admin._views[1]
        assert {source: gettext(source) for source in expected} == expected


def test_admin_menu_names_are_vietnamese():
    assert [view.name for view in admin._views[1:]] == [
        "Môn học",
        "Lớp học phần",
        "Điểm",
        "Phòng học",
        "Giảng viên",
        "Phân công giảng dạy",
        "Khoa",
        "Môn tiên quyết",
        "Cơ sở",
    ]


def test_custom_admin_labels_and_choices_are_vietnamese(test_session):
    assert CourseView(Course, test_session).column_labels["credits"] == "Số tín chỉ"
    assert ClassSectionView(ClassSection, test_session).form_choices["section_type"] == [
        ("THEORY", "Lý thuyết"),
        ("PRACTICE", "Thực hành"),
    ]
    assert RoomView(Room, test_session).form_choices["room_type"] == [
        ("theory", "Lý thuyết"),
        ("practice", "Thực hành"),
    ]
    assert GradeView(Grade, test_session).column_labels["midterm_score"] == "Điểm giữa kỳ"

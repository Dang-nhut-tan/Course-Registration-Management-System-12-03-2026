from app import utils


def test_calculate_total_score_uses_40_60_weight():
    assert utils.calculate_total_score(7.0, 8.0) == 7.6


def test_convert_score_to_scale_4_and_letter():
    assert utils.convert_score_to_scale_4(8.5) == 4.0
    assert utils.convert_score_to_letter(8.5) == "A"
    assert utils.get_pass_fail_result(8.5) == "PASS"

    assert utils.convert_score_to_scale_4(3.9) == 0
    assert utils.convert_score_to_letter(3.9) == "F"
    assert utils.get_pass_fail_result(3.9) == "FAIL"


def test_missing_score_has_no_total_result():
    assert utils.calculate_total_score(None, 8.0) is None
    assert utils.convert_score_to_scale_4(None) is None
    assert utils.convert_score_to_letter(None) is None
    assert utils.get_pass_fail_result(None) is None


def test_calculate_weighted_average_ignores_missing_scores():
    items = [
        {"course": type("Course", (), {"credits": 3})(), "total_score": 8.0},
        {"course": type("Course", (), {"credits": 1})(), "total_score": None},
        {"course": type("Course", (), {"credits": 3})(), "total_score": 6.0},
    ]

    assert utils.calculate_weighted_average(items, "total_score") == 7.0


def test_classify_average():
    assert utils.classify_average(3.7) == "Xuất sắc"
    assert utils.classify_average(3.3) == "Giỏi"
    assert utils.classify_average(2.7) == "Khá"
    assert utils.classify_average(2.1) == "Trung bình"
    assert utils.classify_average(1.9) == "Yếu"

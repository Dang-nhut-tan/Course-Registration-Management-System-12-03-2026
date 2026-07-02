from app.model import ClassSection, ClassSectionType, Enrollment


def calculate_total_score(midterm_score, final_score):
    if midterm_score is None or final_score is None:
        return None
    return round((midterm_score * 0.4) + (final_score * 0.6), 1)


def convert_score_to_scale_4(total_score):
    if total_score is None:
        return None
    if total_score >= 8.5:
        return 4.0
    if total_score >= 7.0:
        return 3.0
    if total_score >= 5.5:
        return 2.0
    if total_score >= 4.0:
        return 1.0
    return 0


def convert_score_to_letter(total_score):
    if total_score is None:
        return None
    if total_score >= 8.5:
        return "A"
    if total_score >= 7.0:
        return "B"
    if total_score >= 5.5:
        return "C"
    if total_score >= 4.0:
        return "D"
    return "F"


def get_pass_fail_result(total_score):
    if total_score is None:
        return None
    return "PASS" if total_score >= 4.0 else "FAIL"


def build_grade_result(enrollment):
    section = enrollment.class_section
    grade = enrollment.grade
    midterm_score = grade.midterm_score if grade else None
    final_score = grade.final_score if grade else None
    total_score = calculate_total_score(midterm_score, final_score)

    return {
        "enrollment": enrollment,
        "section": section,
        "course": section.course,
        "grade": grade,
        "midterm_score": midterm_score,
        "final_score": final_score,
        "total_score": total_score,
        "scale_4_score": convert_score_to_scale_4(total_score),
        "letter_score": convert_score_to_letter(total_score),
        "result": get_pass_fail_result(total_score),
    }


def get_student_grade_results(student_code):
    enrollments = Enrollment.query.join(ClassSection).filter(
        Enrollment.student_code == student_code,
        ClassSection.section_type == ClassSectionType.THEORY,
    ).order_by(ClassSection.semester.desc(), ClassSection.id).all()

    return [build_grade_result(enrollment) for enrollment in enrollments]


def calculate_weighted_average(items, score_key):
    total_points = 0
    total_credits = 0
    for item in items:
        score = item.get(score_key)
        credits = item["course"].credits or 0
        if score is None or credits <= 0:
            continue
        total_points += score * credits
        total_credits += credits

    if total_credits == 0:
        return None
    return round(total_points / total_credits, 2)


def classify_average(scale_4_score):
    if scale_4_score is None:
        return "-"
    if scale_4_score >= 3.6:
        return "Xuất sắc"
    if scale_4_score >= 3.2:
        return "Giỏi"
    if scale_4_score >= 2.5:
        return "Khá"
    if scale_4_score >= 2.0:
        return "Trung bình"
    return "Yếu"


def get_passed_credits(items):
    return sum(
        item["course"].credits or 0
        for item in items
        if item.get("total_score") is not None and item["total_score"] >= 4.0
    )


def get_completed_credits(items):
    return sum(
        item["course"].credits or 0
        for item in items
        if item.get("total_score") is not None
    )


def semester_sort_key(semester):
    try:
        year, term = str(semester).split("-", 1)
        return int(year), int(term)
    except (TypeError, ValueError):
        return 0, 0


def build_study_result_context(student_code):
    grade_results = get_student_grade_results(student_code)
    grouped = {}
    for item in grade_results:
        grouped.setdefault(item["section"].semester, []).append(item)

    semester_rows = []
    cumulative_items = []
    for semester in sorted(grouped, key=semester_sort_key):
        items = grouped[semester]
        cumulative_items.extend(items)

        semester_average_10 = calculate_weighted_average(items, "total_score")
        semester_average_4 = calculate_weighted_average(items, "scale_4_score")
        cumulative_average_4 = calculate_weighted_average(cumulative_items, "scale_4_score")

        semester_rows.append(
            {
                "semester": semester,
                "courses": items,
                "summary": {
                    "semester_average_10": semester_average_10,
                    "semester_average_4": semester_average_4,
                    "semester_credits": get_passed_credits(items),
                    "cumulative_average_4": cumulative_average_4,
                    "cumulative_credits": get_passed_credits(cumulative_items),
                    "classification": classify_average(semester_average_4),
                },
            }
        )

    return list(reversed(semester_rows))

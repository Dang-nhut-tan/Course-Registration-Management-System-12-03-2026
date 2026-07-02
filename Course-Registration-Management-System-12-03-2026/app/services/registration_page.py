"""Build the view model for the student registration page."""

from app import utils


DEFAULT_PAGE_SIZE = 4


def build_registration_page_context(student_code, query_args, student_name=None):
    course_query = (query_args.get("course_query") or "").strip()
    faculty_id = query_args.get("faculty")
    training_program_semester = query_args.get("training_program_semester")
    page = query_args.get("page", default=1, type=int) or 1
    has_manual_training_program_filter = bool(training_program_semester)

    default_semester = str(
        utils.get_default_training_program_semester(student_code) or ""
    )
    current_semester = str(
        utils.get_current_training_program_semester(student_code) or ""
    )
    effective_semester = training_program_semester or default_semester
    _, student_class, _ = utils.get_student_context(student_code)
    selected_faculty_id = faculty_id or ""

    all_sections = utils.get_sections(
        student_code,
        course_query or None,
        selected_faculty_id or None,
        effective_semester or None,
    )
    filters = utils.get_filter_data(
        student_code,
        selected_faculty_id or None,
        effective_semester or None,
    )
    registered_courses = utils.get_registered_courses(student_code)
    registered_credits = utils.get_registered_credits(student_code)
    credit_limit = utils.get_credit_limit_per_semester(student_code)
    minimum_credits = utils.get_minimum_credits_to_enforce(student_code)

    total_sections = len(all_sections)
    total_pages = max(
        (total_sections + DEFAULT_PAGE_SIZE - 1) // DEFAULT_PAGE_SIZE,
        1,
    )
    page = min(max(page, 1), total_pages)
    start = (page - 1) * DEFAULT_PAGE_SIZE
    sections = all_sections[start:start + DEFAULT_PAGE_SIZE]

    count_section_ids = []
    for section in sections:
        count_section_ids.append(section.id)
        if section.linked_section_id:
            count_section_ids.append(section.linked_section_id)

    section_capacity_limits = {}
    for section in sections:
        section_capacity_limits[section.id] = utils.get_section_capacity_limit(section)
        if section.linked_section:
            linked_section = section.linked_section
            section_capacity_limits[linked_section.id] = (
                utils.get_section_capacity_limit(linked_section)
            )

    return {
        "sections": sections,
        "total_sections": total_sections,
        "page": page,
        "total_pages": total_pages,
        "courses": filters["courses"],
        "faculties": filters["faculties"],
        "selected_course_query": course_query,
        "selected_faculty_id": selected_faculty_id,
        "selected_training_program_semester": training_program_semester or "",
        "default_training_program_semester": default_semester,
        "current_training_program_semester": current_semester,
        "has_manual_training_program_filter": has_manual_training_program_filter,
        "training_program_semesters": filters["training_program_semesters"],
        "student_code": student_code,
        "student_name": student_name,
        "student_class": student_class,
        "registered_courses": registered_courses,
        "registered_credits": registered_credits,
        "credit_limit": credit_limit,
        "minimum_registered_credits": minimum_credits,
        "registered_section_ids": [
            enrollment.class_section_id for enrollment in registered_courses
        ],
        "section_registered_counts": utils.get_registered_counts(count_section_ids),
        "section_capacity_limits": section_capacity_limits,
        "message": query_args.get("msg", ""),
        "message_type": query_args.get("msg_type", ""),
    }


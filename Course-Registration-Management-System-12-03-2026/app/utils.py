"""Backward-compatible facade for focused utility modules."""

from app.utilities.auth import (
    check_login_student,
    check_login_admin,
    load_user,
    check_room_conflict,
    check_teacher_conflict,
    login_manager,
)

from app.utilities.curriculum import (
    get_student_context,
    get_student_training_program,
    get_available_training_program_semesters,
    get_default_training_program_semester,
    get_allowed_course_ids,
    get_student_program_course_ids,
    is_current_training_program_semester,
    get_current_open_semester,
    is_current_open_section,
    is_course_in_student_major,
    is_course_in_current_training_program_semester,
    is_course_registrable_for_student,
    get_student_faculty_id,
    get_current_training_program_semester,
    is_course_allowed,
)

from app.utilities.registration import (
    validate_section_registration,
    get_section_registration_start_date,
    get_section_registration_deadline,
    is_section_open_for_registration,
    get_sections,
    get_open_filter_options,
    get_registered_courses,
    get_registered_credits,
    get_credit_limit_per_semester,
    get_current_training_program_credit_load,
    get_minimum_credits_to_enforce,
    get_registered_counts,
    get_section_capacity_limit,
    get_missing_prerequisite_courses,
    schedules_overlap,
    get_schedule_conflict,
    has_registered_same_course,
    get_filter_data,
)

from app.utilities.grades import (
    calculate_total_score,
    convert_score_to_scale_4,
    convert_score_to_letter,
    get_pass_fail_result,
    build_grade_result,
    get_student_grade_results,
    calculate_weighted_average,
    classify_average,
    get_passed_credits,
    get_completed_credits,
    semester_sort_key,
    build_study_result_context,
)

from app.utilities.timetable import (
    build_timetable_rows,
    get_student_timetable,
)

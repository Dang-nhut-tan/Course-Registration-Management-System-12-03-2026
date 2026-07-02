from datetime import datetime, timedelta

from app import db
from app.model import ClassSection, Enrollment, EnrollmentStatus

from app.utilities.curriculum import (
    get_current_open_semester, get_current_training_program_semester,
    get_student_training_program,
)


def build_timetable_rows(schedules):
    """Group every schedule by its exact time slot and weekday."""
    slots = sorted({(item.start_time, item.end_time) for item in schedules})
    rows = []
    for start_time, end_time in slots:
        by_day = {}
        for schedule in schedules:
            if schedule.start_time == start_time and schedule.end_time == end_time:
                by_day.setdefault(schedule.day_of_week, []).append(schedule)
        rows.append({
            "start_time": start_time,
            "end_time": end_time,
            "by_day": by_day,
        })
    return rows


def get_student_timetable(student_code, requested_week=1):
    semester_no = get_current_training_program_semester(student_code)

    training_program = get_student_training_program(student_code)

    if not training_program:
        return {
            "schedules": [],
            "schedule_rows": [],
            "unscheduled_sections": [],
            "semester_no": "N/A",
            "semester_raw": "N/A",
            "week_days": [],
            "week": 1,
            "max_week": 1,
            "can_previous_week": False,
            "can_next_week": False,
            "term_start": None,
            "term_end": None,
        }

    current_open_semester = get_current_open_semester(student_code)
    section_query = db.session.query(ClassSection) \
        .join(Enrollment, Enrollment.class_section_id == ClassSection.id) \
        .filter(
        Enrollment.student_code == student_code,
        Enrollment.status == EnrollmentStatus.REGISTERED,
    )
    if current_open_semester:
        section_query = section_query.filter(ClassSection.semester == current_open_semester)
    registered_sections = section_query.order_by(ClassSection.start_date, ClassSection.id).all()
    schedules = sorted(
        (schedule for section in registered_sections for schedule in section.schedules),
        key=lambda item: (
            item.class_section.start_date,
            item.day_of_week,
            item.start_time,
        ),
    )
    unscheduled_sections = [section for section in registered_sections if not section.schedules]

    raw_semester = current_open_semester or "N/A"

    if registered_sections:
        first_section_date = min(section.start_date.date() for section in registered_sections)
        last_section_date = max(section.end_date.date() for section in registered_sections)
        term_start = first_section_date - timedelta(days=first_section_date.weekday())
        term_end = last_section_date + timedelta(days=6 - last_section_date.weekday())
    else:
        term_start = datetime.now().date()
        term_end = term_start

    max_week = max(((term_end - term_start).days // 7) + 1, 1)
    current_week = min(max(requested_week or 1, 1), max_week)

    week_start_date = term_start + timedelta(days=(current_week - 1) * 7)
    week_days = [{'thu': i + 2 if i < 6 else 8, 'date': week_start_date + timedelta(days=i)} for i in range(7)]
    week_dates_by_day = {day["thu"]: day["date"] for day in week_days}

    active_schedules = []
    for schedule in schedules:
        class_date = week_dates_by_day.get(schedule.day_of_week)
        section_start = schedule.class_section.start_date.date()
        section_end = schedule.class_section.end_date.date()
        if class_date and section_start <= class_date <= section_end:
            active_schedules.append(schedule)

    return {
        "schedules": active_schedules,
        "schedule_rows": build_timetable_rows(active_schedules),
        "unscheduled_sections": unscheduled_sections,
        "semester_no": semester_no,
        "semester_raw": raw_semester,
        "week_days": week_days,
        "week": current_week,
        "max_week": max_week,
        "can_previous_week": current_week > 1,
        "can_next_week": current_week < max_week,
        "term_start": term_start,
        "term_end": term_end,
    }

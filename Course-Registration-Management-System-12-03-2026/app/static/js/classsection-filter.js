(function () {
  const dataElement = document.getElementById('classsection-filter-data');
  if (!dataElement) {
    return;
  }

  const data = JSON.parse(dataElement.textContent);
  const courseSelect = document.querySelector('[name="course"]');
  const studentClassSelect = document.querySelector('[name="student_class"]');
  const teacherSelect = document.querySelector('[name="teacher"]');
  const roomSelect = document.querySelector('[name="room"]');
  const linkedSectionSelect = document.querySelector('[name="linked_section"]');
  const sectionTypeSelect = document.querySelector('[name="section_type"]');
  const semesterInput = document.querySelector('[name="semester"]');
  const daySelect = document.querySelector('[name="schedule_day"]');
  const startTimeSelect = document.querySelector('[name="schedule_start_time"]');
  const endTimeSelect = document.querySelector('[name="schedule_end_time"]');

  if (!courseSelect || !teacherSelect || !roomSelect) {
    return;
  }

  function toMinutes(value) {
    if (!value || !value.includes(':')) {
      return null;
    }

    const parts = value.split(':');
    return Number(parts[0]) * 60 + Number(parts[1]);
  }

  function overlapsBusyTime(item) {
    const selectedStart = toMinutes(startTimeSelect ? startTimeSelect.value : '');
    const selectedEnd = toMinutes(endTimeSelect ? endTimeSelect.value : '');
    const busyStart = toMinutes(item.start);
    const busyEnd = toMinutes(item.end);

    if (selectedStart === null || selectedEnd === null || busyStart === null || busyEnd === null) {
      return true;
    }

    return busyStart < selectedEnd && busyEnd > selectedStart;
  }

  function isBusy(itemId, kind) {
    const semester = semesterInput ? semesterInput.value : '';
    const day = daySelect && daySelect.value ? Number(daySelect.value) : null;
    if (!semester || !day) {
      return false;
    }

    return data.busy.some(function (item) {
      return item.semester === semester
        && item.day === day
        && item[kind] === itemId
        && overlapsBusyTime(item);
    });
  }

  function getCourseFacultyId() {
    const course = data.courses.find(function (item) {
      return item.id === courseSelect.value;
    });
    return course ? course.faculty_id : '';
  }

  function clearOptions(select) {
    while (select.options.length) {
      select.remove(0);
    }
  }

  function addOption(select, value, text) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = text;
    select.appendChild(option);
  }

  function hasOption(select, value) {
    return Array.from(select.options).some(function (option) {
      return option.value === value;
    });
  }

  function filterTeachers() {
    const selected = teacherSelect.value;
    const courseId = courseSelect.value;
    const facultyId = getCourseFacultyId();
    const courseTeacherIds = data.teacher_courses[courseId] || [];
    const useCourseTeachers = courseTeacherIds.length > 0;

    clearOptions(teacherSelect);
    addOption(teacherSelect, '__None', '');

    data.teachers.forEach(function (teacher) {
      const matchCourse = useCourseTeachers && courseTeacherIds.includes(teacher.id);
      const matchFaculty = !useCourseTeachers && teacher.faculty_id === facultyId;
      if ((matchCourse || matchFaculty || !courseId) && !isBusy(teacher.id, 'teacher_id')) {
        addOption(teacherSelect, teacher.id, teacher.name);
      }
    });

    teacherSelect.value = hasOption(teacherSelect, selected) ? selected : '__None';
    teacherSelect.dispatchEvent(new Event('change'));
  }

  function filterRooms() {
    const selected = roomSelect.value;
    const sectionType = sectionTypeSelect ? sectionTypeSelect.value : '';
    const roomType = sectionType === 'practice' ? 'practice' : 'theory';

    clearOptions(roomSelect);
    addOption(roomSelect, '__None', '');

    data.rooms.forEach(function (room) {
      if (room.room_type === roomType && !isBusy(room.id, 'room_id')) {
        addOption(roomSelect, room.id, room.name);
      }
    });

    roomSelect.value = hasOption(roomSelect, selected) ? selected : '__None';
    roomSelect.dispatchEvent(new Event('change'));
  }

  function filterLinkedSections() {
    if (!linkedSectionSelect) {
      return;
    }

    const selected = linkedSectionSelect.value;
    const courseId = courseSelect.value;
    const studentClassId = studentClassSelect ? studentClassSelect.value : '';
    const semester = semesterInput ? semesterInput.value : '';
    const sectionType = sectionTypeSelect ? sectionTypeSelect.value : '';

    clearOptions(linkedSectionSelect);
    addOption(linkedSectionSelect, '__None', '');

    if (sectionType === 'practice') {
      linkedSectionSelect.value = '__None';
      linkedSectionSelect.dispatchEvent(new Event('change'));
      return;
    }

    const matches = data.practice_sections.filter(function (section) {
      const matchCourse = !courseId || section.course_id === courseId;
      const matchSemester = !semester || section.semester === semester;
      const matchStudentClass = !studentClassId || section.student_class_id === studentClassId;
      return matchCourse && matchSemester && matchStudentClass && !section.is_linked;
    });

    matches.sort(function (a, b) {
      if (a.room_type === 'practice' && b.room_type !== 'practice') {
        return -1;
      }
      if (a.room_type !== 'practice' && b.room_type === 'practice') {
        return 1;
      }
      return Number(a.id) - Number(b.id);
    });

    matches.forEach(function (section) {
      addOption(linkedSectionSelect, section.id, section.name);
    });

    linkedSectionSelect.value = hasOption(linkedSectionSelect, selected)
      ? selected
      : (matches.length ? matches[0].id : '__None');
    linkedSectionSelect.dispatchEvent(new Event('change'));
  }

  function updateFilters() {
    filterTeachers();
    filterRooms();
    filterLinkedSections();
  }

  [courseSelect, studentClassSelect, sectionTypeSelect, semesterInput, daySelect, startTimeSelect, endTimeSelect].forEach(function (field) {
    if (field) {
      field.addEventListener('change', updateFilters);
      field.addEventListener('keyup', updateFilters);
    }
  });

  updateFilters();
}());

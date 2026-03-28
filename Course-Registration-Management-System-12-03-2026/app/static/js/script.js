document.getElementById("loginForm").addEventListener("submit", function (e) {
  e.preventDefault();

  const username = document.getElementById("student_code").value;
  const password = document.getElementById("password").value;

  if (username === "" || password === "") {
    alert("Vui lòng nhập đầy đủ thông tin");
    return;
  }
});

function openScheduleModal(code, name, schedules) {
  document.getElementById("modal-subject-code").textContent = code;
  document.getElementById("modal-subject-name").textContent = name;

  const listContainer = document.getElementById("modal-schedule-list");
  listContainer.innerHTML = "";

  schedules.forEach((item) => {
    const div = document.createElement("div");
    div.className = "py-4 text-sm text-on-surface-variant";
    div.textContent = item[0];
    listContainer.appendChild(div);
  });

  document.getElementById("schedule-modal").classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeScheduleModal() {
  document.getElementById("schedule-modal").classList.remove("active");
  document.body.style.overflow = "";
}

// Close modal on escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeScheduleModal();
});

document
  .getElementById("primary-filter-select")
  .addEventListener("change", function () {
    const secondaryFilter = document.getElementById(
      "secondary-filter-container",
    );
    const subjectFilter = document.getElementById("subject-filter-container");
    const label = document.getElementById("secondary-filter-label");
    const icon = document.getElementById("secondary-filter-icon");
    const input = document.getElementById("secondary-filter-input");

    if (this.value === "subject") {
      secondaryFilter.classList.add("hidden");
      subjectFilter.classList.remove("hidden");
    } else if (this.value === "department") {
      secondaryFilter.classList.remove("hidden");
      subjectFilter.classList.add("hidden");
      label.textContent = "Nhập tên Khoa";
      icon.textContent = "school";
      input.placeholder = "Gõ để tìm kiếm khoa...";
    } else if (this.value === "class") {
      secondaryFilter.classList.remove("hidden");
      subjectFilter.classList.add("hidden");
      label.textContent = "Nhập mã Lớp";
      icon.textContent = "groups";
      input.placeholder = "Gõ để tìm kiếm lớp...";
    }
  });

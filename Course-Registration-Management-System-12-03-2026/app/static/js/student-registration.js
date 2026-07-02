(() => {
  const page = document.querySelector("[data-registration-page]");
  if (!page) return;

  function initCourseCombobox(combobox) {
    const input = combobox.querySelector("[data-course-input]");
    const toggle = combobox.querySelector("[data-course-toggle]");
    const options = [...combobox.querySelectorAll("[data-course-option]")];
    if (!input || !toggle) return;

    const close = () => combobox.classList.remove("is-open");
    const filter = () => {
      const term = input.value.trim().toLowerCase();
      let visibleCount = 0;

      options.forEach((option) => {
        const isVisible = !term || option.dataset.searchText.includes(term);
        option.hidden = !isVisible;
        if (isVisible) visibleCount += 1;
      });
      combobox.classList.toggle("has-no-results", visibleCount === 0);
    };
    const open = () => {
      combobox.classList.add("is-open");
      filter();
    };

    input.addEventListener("focus", open);
    input.addEventListener("input", open);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Escape") close();
    });
    toggle.addEventListener("click", () => {
      if (combobox.classList.contains("is-open")) {
        close();
      } else {
        input.focus();
        open();
      }
    });
    options.forEach((option) => {
      option.addEventListener("click", () => {
        input.value = option.dataset.value;
        close();
      });
    });
    document.addEventListener("click", (event) => {
      if (!combobox.contains(event.target)) close();
    });
  }

  async function submitEnrollment(form, method, payload) {
    const button = form.querySelector("button[type='submit']");
    if (button) button.disabled = true;

    try {
      const response = await fetch(form.action, {
        method,
        headers: { "Content-Type": "application/json" },
        body: payload ? JSON.stringify(payload) : null,
      });
      const result = await response.json();
      const params = new URLSearchParams(window.location.search);
      const formData = new FormData(form);

      ["course_query", "faculty", "training_program_semester", "page"].forEach((key) => {
        if (formData.get(key)) params.set(key, formData.get(key));
      });
      params.set("msg", result.message || "API không trả về thông báo.");
      params.set("msg_type", result.success ? "success" : "error");
      window.location.assign(`${page.dataset.indexUrl}?${params.toString()}`);
    } catch (_error) {
      window.alert("Không thể kết nối đến API.");
      if (button) button.disabled = false;
    }
  }

  document.querySelectorAll("[data-course-combobox]").forEach(initCourseCombobox);
  document.querySelectorAll(".js-register-course").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      submitEnrollment(form, "POST", {
        class_section_id: Number(new FormData(form).get("class_section_id")),
      });
    });
  });
  document.querySelectorAll(".js-cancel-course").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      submitEnrollment(form, "DELETE");
    });
  });
})();

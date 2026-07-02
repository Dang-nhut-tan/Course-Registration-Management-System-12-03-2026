(() => {
  const combobox = document.getElementById("roleCombobox");
  const button = document.getElementById("roleComboboxButton");
  const roleText = document.getElementById("roleComboboxText");
  const roleInput = document.getElementById("login_role");
  const form = document.getElementById("loginForm");
  const identifierInput = document.getElementById("student_code");
  const passwordInput = document.getElementById("password");
  if (!combobox || !button || !roleText || !roleInput || !form || !identifierInput || !passwordInput) return;

  const identifierLabel = identifierInput.closest("div").querySelector("label");
  const passwordLabel = passwordInput.closest("div").querySelector("label");
  const close = () => {
    combobox.classList.remove("is-open");
    button.setAttribute("aria-expanded", "false");
  };
  const updateLabels = (role) => {
    const isAdmin = role === "admin";
    identifierLabel.textContent = isAdmin ? "Tên đăng nhập" : "Mã số sinh viên";
    identifierInput.placeholder = isAdmin ? "Tên đăng nhập" : "Mã số sinh viên";
    passwordLabel.textContent = "Mật khẩu";
    passwordInput.placeholder = "********";
  };

  combobox.addEventListener("click", (event) => {
    const option = event.target.closest(".role-combobox__option");
    if (!option) {
      const isOpen = combobox.classList.toggle("is-open");
      button.setAttribute("aria-expanded", String(isOpen));
      return;
    }

    combobox.querySelector(".is-selected")?.classList.remove("is-selected");
    option.classList.add("is-selected");
    roleText.textContent = option.textContent.trim();
    roleInput.value = option.dataset.value;
    updateLabels(roleInput.value);
    close();
  });
  document.addEventListener("click", (event) => {
    if (!combobox.contains(event.target)) close();
  });
  form.addEventListener("submit", (event) => {
    if (!identifierInput.value.trim() || !passwordInput.value) {
      event.preventDefault();
      window.alert("Vui lòng nhập đầy đủ thông tin");
    }
  });

  updateLabels(roleInput.value);
})();

const roleCombobox = document.getElementById("roleCombobox");
const roleButton = document.getElementById("roleComboboxButton");
const roleText = document.getElementById("roleComboboxText");
const roleInput = document.getElementById("login_role");
const loginForm = document.getElementById("loginForm");
const identifierInput = document.getElementById("student_code");
const passwordInput = document.getElementById("password");
const identifierLabel = identifierInput.closest("div").querySelector("label");
const passwordLabel = passwordInput.closest("div").querySelector("label");

function updateLoginFieldText(role) {
  const isAdmin = role === "admin";

  identifierLabel.textContent = isAdmin ? "Username" : "Mã số sinh viên";
  identifierInput.placeholder = isAdmin ? "Username" : "Mã số sinh viên";
  passwordLabel.textContent = isAdmin ? "Password" : "Mật khẩu";
  passwordInput.placeholder = isAdmin ? "Password" : "********";
}

function closeRoleCombobox() {
  roleCombobox.classList.remove("is-open");
  roleButton.setAttribute("aria-expanded", "false");
}

roleCombobox.addEventListener("click", function (e) {
  const option = e.target.closest(".role-combobox__option");

  if (!option) {
    const isOpen = roleCombobox.classList.toggle("is-open");
    roleButton.setAttribute("aria-expanded", String(isOpen));
    return;
  }

  roleCombobox.querySelector(".is-selected").classList.remove("is-selected");
  option.classList.add("is-selected");
  roleText.textContent = option.textContent.trim();
  roleInput.value = option.dataset.value;
  updateLoginFieldText(roleInput.value);
  closeRoleCombobox();
});

document.addEventListener("click", function (e) {
  if (!roleCombobox.contains(e.target)) {
    closeRoleCombobox();
  }
});

loginForm.addEventListener("submit", function (e) {
  e.preventDefault();

  const studentCode = identifierInput.value;
  const password = passwordInput.value;

  if (studentCode === "" || password === "") {
    alert("Vui lòng nhập đầy đủ thông tin");
    return;
  }

  e.target.submit();
});

updateLoginFieldText(roleInput.value);

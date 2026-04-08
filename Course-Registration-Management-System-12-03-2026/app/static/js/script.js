document.getElementById("loginForm").addEventListener("submit", function (e) {
  e.preventDefault();

  const studentCode = document.getElementById("student_code").value;
  const password = document.getElementById("password").value;

  if (studentCode === "" || password === "") {
    alert("Vui lòng nhập đầy đủ thông tin");
    return;
  }

  e.target.submit();
});

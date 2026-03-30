document.getElementById("loginForm").addEventListener("submit", function (e) {
  e.preventDefault();

  const username = document.getElementById("student_code").value;
  const password = document.getElementById("password").value;

  if (username === "" || password === "") {
    alert("Vui lòng nhập đầy đủ thông tin");
    return;
  }
});

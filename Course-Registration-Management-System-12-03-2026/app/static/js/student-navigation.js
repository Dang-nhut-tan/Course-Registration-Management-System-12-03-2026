(() => {
  const navigation = document.querySelector("[data-student-navigation]");
  if (!navigation) return;

  navigation.addEventListener("change", (event) => {
    const targetUrl = event.target.value;
    if (targetUrl) window.location.assign(targetUrl);
  });
})();

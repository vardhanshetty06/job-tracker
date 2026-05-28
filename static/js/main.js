// set today's date for date_applied if empty
document.addEventListener("DOMContentLoaded", function () {
  const dateInput = document.getElementById("date_applied");
  if (dateInput && !dateInput.value) {
    dateInput.value = new Date().toISOString().split("T")[0];
  }
});

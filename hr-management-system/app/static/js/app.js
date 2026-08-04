document.addEventListener("DOMContentLoaded", function () {
  // --- Password show/hide toggle ---
  document.querySelectorAll("[data-toggle-password]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var targetId = btn.getAttribute("data-toggle-password");
      var input = document.getElementById(targetId);
      if (!input) return;

      var showing = input.type === "text";
      input.type = showing ? "password" : "text";

      var eyeIcon = btn.querySelector(".icon-eye");
      var eyeOffIcon = btn.querySelector(".icon-eye-off");
      if (eyeIcon && eyeOffIcon) {
        eyeIcon.style.display = showing ? "block" : "none";
        eyeOffIcon.style.display = showing ? "none" : "block";
      }
      btn.setAttribute("aria-label", showing ? "Show password" : "Hide password");
    });
  });

  // --- Terms & Conditions modal ---
  var modal = document.querySelector("[data-terms-modal]");
  if (modal) {
    var openModal = function (e) {
      if (e) e.preventDefault();
      modal.classList.add("is-open");
    };
    var closeModal = function () {
      modal.classList.remove("is-open");
    };

    document.querySelectorAll("[data-open-terms]").forEach(function (btn) {
      btn.addEventListener("click", openModal);
    });
    document.querySelectorAll("[data-close-terms]").forEach(function (btn) {
      btn.addEventListener("click", closeModal);
    });
    modal.addEventListener("click", function (e) {
      if (e.target === modal) closeModal();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeModal();
    });
  }
});

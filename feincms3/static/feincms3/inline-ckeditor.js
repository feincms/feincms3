(function () {
  const DEFAULTS = JSON.parse(
    document.querySelector("[data-ckeditor-defaults]").dataset.ckeditorDefaults
  );

  function initialize() {
    const config = Object.assign({}, DEFAULTS, window.CKEDITOR_CONFIG);
    document.querySelectorAll("textarea[data-ckeditor]").forEach((el) => {
      if (el.dataset.ckeditor !== "active" && !el.id.includes("__prefix__")) {
        window.CKEDITOR.inline(el, config);
        el.dataset.ckeditor = "active";
      }
    });
  }

  document.addEventListener("DOMContentLoaded", initialize);
})();

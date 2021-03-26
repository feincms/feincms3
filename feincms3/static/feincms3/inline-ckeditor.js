/* global CKEDITOR, django */
django.jQuery(function ($) {
  const configs = {};
  const scripts = document.querySelectorAll("[data-inline-cke-config]");
  scripts.forEach(function parseConfig(script) {
    configs[script.dataset.inlineCkeId] = JSON.parse(
      script.dataset.inlineCkeConfig
    );
  });

  function initializeInlineCKE() {
    document.querySelectorAll("textarea[data-inline-cke]").forEach((el) => {
      if (el.dataset.inlineCke !== "active" && !el.id.includes("__prefix__")) {
        CKEDITOR.inline(el, configs[el.dataset.inlineCke]);
        el.dataset.inlineCke = "active";
      }
    });
  }

  initializeInlineCKE();
  $(document).on("formset:added", initializeInlineCKE);
});

/* global CKEDITOR, django */
django.jQuery(function ($) {
  const script = document.querySelector("[data-inline-cke-config]");
  const config = JSON.parse(script.dataset.inlineCkeConfig);

  function initializeInlineCKE() {
    document.querySelectorAll("textarea[data-inline-cke]").forEach((el) => {
      if (el.dataset.ckeditor !== "active" && !el.id.includes("__prefix__")) {
        CKEDITOR.inline(el, config);
        el.dataset.inlineCke = "active";
      }
    });
  }

  initializeInlineCKE();
  $(document).on("formset:added", initializeInlineCKE);
});

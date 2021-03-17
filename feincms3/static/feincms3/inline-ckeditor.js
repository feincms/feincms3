(function () {
  const DEFAULTS = {
    format_tags: "h1;h2;h3;p",
    toolbar: "Custom",
    toolbar_Custom: [
      [
        "Format",
        "RemoveFormat",
        "-",
        "Bold",
        "Italic",
        "Subscript",
        "Superscript",
        "-",
        "NumberedList",
        "BulletedList",
        "-",
        "Anchor",
        "Link",
        "Unlink",
        "-",
        "HorizontalRule",
        "SpecialChar",
        "-",
        "Source",
      ],
    ],
  };

  function initialize() {
    const config = Object.assign({}, DEFAULTS, window.CKEDITOR_CONFIG);
    document.querySelectorAll("textarea[data-ckeditor]").forEach((el) => {
      if (el.dataset.ckeditor !== "active" && !el.id.includes("__prefix__")) {
        CKEDITOR.inline(el, config);
        el.dataset.ckeditor = "active";
      }
    });
  }

  document.addEventListener("DOMContentLoaded", initialize);
})();

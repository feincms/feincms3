/* global django, CKEDITOR */
(function($) {
  // Activate and deactivate the CKEDITOR because it does not like
  // getting dragged or its underlying ID changed.
  // The 'data-processed' attribute is set for compatibility with
  // django-ckeditor.
  $(document)
    .on("content-editor:activate", function(event, $row, _formsetName) {
      $row.find("textarea[data-type=ckeditortype]").each(function() {
        if (this.getAttribute("data-processed") != "1") {
          this.setAttribute("data-processed", "1");
          $($(this).data("external-plugin-resources")).each(function() {
            CKEDITOR.plugins.addExternal(this[0], this[1], this[2]);
          });
          var config = $(this).data("config");
          config.width = "100%";
          CKEDITOR.replace(this.id, config);
        }
      });
    })
    .on("content-editor:deactivate", function(event, $row, _formsetName) {
      $row.find("textarea[data-type=ckeditortype]").each(function() {
        try {
          CKEDITOR.instances[this.id] && CKEDITOR.instances[this.id].destroy();
          this.setAttribute("data-processed", "0");
        } catch (err) {
          /* intentionally left empty */
        }
      });
    });

  // Make the CKEditor widget occupy the whole width of the fieldset (but not more)
  var style = document.createElement("style");
  style.textContent =
    ".order-machine .django-ckeditor-widget { width: calc(100% - 170px); max-width: 1000px; }";
  style.textContent +=
    "@media (max-width: 767px) { .order-machine .django-ckeditor-widget { width: calc(100%); }";
  document.head.appendChild(style);
})(django.jQuery);

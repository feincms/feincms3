/* global CKEDITOR, django */
;(function () {
  function onReady(fn) {
    if (
      document.readyState === "complete" ||
      document.readyState === "interactive"
    ) {
      // call on next available tick
      setTimeout(fn, 1)
    } else {
      document.addEventListener("DOMContentLoaded", fn)
    }
  }

  onReady(function () {
    const configs = {}
    const scripts = document.querySelectorAll("[data-inline-cke-config]")
    scripts.forEach(function parseConfig(script) {
      configs[script.dataset.inlineCkeId] = JSON.parse(
        script.dataset.inlineCkeConfig
      )
    })

    function initializeInlineCKE() {
      document.querySelectorAll("textarea[data-inline-cke]").forEach((el) => {
        if (
          el.dataset.inlineCke !== "active" &&
          !el.id.includes("__prefix__")
        ) {
          CKEDITOR.inline(el, configs[el.dataset.inlineCke])
          el.dataset.inlineCke = "active"
        }
      })
    }

    function addFormsetAddedHandler() {
      django.jQuery(document).on("formset:added", initializeInlineCKE)
    }

    initializeInlineCKE()

    if (window.django) {
      addFormsetAddedHandler()
    }
  })
})()

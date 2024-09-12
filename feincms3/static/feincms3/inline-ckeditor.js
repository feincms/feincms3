/* global CKEDITOR, django */
;(() => {
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

  onReady(() => {
    const configs = {}
    const scripts = document.querySelectorAll("[data-inline-cke-config]")
    for (const script of scripts) {
      configs[script.dataset.inlineCkeId] = JSON.parse(
        script.dataset.inlineCkeConfig,
      )
    }

    function initializeInlineCKE() {
      const textareas = document.querySelectorAll("textarea[data-inline-cke]")
      for (const el of textareas) {
        if (
          el.dataset.inlineCke !== "active" &&
          !el.id.includes("__prefix__")
        ) {
          CKEDITOR.replace(el, configs[el.dataset.inlineCke])
          el.dataset.inlineCke = "active"
        }
      }
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

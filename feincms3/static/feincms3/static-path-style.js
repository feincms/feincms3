document.addEventListener("DOMContentLoaded", () => {
  const staticPathField = document.querySelector("#id_static_path")
  const pathField = document.querySelector("#id_path")

  function update() {
    pathField.classList.toggle("isAuto", !staticPathField.checked)
    pathField.disabled = !staticPathField.checked
  }

  if (!(staticPathField && pathField)) return

  const style = document.createElement("style")
  style.textContent = `
  #id_path {
    transition: 0.2s;
  }
  #id_path.isAuto {
    opacity: 0.5;
    background: var(--selected-bg, #e4e4e4);
  }
  `
  document.head.append(style)

  update()
  staticPathField.addEventListener("change", update)
})

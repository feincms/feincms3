document.addEventListener("DOMContentLoaded", function () {
  const staticPathField = document.querySelector("#id_static_path");
  const pathRow = document.querySelector(".form-row.field-path");

  function assignOpacity() {
    pathRow.style.opacity = staticPathField.checked ? 1 : 0.5;
  }

  if (staticPathField & pathRow) {
    pathRow.style.transition = "opacity 0.2s";

    assignOpacity();
    staticPathField.addEventListener("change", assignOpacity);
  }
});

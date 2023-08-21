document.addEventListener("DOMContentLoaded", () => {
  const root = document.querySelector("#result_list tbody")

  const PK = 0
  const DEPTH = 1
  const CHILDREN = 2
  const TR = 3
  const TOGGLE = 4

  const nodes = {}
  const parents = []

  for (let toggle of root.querySelectorAll(".collapse-toggle")) {
    const node = toggle.closest("tr")
    const pk = +toggle.dataset.pk
    const treeDepth = +toggle.dataset.treeDepth
    const rec =
      (parents[treeDepth] =
      nodes[pk] =
        [pk, treeDepth, [], node, toggle])
    if (treeDepth > 0) {
      parents[treeDepth - 1][CHILDREN].push(rec)
      parents[treeDepth - 1][TOGGLE].classList.remove("collapse-hide")
    }
  }

  function setCollapsed(pk, collapsed) {
    nodes[pk][TOGGLE].classList.toggle("collapsed", collapsed)
    for (let rec of nodes[pk][CHILDREN]) {
      rec[TR].classList.toggle("collapse-hide", collapsed)
      setCollapsed(rec[PK], collapsed)
    }
  }

  function initiallyCollapse(minDepth) {
    for (let rec of Object.values(nodes)) {
      if (rec[DEPTH] >= minDepth && rec[CHILDREN].length) {
        setCollapsed(rec[PK], true)
      }
    }
  }

  root.addEventListener("click", (e) => {
    let collapseToggle = e.target.closest(".collapse-toggle")
    if (collapseToggle) {
      e.preventDefault()
      setCollapsed(
        +collapseToggle.dataset.pk,
        !collapseToggle.classList.contains("collapsed"),
      )
    }
  })

  initiallyCollapse(1)
})

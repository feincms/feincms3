document.addEventListener("DOMContentLoaded", () => {
  const root = document.querySelector("#result_list tbody")

  const PK = 0
  const DEPTH = 1
  const CHILDREN = 2
  const TR = 3
  const TOGGLE = 4

  const nodes = {}
  const parents = []

  for (const toggle of root.querySelectorAll(".collapse-toggle")) {
    const node = toggle.closest("tr")
    const pk = +toggle.dataset.pk
    const treeDepth = +toggle.dataset.treeDepth
    const rec = [pk, treeDepth, [], node, toggle]
    parents[treeDepth] = rec
    nodes[pk] = rec

    if (treeDepth > 0) {
      // parent may be on the previous page if the changelist is paginated.
      const parent = parents[treeDepth - 1]
      if (parent) {
        parent[CHILDREN].push(rec)
        parent[TOGGLE].classList.remove("collapse-hide")
      }
    }
  }

  function setCollapsed(pk, collapsed) {
    nodes[pk][TOGGLE].classList.toggle("collapsed", collapsed)
    for (const rec of nodes[pk][CHILDREN]) {
      rec[TR].classList.toggle("collapse-hide", collapsed)
      setCollapsed(rec[PK], collapsed)
    }
  }

  function initiallyCollapse(minDepth) {
    for (const rec of Object.values(nodes)) {
      if (rec[DEPTH] >= minDepth && rec[CHILDREN].length) {
        setCollapsed(rec[PK], true)
      }
    }
  }

  root.addEventListener("click", (e) => {
    const collapseToggle = e.target.closest(".collapse-toggle")
    if (collapseToggle) {
      e.preventDefault()
      setCollapsed(
        +collapseToggle.dataset.pk,
        !collapseToggle.classList.contains("collapsed"),
      )
    }
  })

  const context = JSON.parse(
    document.querySelector("#feincms3-context").dataset.context,
  )
  initiallyCollapse(context.initiallyCollapseDepth)
})

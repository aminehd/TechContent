const SKIP = new Set(["grid", "queue", "graph"])

export function drawVars(data, step, total) {
  const panel = document.getElementById("vars-panel")
  const entries = Object.entries(data).filter(([k]) => !SKIP.has(k))

  // Inject cursor coords from grid if present
  const cursor = data.grid?.cursor
  if (cursor) entries.push(["pos", `(${cursor[0]},${cursor[1]})`])

  const cards = {}
  panel.querySelectorAll(".var-card").forEach(el => (cards[el.dataset.key] = el))

  const seen = new Set()

  entries.forEach(([key, val]) => {
    seen.add(key)
    const display = Array.isArray(val) ? `[${val.length}]` : String(val ?? "—")
    if (cards[key]) {
      const vEl = cards[key].querySelector(".var-value")
      if (vEl.textContent !== display) {
        vEl.textContent = display
        vEl.classList.remove("flash")
        void vEl.offsetWidth  // reflow to restart animation
        vEl.classList.add("flash")
        cards[key].classList.add("lit")
        setTimeout(() => cards[key].classList.remove("lit"), 500)
      }
    } else {
      panel.appendChild(_makeCard(key, display, false))
    }
  })

  // Step counter card
  seen.add("__step")
  const stepDisplay = `${step} / ${total}`
  if (cards["__step"]) {
    cards["__step"].querySelector(".var-value").textContent = stepDisplay
  } else {
    panel.appendChild(_makeCard("__step", stepDisplay, true, "STEP"))
  }

  // Remove stale cards
  Object.entries(cards).forEach(([k, el]) => { if (!seen.has(k)) el.remove() })
}

function _makeCard(key, display, small, labelOverride) {
  const el = document.createElement("div")
  el.className = "var-card"
  el.dataset.key = key
  el.innerHTML = `
    <span class="var-label">${(labelOverride ?? key).toUpperCase()}</span>
    <span class="var-value${small ? " small" : ""}">${display}</span>`
  return el
}

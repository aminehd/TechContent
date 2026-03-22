export function drawQueue(queue) {
  const c = document.getElementById("queue-items")
  if (!queue?.length) {
    c.innerHTML = '<span class="q-empty">(empty)</span>'
    return
  }
  c.innerHTML = queue.map((item, i) => {
    const label = Array.isArray(item) ? `(${item.join(",")})` : String(item)
    const cls   = i === 0 ? "front" : ""
    const arrow = i < queue.length - 1 ? '<span class="q-arrow">→</span>' : ""
    return `<div class="q-item ${cls}">${label}</div>${arrow}`
  }).join("")
}

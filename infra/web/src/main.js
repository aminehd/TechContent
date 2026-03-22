import * as d3 from "d3"
import { fetchFrames, fetchProblems } from "./api.js"
import { initPixiGrid, drawPixiGrid, destroyPixiGrid } from "./pixi-grid.js"
import { drawGraph, resetGraph } from "./graph.js"
import { buildCodePanel, highlightLine } from "./code.js"
import { drawVars }  from "./vars.js"
import { drawQueue } from "./queue.js"

// ── App state ──────────────────────────────────────────────────────────────
let runs        = []
let snapshots   = []
let sourceLines = []
let snapIdx     = 0

const graphSvg = d3.select("#graph-svg")

// ── Viz router ─────────────────────────────────────────────────────────────
let pixiReady = false

function drawViz(data) {
  if (data.graph) {
    document.getElementById("pixi-container").style.display = "none"
    document.getElementById("graph-svg").style.display      = "block"
    document.getElementById("viz-label").textContent        = "GRAPH"
    drawGraph(graphSvg, data.graph)
  } else {
    document.getElementById("pixi-container").style.display = "block"
    document.getElementById("graph-svg").style.display      = "none"
    document.getElementById("viz-label").textContent        = "GRID"
    if (!pixiReady) {
      initPixiGrid(document.getElementById("pixi-container"))
      pixiReady = true
    }
    drawPixiGrid(data.grid || [], data.queue || [])
  }
}

// ── Show snapshot ──────────────────────────────────────────────────────────
function showSnap(idx) {
  snapIdx = Math.max(0, Math.min(snapshots.length - 1, idx))
  const s = snapshots[snapIdx]

  drawViz(s.data)
  drawQueue(s.data.queue || [])
  drawVars(s.data, snapIdx + 1, snapshots.length)
  highlightLine(s.line)

  document.getElementById("desc-bar").textContent   = s.description || ""
  document.getElementById("step-label").textContent = `${snapIdx + 1} / ${snapshots.length}`
  document.getElementById("btn-prev").disabled = snapIdx === 0
  document.getElementById("btn-next").disabled = snapIdx === snapshots.length - 1
}

// ── Load run ───────────────────────────────────────────────────────────────
function loadRun(idx) {
  resetGraph()
  pixiReady = false
  destroyPixiGrid()
  document.getElementById("vars-panel").innerHTML = ""

  const run   = runs[idx]
  snapshots   = run.snapshots
  sourceLines = run.source_lines || []

  buildCodePanel(sourceLines)

  const first = snapshots.findIndex(s => Object.keys(s.data).length > 0)
  showSnap(first > 0 ? first : 0)
}

// ── Load problem ───────────────────────────────────────────────────────────
function loadProblem(problemId) {
  document.getElementById("prob-title").textContent = "Loading..."

  fetchFrames(problemId)
    .then(data => {
      document.getElementById("prob-title").textContent =
        `${data.problem} · ${data.title}`

      // Badges
      const b1 = document.getElementById("badge-diff")
      const b2 = document.getElementById("badge-pat")
      b1.textContent = data.difficulty ?? "Medium"
      b2.textContent = (data.pattern ?? []).join(" · ")

      runs = data.runs

      // Example selector
      const sel = document.getElementById("example-select")
      sel.innerHTML = ""
      runs.forEach((run, i) => {
        const opt = document.createElement("option")
        opt.value = i
        opt.textContent = `Example ${run.example}`
        sel.appendChild(opt)
      })

      loadRun(0)
    })
    .catch(() => {
      document.getElementById("prob-title").textContent = "API error — is the server running?"
    })
}

// ── Controls ───────────────────────────────────────────────────────────────
document.getElementById("btn-next").addEventListener("click",  () => showSnap(snapIdx + 1))
document.getElementById("btn-prev").addEventListener("click",  () => showSnap(snapIdx - 1))
document.getElementById("btn-reset").addEventListener("click", () => showSnap(0))
document.getElementById("example-select").addEventListener("change", e => loadRun(+e.target.value))

document.getElementById("problem-select").addEventListener("change", e => {
  const id = e.target.value
  const url = new URL(window.location)
  url.searchParams.set("p", id)
  window.history.pushState({}, "", url)
  loadProblem(id)
})

document.addEventListener("keydown", e => {
  if (e.key === "ArrowRight" || e.key === " ") { e.preventDefault(); showSnap(snapIdx + 1) }
  if (e.key === "ArrowLeft")  { e.preventDefault(); showSnap(snapIdx - 1) }
  if (e.key === "Home")       showSnap(0)
  if (e.key === "End")        showSnap(snapshots.length - 1)
})

// ── Init ───────────────────────────────────────────────────────────────────
const problemId = new URL(window.location).searchParams.get("p") ?? "lc200"

fetchProblems()
  .then(data => {
    const sel = document.getElementById("problem-select")
    data.problems.forEach(p => {
      const opt = document.createElement("option")
      opt.value       = p.id
      opt.textContent = `${p.id.toUpperCase()} — ${p.title}`
      opt.selected    = p.id === problemId
      sel.appendChild(opt)
    })
  })

loadProblem(problemId)

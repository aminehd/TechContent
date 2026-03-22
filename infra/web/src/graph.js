import * as d3 from "d3"
import { nodeColor, nodeStroke } from "./colors.js"

let layout = null  // stable positions, computed once per run

export function resetGraph() {
  layout = null
}

export function drawGraph(svg, graphData) {
  if (!layout) {
    _computeLayout(svg, graphData)
  } else {
    _updateStates(graphData)
  }
}

function _computeLayout(svg, graphData) {
  const panel = document.getElementById("viz-panel")
  const W = panel.clientWidth  - 32
  const H = panel.clientHeight - 60

  const nodes = graphData.nodes.map(n => ({ ...n }))
  const links = graphData.edges.map(([s, t]) => ({ source: s, target: t }))

  // Settle force simulation — positions lock in, never recompute
  const sim = d3.forceSimulation(nodes)
    .force("link",   d3.forceLink(links).id(d => d.id).distance(90).strength(0.9))
    .force("charge", d3.forceManyBody().strength(-320))
    .force("center", d3.forceCenter(W / 2, H / 2))
    .stop()

  for (let i = 0; i < 400; i++) sim.tick()
  nodes.forEach(n => {
    n.x = Math.max(36, Math.min(W - 36, n.x))
    n.y = Math.max(36, Math.min(H - 36, n.y))
  })

  layout = { nodes, links }

  svg.attr("width", W).attr("height", H).selectAll("*").remove()

  // Arrow marker
  svg.append("defs").append("marker")
    .attr("id", "arrow").attr("markerWidth", 8).attr("markerHeight", 8)
    .attr("refX", 30).attr("refY", 4).attr("orient", "auto")
    .append("path").attr("d", "M0,0 L0,8 L8,4 z").attr("fill", "#2a3a58")

  // Edges
  svg.append("g").selectAll("line")
    .data(links).enter().append("line")
    .attr("class", "g-edge")
    .attr("marker-end", "url(#arrow)")
    .attr("x1", d => nodes.find(n => n.id === d.source).x)
    .attr("y1", d => nodes.find(n => n.id === d.source).y)
    .attr("x2", d => nodes.find(n => n.id === d.target).x)
    .attr("y2", d => nodes.find(n => n.id === d.target).y)

  // Node groups
  const ng = svg.append("g").selectAll("g")
    .data(nodes).enter().append("g")
    .attr("class", "g-node")
    .attr("data-id", d => d.id)
    .attr("transform", d => `translate(${d.x},${d.y})`)

  ng.append("circle")
    .attr("r", 22)
    .attr("fill",   d => nodeColor(d.state ?? 0))
    .attr("stroke", d => nodeStroke(d.state ?? 0))
    .attr("stroke-width", 2)

  ng.append("text").attr("class", "node-id").text(d => d.id)

  ng.filter(d => d.val !== undefined)
    .append("text").attr("class", "node-val").attr("dy", 36)
    .text(d => `t=${d.val}`)
}

function _updateStates(graphData) {
  const svg = d3.select("#graph-svg")
  const stateById = Object.fromEntries(graphData.nodes.map(n => [n.id, n.state ?? 0]))
  const valById   = Object.fromEntries(graphData.nodes.map(n => [n.id, n.val]))

  svg.selectAll(".g-node").each(function () {
    const id    = +d3.select(this).attr("data-id")
    const state = stateById[id] ?? 0
    d3.select(this).select("circle")
      .transition().duration(220).ease(d3.easeCubicOut)
      .attr("fill",         nodeColor(state))
      .attr("stroke",       nodeStroke(state))
      .attr("stroke-width", state === 0 ? 1.5 : 2.5)
    if (valById[id] !== undefined) {
      d3.select(this).select(".node-val").text(`t=${valById[id]}`)
    }
  })
}

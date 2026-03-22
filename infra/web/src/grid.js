import * as d3 from "d3"
import { cellColor, cellStroke, PALETTE } from "./colors.js"

function ensureDefs(svg) {
  if (!svg.select("defs").empty()) return
  const defs = svg.append("defs")

  // Glow bloom filter — used on island/active cells
  const glow = defs.append("filter")
    .attr("id", "glow")
    .attr("x", "-40%").attr("y", "-40%")
    .attr("width", "180%").attr("height", "180%")
  glow.append("feGaussianBlur").attr("stdDeviation", "4").attr("result", "blur")
  const merge = glow.append("feMerge")
  merge.append("feMergeNode").attr("in", "blur")
  merge.append("feMergeNode").attr("in", "SourceGraphic")

  // Soft shadow for water
  const shadow = defs.append("filter").attr("id", "shadow")
  shadow.append("feDropShadow")
    .attr("dx", 0).attr("dy", 1)
    .attr("stdDeviation", 1)
    .attr("flood-color", "#000").attr("flood-opacity", 0.4)
}

export function drawGrid(svg, gridData) {
  const cells     = gridData?.cells     ?? gridData
  const cursor    = gridData?.cursor    ?? null
  const neighbors = gridData?.neighbors ?? []

  if (!cells?.length) return

  const rows  = cells.length
  const cols  = cells[0].length
  const panel = document.getElementById("viz-panel")
  const panW  = panel.clientWidth  - 32
  const panH  = panel.clientHeight - 60
  const gap   = 6
  const cell  = Math.min(Math.floor(panW / cols), Math.floor(panH / rows), 90) - gap

  svg.attr("width",  cols * (cell + gap) - gap)
     .attr("height", rows * (cell + gap) - gap)

  ensureDefs(svg)

  const rowG = svg.selectAll("g.row").data(cells, (_, i) => i)
  const rowEnter = rowG.enter().append("g").attr("class", "row")
  rowG.merge(rowEnter).attr("transform", (_, i) => `translate(0,${i * (cell + gap)})`)
  rowG.exit().remove()

  svg.selectAll("g.row").each(function (rowData, r) {
    const sel = d3.select(this).selectAll("g.cell").data(rowData, (_, c) => c)

    // ── Enter: build cell structure once ─────────────
    const enter = sel.enter().append("g")
      .attr("class", "cell")
      .attr("data-state", -1)

    // Background rect
    enter.append("rect").attr("class", "bg")
      .attr("rx", 7).attr("ry", 7)
      .attr("width", cell).attr("height", cell)

    // Icon layer
    enter.append("g").attr("class", "icon")

    // Ring overlay (cursor / neighbor)
    enter.append("rect").attr("class", "ring")
      .attr("rx", 7).attr("ry", 7)
      .attr("width", cell).attr("height", cell)
      .attr("fill", "none").attr("stroke", "none")
      .attr("pointer-events", "none")

    const merged = sel.merge(enter)
      .attr("transform", (_, c) => `translate(${c * (cell + gap)},0)`)

    // ── Update: background color + glow ──────────────
    merged.each(function (s, c) {
      const g         = d3.select(this)
      const prevState = +g.attr("data-state")
      const changed   = prevState !== -1 && prevState !== s

      g.attr("data-state", s)

      const bg = g.select("rect.bg")

      // State-change: quick scale bounce via transform on the group
      if (changed) {
        const tx = c * (cell + gap)
        const ty = 0
        const cx = cell / 2, cy = cell / 2
        d3.select(this)
          .attr("transform", `translate(${tx + cx},${ty + cy}) scale(1.18) translate(${-cx},${-cy})`)
          .transition().duration(200).ease(d3.easeBackOut.overshoot(2))
          .attr("transform", `translate(${tx},${ty}) scale(1)`)
      }

      bg.transition().duration(200).ease(d3.easeCubicOut)
        .attr("fill",         cellColor(s))
        .attr("stroke",       cellStroke(s))
        .attr("stroke-width", s === 2 || s >= 10 ? 2 : 1)
        .attr("filter",       s >= 10 || s === 2 ? "url(#glow)" : null)
    })

    // ── Update: icons ─────────────────────────────────
    merged.select("g.icon").each(function (s) {
      const g  = d3.select(this)
      const cx = cell / 2, cy = cell / 2
      g.selectAll("*").remove()

      if (s === 1) {
        const mh = Math.max(6, cell / 5), mw = Math.max(8, cell / 3.5)
        g.append("polygon")
          .attr("points", `${cx},${cy - mh} ${cx - mw},${cy + mh / 2} ${cx + mw},${cy + mh / 2}`)
          .attr("fill", "#3cd460").attr("opacity", 0.7)
      } else if (s === 2) {
        g.append("circle").attr("cx", cx).attr("cy", cy)
          .attr("r", Math.max(4, cell / 7))
          .attr("fill", "#ffe070").attr("filter", "url(#glow)")
      } else if (s >= 10) {
        const col = PALETTE[(s - 10) % PALETTE.length]
        g.append("circle").attr("cx", cx).attr("cy", cy)
          .attr("r", Math.max(5, cell / 6))
          .attr("fill", col).attr("opacity", 0.85)
          .attr("filter", "url(#glow)")
      }
    })

    // ── Update: ring overlay (cursor / neighbor) ──────
    merged.select("rect.ring").each(function (_, c) {
      const isCursor   = cursor    && cursor[0] === r    && cursor[1] === c
      const isNeighbor = neighbors.some(([nr, nc]) => nr === r && nc === c)
      const el = d3.select(this)

      el.classed("ring-cursor",   isCursor)
        .classed("ring-neighbor", isNeighbor && !isCursor)

      el.attr("stroke",       isCursor ? "#00e6e6" : isNeighbor ? "#ffd033" : "none")
        .attr("stroke-width", isCursor ? 3 : isNeighbor ? 2.5 : 0)
    })

    sel.exit().remove()
  })
}

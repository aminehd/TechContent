import * as PIXI from "pixi.js"
import { cellColor, cellStroke, PALETTE } from "./colors.js"

// ── Hex string → PIXI number ──────────────────────
function hx(hex) { return parseInt(hex.replace("#", ""), 16) }

// ── Singleton ─────────────────────────────────────
let app    = null
let gLayer = null   // cell backgrounds + icons
let rLayer = null   // ring overlays (cursor / neighbor)
let cells  = []     // cells[r][c] = { bg, icon, ring, state }
let _cursor    = null
let _prevCursor = null
let _neighbors = []
let _queue     = []     // [[r,c], ...] cells currently in the queue
let _ghosts    = []      // [{r, c, alpha}] fading trail cells
let _phase     = 0
let _cellSize  = 0

// ── Lifecycle ─────────────────────────────────────
export function initPixiGrid(container) {
  if (app) { app.destroy(true, { children: true }); app = null }

  const W = container.clientWidth
  const H = container.clientHeight

  app = new PIXI.Application({
    width:           W,
    height:          H,
    antialias:       false,           // pixel-sharp
    backgroundColor: 0x080a12,
    resolution:      1,
  })

  container.appendChild(app.view)
  app.view.style.display = "block"

  gLayer = new PIXI.Container()
  rLayer = new PIXI.Container()
  app.stage.addChild(gLayer)
  app.stage.addChild(rLayer)

  // Ticker drives cursor flicker, ghost trail, neighbor marching ants
  app.ticker.add(delta => {
    _phase += delta * 0.055
    // Fade ghosts
    _ghosts = _ghosts
      .map(g => ({ ...g, alpha: g.alpha - delta * 0.06 }))
      .filter(g => g.alpha > 0)
    _redrawRings()
  })
}

export function destroyPixiGrid() {
  if (!app) return
  app.destroy(true, { children: true })
  app = null
  cells = []
  _ghosts = []
  _cursor = null
  _prevCursor = null
}

// ── Build cell objects ─────────────────────────────
function _buildCells(rows, cols, cell, gap, offX, offY) {
  gLayer.removeChildren()
  rLayer.removeChildren()
  cells = []

  for (let r = 0; r < rows; r++) {
    cells[r] = []
    for (let c = 0; c < cols; c++) {
      const x = offX + c * (cell + gap)
      const y = offY + r * (cell + gap)

      const bg   = new PIXI.Graphics()
      const icon = new PIXI.Graphics()
      const ring = new PIXI.Graphics()

      const fs = Math.max(7, Math.floor(cell / 4.5))
      const cornerStyle = (color) => new PIXI.TextStyle({
        fontFamily:  '"Courier New", monospace',
        fontSize:    fs,
        fontWeight:  "bold",
        fill:        color,
        dropShadow:      true,
        dropShadowColor: "#000000",
        dropShadowBlur:  2,
        dropShadowDistance: 1,
      })
      const pad = 3

      // Top-left: Q (in queue)
      const labelTL = new PIXI.Text("", new PIXI.TextStyle({
        fontFamily: '"Courier New", monospace',
        fontSize:   Math.max(9, Math.floor(cell / 3.2)),
        fontWeight: "bold",
        fill:       "#000000",
        stroke:     "#000000",
        strokeThickness: 1,
      }))
      labelTL.anchor.set(0, 0)
      labelTL.x = x + pad
      labelTL.y = y + pad

      // Top-right: island number
      const labelTR = new PIXI.Text("", cornerStyle("#ffffff"))
      labelTR.anchor.set(1, 0)
      labelTR.x = x + cell - pad
      labelTR.y = y + pad

      bg.x = icon.x = ring.x = x
      bg.y = icon.y = ring.y = y

      gLayer.addChild(bg)
      gLayer.addChild(icon)
      gLayer.addChild(labelTL)
      gLayer.addChild(labelTR)
      rLayer.addChild(ring)

      cells[r][c] = { bg, icon, ring, labelTL, labelTR, state: -1 }
    }
  }
  _cellSize = cell
}

// ── Draw a single cell ─────────────────────────────
function _drawCell(r, c, s, cell) {
  const { bg, icon, labelTL, labelTR } = cells[r][c]
  const fill   = hx(cellColor(s))
  const stroke = hx(cellStroke(s))
  const sw     = s === 2 || s >= 10 ? 2 : 1

  bg.clear()
  bg.lineStyle(sw, stroke, 1)
  bg.beginFill(fill)
  bg.drawRect(0, 0, cell, cell)
  bg.endFill()

  // Pixel scanline texture on water cells
  if (s === 0) {
    bg.lineStyle(1, 0x0d1f3c, 0.45)
    for (let y = 5; y < cell; y += 6) {
      bg.moveTo(2, y)
      bg.lineTo(cell - 2, y)
    }
  }

  // Pixel corner accent on visited/island cells
  if (s >= 10 || s === 2) {
    const col = s === 2 ? 0xffe070 : hx(PALETTE[(s - 10) % PALETTE.length])
    bg.lineStyle(0)
    bg.beginFill(col, 0.6)
    const dot = 3
    bg.drawRect(0, 0, dot, dot)
    bg.drawRect(cell - dot, 0, dot, dot)
    bg.drawRect(0, cell - dot, dot, dot)
    bg.drawRect(cell - dot, cell - dot, dot, dot)
    bg.endFill()
  }

  const inQueue = _queue.some(([qr, qc]) => qr === r && qc === c)
  labelTL.text = inQueue ? "Q" : ""
  labelTR.text = String(s)

  _drawIcon(icon, s, cell)
}

function _drawIcon(g, s, cell) {
  g.clear()
  const cx = cell / 2, cy = cell / 2

  if (s === 1) {
    // Pixel mountain
    const mh = Math.max(6, cell / 5), mw = Math.max(8, cell / 3.5)
    g.beginFill(0x3cd460, 0.75)
    g.drawPolygon([cx, cy - mh, cx - mw, cy + mh / 2, cx + mw, cy + mh / 2])
    g.endFill()
    // Pixel snow cap
    g.beginFill(0xffffff, 0.35)
    g.drawRect(cx - 2, cy - mh, 4, 4)
    g.endFill()
  } else if (s === 2) {
    // Visiting: pixel cross
    const r = Math.max(4, cell / 7)
    g.beginFill(0xffe070)
    g.drawRect(cx - r, cy - 1, r * 2, 2)
    g.drawRect(cx - 1, cy - r, 2, r * 2)
    g.endFill()
  } else if (s >= 10) {
    const col = hx(PALETTE[(s - 10) % PALETTE.length])
    const r   = Math.max(5, cell / 6)
    g.beginFill(col, 0.9)
    g.drawCircle(cx, cy, r)
    g.endFill()
    // Inner highlight dot
    g.beginFill(0xffffff, 0.3)
    g.drawRect(cx - 2, cy - 2, 3, 3)
    g.endFill()
  }
}

// ── Ring overlays (redrawn every ticker tick) ──────
function _redrawRings() {
  if (!cells.length) return
  const cell = _cellSize

  // Irregular flicker: combine three sine waves at different frequencies
  // gives an electric, unpredictable strobe rather than a smooth pulse
  const t       = _phase
  const flicker = Math.abs(Math.sin(t * 6.1) * Math.cos(t * 3.7) * Math.sin(t * 11.3))
  const cursorAlpha = 0.25 + 0.75 * flicker

  for (let r = 0; r < cells.length; r++) {
    for (let c = 0; c < cells[r].length; c++) {
      const isCursor   = _cursor    && _cursor[0] === r && _cursor[1] === c
      const isNeighbor = _neighbors.some(([nr, nc]) => nr === r && nc === c)
      const ghost      = _ghosts.find(g => g.r === r && g.c === c)
      const { ring }   = cells[r][c]
      ring.clear()

      if (isCursor) {
        // Flickering border
        ring.lineStyle(2, 0x00e6e6, cursorAlpha)
        ring.drawRect(1, 1, cell - 2, cell - 2)

        // Pixel corner brackets
        ring.lineStyle(0)
        ring.beginFill(0x00e6e6, Math.max(0.5, cursorAlpha))
        const d = 3
        ring.drawRect(0, 0, d, d)
        ring.drawRect(cell - d, 0, d, d)
        ring.drawRect(0, cell - d, d, d)
        ring.drawRect(cell - d, cell - d, d, d)
        ring.endFill()

        // ── Medallion ────────────────────────────────
        const MEDAL = 0xdd44ff   // neon purple-pink
        const cx = cell / 2
        const cy = cell / 2
        // px = one "pixel" unit, half = rows from center to tip
        const px   = Math.max(2, Math.floor(cell / 14))
        const half = 4

        // Filled pixelated diamond — row by row rectangles
        ring.lineStyle(0)
        ring.beginFill(MEDAL, cursorAlpha)
        for (let row = -half; row <= half; row++) {
          const w = (half - Math.abs(row)) * 2 + 1   // width in px units
          ring.drawRect(
            Math.floor(cx - (w * px) / 2),
            Math.floor(cy + row * px - px / 2),
            w * px,
            px
          )
        }
        ring.endFill()

        // Top-left highlight pixel for gem sparkle
        ring.beginFill(0xffffff, cursorAlpha * 0.9)
        ring.drawRect(Math.floor(cx - px), Math.floor(cy - px * 2), px, px)
        ring.endFill()

        // Bright center pixel
        ring.beginFill(0xffffff, Math.min(1, cursorAlpha + 0.15))
        ring.drawRect(Math.floor(cx - px / 2), Math.floor(cy - px / 2), px, px)
        ring.endFill()
      } else if (ghost) {
        // Fading ghost trail — shrinks inward as it fades
        const inset = Math.floor((1 - ghost.alpha) * 4)
        ring.lineStyle(1.5, 0x00e6e6, ghost.alpha * 0.6)
        ring.drawRect(inset, inset, cell - inset * 2, cell - inset * 2)
        // Corner dots fade too
        ring.lineStyle(0)
        ring.beginFill(0x00e6e6, ghost.alpha * 0.4)
        const d = 2
        ring.drawRect(inset, inset, d, d)
        ring.drawRect(cell - inset - d, inset, d, d)
        ring.drawRect(inset, cell - inset - d, d, d)
        ring.drawRect(cell - inset - d, cell - inset - d, d, d)
        ring.endFill()
      } else if (isNeighbor) {
        // Marching ants dashed border
        _drawDashedRect(ring, 1, 1, cell - 2, cell - 2, 0xffd033, 0.9, _phase)
      }
    }
  }
}

function _drawDashedRect(g, x, y, w, h, color, alpha, phase) {
  const dash = 5, gap = 4
  g.lineStyle(2.5, color, alpha)
  _dashLine(g, x,     y,     x + w, y,     dash, gap, phase)
  _dashLine(g, x + w, y,     x + w, y + h, dash, gap, phase + w)
  _dashLine(g, x + w, y + h, x,     y + h, dash, gap, phase + w + h)
  _dashLine(g, x,     y + h, x,     y,     dash, gap, phase + 2 * w + h)
}

function _dashLine(g, x1, y1, x2, y2, dashLen, gapLen, phase) {
  const dx = x2 - x1, dy = y2 - y1
  const len = Math.sqrt(dx * dx + dy * dy)
  const nx = dx / len, ny = dy / len
  const period = dashLen + gapLen
  const offset = ((phase * 28) % period + period) % period
  let pos = -offset

  while (pos < len) {
    const s = Math.max(0, pos)
    const e = Math.min(len, pos + dashLen)
    if (e > s) {
      g.moveTo(x1 + nx * s, y1 + ny * s)
      g.lineTo(x1 + nx * e, y1 + ny * e)
    }
    pos += period
  }
}

// ── Public: draw ───────────────────────────────────
export function drawPixiGrid(gridData, queueData) {
  if (!app) return

  const gridCells  = gridData?.cells     ?? gridData
  const newCursor  = gridData?.cursor    ?? null
  _neighbors       = gridData?.neighbors ?? []
  _queue           = queueData ?? []

  // Spawn ghost at old cursor position when cursor moves
  if (_cursor && newCursor &&
      (_cursor[0] !== newCursor[0] || _cursor[1] !== newCursor[1])) {
    _ghosts.push({ r: _cursor[0], c: _cursor[1], alpha: 0.7 })
  }
  _prevCursor = _cursor
  _cursor     = newCursor

  if (!gridCells?.length) return

  const rows = gridCells.length
  const cols = gridCells[0].length
  const W    = app.screen.width
  const H    = app.screen.height
  const gap  = 5
  const cell = Math.min(Math.floor((W * 0.78) / cols), Math.floor((H * 0.78) / rows), 62) - gap
  const offX = Math.floor((W - (cols * (cell + gap) - gap)) / 2)
  const offY = Math.floor((H - (rows * (cell + gap) - gap)) / 2)

  if (cells.length !== rows || (cells[0]?.length ?? 0) !== cols) {
    _buildCells(rows, cols, cell, gap, offX, offY)
  }

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const s = gridCells[r][c]
      cells[r][c].state = s
      _drawCell(r, c, s, cell)
    }
  }
}

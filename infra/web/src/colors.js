export const PALETTE = ["#32c8ff", "#ff8c1a", "#b450ff", "#00e6b4", "#ff5080", "#ffd033"]

export function cellColor(s) {
  if (s === 0) return "#0a1428"   // water
  if (s === 1) return "#28b44a"   // land
  if (s === 2) return "#00c8a0"   // visited
  return "#0a1428"
}

export function cellStroke(s) {
  if (s === 0) return "#142040"
  if (s === 1) return "#3cd460"
  if (s === 2) return "#00e6b8"
  return "#142040"
}

const NODE_STATE = { 0: "#0d1a30", 1: "#ffd033", 2: "#00e6e6", 3: "#46dc6e" }

export function nodeColor(state) {
  if (state >= 10) return PALETTE[(state - 10) % PALETTE.length]
  return NODE_STATE[state] ?? NODE_STATE[0]
}

export function nodeStroke(state) {
  if (state === 0) return "#1e2a50"
  return nodeColor(state)
}

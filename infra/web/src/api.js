const BASE = "/api"

export async function fetchFrames(problemId) {
  const res = await fetch(`${BASE}/problems/${problemId}/frames`)
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`)
  return res.json()
}

export async function fetchProblems() {
  const res = await fetch(`${BASE}/problems`)
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`)
  return res.json()
}

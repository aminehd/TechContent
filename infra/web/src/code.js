const KW  = new Set(["def","return","if","else","elif","for","while","in","not","and","or","True","False","None","import","from","as","class","with","yield","nonlocal"])
const BLT = new Set(["len","range","print","int","str","list","dict","set","min","max","enumerate","zip","deque"])
const TOK = /(\s+|#[^\n]*|"[^"]*"|'[^']*'|\b\d+\b|[+\-*/=<>!&|%^~]+|\w+|.)/g

function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
}

function syntaxHL(text) {
  return text.replace(TOK, t => {
    if (!t.trim()) return t
    if (t.startsWith("#"))                      return `<span class="cm">${esc(t)}</span>`
    if (t.startsWith('"') || t.startsWith("'")) return `<span class="st">${esc(t)}</span>`
    if (KW.has(t))                              return `<span class="kw">${esc(t)}</span>`
    if (BLT.has(t))                             return `<span class="bn">${esc(t)}</span>`
    if (/^\d+$/.test(t))                        return `<span class="nm">${esc(t)}</span>`
    if (/^[+\-*/=<>!&|%^~]+$/.test(t))         return `<span class="op">${esc(t)}</span>`
    return esc(t)
  })
}

export function buildCodePanel(lines) {
  document.getElementById("code-scroll").innerHTML = lines.map((line, i) => `
    <div class="code-line" id="cl-${i}">
      <span class="ln" id="ln-${i}">${i + 1}</span>
      <span class="ptr" id="ptr-${i}"></span>
      <span class="code-text">${syntaxHL(line)}</span>
    </div>`).join("")
}

export function highlightLine(line) {
  document.querySelectorAll(".code-line").forEach(el => el.classList.remove("active"))
  document.querySelectorAll(".ln").forEach(el => el.classList.remove("active-ln"))
  document.querySelectorAll(".ptr").forEach(el => (el.textContent = ""))

  const el = document.getElementById(`cl-${line}`)
  if (!el) return
  el.classList.add("active")
  document.getElementById(`ln-${line}`).classList.add("active-ln")
  document.getElementById(`ptr-${line}`).textContent = "►"
  el.scrollIntoView({ block: "nearest", behavior: "smooth" })
}

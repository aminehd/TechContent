"""
lc30_viz.py  –  Sliding-window visualiser for
  LC 30 · Substring with Concatenation of All Words   (Hard)

Run:
    python3 lc30_viz.py                        # auto-play, 1 s/frame
    python3 lc30_viz.py --speed 0.4            # faster
    python3 lc30_viz.py --interactive          # press Enter to step
    python3 lc30_viz.py --example 2            # different test case

──────────────────────────────────────────────────────────────────────────────

Algorithm: Sliding Window with word-frequency map   O(n)
──────────────────────────────────────────────────────────────────────────────
1. Build target = Counter(words).
2. All words share the same length (word_len).
   A valid concatenation window is exactly word_len * n_words characters long.
3. There are word_len possible "phases" for where a word boundary can start.
   Run one independent sliding window per offset k in [0, word_len).
4. For each offset, advance `right` by word_len at a time:
     • if the word at `right` is in target:
         – add it to curr_count, increment words_used
         – while a word is over-counted: evict from `left` (shrink)
         – if words_used == n_words: MATCH at `left`, then slide `left`
     • else: unknown word → clear window, jump `left` past `right`
"""
import os, sys, re, shutil, time, argparse, linecache, inspect
from collections import Counter

# ── ANSI colour helpers ────────────────────────────────────────────────────
R   = "\033[0m";  B   = "\033[1m";  DIM = "\033[2m"
CG  = "\033[92m"; CY  = "\033[93m"; CC  = "\033[96m"
CR  = "\033[91m"; CGR = "\033[90m"; CW  = "\033[97m"
BGG = "\033[42m"; BGY = "\033[43m"; BGR = "\033[41m"; BGB = "\033[44m"

def vlen(s: str) -> int:
    return len(re.sub(r"\033\[[0-9;]*m", "", s))

def clr():
    os.system("cls" if os.name == "nt" else "clear")

def tw() -> int:
    return shutil.get_terminal_size(fallback=(100, 30)).columns


# ══════════════════════════════════════════════════════════════════════════════
#  Pure solution  (no viz hooks – clean to read)
# ══════════════════════════════════════════════════════════════════════════════

def findSubstring(s: str, words: list) -> list:
    if not s or not words:
        return []
    word_len = len(words[0])
    n_words  = len(words)
    n        = len(s)
    target   = Counter(words)
    result   = []

    for k in range(word_len):
        left       = k
        curr_count = Counter()
        words_used = 0

        for right in range(k, n - word_len + 1, word_len):
            word = s[right : right + word_len]

            if word in target:
                curr_count[word] += 1
                words_used       += 1

                while curr_count[word] > target[word]:
                    lw = s[left : left + word_len]
                    curr_count[lw] -= 1
                    words_used     -= 1
                    left           += word_len

                if words_used == n_words:
                    result.append(left)
                    lw = s[left : left + word_len]
                    curr_count[lw] -= 1
                    words_used     -= 1
                    left           += word_len
            else:
                curr_count.clear()
                words_used = 0
                left       = right + word_len

    return result


# ══════════════════════════════════════════════════════════════════════════════
#  Renderer
# ══════════════════════════════════════════════════════════════════════════════

def _render_source(
    filename: str,
    current_line: int,
    func_start: int,
    func_end: int,
    width: int,
) -> None:
    """Show func_start..func_end with ► on current_line."""
    short = os.path.basename(filename)
    print(f"  {DIM}Source: {short}{R}")
    print(f"  {CGR}{'─'*(width-4)}{R}")

    for ln in range(func_start, func_end + 1):
        raw = linecache.getline(filename, ln)
        if not raw:
            continue
        text = raw.rstrip()
        if ln == current_line:
            gutter = f"{B}{CG}►{R}"
            code   = f"{B}{CW}{text}{R}"
        else:
            gutter = " "
            code   = f"{DIM}{text}{R}"
        print(f"  {gutter} {CGR}{ln:4}{R} │ {code}")

    print(f"  {CGR}{'─'*(width-4)}{R}\n")


def _render(
    s, words, word_len, n_words, target, result,
    k, left, right, curr_word, curr_count, words_used,
    phase, msg, speed, interactive,
    source_file=None, source_line=None, func_start=None, func_end=None,
):
    clr()
    W = tw()

    # ── header ──────────────────────────────────────────────────────────────
    print(f"{B}{'━'*W}{R}")
    print(f"  {B}LC 30 · Substring with Concatenation of All Words{R}"
          f"   {CGR}(Hard){R}")
    print(f"{B}{'━'*W}{R}\n")
    wds_str = "[" + ", ".join(f'"{w}"' for w in words) + "]"
    print(f"  {DIM}words{R} = {CC}{wds_str}{R}   "
          f"{DIM}word_len{R} = {word_len}   "
          f"{DIM}n_words{R} = {n_words}\n")
    print(f"  {DIM}s{R} = {CW}\"{s}\"{R}\n")

    # ── source code panel ─────────────────────────────────────────────────────
    if source_file and source_line and func_start and func_end:
        _render_source(source_file, source_line, func_start, func_end, W)


    # ── string grid  ─────────────────────────────────────────────────────────
    n  = len(s)
    cw = word_len + 2          # cell width (1 space padding each side)

    chunk_starts = list(range(k, n - word_len + 1, word_len))
    nc           = len(chunk_starts)

    if k > 0:
        print(f"  {CGR}prefix \"{s[:k]}\" (first {k} char{'s' if k>1 else ''}) skipped for offset k={k}{R}\n")

    if nc > 0:
        # ── colour each cell ────────────────────────────────────────────────
        def cell_color(cs: int) -> str:
            if phase in ("done", "new_offset"):
                return CGR
            in_win    = (left <= cs < right)   # accumulated before current word
            is_right  = (cs == right)
            is_left   = (cs == left)

            if phase == "match":
                return (B + BGG) if (left <= cs <= right) else (DIM + CGR)

            if phase == "examine":
                if is_right:  return B + BGY    # yellow bg: word under inspection
                if in_win:    return B + CC     # cyan: already in valid window
                return DIM + CGR

            if phase == "shrink":
                if is_left:   return B + BGR    # red bg: word being evicted
                if is_right:  return B + CY     # yellow: over-count culprit
                if in_win:    return B + CY     # yellow: window being adjusted
                return DIM + CGR

            if phase == "invalid":
                if is_right:  return B + CR     # red text: bad word
                if in_win:    return B + CC     # cyan: still counted (about to clear)
                return DIM + CGR

            return DIM + CGR

        # ── box rows ────────────────────────────────────────────────────────
        top = "  ┌" + "┬".join(["─" * cw] * nc) + "┐"
        bot = "  └" + "┴".join(["─" * cw] * nc) + "┘"

        val_parts = []
        for cs in chunk_starts:
            word_str = s[cs : cs + word_len]
            color    = cell_color(cs)
            lp       = (cw - word_len) // 2
            rp       = cw - word_len - lp
            val_parts.append(" " * lp + f"{color}{word_str}{R}" + " " * rp)

        idx_parts = [f"{cs:^{cw}}" for cs in chunk_starts]
        print(top)
        print("  │" + "│".join(val_parts) + "│")
        print(bot)
        print("   " + " ".join(idx_parts))

        # ── L / R pointer labels ─────────────────────────────────────────────
        if phase not in ("done", "new_offset"):
            ptr = [" " * cw for _ in chunk_starts]
            for ci, cs in enumerate(chunk_starts):
                is_l = (cs == left)
                is_r = (cs == right)
                if is_l and is_r:
                    ptr[ci] = f"{B}{CY}{'L=R':^{cw}}{R}"
                elif is_l and words_used > 0:
                    ptr[ci] = f"{B}{CG}{'L':^{cw}}{R}"
                elif is_r:
                    ptr[ci] = f"{B}{CY}{'R':^{cw}}{R}"
            print("   " + " ".join(ptr))

        print()

    # ── stats bar ────────────────────────────────────────────────────────────
    phase_color = {"match": CG, "invalid": CR, "shrink": CY,
                   "examine": CY, "new_offset": CGR, "done": CG}.get(phase, CGR)
    print(
        f"  {CGR}k{R}={B}{k}{R}   "
        f"{CGR}left{R}={B}{left}{R}   "
        f"{CGR}right{R}={B}{right}{R}   "
        f"words_used={B}{words_used}{R}/{n_words}   "
        f"phase={phase_color}{phase}{R}"
    )
    print()

    # ── word-count comparison table ──────────────────────────────────────────
    all_wds = sorted(target.keys())

    tgt_cells = "   ".join(
        f"{CC}{w}{R} ×{target[w]}" for w in all_wds
    )

    def cur_cell(w):
        cnt   = curr_count.get(w, 0)
        t_cnt = target[w]
        if   cnt > t_cnt:           c = CR
        elif cnt == t_cnt and cnt:  c = CG
        elif cnt:                   c = CY
        else:                       c = CGR
        return f"{CC}{w}{R} ×{c}{B}{cnt}{R}"

    cur_cells = "   ".join(cur_cell(w) for w in all_wds)
    status    = (f"  {B}{CG}✓ FULL ({words_used}/{n_words}){R}"
                 if words_used == n_words
                 else f"  {CGR}({words_used}/{n_words}){R}")

    print(f"  {DIM}Target:{R}  {tgt_cells}")
    print(f"  {DIM}Window:{R}  {cur_cells}{status}")
    print()

    # ── action banner ─────────────────────────────────────────────────────────
    if   phase == "match":
        banner = f"  {B}{BGG}  ✓  {msg}  {R}"
    elif phase == "invalid":
        banner = f"  {B}{BGR}  ✗  {msg}  {R}"
    elif phase == "shrink":
        banner = f"  {B}{BGY}  ↑  {msg}  {R}"
    elif phase == "done":
        banner = f"  {B}{BGG}  ★  {msg}  {R}"
    else:
        banner = f"  {DIM}▸  {msg}{R}"
    print(banner)
    print()

    # ── result accumulator ───────────────────────────────────────────────────
    res_str = str(result) if result else "[ ]"
    rc      = CG if result else CGR
    print(f"  {B}Result so far:{R}  {rc}{B}{res_str}{R}")

    print(f"\n{CGR}{'─'*W}{R}")

    # ── advance ──────────────────────────────────────────────────────────────
    if interactive:
        try:
            input(f"  {DIM}[Enter] next frame  [Ctrl-C] quit{R}  ")
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
    else:
        time.sleep(speed)


# ══════════════════════════════════════════════════════════════════════════════
#  Solution with visualisation hooks
# ══════════════════════════════════════════════════════════════════════════════

def findSubstring_viz(
    s: str,
    words: list,
    speed: float = 1.0,
    interactive: bool = False,
) -> list:
    if not s or not words:
        return []
    word_len = len(words[0])
    n_words  = len(words)
    n        = len(s)
    target   = Counter(words)
    result   = []

    # Detect exact line range of this function once, up front
    src_lines, func_start = inspect.getsourcelines(findSubstring_viz)
    func_end = func_start + len(src_lines) - 1

    def snap(k, left, right, curr_word, curr_count, words_used, phase, msg):
        caller = inspect.currentframe().f_back
        _render(s, words, word_len, n_words, target, result,
                k, left, right, curr_word, Counter(curr_count),
                words_used, phase, msg, speed, interactive,
                source_file=caller.f_code.co_filename,
                source_line=caller.f_lineno,
                func_start=func_start,
                func_end=func_end)

    for k in range(word_len):
        left       = k
        curr_count = Counter()
        words_used = 0

        snap(k, left, k, "", Counter(), 0, "new_offset",
             f"Offset k={k}  →  check words at positions "
             f"{k}, {k+word_len}, {k+2*word_len}, …")

        for right in range(k, n - word_len + 1, word_len):
            word = s[right : right + word_len]

            snap(k, left, right, word, curr_count, words_used, "examine",
                 f"Reading  '{word}'  at pos {right}")

            if word in target:
                curr_count[word] += 1
                words_used       += 1

                # ── shrink while any word is over-represented ────────────
                while curr_count[word] > target[word]:
                    lw = s[left : left + word_len]
                    snap(k, left, right, word, curr_count, words_used, "shrink",
                         f"'{word}' count {curr_count[word]} > target {target[word]}"
                         f"  →  evict '{lw}' from left (pos {left})")
                    curr_count[lw] -= 1
                    words_used     -= 1
                    left           += word_len

                # ── match! ───────────────────────────────────────────────
                if words_used == n_words:
                    result.append(left)
                    snap(k, left, right, word, curr_count, words_used, "match",
                         f"MATCH  →  result.append({left})")
                    lw = s[left : left + word_len]
                    curr_count[lw] -= 1
                    words_used     -= 1
                    left           += word_len

            else:
                # ── unknown word → reset ─────────────────────────────────
                snap(k, left, right, word, curr_count, words_used, "invalid",
                     f"'{word}' not in words  →  clear window, jump left to {right+word_len}")
                curr_count.clear()
                words_used = 0
                left       = right + word_len

    snap(0, 0, 0, "", Counter(), 0, "done",
         f"Finished!   Result = {result}")

    return result


# ══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════════════════

EXAMPLES = [
    # (s, words, expected)
    ("barfoothefoobarman",        ["foo", "bar"],              [0, 9]),
    ("wordgoodgoodgoodbestword",  ["word", "good", "best", "word"], []),
    ("barfoofoobarthefoobarman",  ["bar", "foo", "the"],       [6, 9, 12]),
    ("aaa",                       ["a", "a"],                  [0, 1]),
]

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="LC 30 Visualiser")
    ap.add_argument("--speed",       type=float, default=1.0,
                    help="Seconds per frame in auto mode (default 1.0)")
    ap.add_argument("--interactive", action="store_true",
                    help="Press Enter to advance each frame")
    ap.add_argument("--example",     type=int,   default=1,
                    choices=[1, 2, 3, 4],
                    help="Which example to run (1-4, default 1)")
    args = ap.parse_args()

    s, words, expected = EXAMPLES[args.example - 1]

    print(f"\n  Running example {args.example}:")
    print(f"    s     = \"{s}\"")
    print(f"    words = {words}")
    print(f"    expected output: {expected}\n")
    time.sleep(1.5)

    result = findSubstring_viz(
        s, words,
        speed=args.speed,
        interactive=args.interactive,
    )

    clr()
    print(f"\n  {'━'*50}")
    print(f"  Final result : {CG}{B}{result}{R}")
    print(f"  Expected     : {expected}")
    ok = sorted(result) == sorted(expected)
    print(f"  Correct?     : {(CG+'✓ YES') if ok else (CR+'✗ NO')}{R}")
    print(f"  {'━'*50}\n")

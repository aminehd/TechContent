"""
renderer.py  –  ANSI terminal rendering of FrameSnapshots.

Everything is zero-dependency (just stdlib).
Rendering pipeline per frame:
  1. Header bar          (full width)
  2. Two-column body:
       LEFT  (~44%)  Source context  (± context_lines around current line)
       RIGHT (~56%)  Arrays  →  Variables  →  Call stack
  3. Footer              (full width)
"""
import os
import re
import shutil
import linecache
from typing import Dict, List, Optional, Tuple, Any

from .tracer import FrameSnapshot
from .inspector import classify, find_array_pointers

# ---------------------------------------------------------------------------
# ANSI helpers
# ---------------------------------------------------------------------------

R   = "\033[0m"
B   = "\033[1m"        # bold
DIM = "\033[2m"
U   = "\033[4m"        # underline

C_RED        = "\033[91m"
C_GREEN      = "\033[92m"
C_YELLOW     = "\033[93m"
C_BLUE       = "\033[94m"
C_CYAN       = "\033[96m"
C_GRAY       = "\033[90m"
C_WHITE      = "\033[97m"
C_NEON_GREEN = "\033[38;5;118m"  # vivid neon / lime green for source code
C_FLASH      = "\033[38;5;213m"  # bright pink/magenta — "this just changed"

BG_RED    = "\033[41m"
BG_GREEN  = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE   = "\033[44m"

# Colours cycling for pointer arrows / highlighted cells
PTR_COLORS = [C_CYAN, C_GREEN, C_YELLOW, C_RED, "\033[95m", C_BLUE]


def _vlen(s: str) -> int:
    """Visible length of a string (strips ANSI escape codes)."""
    return len(re.sub(r"\033\[[0-9;]*m", "", s))


def _term_width() -> int:
    return shutil.get_terminal_size(fallback=(100, 30)).columns


def _clear():
    os.system("cls" if os.name == "nt" else "clear")


def _hr(width: int, char: str = "─") -> str:
    return char * width


# ---------------------------------------------------------------------------
# Array widget
# ---------------------------------------------------------------------------

def _render_array(
    name: str,
    arr: list,
    pointers: Dict[str, int],   # {ptr_name: index_value}
    max_width: int,
    prev_arr: Optional[list] = None,   # previous frame's array for diff flash
) -> List[str]:
    """
    Return lines like:

      nums:
      ┌─────┬─────┬─────┬─────┐
      │  2  │  7  │ 11  │ 15  │
      └─────┴─────┴─────┴─────┘
        0     1     2     3
        ↑           ↑
        i           j
    """
    if not arr:
        return [f"  {B}{C_CYAN}{name}{R} = []"]

    # ---- cell width -------------------------------------------------------
    max_val_len = max(_vlen(str(v)) for v in arr)
    cell_w = max(max_val_len + 2, 4)   # at least 4 wide (1 padding each side)

    # ---- truncate if too wide ---------------------------------------------
    # Maximum cells that fit in max_width
    max_cells = max(4, (max_width - 4) // (cell_w + 1))
    n_orig = len(arr)

    if n_orig <= max_cells:
        display_idxs = list(range(n_orig))
    else:
        # Show cells around pointer positions + leading/trailing cells
        active = {v for v in pointers.values()
                  if isinstance(v, int) and 0 <= v < n_orig}
        wing = max(1, (max_cells - len(active) - 1) // 2)
        keep: set = set()
        for a in active:
            for k in range(max(0, a - wing), min(n_orig, a + wing + 1)):
                keep.add(k)
        # Fill with leading indices if room
        for k in range(n_orig):
            if len(keep) >= max_cells:
                break
            keep.add(k)
        display_idxs = sorted(keep)[:max_cells]

    display_arr = [arr[i] for i in display_idxs]
    n_disp = len(display_arr)

    # ---- assign a colour to each pointer ----------------------------------
    ptr_color: Dict[str, str] = {}
    for pi, ptr_name in enumerate(sorted(pointers)):
        ptr_color[ptr_name] = PTR_COLORS[pi % len(PTR_COLORS)]

    # ---- which display positions are highlighted? -------------------------
    # di (display index) → colour
    cell_highlight: Dict[int, str] = {}
    for ptr_name, ptr_val in pointers.items():
        if isinstance(ptr_val, int) and ptr_val in display_idxs:
            di = display_idxs.index(ptr_val)
            if di not in cell_highlight:
                cell_highlight[di] = ptr_color[ptr_name]

    # ---- build box rows ---------------------------------------------------
    top_row = "┌" + "┬".join(["─" * cell_w] * n_disp) + "┐"
    bot_row = "└" + "┴".join(["─" * cell_w] * n_disp) + "┘"

    val_parts: List[str] = []
    for di, v in enumerate(display_arr):
        real_idx = display_idxs[di]
        cell = str(v).center(cell_w)
        value_changed = (
            prev_arr is not None
            and real_idx < len(prev_arr)
            and prev_arr[real_idx] != v
        )
        if value_changed:
            cell = f"{B}{C_FLASH}{cell}{R}"   # pink flash — value changed
        elif di in cell_highlight:
            col = cell_highlight[di]
            cell = f"{B}{col}{cell}{R}"
        val_parts.append(cell)
    val_row = "│" + "│".join(val_parts) + "│"

    # index labels row (plain, for alignment)
    idx_parts = [str(i).center(cell_w) for i in display_idxs]
    idx_row = " " + " ".join(idx_parts) + " "

    # ---- arrow / name rows ------------------------------------------------
    row_w = n_disp * (cell_w + 1) + 1   # total visible width of box

    def cell_center(di: int) -> int:
        return 1 + di * (cell_w + 1) + cell_w // 2

    # ptr_groups[di] = [(ptr_name, colour), ...]
    ptr_groups: Dict[int, List[Tuple[str, str]]] = {}
    for ptr_name, ptr_val in pointers.items():
        if isinstance(ptr_val, int) and ptr_val in display_idxs:
            di = display_idxs.index(ptr_val)
            ptr_groups.setdefault(di, []).append((ptr_name, ptr_color[ptr_name]))

    lines: List[str] = [
        f"  {B}{C_CYAN}{name}{R}:",
        f"  {top_row}",
        f"  {val_row}",
        f"  {bot_row}",
        f"  {idx_row}",
    ]

    if ptr_groups:
        arrow_chars = [" "] * row_w
        arrow_clrs:  Dict[int, str] = {}
        name_chars  = [" "] * row_w
        name_clrs:   Dict[int, str] = {}

        for di, ptrs in ptr_groups.items():
            c = cell_center(di)
            combined = "/".join(p[0] for p in ptrs)
            color    = ptrs[0][1]
            if c < row_w:
                arrow_chars[c] = "↑"
                arrow_clrs[c]  = color
            start = c - len(combined) // 2
            for k, ch in enumerate(combined):
                pos = start + k
                if 0 <= pos < row_w:
                    name_chars[pos] = ch
                    name_clrs[pos]  = color

        def _colorize(chars, clrs):
            out = []
            for p, ch in enumerate(chars):
                if p in clrs:
                    out.append(f"{B}{clrs[p]}{ch}{R}")
                else:
                    out.append(ch)
            return "".join(out)

        lines.append(f"  {_colorize(arrow_chars, arrow_clrs)}")
        lines.append(f"  {_colorize(name_chars,  name_clrs)}")

    return lines


# ---------------------------------------------------------------------------
# Source context widget
# ---------------------------------------------------------------------------

def _render_source(
    filename: str,
    current_line: int,
    context: int = 3,
    width: int = 80,
) -> List[str]:
    """Show ±context lines of source with the current line highlighted."""
    short_name = os.path.basename(filename)
    lines: List[str] = [
        f"  {DIM}Source: {short_name}{R}",
        f"  {C_GRAY}{_hr(width - 4)}{R}",
    ]

    start = max(1, current_line - context)
    end   = current_line + context + 1

    # gutter overhead: "  " + marker(1) + " " + lineno(4) + " │ " = 11 visible chars
    _GUTTER = 11
    max_code = max(10, width - _GUTTER)

    for ln in range(start, end):
        raw = linecache.getline(filename, ln)
        if not raw:
            continue
        text = raw.rstrip()
        # Truncate long lines so they never overflow the left column
        if len(text) > max_code:
            text = text[:max_code - 1] + "…"
        is_current = (ln == current_line)
        gutter = f"{B}{C_GREEN}►{R}" if is_current else " "
        ln_str = f"{C_GRAY}{ln:4}{R}"
        if is_current:
            code = f"{B}{C_WHITE}{text}{R}"
        else:
            code = f"{C_NEON_GREEN}{text}{R}"
        lines.append(f"  {gutter} {ln_str} │ {code}")

    lines.append(f"  {C_GRAY}{_hr(width - 4)}{R}")
    return lines


# ---------------------------------------------------------------------------
# Variables panel
# ---------------------------------------------------------------------------

def _render_variables(
    pointers:   Dict[str, int],
    scalars:    Dict[str, Any],
    other:      Dict[str, Any],
    width:      int = 80,
    changed:    Optional[set] = None,     # names that differ from prev frame
    prev_vals:  Optional[dict] = None,    # prev frame locals for delta calc
) -> List[str]:
    lines: List[str] = [f"  {B}Variables{R}"]
    changed   = changed   or set()
    prev_vals = prev_vals or {}

    simple = {**pointers, **scalars}
    if not simple and not other:
        lines.append(f"  {DIM}(none){R}")
        return lines

    for name, val in simple.items():
        if name in changed:
            # Flash: bright pink name + value
            marker   = f"{B}{C_FLASH}▶ {R}"
            name_col = f"{B}{C_FLASH}{name}{R}"
            val_col  = f"{B}{C_FLASH}{val}{R}"
            # Numeric delta  (+3) / (-1)
            delta_str = ""
            prev = prev_vals.get(name)
            if isinstance(val, (int, float)) and isinstance(prev, (int, float)):
                d = val - prev
                delta_str = f"  {C_GRAY}({'+' if d >= 0 else ''}{d}){R}"
            lines.append(f"  {marker}{name_col}  =  {val_col}{delta_str}")
        else:
            lines.append(f"  {DIM}  {R}{B}{C_YELLOW}{name}{R}  =  {C_WHITE}{val}{R}")

    for name, val in other.items():
        short = repr(val)
        cap = max(20, width - len(name) - 10)
        if len(short) > cap:
            short = short[:cap - 1] + "…"
        if name in changed:
            lines.append(f"  {B}{C_FLASH}▶ {name}{R}  =  {C_FLASH}{short}{R}")
        else:
            lines.append(f"  {DIM}  {R}{B}{C_YELLOW}{name}{R}  =  {C_GRAY}{short}{R}")

    return lines


# ---------------------------------------------------------------------------
# Call-stack panel
# ---------------------------------------------------------------------------

def _render_call_stack(
    call_stack: List[Tuple[str, str, int]],
    current_func: str,
    current_line: int,
) -> List[str]:
    lines: List[str] = [f"  {B}Call Stack{R}"]
    if not call_stack:
        lines.append(f"  {DIM}(top level){R}")
        return lines
    for depth, (fn, _fname, ln) in enumerate(call_stack):
        is_current = (depth == len(call_stack) - 1)
        marker = f"{B}{C_GREEN}▸{R}" if is_current else f"  "
        fn_col = f"{B}{C_CYAN}{fn}{R}" if is_current else f"{DIM}{fn}{R}"
        lines.append(f"  {marker} [{depth}] {fn_col}  line {ln}")
    return lines


# ---------------------------------------------------------------------------
# Two-column merge helper
# ---------------------------------------------------------------------------

def _merge_cols(
    left: List[str],
    right: List[str],
    left_w: int,
    sep: str = "  │  ",
) -> List[str]:
    """
    Zip two lists of lines side-by-side.
    Left column is padded to exactly left_w visible characters.
    """
    rows = max(len(left), len(right))
    out: List[str] = []
    for i in range(rows):
        l = left[i]  if i < len(left)  else ""
        r = right[i] if i < len(right) else ""
        pad = max(0, left_w - _vlen(l))
        out.append(l + " " * pad + sep + r)
    return out


# ---------------------------------------------------------------------------
# Main render entry point
# ---------------------------------------------------------------------------

def render_frame(
    snap: FrameSnapshot,
    frame_idx: int,
    total_frames: int,
    events_filter: Optional[set] = None,
    context_lines: int = 3,
    footer_hint: str = "[Enter] next  [b] back  [q] quit  [N] jump to frame",
    prev_snap: Optional["FrameSnapshot"] = None,
    layout: str = "columns",   # "columns" = side-by-side | "stack" = source top, viz bottom
) -> None:
    """
    Clear the screen and render a complete frame visualization.

    layout="columns"  (default, terminal / landscape):
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  header (full width)
      SOURCE (44%)  │  ARRAYS / VARS / STACK (56%)
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  footer (full width)

    layout="stack"  (portrait / Shorts):
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  header (full width)
      SOURCE  (full width)
      ────────────────────────────
      ARRAYS / VARS / STACK  (full width)
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  footer (full width)
    """
    _clear()
    w = _term_width()

    # ------------------------------------------------------------------
    # Column geometry
    # ------------------------------------------------------------------
    COL_SEP   = f"  {C_GRAY}│{R}  "   # 5 visible chars
    COL_SEP_W = 5
    if layout == "stack":
        left_w  = w
        right_w = w
    else:
        left_w  = max(10, w * 44 // 100)
        right_w = max(10, w - left_w - COL_SEP_W)

    # ------------------------------------------------------------------
    # Header bar  (full width)
    # ------------------------------------------------------------------
    event_color = {
        "line":      C_GREEN,
        "call":      C_CYAN,
        "return":    C_YELLOW,
        "exception": C_RED,
    }.get(snap.event, C_WHITE)

    header = (
        f" {B}LC-Viz{R}  │  "
        f"Frame {B}{frame_idx + 1}{R}/{total_frames}  │  "
        f"{B}{C_CYAN}{snap.func_name}(){R}  │  "
        f"line {snap.line_no}  │  "
        f"{event_color}{snap.event}{R}  │  "
        f"depth {len(snap.call_stack)}"
    )
    print("━" * w)
    print(header)
    print("━" * w)

    # ------------------------------------------------------------------
    # Classify variables + compute change diff vs previous frame
    # ------------------------------------------------------------------
    cats     = classify(snap.locals_copy)
    arrays   = cats["arrays"]
    pointers = cats["pointers"]
    scalars  = cats["scalars"]
    other_   = cats["other"]

    arr_ptrs = find_array_pointers(arrays, pointers)

    if prev_snap is not None:
        prev_locals = prev_snap.locals_copy
        prev_cats   = classify(prev_locals)
        changed_names = {
            k for k in snap.locals_copy
            if snap.locals_copy[k] != prev_locals.get(k)
        }
        prev_arrays = prev_cats["arrays"]
    else:
        prev_locals   = {}
        changed_names = set()
        prev_arrays   = {}

    # ------------------------------------------------------------------
    # LEFT column – source context
    # ------------------------------------------------------------------
    left_lines = _render_source(
        snap.filename, snap.line_no,
        context=context_lines,
        width=left_w,
    )

    # ------------------------------------------------------------------
    # RIGHT column – arrays → return value → variables → call stack
    # ------------------------------------------------------------------
    right_lines: List[str] = []

    # Arrays
    if arrays:
        right_lines.append(f"  {B}Arrays{R}")
        for arr_name, arr in arrays.items():
            right_lines.extend(
                _render_array(arr_name, arr,
                              arr_ptrs.get(arr_name, {}),
                              max_width=right_w - 2,
                              prev_arr=prev_arrays.get(arr_name))
            )
            right_lines.append("")

    # Return value
    if snap.event == "return" and snap.return_value is not None:
        right_lines.append(
            f"  {B}{C_GREEN}↩ return{R}  {repr(snap.return_value)}"
        )
        right_lines.append("")

    # Variables
    right_lines.extend(
        _render_variables(pointers, scalars, other_,
                          width=right_w,
                          changed=changed_names,
                          prev_vals=prev_locals)
    )
    right_lines.append("")

    # Call stack
    right_lines.extend(
        _render_call_stack(snap.call_stack, snap.func_name, snap.line_no)
    )

    # ------------------------------------------------------------------
    # Print side-by-side or stacked
    # ------------------------------------------------------------------
    if layout == "stack":
        for line in left_lines:
            print(line)
        print(f"  {C_GRAY}{_hr(w - 4)}{R}")
        for line in right_lines:
            print(line)
    else:
        for row in _merge_cols(left_lines, right_lines, left_w, COL_SEP):
            print(row)

    # ------------------------------------------------------------------
    # Footer  (full width)
    # ------------------------------------------------------------------
    print()
    print("━" * w)
    print(f"  {DIM}{footer_hint}{R}")

#!/usr/bin/env python3
"""
LC 994 — Rotting Oranges
Rich Grid BFS Visualization with Pillow

Renders: Grid with oranges + BFS wave animation + code panel + queue + timer
Outputs: MP4 video
"""
import os
import sys
import subprocess
import tempfile
from collections import deque
from math import sin, cos, pi, sqrt
from PIL import Image, ImageDraw, ImageFont

# ═══════════════════════════════════════════════════
#  DESIGN SYSTEM
# ═══════════════════════════════════════════════════

BG         = (15, 17, 23)
BG_PANEL   = (22, 24, 33)
BG_CODE    = (18, 20, 28)
GRID_LINE  = (35, 38, 50)

WHITE      = (230, 230, 240)
GRAY       = (100, 105, 120)
DIM        = (60, 62, 75)

CYAN       = (80, 220, 240)
GREEN      = (80, 220, 120)
YELLOW     = (255, 220, 80)
ORANGE     = (255, 160, 60)
RED        = (255, 85, 85)
PINK       = (255, 100, 200)
BLUE       = (80, 140, 255)
PURPLE     = (160, 100, 255)

# Cell states
EMPTY       = 0
FRESH       = 1
ROTTEN      = 2
JUST_ROTTEN = 3   # just turned rotten this minute (for animation)

# Cell colors
CELL_COLORS = {
    EMPTY:       (30, 33, 45),
    FRESH:       (255, 180, 40),     # bright orange
    ROTTEN:      (100, 55, 20),      # dark brown/rotten
    JUST_ROTTEN: (200, 80, 30),      # transitioning — red-orange
}

CELL_BORDER = {
    EMPTY:       (45, 48, 60),
    FRESH:       (255, 200, 80),
    ROTTEN:      (130, 75, 30),
    JUST_ROTTEN: (255, 100, 50),
}

# Orange emoji-style faces
FRESH_FACE  = ":)"
ROTTEN_FACE = "X("
EMPTY_FACE  = ""


# ═══════════════════════════════════════════════════
#  FONTS
# ═══════════════════════════════════════════════════

def load_font(size):
    paths = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/SFMono-Regular.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=0)
            except:
                pass
    return ImageFont.load_default()

def load_font_bold(size):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", size, index=1)
    except:
        return load_font(size)


# ═══════════════════════════════════════════════════
#  DRAWING PRIMITIVES
# ═══════════════════════════════════════════════════

def draw_rounded_rect(draw, bbox, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)


def draw_cell(draw, x, y, size, state, font, font_sm, wave_ring=False, coord_text=None):
    """Draw a single grid cell (orange or empty)."""
    fill = CELL_COLORS.get(state, CELL_COLORS[EMPTY])
    border = CELL_BORDER.get(state, CELL_BORDER[EMPTY])
    bw = 2

    # Glow ring for just-rotten cells
    if wave_ring:
        for r in range(3):
            glow_col = (255, 120 - r * 30, 50 - r * 15)
            draw.rounded_rectangle(
                [x - r - 1, y - r - 1, x + size + r + 1, y + size + r + 1],
                radius=6 + r, outline=glow_col, width=1
            )

    draw.rounded_rectangle([x, y, x + size, y + size],
                          radius=5, fill=fill, outline=border, width=bw)

    # Face / icon
    if state == FRESH:
        # Draw a cute orange circle
        cx, cy = x + size // 2, y + size // 2
        r = size // 3
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                    fill=(255, 200, 60), outline=(220, 160, 30), width=2)
        # Smiley
        eye_r = max(2, r // 5)
        draw.ellipse([cx - r//3 - eye_r, cy - r//4 - eye_r,
                     cx - r//3 + eye_r, cy - r//4 + eye_r], fill=(60, 40, 10))
        draw.ellipse([cx + r//3 - eye_r, cy - r//4 - eye_r,
                     cx + r//3 + eye_r, cy - r//4 + eye_r], fill=(60, 40, 10))
        # Smile arc
        draw.arc([cx - r//3, cy - r//6, cx + r//3, cy + r//3],
                start=10, end=170, fill=(60, 40, 10), width=max(1, r//6))

    elif state == ROTTEN or state == JUST_ROTTEN:
        cx, cy = x + size // 2, y + size // 2
        r = size // 3
        rot_color = (80, 45, 15) if state == ROTTEN else (160, 60, 20)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                    fill=rot_color, outline=(50, 30, 10), width=2)
        # X eyes
        eye_r = max(2, r // 4)
        for ex in [cx - r//3, cx + r//3]:
            draw.line([ex - eye_r, cy - r//4 - eye_r, ex + eye_r, cy - r//4 + eye_r],
                     fill=(200, 200, 180), width=max(1, r//6))
            draw.line([ex + eye_r, cy - r//4 - eye_r, ex - eye_r, cy - r//4 + eye_r],
                     fill=(200, 200, 180), width=max(1, r//6))
        # Frown
        draw.arc([cx - r//3, cy + r//8, cx + r//3, cy + r//2],
                start=190, end=350, fill=(200, 200, 180), width=max(1, r//6))

        # Stink lines for rotten
        if state == ROTTEN:
            for sx in [-r//2, 0, r//2]:
                draw.line([cx + sx, cy - r - 4, cx + sx + 2, cy - r - 10],
                         fill=(120, 160, 100), width=1)

    # Coordinate label (small, below cell)
    if coord_text:
        bb = draw.textbbox((0, 0), coord_text, font=font_sm)
        tw = bb[2] - bb[0]
        draw.text((x + size // 2 - tw // 2, y + size + 2),
                 coord_text, fill=DIM, font=font_sm)


# ═══════════════════════════════════════════════════
#  CODE PANEL
# ═══════════════════════════════════════════════════

def draw_code_panel(draw, x, y, w, h, source_lines, current_line, font_code, font_sm):
    """Draw source code with line highlight."""
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_CODE, GRID_LINE, 1)
    draw.text((x + 10, y + 8), "SOURCE", fill=CYAN, font=font_sm)

    code_y = y + 32
    line_h = 22
    context = 8
    start = max(0, current_line - context - 1)
    end = min(len(source_lines), current_line + context)

    for i in range(start, end):
        ly = code_y + (i - start) * line_h
        if ly + line_h > y + h - 4:
            break

        is_current = (i == current_line - 1)

        if is_current:
            draw.rectangle([x + 2, ly - 2, x + w - 2, ly + line_h - 1],
                          fill=(35, 55, 65))
            draw.text((x + 8, ly), "►", fill=GREEN, font=font_code)

        line_num_color = GREEN if is_current else DIM
        draw.text((x + 26, ly), f"{i+1:3}", fill=line_num_color, font=font_code)

        code_color = WHITE if is_current else (140, 200, 140)
        text = source_lines[i] if i < len(source_lines) else ""
        max_chars = (w - 80) // 9
        if len(text) > max_chars:
            text = text[:max_chars - 1] + "…"
        draw.text((x + 68, ly), text, fill=code_color, font=font_code)


# ═══════════════════════════════════════════════════
#  QUEUE PANEL
# ═══════════════════════════════════════════════════

def draw_queue_panel(draw, x, y, w, h, queue_contents, font, font_sm, label="QUEUE (BFS)"):
    """Draw the BFS queue showing (row, col) pairs."""
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_PANEL, GRID_LINE, 1)
    draw.text((x + 10, y + 6), label, fill=CYAN, font=font_sm)

    qx = x + 10
    qy = y + 28
    box_w = 52
    box_h = 28
    gap = 4
    items_per_row = max(1, (w - 20) // (box_w + gap))

    for i, (r, c) in enumerate(queue_contents[:items_per_row * 3]):  # max 3 rows
        row_idx = i // items_per_row
        col_idx = i % items_per_row
        bx = qx + col_idx * (box_w + gap)
        by = qy + row_idx * (box_h + gap)
        if by + box_h > y + h - 5:
            break

        draw.rounded_rectangle([bx, by, bx + box_w, by + box_h],
                              radius=4, fill=(200, 80, 30), outline=ORANGE, width=2)
        text = f"{r},{c}"
        bb = draw.textbbox((0, 0), text, font=font_sm)
        tw = bb[2] - bb[0]
        draw.text((bx + box_w//2 - tw//2, by + 4), text,
                 fill=WHITE, font=font_sm)

    if not queue_contents:
        draw.text((qx, qy + 4), "(empty)", fill=DIM, font=font_sm)


# ═══════════════════════════════════════════════════
#  STATS PANEL
# ═══════════════════════════════════════════════════

def draw_stats_panel(draw, x, y, w, h, stats, font, font_sm):
    """Draw statistics: minute, fresh count, etc."""
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_PANEL, GRID_LINE, 1)
    draw.text((x + 10, y + 6), "STATUS", fill=CYAN, font=font_sm)

    sy = y + 30
    for key, val, color in stats:
        draw.text((x + 12, sy), f"{key}:", fill=GRAY, font=font_sm)
        draw.text((x + 12 + len(key) * 9 + 10, sy), str(val), fill=color, font=font)
        sy += 26


# ═══════════════════════════════════════════════════
#  WAVE PROGRESS BAR
# ═══════════════════════════════════════════════════

def draw_wave_bar(draw, x, y, w, h, minute, max_minutes, total_fresh, remaining_fresh, font_sm):
    """Draw a progress bar showing the BFS wave propagation."""
    draw_rounded_rect(draw, (x, y, x+w, y+h), 8, BG_PANEL, GRID_LINE, 1)
    draw.text((x + 10, y + 6), "INFECTION PROGRESS", fill=CYAN, font=font_sm)

    bar_x = x + 12
    bar_y = y + 28
    bar_w = w - 24
    bar_h = 20

    # Background
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                          radius=4, fill=(40, 42, 55))

    # Progress
    if total_fresh > 0:
        progress = (total_fresh - remaining_fresh) / total_fresh
        pw = int(bar_w * progress)
        if pw > 0:
            # Gradient from orange to dark brown
            draw.rounded_rectangle([bar_x, bar_y, bar_x + pw, bar_y + bar_h],
                                  radius=4, fill=(200, 80, 30))

        # Percentage
        pct_text = f"{int(progress * 100)}% infected"
        bb = draw.textbbox((0, 0), pct_text, font=font_sm)
        tw = bb[2] - bb[0]
        draw.text((bar_x + bar_w // 2 - tw // 2, bar_y + 3),
                 pct_text, fill=WHITE, font=font_sm)

    # Minute markers
    if max_minutes > 0:
        for m in range(max_minutes + 1):
            mx = bar_x + int(bar_w * m / max_minutes) if max_minutes > 0 else bar_x
            draw.text((mx - 3, bar_y + bar_h + 4), str(m), fill=DIM, font=font_sm)


# ═══════════════════════════════════════════════════
#  SIMULATION ENGINE
# ═══════════════════════════════════════════════════

def simulate(grid):
    """
    Run BFS step by step, yielding frame data for visualization.
    """
    source_lines = [
        "def orangesRotting(grid):",
        "    rows, cols = len(grid), len(grid[0])",
        "    queue = deque()",
        "    fresh = 0",
        "",
        "    # Find all rotten & count fresh",
        "    for r in range(rows):",
        "        for c in range(cols):",
        "            if grid[r][c] == 2:",
        "                queue.append((r, c))",
        "            elif grid[r][c] == 1:",
        "                fresh += 1",
        "",
        "    if fresh == 0: return 0",
        "    minutes = 0",
        "",
        "    while queue and fresh > 0:",
        "        minutes += 1",
        "        # Process entire wave",
        "        for _ in range(len(queue)):",
        "            r, c = queue.popleft()",
        "            for dr, dc in [(-1,0),(1,0),",
        "                           (0,-1),(0,1)]:",
        "                nr, nc = r+dr, c+dc",
        "                if (0<=nr<rows and",
        "                    0<=nc<cols and",
        "                    grid[nr][nc]==1):",
        "                    grid[nr][nc] = 2",
        "                    fresh -= 1",
        "                    queue.append((nr,nc))",
        "",
        "    return minutes if fresh==0 else -1",
    ]

    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    # Deep copy grid for simulation
    g = [row[:] for row in grid]

    queue = deque()
    fresh = 0
    total_fresh = 0

    def snap(line, desc, extra_vars=None, highlight_cells=None):
        return {
            "line": line,
            "desc": desc,
            "grid": [row[:] for row in g],
            "queue": list(queue),
            "fresh": fresh,
            "total_fresh": total_fresh,
            "source": source_lines,
            "variables": extra_vars or {},
            "highlight_cells": highlight_cells or set(),
        }

    # ── Init: find rotten, count fresh ──
    yield snap(2, f"Scanning {rows}×{cols} grid for oranges...")

    for r in range(rows):
        for c in range(cols):
            if g[r][c] == 2:
                queue.append((r, c))
            elif g[r][c] == 1:
                fresh += 1
                total_fresh += 1

    yield snap(12, f"Found {len(queue)} rotten orange(s), {fresh} fresh orange(s)",
               {"rotten_count": len(queue), "fresh": fresh})

    if fresh == 0:
        yield snap(14, "No fresh oranges! Answer = 0", {"result": 0})
        return

    minutes = 0

    # ── BFS waves ──
    while queue and fresh > 0:
        minutes += 1
        wave_size = len(queue)

        yield snap(18, f"⏱ Minute {minutes} begins — processing wave of {wave_size} rotten orange(s)",
                   {"minutes": minutes, "wave_size": wave_size, "fresh": fresh})

        newly_rotten = []

        for i in range(wave_size):
            r, c = queue.popleft()

            yield snap(21, f"Processing rotten orange at ({r},{c})",
                       {"r": r, "c": c, "minutes": minutes, "fresh": fresh},
                       highlight_cells={(r, c)})

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and g[nr][nc] == 1:
                    g[nr][nc] = JUST_ROTTEN
                    fresh -= 1
                    queue.append((nr, nc))
                    newly_rotten.append((nr, nc))

                    yield snap(29, f"🍊→🤢 Orange at ({nr},{nc}) infected! Fresh remaining: {fresh}",
                               {"nr": nr, "nc": nc, "fresh": fresh, "minutes": minutes},
                               highlight_cells={(r, c), (nr, nc)})

        # Convert JUST_ROTTEN → ROTTEN for next wave
        for rr, cc in newly_rotten:
            if g[rr][cc] == JUST_ROTTEN:
                g[rr][cc] = ROTTEN

        yield snap(17, f"Minute {minutes} complete — {fresh} fresh remaining",
                   {"minutes": minutes, "fresh": fresh})

    if fresh == 0:
        yield snap(32, f"✅ All oranges rotten in {minutes} minute(s)!",
                   {"result": minutes})
    else:
        yield snap(32, f"❌ Impossible! {fresh} orange(s) unreachable. Answer = -1",
                   {"result": -1, "unreachable": fresh})


# ═══════════════════════════════════════════════════
#  RENDER FRAME → IMAGE
# ═══════════════════════════════════════════════════

def render_frame_image(frame_data, frame_idx, total_frames,
                       orig_grid, total_fresh_start,
                       img_w=1920, img_h=1080):
    """Render one simulation frame to a PIL Image."""
    img = Image.new("RGB", (img_w, img_h), BG)
    draw = ImageDraw.Draw(img)

    font_lg = load_font_bold(24)
    font_md = load_font(18)
    font_sm = load_font(15)
    font_xs = load_font(12)
    font_code = load_font(15)

    grid = frame_data["grid"]
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    highlight = frame_data.get("highlight_cells", set())

    # ── Header ──
    draw.rectangle([0, 0, img_w, 50], fill=(20, 22, 32))
    draw.text((16, 12), "LC 994 — Rotting Oranges 🍊", fill=ORANGE, font=font_lg)
    draw.text((img_w - 220, 16), f"Frame {frame_idx+1}/{total_frames}",
              fill=GRAY, font=font_sm)

    # Description bar
    draw.rectangle([0, 50, img_w, 86], fill=(25, 28, 40))
    draw.text((16, 58), frame_data["desc"], fill=WHITE, font=font_md)

    # ── Layout ──
    # Left: Grid (50%)  Right: Code + Queue + Stats (50%)
    grid_panel_x = 16
    grid_panel_y = 96
    grid_panel_w = int(img_w * 0.48)
    grid_panel_h = int(img_h * 0.60)

    code_x = grid_panel_x + grid_panel_w + 16
    code_y = 96
    code_w = img_w - code_x - 16
    code_h = int(img_h * 0.40)

    queue_x = code_x
    queue_y = code_y + code_h + 10
    queue_w = code_w * 3 // 5 - 5
    queue_h = int(img_h * 0.18)

    stats_x = queue_x + queue_w + 10
    stats_y = queue_y
    stats_w = code_w - queue_w - 10
    stats_h = queue_h

    wave_x = 16
    wave_y = grid_panel_y + grid_panel_h + 16
    wave_w = img_w - 32
    wave_h = 70

    legend_x = 16
    legend_y = wave_y + wave_h + 10
    legend_w = img_w - 32
    legend_h = img_h - legend_y - 10

    # ── Draw Grid Panel ──
    draw_rounded_rect(draw, (grid_panel_x, grid_panel_y,
                             grid_panel_x + grid_panel_w,
                             grid_panel_y + grid_panel_h),
                      8, BG_PANEL, GRID_LINE, 1)
    draw.text((grid_panel_x + 10, grid_panel_y + 6), "ORANGE GRID", fill=ORANGE, font=font_sm)

    if rows > 0 and cols > 0:
        # Compute cell size to fit
        avail_w = grid_panel_w - 40
        avail_h = grid_panel_h - 50
        cell_size = min(avail_w // cols, avail_h // rows, 80)
        cell_gap = 4

        total_grid_w = cols * (cell_size + cell_gap) - cell_gap
        total_grid_h = rows * (cell_size + cell_gap) - cell_gap
        gx0 = grid_panel_x + (grid_panel_w - total_grid_w) // 2
        gy0 = grid_panel_y + 30 + (grid_panel_h - 30 - total_grid_h) // 2

        for r in range(rows):
            for c in range(cols):
                cx = gx0 + c * (cell_size + cell_gap)
                cy = gy0 + r * (cell_size + cell_gap)
                state = grid[r][c]
                is_highlight = (r, c) in highlight
                draw_cell(draw, cx, cy, cell_size, state,
                         font_sm, font_xs,
                         wave_ring=is_highlight)

        # Row/col labels
        for r in range(rows):
            cy = gy0 + r * (cell_size + cell_gap) + cell_size // 2
            draw.text((gx0 - 18, cy - 6), str(r), fill=DIM, font=font_xs)
        for c in range(cols):
            cx = gx0 + c * (cell_size + cell_gap) + cell_size // 2
            draw.text((cx - 3, gy0 - 16), str(c), fill=DIM, font=font_xs)

    # ── Draw Code Panel ──
    draw_code_panel(draw, code_x, code_y, code_w, code_h,
                    frame_data["source"], frame_data["line"], font_code, font_xs)

    # ── Draw Queue Panel ──
    draw_queue_panel(draw, queue_x, queue_y, queue_w, queue_h,
                     frame_data["queue"], font_sm, font_xs)

    # ── Draw Stats Panel ──
    minutes = frame_data["variables"].get("minutes", 0)
    fresh = frame_data["fresh"]
    result = frame_data["variables"].get("result", "—")
    stats = [
        ("Minute", minutes, CYAN),
        ("Fresh", fresh, YELLOW if fresh > 0 else GREEN),
        ("Queue", len(frame_data["queue"]), ORANGE),
        ("Answer", result, GREEN if result != "—" else GRAY),
    ]
    draw_stats_panel(draw, stats_x, stats_y, stats_w, stats_h,
                     stats, font_md, font_sm)

    # ── Draw Wave Progress Bar ──
    remaining = frame_data["fresh"]
    # Estimate max minutes for bar width (rough upper bound)
    max_min = max(minutes + 2, rows + cols)
    draw_wave_bar(draw, wave_x, wave_y, wave_w, wave_h,
                  minutes, max_min, total_fresh_start, remaining, font_xs)

    # ── Legend ──
    if legend_h > 20:
        draw_rounded_rect(draw, (legend_x, legend_y, legend_x + legend_w, legend_y + legend_h),
                          8, BG_PANEL, GRID_LINE, 1)
        lx = legend_x + 16
        ly = legend_y + 8
        items = [
            ((255, 200, 60), "Fresh 🍊"),
            ((200, 80, 30), "Just Infected 🤢"),
            ((80, 45, 15), "Rotten 💀"),
            ((30, 33, 45), "Empty"),
        ]
        for color, label in items:
            draw.rounded_rectangle([lx, ly, lx + 18, ly + 18], radius=3, fill=color)
            draw.text((lx + 24, ly + 1), label, fill=GRAY, font=font_xs)
            lx += 170

    return img


# ═══════════════════════════════════════════════════
#  MAIN — Generate MP4
# ═══════════════════════════════════════════════════

def generate_video(grid, output="lc994_viz.mp4", fps=1.5,
                   img_w=1920, img_h=1080):
    """Generate the full visualization video."""
    # Count initial fresh
    total_fresh_start = sum(1 for row in grid for c in row if c == 1)

    frames = list(simulate(grid))
    total = len(frames)
    print(f"Simulated {total} frames")

    with tempfile.TemporaryDirectory() as tmp:
        for i, fdata in enumerate(frames):
            img = render_frame_image(fdata, i, total, grid, total_fresh_start,
                                     img_w, img_h)
            img.save(os.path.join(tmp, f"frame_{i:05d}.png"))
            print(f"  rendered {i+1}/{total}", end="\r", flush=True)

        print(f"\nStitching {total} frames → {output}")
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", os.path.join(tmp, "frame_%05d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True)

    print(f"✓ Saved → {output}")
    return output


if __name__ == "__main__":
    # Example 1: Standard case
    print("═" * 50)
    print("Example 1: [[2,1,1],[1,1,0],[0,1,1]]")
    print("═" * 50)
    generate_video(
        grid=[[2, 1, 1],
              [1, 1, 0],
              [0, 1, 1]],
        output="videos/lc994_ex1.mp4",
        fps=1.2,
    )

    # Example 2: Impossible case
    print("\n" + "═" * 50)
    print("Example 2: [[2,1,1],[0,1,1],[1,0,1]]")
    print("═" * 50)
    generate_video(
        grid=[[2, 1, 1],
              [0, 1, 1],
              [1, 0, 1]],
        output="videos/lc994_ex2.mp4",
        fps=1.2,
    )

    # Example 3: Bigger grid, multiple rotten sources
    print("\n" + "═" * 50)
    print("Example 3: 4x5 grid with 2 rotten sources")
    print("═" * 50)
    generate_video(
        grid=[[2, 1, 1, 1, 1],
              [1, 1, 0, 0, 1],
              [1, 0, 1, 1, 1],
              [1, 1, 1, 1, 2]],
        output="videos/lc994_ex3.mp4",
        fps=1.0,
    )

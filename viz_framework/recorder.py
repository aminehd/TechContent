"""
recorder.py  –  Render a sequence of FrameSnapshots to an MP4 video.

Each frame is captured from the existing renderer (same layout as the
interactive viewer), rendered onto a dark image via Pillow, then stitched
into an MP4 with ffmpeg.

Requirements
------------
    pip install Pillow
    brew install ffmpeg

Usage (CLI)
-----------
    python3 -m viz_framework.run solutions/lc167.py two_sum "[2,7,11,15]" 9 \\
        --record out.mp4 --fps 2

    # YouTube Shorts (9:16 vertical):
    python3 -m viz_framework.run solutions/lc167.py two_sum "[2,7,11,15]" 9 \\
        --record shorts.mp4 --shorts

Programmatic
------------
    from viz_framework.recorder import record_mp4
    record_mp4(tracer.snapshots, "viz.mp4", fps=2)
"""

import contextlib
import io
import os
import re
import shutil
import subprocess
import tempfile
from typing import List, Optional, Tuple

from .tracer import FrameSnapshot
from .viewer import DEFAULT_EVENTS, _apply_filter


# ── Terminal background colour ─────────────────────────────────────────────────
_BG = (18, 18, 28)

# ── ANSI fg colour map (mirrors renderer.py constants) ──────────────────────
_DEFAULT_FG: Tuple = (204, 204, 204)

_ANSI_FG = {
    "30":  (40,  40,  40),
    "90":  (100, 100, 100),
    "91":  (255,  85,  85),
    "92":  (80,  220, 100),
    "93":  (255, 235,  80),
    "94":  (100, 160, 255),
    "96":  (100, 240, 240),
    "97":  (255, 255, 255),
}


def _256_to_rgb(n: int) -> Tuple[int, int, int]:
    """xterm-256 palette index → (R, G, B)."""
    if n < 16:
        basic = [
            (0,0,0),(128,0,0),(0,128,0),(128,128,0),
            (0,0,128),(128,0,128),(0,128,128),(192,192,192),
            (128,128,128),(255,0,0),(0,255,0),(255,255,0),
            (0,0,255),(255,0,255),(0,255,255),(255,255,255),
        ]
        return basic[n]
    if n < 232:
        n -= 16
        b, g, r = n % 6, (n // 6) % 6, n // 36
        return (r * 51, g * 51, b * 51)
    gray = 8 + (n - 232) * 10
    return (gray, gray, gray)


# ── ANSI span parser ──────────────────────────────────────────────────────────
_ESC_RE = re.compile(r"\033\[([0-9;]*)m")


def _parse_ansi(text: str) -> List[Tuple[str, Tuple, bool, bool]]:
    """Parse an ANSI-coloured string into (chunk, fg_rgb, bold, dim) spans."""
    spans: List[Tuple] = []
    fg   = _DEFAULT_FG
    bold = False
    dim  = False
    pos  = 0

    for m in _ESC_RE.finditer(text):
        if m.start() > pos:
            spans.append((text[pos:m.start()], fg, bold, dim))

        codes = m.group(1).split(";") if m.group(1) else ["0"]
        i = 0
        while i < len(codes):
            c = codes[i]
            if c in ("0", ""):
                fg, bold, dim = _DEFAULT_FG, False, False
            elif c == "1":
                bold = True
            elif c == "2":
                dim = True
            elif c in _ANSI_FG:
                fg = _ANSI_FG[c]
            elif c == "38" and i + 2 < len(codes) and codes[i + 1] == "5":
                fg = _256_to_rgb(int(codes[i + 2]))
                i += 2
            i += 1
        pos = m.end()

    if pos < len(text):
        spans.append((text[pos:], fg, bold, dim))

    return spans


# ── Font loader ───────────────────────────────────────────────────────────────
def _load_fonts(size: int):
    """Return (regular, bold) ImageFont objects. Falls back to bitmap default."""
    try:
        from PIL import ImageFont
    except ImportError:
        return None, None

    # (path, regular_index, bold_index)
    candidates = [
        ("/System/Library/Fonts/Menlo.ttc",                              0, 1),
        ("/Library/Fonts/Courier New.ttf",                               0, 0),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",          0, 0),
        ("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", 0, 0),
    ]

    for path, ri, bi in candidates:
        if os.path.exists(path):
            try:
                reg  = ImageFont.truetype(path, size, index=ri)
                bold = ImageFont.truetype(path, size, index=bi)
                return reg, bold
            except Exception:
                continue

    fallback = ImageFont.load_default()
    return fallback, fallback


# ── Capture render_frame output as a raw ANSI string ─────────────────────────
def _capture_frame(
    snap: FrameSnapshot,
    frame_idx: int,
    total_frames: int,
    context_lines: int,
    footer_hint: str,
    term_cols: int,
    layout: str = "columns",
) -> str:
    from . import renderer as _rend  # local import avoids circular

    old_size  = shutil.get_terminal_size
    old_clear = _rend._clear

    # Stub out terminal dimensions and screen-clear
    shutil.get_terminal_size = lambda fallback=(80, 24): \
        type("S", (), {"columns": term_cols, "lines": 60})()
    _rend._clear = lambda: None

    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            _rend.render_frame(
                snap, frame_idx, total_frames,
                context_lines=context_lines,
                footer_hint=footer_hint,
                layout=layout,
            )
    finally:
        shutil.get_terminal_size = old_size
        _rend._clear             = old_clear

    return buf.getvalue()


# ── Render one ANSI string → PIL Image ───────────────────────────────────────
def _ansi_to_image(
    ansi_text: str,
    img_w: int,
    img_h: int,
    font_size: int,
) -> "Image":
    from PIL import Image, ImageDraw

    reg_font, bold_font = _load_fonts(font_size)

    # Measure monospace cell size from a sample character
    probe = Image.new("RGB", (font_size * 4, font_size * 4))
    probe_draw = ImageDraw.Draw(probe)
    bb = probe_draw.textbbox((0, 0), "W", font=reg_font)
    char_w = bb[2] - bb[0]
    char_h = int(char_w * 1.65)   # line height ≈ 1.65 × char width

    img  = Image.new("RGB", (img_w, img_h), color=_BG)
    draw = ImageDraw.Draw(img)

    y = 6
    for raw_line in ansi_text.split("\n"):
        if y + char_h > img_h:
            break
        x = 6
        for chunk, fg, is_bold, is_dim in _parse_ansi(raw_line):
            if not chunk:
                continue
            r, g, b = fg
            if is_dim:
                r, g, b = r // 3, g // 3, b // 3
            font = bold_font if is_bold else reg_font
            draw.text((x, y), chunk, fill=(r, g, b), font=font)
            x += len(chunk) * char_w
        y += char_h

    return img


# ── Public API ────────────────────────────────────────────────────────────────
def record_mp4(
    snapshots: List[FrameSnapshot],
    output: str = "viz.mp4",
    fps: float = 2.0,
    context_lines: int = 3,
    show_all_events: bool = False,
    img_width: int = 1920,
    img_height: int = 1080,
    font_size: int = 18,
) -> None:
    """
    Render every (filtered) frame to a PNG, then stitch into MP4 via ffmpeg.

    Parameters
    ----------
    snapshots       : list from Tracer.trace()
    output          : destination .mp4 path
    fps             : frames per second  (default 2 — good for stepping through)
    context_lines   : source lines shown above/below current line
    show_all_events : include call/return events (default: line events only)
    img_width/height: video resolution  (default 1920×1080)
    font_size       : pt size for the monospace font  (default 18)
    """
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        raise ImportError(
            "Pillow is required for MP4 recording:\n"
            "    pip install Pillow"
        )

    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg not found. Install it with:\n"
            "    brew install ffmpeg"
        )

    events = None if show_all_events else DEFAULT_EVENTS
    frames = snapshots if events is None else _apply_filter(snapshots, events)

    if not frames:
        print("No frames to record.")
        return

    # Portrait images (Shorts) use stacked layout — full width for each panel
    layout = "stack" if img_height > img_width else "columns"

    # Approximate how many terminal columns fit in the image width
    # (monospace char width ≈ 0.60 × font_size px)
    term_cols = max(60, int((img_width - 12) / (font_size * 0.60)))

    print(f"Recording {len(frames)} frames → {output}  ({fps} fps, {img_width}×{img_height}, layout={layout})")

    with tempfile.TemporaryDirectory() as tmp:
        for i, snap in enumerate(frames):
            hint  = f"frame {i + 1}/{len(frames)}"
            text  = _capture_frame(snap, i, len(frames),
                                   context_lines, hint, term_cols, layout=layout)
            img   = _ansi_to_image(text, img_width, img_height, font_size)
            img.save(os.path.join(tmp, f"frame_{i:05d}.png"))
            print(f"  rendered {i + 1}/{len(frames)}", end="\r", flush=True)

        print()
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", os.path.join(tmp, "frame_%05d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            output,
        ]
        print("Running ffmpeg …")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stderr[-2000:])
            raise RuntimeError("ffmpeg failed — see output above")

    print(f"Saved  →  {output}")

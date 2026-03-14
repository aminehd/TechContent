"""
produce.py — YouTube production pipeline for LC-Viz

Usage:
  python infra/pipeline/produce.py lc200
  python infra/pipeline/produce.py lc994 --music path/to/track.mp3
  python infra/pipeline/produce.py lc102 --output videos/lc102_final.mp4
  python infra/pipeline/produce.py series994 --music track.mp3   # full BFS series

Produces one upload-ready MP4: intro → examples → outro, with optional background music.
"""

import argparse
import math
import os
import random
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
VIDEOS = ROOT / "videos"
FONTS = ROOT / "viz_framework" / "fonts"

# Per-problem config
PROBLEMS = {
    "lc102": {
        "title": "LC 102",
        "subtitle": "Binary Tree Level Order Traversal",
        "difficulty": "Medium",
        "pattern": ["BFS", "Tree", "Queue"],
        "accent": (0, 230, 230),       # CYAN
        "examples": [
            VIDEOS / "lc102_ex1.mp4",
            VIDEOS / "lc102_ex2.mp4",
        ],
    },
    "lc200": {
        "title": "LC 200",
        "subtitle": "Number of Islands",
        "difficulty": "Medium",
        "pattern": ["BFS", "Grid", "DFS"],
        "accent": (50, 220, 100),       # GREEN
        "examples": [
            VIDEOS / "lc200_ex1.mp4",
            VIDEOS / "lc200_ex2.mp4",
        ],
    },
    "lc994": {
        "title": "LC 994",
        "subtitle": "Rotting Oranges",
        "difficulty": "Medium",
        "pattern": ["BFS", "Grid", "Multi-source"],
        "accent": (255, 140, 30),       # ORANGE
        "examples": [
            VIDEOS / "lc994_ex1.mp4",
            VIDEOS / "lc994_ex2.mp4",
            VIDEOS / "lc994_ex3.mp4",
        ],
    },
    # Full BFS series: lc102 → lc200 → lc994
    "series994": {
        "title": "BFS Series",
        "subtitle": "Tree → Islands → Rotting Oranges",
        "difficulty": "Medium",
        "pattern": ["BFS", "Grid", "Tree"],
        "accent": (180, 80, 255),       # PURPLE
        "examples": [
            VIDEOS / "lc102_ex1.mp4",
            VIDEOS / "lc102_ex2.mp4",
            VIDEOS / "lc200_ex1.mp4",
            VIDEOS / "lc200_ex2.mp4",
            VIDEOS / "lc994_ex1.mp4",
            VIDEOS / "lc994_ex2.mp4",
            VIDEOS / "lc994_ex3.mp4",
        ],
    },
}

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

W, H = 1920, 1080
BG     = (8, 10, 18)
GRAY   = (80, 90, 110)
WHITE  = (230, 235, 245)
DIM    = (50, 55, 70)
FPS    = 30

CHANNEL = "aminehdadsetan"
GITHUB  = "github.com/aminehdadsetan/Viz"


# ---------------------------------------------------------------------------
# Font helpers
# ---------------------------------------------------------------------------

def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a monospace font, fall back to default."""
    candidates = [
        FONTS / ("JetBrainsMono-Bold.ttf" if bold else "JetBrainsMono-Regular.ttf"),
        Path("/System/Library/Fonts/Supplemental/CourierNewBold.ttf") if bold else None,
        Path("/System/Library/Fonts/Supplemental/CourierNew.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    ]
    for p in candidates:
        if p and p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Drawing utilities
# ---------------------------------------------------------------------------

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))

def ease_in_out(t):
    return t * t * (3 - 2 * t)

def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def neon_rect(draw: ImageDraw.Draw, x, y, w, h, color, layers=6, radius=12):
    """Draw a glowing neon rectangle."""
    for i in range(layers, 0, -1):
        alpha = 0.08 * i
        c = lerp_color(BG, color, alpha)
        pad = i * 3
        draw.rounded_rectangle(
            [x - pad, y - pad, x + w + pad, y + h + pad],
            radius=radius + pad // 2,
            outline=c,
            width=1,
        )
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, outline=color, width=2)


def scanlines(img: Image.Image) -> Image.Image:
    """Overlay CRT scanlines."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(0, img.height, 3):
        d.line([(0, y), (img.width, y)], fill=(0, 0, 0, 35))
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


def vignette(img: Image.Image, strength=0.55) -> Image.Image:
    """Darken corners."""
    vig = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(vig)
    cx, cy = img.width // 2, img.height // 2
    for i in range(80):
        t = i / 80
        alpha = int(255 * strength * (1 - ease_out_cubic(t)))
        pad = int(i * (max(img.width, img.height) / 80))
        d.rectangle([pad, pad, img.width - pad, img.height - pad], fill=255 - alpha)
    r, g, b = img.split()
    dark = Image.new("RGB", img.size, (0, 0, 0))
    return Image.composite(dark, img, ImageOps_invert_L(vig))


# PIL doesn't have ImageOps here without import, keep it simple:
def _apply_vignette(img: Image.Image) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    cx, cy = img.width // 2, img.height // 2
    # draw dark edges
    for i in range(60):
        t = ease_out_cubic(i / 60)
        alpha = int(80 * (1 - t))
        pad = i * 8
        d.rectangle([pad, pad, img.width - pad, img.height - pad], fill=(0, 0, 0, 0))
    # simple corner darken via rounded rect outside
    corner_alpha = 90
    for pad in range(0, 180, 20):
        a = int(corner_alpha * (1 - pad / 180))
        d.rounded_rectangle(
            [pad, pad, img.width - pad, img.height - pad],
            radius=max(1, 300 - pad * 2),
            outline=(0, 0, 0, a),
            width=20,
        )
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


def grid_bg(draw: ImageDraw.Draw, accent):
    """Faint grid lines in accent color."""
    gc = lerp_color(BG, accent, 0.04)
    for x in range(0, W, 80):
        draw.line([(x, 0), (x, H)], fill=gc, width=1)
    for y in range(0, H, 80):
        draw.line([(0, y), (W, y)], fill=gc, width=1)


def scanner_line(draw: ImageDraw.Draw, t: float, accent):
    """Horizontal scanner sweep (0→1)."""
    y = int(H * ease_in_out(t))
    beam_color = lerp_color(BG, accent, 0.6)
    for dy in range(-8, 9):
        alpha = max(0, 1 - abs(dy) / 8)
        c = lerp_color(BG, beam_color, alpha * 0.9)
        draw.line([(0, y + dy), (W, y + dy)], fill=c, width=1)


# ---------------------------------------------------------------------------
# Card generators
# ---------------------------------------------------------------------------

def make_intro_frames(cfg: dict, n_frames: int) -> list[Image.Image]:
    """
    5-second animated intro card.
    Phases:
      0.0-0.3 — scanner sweep
      0.2-0.6 — grid fade in
      0.4-0.8 — title fade + slide up
      0.6-0.9 — subtitle + badges
      0.8-1.0 — final hold with pulse
    """
    accent = cfg["accent"]
    font_title  = _font(96, bold=True)
    font_sub    = _font(40)
    font_badge  = _font(28, bold=True)
    font_small  = _font(22)
    frames = []

    for fi in range(n_frames):
        t = fi / (n_frames - 1)

        img  = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Grid background
        grid_t = max(0, min(1, (t - 0.2) / 0.4))
        if grid_t > 0:
            gc = lerp_color(BG, lerp_color(BG, accent, 0.06), grid_t)
            for x in range(0, W, 80):
                draw.line([(x, 0), (x, H)], fill=gc, width=1)
            for y in range(0, H, 80):
                draw.line([(0, y), (W, y)], fill=gc, width=1)

        # Scanner sweep (first 40% of time)
        if t < 0.4:
            scanner_line(draw, t / 0.4, accent)

        # Corner accent lines
        corner_t = max(0, min(1, (t - 0.3) / 0.3))
        if corner_t > 0:
            length = int(200 * corner_t)
            lc = lerp_color(BG, accent, 0.7 * corner_t)
            draw.line([(0, 0), (length, 0)], fill=lc, width=2)
            draw.line([(0, 0), (0, length)], fill=lc, width=2)
            draw.line([(W, H), (W - length, H)], fill=lc, width=2)
            draw.line([(W, H), (W, H - length)], fill=lc, width=2)

        # Center Y base
        cy = H // 2

        # Title
        title_t = max(0, min(1, (t - 0.35) / 0.35))
        if title_t > 0:
            title_et = ease_out_cubic(title_t)
            title_y  = int(lerp(cy - 30, cy - 80, title_et))
            title_alpha = title_et
            tc = lerp_color(BG, accent, title_alpha)
            # Neon glow behind title
            try:
                bbox = draw.textbbox((0, 0), cfg["title"], font=font_title)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            except Exception:
                tw, th = len(cfg["title"]) * 58, 96
            tx = (W - tw) // 2
            for gl in range(8, 0, -1):
                gc2 = lerp_color(BG, accent, 0.06 * gl * title_alpha)
                draw.text((tx - gl, title_y - gl), cfg["title"], font=font_title, fill=gc2)
            draw.text((tx, title_y), cfg["title"], font=font_title, fill=tc)

        # Subtitle
        sub_t = max(0, min(1, (t - 0.55) / 0.3))
        if sub_t > 0:
            sub_et = ease_out_cubic(sub_t)
            sub_y  = int(lerp(cy + 60, cy + 20, sub_et))
            sc = lerp_color(BG, WHITE, sub_et * 0.85)
            try:
                bbox = draw.textbbox((0, 0), cfg["subtitle"], font=font_sub)
                sw = bbox[2] - bbox[0]
            except Exception:
                sw = len(cfg["subtitle"]) * 24
            draw.text(((W - sw) // 2, sub_y), cfg["subtitle"], font=font_sub, fill=sc)

        # Difficulty badge + pattern tags
        badge_t = max(0, min(1, (t - 0.65) / 0.3))
        if badge_t > 0:
            badge_et = ease_out_cubic(badge_t)
            badge_y  = cy + 90

            DIFF_COLORS = {
                "Easy":   (50, 200, 80),
                "Medium": (255, 180, 30),
                "Hard":   (255, 70, 70),
            }
            diff_color = DIFF_COLORS.get(cfg["difficulty"], WHITE)
            diff_color = lerp_color(BG, diff_color, badge_et)

            # Build all badges: [difficulty] + patterns
            tags = [cfg["difficulty"]] + cfg["pattern"]
            tag_colors = [diff_color] + [lerp_color(BG, accent, 0.8 * badge_et)] * len(cfg["pattern"])

            # Measure total width
            pad_x, pad_y = 18, 8
            tag_sizes = []
            for tag in tags:
                try:
                    bb = draw.textbbox((0, 0), tag, font=font_badge)
                    tw2 = bb[2] - bb[0]
                except Exception:
                    tw2 = len(tag) * 17
                tag_sizes.append(tw2)

            total_w = sum(s + pad_x * 2 for s in tag_sizes) + 16 * (len(tags) - 1)
            bx = (W - total_w) // 2

            for i, (tag, color, ts) in enumerate(zip(tags, tag_colors, tag_sizes)):
                bw = ts + pad_x * 2
                bh = 46
                neon_rect(draw, bx, badge_y, bw, bh, color, layers=4, radius=8)
                tc2 = lerp_color(BG, WHITE, badge_et * 0.9)
                draw.text((bx + pad_x, badge_y + pad_y + 2), tag, font=font_badge, fill=tc2)
                bx += bw + 16

        # Bottom channel name
        ch_t = max(0, min(1, (t - 0.8) / 0.2))
        if ch_t > 0:
            cc = lerp_color(BG, GRAY, ch_t)
            ch_text = f"@{CHANNEL}"
            try:
                bb = draw.textbbox((0, 0), ch_text, font=font_small)
                chw = bb[2] - bb[0]
            except Exception:
                chw = len(ch_text) * 13
            draw.text(((W - chw) // 2, H - 60), ch_text, font=font_small, fill=cc)

        # Pulse on accent line at bottom of title area
        if t > 0.75:
            pulse_t = (t - 0.75) / 0.25
            pulse_alpha = 0.4 + 0.3 * math.sin(pulse_t * math.pi * 3)
            lc2 = lerp_color(BG, accent, pulse_alpha)
            line_w = int(lerp(0, 400, ease_out_cubic(min(1, (t - 0.75) / 0.15))))
            lx = (W - line_w) // 2
            draw.line([(lx, cy - 20), (lx + line_w, cy - 20)], fill=lc2, width=2)

        img = scanlines(img)
        frames.append(img)

    return frames


def make_transition_frames(label: str, accent, n_frames: int) -> list[Image.Image]:
    """
    2-second "Example N" transition card.
    Quick flash with label centered.
    """
    font_label = _font(72, bold=True)
    frames = []

    for fi in range(n_frames):
        t = fi / max(1, n_frames - 1)
        # fade in 0→0.3, hold, fade out 0.7→1.0
        if t < 0.3:
            alpha = ease_out_cubic(t / 0.3)
        elif t > 0.7:
            alpha = ease_out_cubic((1 - t) / 0.3)
        else:
            alpha = 1.0

        img  = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        grid_bg(draw, accent)

        lc2 = lerp_color(BG, accent, 0.7 * alpha)
        try:
            bb = draw.textbbox((0, 0), label, font=font_label)
            lw = bb[2] - bb[0]
            lh = bb[3] - bb[1]
        except Exception:
            lw, lh = len(label) * 43, 72

        lx = (W - lw) // 2
        ly = (H - lh) // 2

        # Glow
        for gl in range(6, 0, -1):
            gc3 = lerp_color(BG, accent, 0.06 * gl * alpha)
            draw.text((lx - gl * 2, ly - gl * 2), label, font=font_label, fill=gc3)

        draw.text((lx, ly), label, font=font_label, fill=lc2)

        # Horizontal line above/below
        line_c = lerp_color(BG, accent, 0.4 * alpha)
        draw.line([(W // 4, ly - 20), (3 * W // 4, ly - 20)], fill=line_c, width=1)
        draw.line([(W // 4, ly + lh + 20), (3 * W // 4, ly + lh + 20)], fill=line_c, width=1)

        img = scanlines(img)
        frames.append(img)

    return frames


def make_outro_frames(n_frames: int) -> list[Image.Image]:
    """
    3-second outro card.
    Channel name + GitHub + subscribe prompt.
    """
    accent = (180, 80, 255)  # purple
    font_big   = _font(72, bold=True)
    font_med   = _font(38)
    font_small = _font(26)
    frames = []

    for fi in range(n_frames):
        t = fi / max(1, n_frames - 1)
        alpha = ease_out_cubic(min(1, t / 0.4)) if t < 0.4 else 1.0

        img  = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        grid_bg(draw, accent)

        cy = H // 2

        # Main channel name
        main_text = f"@{CHANNEL}"
        ac = lerp_color(BG, accent, alpha)
        try:
            bb = draw.textbbox((0, 0), main_text, font=font_big)
            mw = bb[2] - bb[0]
        except Exception:
            mw = len(main_text) * 43
        mx = (W - mw) // 2
        for gl in range(7, 0, -1):
            gc4 = lerp_color(BG, accent, 0.07 * gl * alpha)
            draw.text((mx - gl, cy - 50 - gl), main_text, font=font_big, fill=gc4)
        draw.text((mx, cy - 50), main_text, font=font_big, fill=ac)

        # GitHub
        gh_t = max(0, min(1, (t - 0.3) / 0.35))
        if gh_t > 0:
            gh_et = ease_out_cubic(gh_t)
            gh_c = lerp_color(BG, WHITE, 0.7 * gh_et)
            try:
                bb = draw.textbbox((0, 0), GITHUB, font=font_med)
                gw = bb[2] - bb[0]
            except Exception:
                gw = len(GITHUB) * 23
            draw.text(((W - gw) // 2, cy + 30), GITHUB, font=font_med, fill=gh_c)

        # Subscribe line
        sub_t = max(0, min(1, (t - 0.6) / 0.35))
        if sub_t > 0:
            sub_et = ease_out_cubic(sub_t)
            sub_text = "Subscribe  ·  More breakdowns coming"
            sc2 = lerp_color(BG, GRAY, sub_et)
            try:
                bb = draw.textbbox((0, 0), sub_text, font=font_small)
                sw2 = bb[2] - bb[0]
            except Exception:
                sw2 = len(sub_text) * 16
            draw.text(((W - sw2) // 2, cy + 100), sub_text, font=font_small, fill=sc2)

        # Decorative corner lines
        corner_c = lerp_color(BG, accent, 0.5 * alpha)
        length = 120
        draw.line([(0, 0), (length, 0)], fill=corner_c, width=2)
        draw.line([(0, 0), (0, length)], fill=corner_c, width=2)
        draw.line([(W, H), (W - length, H)], fill=corner_c, width=2)
        draw.line([(W, H), (W, H - length)], fill=corner_c, width=2)

        img = scanlines(img)
        frames.append(img)

    return frames


# ---------------------------------------------------------------------------
# Render sequence to temp PNGs + write concat manifest
# ---------------------------------------------------------------------------

def render_sequence(frames: list[Image.Image], tmpdir: str, prefix: str,
                    manifest_lines: list, duration_per_frame: float):
    """Save frames to PNGs, append concat manifest entries."""
    for i, frame in enumerate(frames):
        path = os.path.join(tmpdir, f"{prefix}_{i:04d}.png")
        frame.save(path)
        manifest_lines.append(f"file '{path}'")
        manifest_lines.append(f"duration {duration_per_frame:.6f}")


# ---------------------------------------------------------------------------
# Main produce function
# ---------------------------------------------------------------------------

def produce(problem_key: str, music_path: str | None = None,
            output: str | None = None, fps: int = FPS):
    cfg = PROBLEMS[problem_key]
    accent = cfg["accent"]

    # Validate example videos exist
    examples = [p for p in cfg["examples"] if Path(p).exists()]
    if not examples:
        print(f"No example videos found for {problem_key}. Expected files like:")
        for p in cfg["examples"]:
            print(f"  {p}")
        return

    print(f"Producing: {cfg['title']} — {cfg['subtitle']}")
    print(f"  Examples found: {len(examples)}")

    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_lines = []

        # ── Intro (5 seconds) ──────────────────────────────────────────────
        print("  Rendering intro...")
        intro_frames = make_intro_frames(cfg, n_frames=5 * fps)
        render_sequence(intro_frames, tmpdir, "intro", manifest_lines, 1.0 / fps)

        # ── Examples ──────────────────────────────────────────────────────
        for i, ex_path in enumerate(examples, start=1):
            label = f"Example {i}"
            if len(cfg["examples"]) == 1:
                label = "Example"

            # Transition card (2 seconds)
            print(f"  Rendering transition: {label}...")
            t_frames = make_transition_frames(label, accent, n_frames=2 * fps)
            render_sequence(t_frames, tmpdir, f"trans_{i}", manifest_lines, 1.0 / fps)

            # The actual example video
            manifest_lines.append(f"file '{ex_path}'")

        # ── Outro (3 seconds) ─────────────────────────────────────────────
        print("  Rendering outro...")
        outro_frames = make_outro_frames(n_frames=3 * fps)
        render_sequence(outro_frames, tmpdir, "outro", manifest_lines, 1.0 / fps)

        # Write manifest
        manifest_path = os.path.join(tmpdir, "manifest.txt")
        with open(manifest_path, "w") as f:
            f.write("\n".join(manifest_lines))

        # ── ffmpeg stitch ─────────────────────────────────────────────────
        if output is None:
            output = str(VIDEOS / f"{problem_key}_final.mp4")

        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        print(f"  Stitching → {output}")

        if music_path and Path(music_path).exists():
            # With music: concat demuxer for video, stream_loop for audio
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", manifest_path,
                "-stream_loop", "-1", "-i", str(music_path),
                "-vf", f"fps={fps}",
                "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-af", "volume=0.15",
                "-shortest",
                "-map", "0:v:0", "-map", "1:a:0",
                output,
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", manifest_path,
                "-vf", f"fps={fps}",
                "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                "-pix_fmt", "yuv420p",
                "-an",
                output,
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("ffmpeg error:")
            print(result.stderr[-3000:])
            return

    size_mb = Path(output).stat().st_size / 1e6
    print(f"\nDone: {output}  ({size_mb:.1f} MB)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="produce",
        description="LC-Viz YouTube production pipeline.",
    )
    parser.add_argument("problem",
                        choices=list(PROBLEMS.keys()),
                        help="Problem key (lc102, lc200, lc994, series994)")
    parser.add_argument("--music", metavar="FILE",
                        help="Background music MP3 (played at 15%% volume)")
    parser.add_argument("--output", metavar="FILE",
                        help="Output MP4 path (default: videos/<problem>_final.mp4)")
    parser.add_argument("--fps", type=int, default=FPS,
                        help=f"Output FPS (default {FPS})")

    ns = parser.parse_args()
    produce(ns.problem, music_path=ns.music, output=ns.output, fps=ns.fps)


if __name__ == "__main__":
    main()

"""
produce.py — YouTube production pipeline for LC-Viz

Usage:
  python infra/pipeline/produce.py lc200
  python infra/pipeline/produce.py lc994 --music assets/music/lofi-dark.mp3
  python infra/pipeline/produce.py series994 --music assets/music/lofi-dark.mp3

Produces one upload-ready MP4: intro → examples → outro, with optional background music.
"""

import argparse
import math
import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ROOT   = Path(__file__).resolve().parents[2]
VIDEOS = ROOT / "videos"
FONTS  = ROOT / "viz_framework" / "fonts"

PROBLEMS = {
    "lc102": {
        "title":    "LC 102 · Binary Tree Level Order",
        "accent":   (0, 230, 230),
        "examples": [VIDEOS / "lc102_ex1.mp4", VIDEOS / "lc102_ex2.mp4"],
    },
    "lc200": {
        "title":    "LC 200 · Number of Islands",
        "accent":   (50, 220, 100),
        "examples": [VIDEOS / "lc200_ex1.mp4", VIDEOS / "lc200_ex2.mp4"],
    },
    "lc994": {
        "title":    "LC 994 · Rotting Oranges",
        "accent":   (255, 140, 30),
        "examples": [VIDEOS / "lc994_ex1.mp4", VIDEOS / "lc994_ex2.mp4", VIDEOS / "lc994_ex3.mp4"],
    },
    "series994": {
        "title":    "BFS · Tree → Islands → Rotting Oranges",
        "accent":   (180, 80, 255),
        "examples": [
            VIDEOS / "lc102_ex1.mp4", VIDEOS / "lc102_ex2.mp4",
            VIDEOS / "lc200_ex1.mp4", VIDEOS / "lc200_ex2.mp4",
            VIDEOS / "lc994_ex1.mp4", VIDEOS / "lc994_ex2.mp4", VIDEOS / "lc994_ex3.mp4",
        ],
    },
}

W, H   = 1920, 1080
BG     = (8, 10, 18)
WHITE  = (230, 235, 245)
GRAY   = (80, 90, 110)
FPS    = 30

CHANNEL = "algoviz1000"
GITHUB  = "github.com/algoviz1000/Viz"

ASSETS = ROOT / "assets"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _font_pixel(size):
    """Press Start 2P — pixel arcade font."""
    p = ASSETS / "fonts" / "PressStart2P.ttf"
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()

def _font(size, bold=False):
    candidates = [
        FONTS / ("JetBrainsMono-Bold.ttf" if bold else "JetBrainsMono-Regular.ttf"),
        Path("/System/Library/Fonts/Supplemental/Courier New Bold.ttf") if bold else None,
        Path("/System/Library/Fonts/Supplemental/Courier New.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    ]
    for p in candidates:
        if p and p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()

def lerp(a, b, t):      return a + (b - a) * t
def lerp_c(c1, c2, t):  return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))
def ease_out(t):         return 1 - (1 - t) ** 3
def ease_io(t):          return t * t * (3 - 2 * t)

def scanlines(img):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d  = ImageDraw.Draw(ov)
    for y in range(0, img.height, 3):
        d.line([(0, y), (img.width, y)], fill=(0, 0, 0, 35))
    base = img.convert("RGBA")
    base.alpha_composite(ov)
    return base.convert("RGB")

def text_center(draw, text, font, y, color):
    try:
        bb = draw.textbbox((0, 0), text, font=font)
        w  = bb[2] - bb[0]
    except Exception:
        w = len(text) * (font.size // 2 + 2)
    draw.text(((W - w) // 2, y), text, font=font, fill=color)

def neon_text(draw, text, font, y, color, alpha=1.0):
    """Draw text with neon glow."""
    try:
        bb = draw.textbbox((0, 0), text, font=font)
        tw = bb[2] - bb[0]
    except Exception:
        tw = len(text) * (font.size // 2 + 2)
    x = (W - tw) // 2
    for gl in range(8, 0, -1):
        gc = lerp_c(BG, color, 0.06 * gl * alpha)
        draw.text((x - gl, y - gl), text, font=font, fill=gc)
    draw.text((x, y), text, font=font, fill=lerp_c(BG, color, alpha))


# ---------------------------------------------------------------------------
# Card generators — return list of PIL Images
# ---------------------------------------------------------------------------

def make_intro(cfg, n_frames):
    """
    5 seconds. Pixel font title — large, centered, neon glow, scanlines.
    Title split into two lines if it has ' · '.
    """
    title  = cfg["title"]
    accent = cfg["accent"]

    # Split on · for two-line layout
    if " · " in title:
        line1, line2 = title.split(" · ", 1)
    else:
        line1, line2 = title, None

    # Auto-scale title to fill ~80% of screen width
    target_w = int(W * 0.80)
    size = 120
    while size > 20:
        f_test = _font_pixel(size)
        try:
            bb = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), line1, font=f_test)
            if bb[2] - bb[0] <= target_w:
                break
        except Exception:
            break
        size -= 4
    f_title = _font_pixel(size)
    f_sub   = _font_pixel(max(16, size // 3))
    f_chan  = _font_pixel(max(14, size // 6))
    frames  = []

    for fi in range(n_frames):
        t   = fi / max(1, n_frames - 1)
        img = Image.new("RGB", (W, H), BG)
        d   = ImageDraw.Draw(img)

        # Faint grid
        gc = lerp_c(BG, accent, 0.05)
        for x in range(0, W, 80): d.line([(x, 0), (x, H)], fill=gc)
        for y in range(0, H, 80): d.line([(0, y), (W, y)], fill=gc)

        # Corner lines grow in
        ca  = ease_out(min(1, t / 0.35))
        cl  = lerp_c(BG, accent, 0.7 * ca)
        ln  = int(200 * ca)
        d.line([(0, 0), (ln, 0)],     fill=cl, width=3)
        d.line([(0, 0), (0, ln)],     fill=cl, width=3)
        d.line([(W, H), (W-ln, H)],   fill=cl, width=3)
        d.line([(W, H), (W, H-ln)],   fill=cl, width=3)

        # Title fade + slide up
        title_t = ease_out(min(1, max(0, (t - 0.2) / 0.45)))
        if title_t > 0:
            if line2:
                try:
                    bb1 = d.textbbox((0, 0), line1, font=f_title)
                    title_h = bb1[3] - bb1[1]
                except Exception:
                    title_h = size
                # center the two-line block vertically
                gap = 40
                block_h = title_h + gap + f_sub.size
                cy = (H - block_h) // 2
                neon_text(d, line1, f_title, cy, accent, title_t)
                sub_t = ease_out(min(1, max(0, (t - 0.45) / 0.35)))
                if sub_t > 0:
                    neon_text(d, line2, f_sub, cy + title_h + gap, accent, sub_t * 0.75)
            else:
                cy = int(lerp(H // 2 + 20, H // 2 - 30, title_t))
                neon_text(d, line1, f_title, cy, accent, title_t)

        # Blinking cursor after title settles
        if t > 0.7:
            blink = int((t - 0.7) / 0.1) % 2 == 0
            if blink:
                bc = lerp_c(BG, accent, 0.8)
                # find title right edge to place cursor
                try:
                    bb = d.textbbox((0, 0), line1, font=f_title)
                    tw = bb[2] - bb[0]
                except Exception:
                    tw = len(line1) * 32
                cx2 = (W + tw) // 2 + 10
                cy2 = (H // 2 - 40) if line2 else (H // 2 - 30)
                d.rectangle([cx2, cy2 + 8, cx2 + 6, cy2 + 56], fill=bc)

        # Channel bottom
        if t > 0.8:
            cc = lerp_c(BG, GRAY, ease_out((t - 0.8) / 0.2))
            text_center(d, f"@{CHANNEL}", f_chan, H - 70, cc)

        frames.append(scanlines(img))
    return frames


def make_outro(n_frames):
    accent = (180, 80, 255)
    f_big  = _font_pixel(42)
    f_med  = _font_pixel(22)
    f_sm   = _font_pixel(14)
    frames = []

    for fi in range(n_frames):
        t   = fi / max(1, n_frames - 1)
        img = Image.new("RGB", (W, H), BG)
        d   = ImageDraw.Draw(img)

        gc = lerp_c(BG, accent, 0.05)
        for x in range(0, W, 80): d.line([(x, 0), (x, H)], fill=gc)
        for y in range(0, H, 80): d.line([(0, y), (W, y)], fill=gc)

        a1 = ease_out(min(1, t / 0.4))
        neon_text(d, f"@{CHANNEL}", f_big, H // 2 - 60, accent, a1)

        if t > 0.3:
            a2 = ease_out(min(1, (t - 0.3) / 0.35))
            text_center(d, GITHUB, f_med, H // 2 + 20, lerp_c(BG, WHITE, 0.7 * a2))

        if t > 0.6:
            a3 = ease_out(min(1, (t - 0.6) / 0.35))
            text_center(d, "Subscribe  ·  More breakdowns coming", f_sm,
                        H // 2 + 90, lerp_c(BG, GRAY, a3))

        frames.append(scanlines(img))
    return frames


# ---------------------------------------------------------------------------
# Render card frames → temp MP4
# ---------------------------------------------------------------------------

def frames_to_mp4(frames, path, fps=FPS):
    """Write list of PIL Images to an MP4 via ffmpeg pipe."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "pipe:0",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-an",
        str(path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for frame in frames:
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()


# ---------------------------------------------------------------------------
# Main produce
# ---------------------------------------------------------------------------

def produce(problem_key, music_path=None, output=None, fps=FPS):
    cfg      = PROBLEMS[problem_key]
    examples = [p for p in cfg["examples"] if Path(p).exists()]

    if not examples:
        print(f"No example videos found. Expected:")
        for p in cfg["examples"]: print(f"  {p}")
        return

    print(f"Producing: {cfg['title']}")
    print(f"  Examples: {len(examples)}")

    with tempfile.TemporaryDirectory() as tmp:
        parts = []  # ordered list of MP4 paths to concat

        # Intro
        print("  Rendering intro...")
        intro_path = os.path.join(tmp, "intro.mp4")
        frames_to_mp4(make_intro(cfg, 5 * fps), intro_path, fps)
        parts.append(intro_path)

        # Examples
        for i, ex in enumerate(examples, 1):
            parts.append(str(ex))

        # Outro
        print("  Rendering outro...")
        outro_path = os.path.join(tmp, "outro.mp4")
        frames_to_mp4(make_outro(3 * fps), outro_path, fps)
        parts.append(outro_path)

        # Write concat manifest
        manifest = os.path.join(tmp, "manifest.txt")
        with open(manifest, "w") as f:
            for p in parts:
                f.write(f"file '{p}'\n")

        if output is None:
            output = str(VIDEOS / f"{problem_key}_final.mp4")
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

        print(f"  Stitching {len(parts)} segments → {output}")

        if music_path and Path(music_path).exists():
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", manifest,
                "-stream_loop", "-1", "-i", str(music_path),
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k",
                "-af", "volume=0.15",
                "-shortest",
                "-map", "0:v:0", "-map", "1:a:0",
                output,
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", manifest,
                "-c:v", "copy", "-an",
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
# Series: stitch multiple problems with per-problem intros + shared outro
# ---------------------------------------------------------------------------

SERIES = {
    "bfs": ["lc102", "lc200", "lc994"],
}

SERIES_TITLES = {
    "bfs": "Breadth-First Search",
}

def produce_series(series_key, music_path=None, output=None, fps=FPS):
    keys = SERIES[series_key]
    print(f"Producing series: {' → '.join(keys)}")

    with tempfile.TemporaryDirectory() as tmp:
        parts = []

        # Single series intro card at the very start
        series_title = SERIES_TITLES.get(series_key, series_key.upper())
        print(f"  Rendering series intro: {series_title}...")
        series_cfg   = {"title": series_title, "accent": (180, 80, 255)}
        series_intro = os.path.join(tmp, "series_intro.mp4")
        frames_to_mp4(make_intro(series_cfg, 5 * fps), series_intro, fps)
        parts.append(series_intro)

        for ki, key in enumerate(keys):
            cfg      = PROBLEMS[key]
            examples = [p for p in cfg["examples"] if Path(p).exists()]
            if not examples:
                print(f"  Skipping {key} — no videos found")
                continue

            print(f"  [{ki+1}/{len(keys)}] Intro for {key}...")
            intro_path = os.path.join(tmp, f"intro_{key}.mp4")
            frames_to_mp4(make_intro(cfg, 5 * fps), intro_path, fps)
            parts.append(intro_path)

            for ex in examples:
                parts.append(str(ex))

        print("  Rendering outro...")
        outro_path = os.path.join(tmp, "outro.mp4")
        frames_to_mp4(make_outro(3 * fps), outro_path, fps)
        parts.append(outro_path)

        manifest = os.path.join(tmp, "manifest.txt")
        with open(manifest, "w") as f:
            for p in parts:
                f.write(f"file '{p}'\n")

        if output is None:
            output = str(VIDEOS / f"{series_key}_final.mp4")
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        print(f"  Stitching {len(parts)} segments → {output}")

        if music_path and Path(music_path).exists():
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", manifest,
                "-stream_loop", "-1", "-i", str(music_path),
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k", "-af", "volume=0.15",
                "-shortest", "-map", "0:v:0", "-map", "1:a:0",
                output,
            ]
        else:
            cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", manifest,
                   "-c:v", "copy", "-an", output]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("ffmpeg error:"); print(result.stderr[-3000:]); return

    print(f"\nDone: {output}  ({Path(output).stat().st_size / 1e6:.1f} MB)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    all_choices = list(PROBLEMS.keys()) + list(SERIES.keys())
    parser = argparse.ArgumentParser(prog="produce")
    parser.add_argument("problem", choices=all_choices)
    parser.add_argument("--music",  metavar="FILE")
    parser.add_argument("--output", metavar="FILE")
    parser.add_argument("--fps",    type=int, default=FPS)
    ns = parser.parse_args()

    if ns.problem in SERIES:
        produce_series(ns.problem, music_path=ns.music, output=ns.output, fps=ns.fps)
    else:
        produce(ns.problem, music_path=ns.music, output=ns.output, fps=ns.fps)

if __name__ == "__main__":
    main()

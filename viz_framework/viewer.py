"""
viewer.py  –  Interactive and auto-play frame viewers.
"""
import sys
import time
from typing import List, Optional

from .tracer import FrameSnapshot
from .renderer import render_frame


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_key() -> str:
    """
    Read a single key press (non-blocking on POSIX) or fall back to input().
    Returns the raw character(s) as a string.
    """
    try:
        import tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ch
    except Exception:
        # Windows or no tty – fall back
        return input()


# ---------------------------------------------------------------------------
# Filter helpers
# ---------------------------------------------------------------------------

DEFAULT_EVENTS = {"line"}   # skip call/return noise by default


def _apply_filter(
    snapshots: List[FrameSnapshot],
    events: set,
) -> List[FrameSnapshot]:
    """Return only snapshots whose event type is in `events`."""
    return [s for s in snapshots if s.event in events]


# ---------------------------------------------------------------------------
# Interactive viewer
# ---------------------------------------------------------------------------

def interactive(
    snapshots: List[FrameSnapshot],
    events: Optional[set] = None,
    show_all_events: bool = False,
    context_lines: int = 3,
) -> None:
    """
    Step through frames one at a time.

    Keys:
      Enter / → / n  – next frame
      b / ← / p      – previous frame
      q / Ctrl-C     – quit
      <number> Enter – jump to that frame (1-based)
    """
    if events is None:
        events = None if show_all_events else DEFAULT_EVENTS
    frames = snapshots if events is None else _apply_filter(snapshots, events)

    if not frames:
        print("No frames to display (try --all-events to include call/return).")
        return

    idx = 0
    pending_digits = ""

    while True:
        snap      = frames[idx]
        prev_snap = frames[idx - 1] if idx > 0 else None
        render_frame(
            snap,
            frame_idx=idx,
            total_frames=len(frames),
            context_lines=context_lines,
            prev_snap=prev_snap,
            footer_hint=(
                "[Enter/→] next  [b/←] back  [q] quit  "
                "[number+Enter] jump to frame"
            ),
        )

        # ------------------------------------------------------------------
        # Key handling
        # ------------------------------------------------------------------
        try:
            key = _read_key()
        except (EOFError, KeyboardInterrupt):
            break

        if key in ("q", "Q", "\x03"):   # q or Ctrl-C
            break
        elif key in ("\r", "\n", "", "\x1b[C"):  # Enter / right arrow
            if pending_digits:
                try:
                    target = int(pending_digits) - 1   # 1-based input
                    idx = max(0, min(len(frames) - 1, target))
                except ValueError:
                    pass
                pending_digits = ""
            else:
                idx = min(idx + 1, len(frames) - 1)
        elif key in ("b", "B", "\x1b[D"):       # b / left arrow
            pending_digits = ""
            idx = max(idx - 1, 0)
        elif key.isdigit():
            pending_digits += key
        else:
            pending_digits = ""


# ---------------------------------------------------------------------------
# Auto-play viewer
# ---------------------------------------------------------------------------

def autoplay(
    snapshots: List[FrameSnapshot],
    speed: float = 0.6,
    events: Optional[set] = None,
    show_all_events: bool = False,
    context_lines: int = 3,
) -> None:
    """
    Play through frames automatically with a configurable delay (seconds).
    Press Ctrl-C to stop.
    """
    if events is None:
        events = None if show_all_events else DEFAULT_EVENTS
    frames = snapshots if events is None else _apply_filter(snapshots, events)

    if not frames:
        print("No frames to display.")
        return

    try:
        for idx, snap in enumerate(frames):
            prev_snap = frames[idx - 1] if idx > 0 else None
            render_frame(
                snap,
                frame_idx=idx,
                total_frames=len(frames),
                context_lines=context_lines,
                prev_snap=prev_snap,
                footer_hint=f"Auto-play  speed={speed}s  [Ctrl-C to stop]",
            )
            time.sleep(speed)
    except KeyboardInterrupt:
        pass
    finally:
        print("\nStopped.")

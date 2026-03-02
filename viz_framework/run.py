"""
run.py  –  CLI entry point for the LC-Viz framework.

Usage examples
--------------
Interactive (step through frames with Enter):
  python -m viz_framework.run solution.py twoSum "[2,7,11,15]" 9

Auto-play (0.5 s per frame):
  python -m viz_framework.run solution.py twoSum "[2,7,11,15]" 9 --auto --speed 0.5

Show call/return events too:
  python -m viz_framework.run solution.py twoSum "[2,7,11,15]" 9 --all-events

Run a class method  (class name / method name):
  python -m viz_framework.run solution.py Solution.twoSum "[2,7,11,15]" 9
"""

import sys
import os
import ast
import argparse
import importlib.util


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_module(filepath: str):
    """Import a .py file as a module, return (module, abs_path)."""
    abs_path = os.path.abspath(filepath)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"File not found: {abs_path}")

    spec   = importlib.util.spec_from_file_location("_lc_solution", abs_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, abs_path


def _get_function(module, func_spec: str):
    """
    Resolve a function from a module.
    func_spec may be "functionName" or "ClassName.methodName".
    For a class method, instantiate the class with no args then use the method.
    """
    if "." in func_spec:
        class_name, method_name = func_spec.split(".", 1)
        cls  = getattr(module, class_name)
        inst = cls()
        return getattr(inst, method_name)
    return getattr(module, func_spec)


def _parse_args_list(raw_args):
    """
    Parse CLI argument strings into Python values via ast.literal_eval.
    Falls back to the raw string if parsing fails.
    """
    parsed = []
    for raw in raw_args:
        try:
            parsed.append(ast.literal_eval(raw))
        except (ValueError, SyntaxError):
            parsed.append(raw)
    return parsed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m viz_framework.run",
        description="LC-Viz: visualise a LeetCode-style Python function frame by frame.",
    )
    parser.add_argument("file",      help="Path to the Python solution file.")
    parser.add_argument("function",  help="Function name (or Class.method) to visualise.")
    parser.add_argument("args",      nargs="*", help="Arguments to pass to the function.")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--auto",        action="store_true",
                      help="Auto-play frames (default: interactive stepping).")
    mode.add_argument("--interactive", action="store_true", default=True,
                      help="Step through frames interactively (default).")

    parser.add_argument("--speed",      type=float, default=0.6,
                        help="Seconds between frames in auto-play mode (default: 0.6).")
    parser.add_argument("--all-events", action="store_true",
                        help="Show call/return events in addition to line events.")
    parser.add_argument("--context-lines", type=int, default=3,
                        help="Lines of source shown above/below current line (default 3).")

    # ── Recording ──────────────────────────────────────────────────────────
    parser.add_argument("--record", metavar="FILE",
                        help="Record frames to an MP4 file instead of showing viewer. "
                             "Requires: pip install Pillow  &&  brew install ffmpeg")
    parser.add_argument("--fps",    type=float, default=2.0,
                        help="Frames per second for recorded video (default 2).")
    parser.add_argument("--shorts", action="store_true",
                        help="Record in YouTube Shorts format (1080×1920, larger font).")
    parser.add_argument("--rec-width",  type=int, default=1920,
                        help="Video width in pixels (default 1920). Ignored with --shorts.")
    parser.add_argument("--rec-height", type=int, default=1080,
                        help="Video height in pixels (default 1080). Ignored with --shorts.")
    parser.add_argument("--font-size",  type=int, default=0,
                        help="Font size in pt for recorded video (0 = auto).")

    ns = parser.parse_args(argv)

    # ------------------------------------------------------------------
    # Load and trace
    # ------------------------------------------------------------------
    try:
        module, abs_path = _load_module(ns.file)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        func = _get_function(module, ns.function)
    except AttributeError:
        print(f"Error: '{ns.function}' not found in {ns.file}")
        sys.exit(1)

    call_args = _parse_args_list(ns.args)

    from .tracer import Tracer
    tracer = Tracer(target_file=abs_path)

    print(f"Tracing  {ns.function}({', '.join(repr(a) for a in call_args)})  …")
    try:
        result = tracer.trace(func, *call_args)
    except Exception as exc:
        print(f"Function raised an exception: {type(exc).__name__}: {exc}")
        if not tracer.snapshots:
            sys.exit(1)

    print(f"Captured {len(tracer.snapshots)} events.  Starting viewer …")

    # ------------------------------------------------------------------
    # Record to MP4 (--record)
    # ------------------------------------------------------------------
    if ns.record:
        if ns.shorts:
            img_w, img_h, font = 1080, 1920, ns.font_size or 28
        else:
            img_w, img_h, font = ns.rec_width, ns.rec_height, ns.font_size or 18

        from .recorder import record_mp4
        record_mp4(
            tracer.snapshots,
            output=ns.record,
            fps=ns.fps,
            context_lines=ns.context_lines,
            show_all_events=ns.all_events,
            img_width=img_w,
            img_height=img_h,
            font_size=font,
        )
        print(f"\nResult: {result!r}")
        return

    # ------------------------------------------------------------------
    # Interactive / auto-play viewer
    # ------------------------------------------------------------------
    import time; time.sleep(0.8)
    from .viewer import interactive, autoplay

    if ns.auto:
        autoplay(
            tracer.snapshots,
            speed=ns.speed,
            show_all_events=ns.all_events,
            context_lines=ns.context_lines,
        )
    else:
        interactive(
            tracer.snapshots,
            show_all_events=ns.all_events,
            context_lines=ns.context_lines,
        )

    # Show final result
    print(f"\nResult: {result!r}")


if __name__ == "__main__":
    main()

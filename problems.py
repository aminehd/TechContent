"""
problems.py  –  Interactive menu to launch LC-Viz on a chosen LeetCode problem.

When running inside tmux, selecting a problem opens a NEW tmux window with a
two-pane layout:
  LEFT  (42 %)  nvim  solutions/lcXXX.py   ← full question + solution to read
  RIGHT (58 %)  viz_framework runner        ← step through the algorithm

Usage:
    python3 problems.py
    python3 problems.py --auto --speed 0.4
    python3 problems.py --context-lines 8
"""

import argparse
import os
import shlex
import shutil
import subprocess
import sys

# ── Problem registry ──────────────────────────────────────────────────────────
# (menu title,  solution file,  function name,  CLI args for the function)
PROBLEMS = [
    # ── Sliding window ────────────────────────────────────────────────────
    (
        "LC 3   Longest Substring Without Repeating Characters  [sliding window]",
        "solutions/lc003_sliding_window.py",
        "longest_substring",
        ['"abcabcbb"'],
    ),
    (
        "LC 30  Substring with Concatenation of All Words  [sliding window]",
        "solutions/lc030_sliding_window.py",
        "find_substring",
        ['"barfoothefoobarman"', '["foo","bar"]'],
    ),
    # ── DP ────────────────────────────────────────────────────────────────
    (
        "LC 53  Maximum Subarray  [Kadane's DP]",
        "solutions/lc053_kadanes_dp.py",
        "max_subarray",
        ["[-2,1,-3,4,-1,2,1,-5,4]"],
    ),
    (
        "LC 56  Merge Intervals  [sort + greedy]",
        "solutions/lc056_sort_greedy.py",
        "merge",
        ["[[1,3],[2,6],[8,10],[15,18]]"],
    ),
    (
        "LC 238 Product of Array Except Self  [prefix/suffix]",
        "solutions/lc238_prefix_suffix.py",
        "product_except_self",
        ["[1,2,3,4]"],
    ),
    # ── Two Pointers ──────────────────────────────────────────────────────
    (
        "LC 11  Container With Most Water  [two pointers]",
        "solutions/lc011_two_pointers.py",
        "max_water",
        ["[1,8,6,2,5,4,8,3,7]"],
    ),
    (
        "LC 15  3Sum  [sort + two pointers]",
        "solutions/lc015_two_pointers.py",
        "three_sum",
        ["[-1,0,1,2,-1,-4]"],
    ),
    (
        "LC 167 Two Sum II – Input Array Is Sorted  [two pointers]",
        "solutions/lc167_two_pointers.py",
        "two_sum",
        ["[2,7,11,15]", "9"],
    ),
    # ── Monotonic Stack ───────────────────────────────────────────────────
    (
        "LC 456 132 Pattern  [monotonic stack]",
        "solutions/lc456_mono_stack.py",
        "find132pattern",
        ["[3,1,4,2]"],
    ),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _in_tmux() -> bool:
    return bool(os.environ.get("TMUX"))


def _build_viz_cmd(filepath, func_name, func_args, ns) -> list:
    cmd = [
        sys.executable, "-m", "viz_framework.run",
        filepath, func_name, *func_args,
        "--context-lines", str(ns.context_lines),
    ]
    if ns.auto:
        cmd += ["--auto", "--speed", str(ns.speed)]
    return cmd


def _launch_tmux(title, filepath, viz_cmd, cwd):
    """
    Open a new tmux window named after the problem:
      LEFT  pane (42%) – nvim with the solution file (question + code)
      RIGHT pane (58%) – viz_framework runner
    Focus ends up on the right (viz) pane so the user can step through frames.
    """
    nvim = shutil.which("nvim") or shutil.which("vim") or "vi"
    abs_filepath = os.path.join(cwd, filepath)
    win_name = title.split()[0] + title.split()[1]  # e.g. "LC3"

    # 1. New window: start nvim in it (becomes the left pane)
    subprocess.run([
        "tmux", "new-window",
        "-n", win_name,
        "-c", cwd,
        nvim, abs_filepath,
    ])

    # 2. Split right (58% width) and run the viz there
    viz_str = " ".join(shlex.quote(a) for a in viz_cmd)
    subprocess.run([
        "tmux", "split-window",
        "-h", "-p", "58",
        "-c", cwd,
        "bash", "-c", viz_str,
    ])
    # Focus is now on the right (viz) pane — ready to step through


def print_menu():
    print()
    print("  LC-Viz  –  Problem Library")
    if _in_tmux():
        print("  (tmux detected – will open 2-pane window per problem)")
    print("  " + "─" * 52)
    for i, (title, *_) in enumerate(PROBLEMS, 1):
        print(f"  [{i}]  {title}")
    print("  [q]  Quit")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="LC-Viz problem picker."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--auto", action="store_true",
                      help="Auto-play frames instead of interactive stepping.")
    mode.add_argument("--interactive", action="store_true", default=True,
                      help="Step through frames interactively (default).")
    parser.add_argument("--speed", type=float, default=0.6,
                        help="Seconds between frames in auto-play mode (default 0.6).")
    parser.add_argument("--context-lines", type=int, default=3,
                        help="Source lines shown above/below current line (default 3).")
    ns = parser.parse_args()

    cwd = os.path.dirname(os.path.abspath(__file__))

    while True:
        print_menu()
        try:
            choice = input("  Select a problem: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice.lower() in ("q", "quit", "exit"):
            break

        try:
            idx = int(choice) - 1
        except ValueError:
            print("  Please enter a number or 'q'.")
            continue

        if not (0 <= idx < len(PROBLEMS)):
            print(f"  Invalid choice. Enter 1–{len(PROBLEMS)} or 'q'.")
            continue

        title, filepath, func_name, func_args = PROBLEMS[idx]
        viz_cmd = _build_viz_cmd(filepath, func_name, func_args, ns)

        if _in_tmux():
            print(f"\n  Opening tmux window: {title}\n")
            _launch_tmux(title, filepath, viz_cmd, cwd)
            print("  Opened! Switch to the new tmux window to step through the viz.")
            print("  (Ctrl-a n  or  Ctrl-a <window-number>  to jump to it)")
        else:
            print(f"\n  Launching: {title}\n")
            subprocess.run(viz_cmd, cwd=cwd)
            input("\n  Press Enter to return to menu…")


if __name__ == "__main__":
    main()

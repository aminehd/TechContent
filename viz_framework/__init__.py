"""
viz_framework – Frame-by-frame LeetCode visualiser.

Quick API
---------
    from viz_framework import trace_interactive, trace_autoplay

    def twoSum(nums, target):
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]

    trace_interactive(twoSum, [2, 7, 11, 15], 9)
    trace_autoplay(twoSum, [2, 7, 11, 15], 9, speed=0.5)

CLI
---
    python -m viz_framework.run solution.py twoSum "[2,7,11,15]" 9
"""

from .tracer    import Tracer, FrameSnapshot
from .inspector import classify, find_array_pointers
from .viewer    import interactive, autoplay

__all__ = [
    "Tracer",
    "FrameSnapshot",
    "classify",
    "find_array_pointers",
    "trace_interactive",
    "trace_autoplay",
]


def _run(func, args, kwargs, target_file=None, **viewer_kwargs):
    import inspect
    if target_file is None:
        try:
            target_file = inspect.getfile(func)
        except (TypeError, OSError):
            target_file = None

    tracer = Tracer(target_file=target_file)
    result = tracer.trace(func, *args, **kwargs)
    return tracer.snapshots, result


def trace_interactive(func, *args, show_all_events=False, context_lines=3, **kwargs):
    """
    Run func(*args, **kwargs) under the tracer and open the interactive viewer.
    """
    snapshots, result = _run(func, args, kwargs)
    interactive(snapshots, show_all_events=show_all_events, context_lines=context_lines)
    return result


def trace_autoplay(func, *args, speed=0.6, show_all_events=False, context_lines=3, **kwargs):
    """
    Run func(*args, **kwargs) under the tracer and auto-play the frames.
    """
    snapshots, result = _run(func, args, kwargs)
    autoplay(snapshots, speed=speed, show_all_events=show_all_events, context_lines=context_lines)
    return result

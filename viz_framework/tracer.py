"""
tracer.py  –  Capture Python execution frame-by-frame using sys.settrace.
"""
import sys
import os
import copy
import linecache
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class FrameSnapshot:
    """A snapshot of the interpreter state at one trace event."""
    frame_idx: int
    event: str                                 # 'call' | 'line' | 'return' | 'exception'
    func_name: str
    filename: str
    line_no: int
    source_line: str
    locals_copy: Dict[str, Any]
    call_stack: List[Tuple[str, str, int]]     # [(func_name, filename, lineno), ...]
    return_value: Any = None
    exception_info: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_copy(val, _depth=0):
    """Deep-copy a value; fall back gracefully for non-copyable objects."""
    if _depth > 4:
        return repr(val)
    try:
        return copy.deepcopy(val)
    except Exception:
        try:
            return copy.copy(val)
        except Exception:
            return repr(val)


# ---------------------------------------------------------------------------
# Tracer
# ---------------------------------------------------------------------------

class Tracer:
    """
    Traces execution of a function and records every event as a FrameSnapshot.

    Usage::

        tracer = Tracer(target_file="/abs/path/to/solution.py")
        result = tracer.trace(my_func, arg1, arg2)
        snapshots = tracer.snapshots   # list[FrameSnapshot]
    """

    def __init__(self, target_file: Optional[str] = None):
        """
        target_file: absolute path of the file to trace.
                     If None, all files are traced (includes stdlib — slow).
        """
        self.target_file: Optional[str] = (
            os.path.abspath(target_file) if target_file else None
        )
        self.snapshots: List[FrameSnapshot] = []
        self._counter: int = 0
        self._call_stack: List[Tuple[str, str, int]] = []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _should_trace(self, filename: str) -> bool:
        if self.target_file is None:
            return True
        try:
            return os.path.abspath(filename) == self.target_file
        except Exception:
            return False

    def _get_source_line(self, filename: str, lineno: int) -> str:
        line = linecache.getline(filename, lineno)
        return line.rstrip() if line else ""

    def _record(self, frame, event: str, arg) -> None:
        filename  = frame.f_code.co_filename
        func_name = frame.f_code.co_name
        lineno    = frame.f_lineno

        source_line  = self._get_source_line(filename, lineno)
        locals_copy  = {k: _safe_copy(v) for k, v in frame.f_locals.items()}
        return_value = None
        exception_info = None

        if event == "return":
            return_value = _safe_copy(arg)
        elif event == "exception" and arg:
            exception_info = f"{type(arg[1]).__name__}: {arg[1]}"

        snap = FrameSnapshot(
            frame_idx      = self._counter,
            event          = event,
            func_name      = func_name,
            filename       = filename,
            line_no        = lineno,
            source_line    = source_line,
            locals_copy    = locals_copy,
            call_stack     = list(self._call_stack),
            return_value   = return_value,
            exception_info = exception_info,
        )
        self.snapshots.append(snap)
        self._counter += 1

    # ------------------------------------------------------------------
    # sys.settrace callbacks
    # ------------------------------------------------------------------

    def _global_trace(self, frame, event, arg):
        """Called by Python for every 'call' event."""
        filename = frame.f_code.co_filename
        if not self._should_trace(filename):
            return None  # skip stdlib / third-party frames entirely

        if event == "call":
            self._call_stack.append(
                (frame.f_code.co_name, filename, frame.f_lineno)
            )
            self._record(frame, event, arg)

        return self._local_trace

    def _local_trace(self, frame, event, arg):
        """Called for 'line', 'return', 'exception' within a traced frame."""
        if event in ("line", "return", "exception"):
            self._record(frame, event, arg)

        if event == "return" and self._call_stack:
            self._call_stack.pop()

        return self._local_trace

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def trace(self, func, *args, **kwargs):
        """Execute func(*args, **kwargs) under the tracer. Returns the result."""
        self.snapshots.clear()
        self._counter = 0
        self._call_stack = []
        linecache.clearcache()

        sys.settrace(self._global_trace)
        try:
            result = func(*args, **kwargs)
        finally:
            sys.settrace(None)

        return result

"""
inspector.py  –  Classify local variables and infer pointer relationships.
"""
from typing import Any, Dict, List, Set, Tuple


# ---------------------------------------------------------------------------
# Heuristic: names that are likely array index / pointer variables
# ---------------------------------------------------------------------------

POINTER_NAMES: Set[str] = {
    # Single-letter classics
    "i", "j", "k", "l", "r", "p", "q",
    # Named range boundaries
    "lo", "hi", "low", "high", "left", "right", "mid",
    "start", "end", "begin", "finish", "front", "back",
    # Descriptive variants
    "head", "tail", "ptr", "pos", "idx", "index",
    "slow", "fast", "prev", "curr", "next",
    # Common suffixed forms (checked via endswith below)
}

POINTER_SUFFIXES: Tuple[str, ...] = (
    "_idx", "_index", "_ptr", "_pos",
    "_lo", "_hi", "_left", "_right",
    "_start", "_end",
)


def _looks_like_pointer(name: str) -> bool:
    if name in POINTER_NAMES:
        return True
    return any(name.endswith(s) for s in POINTER_SUFFIXES)


# ---------------------------------------------------------------------------
# Variable classifier
# ---------------------------------------------------------------------------

def classify(locals_dict: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Split a frame's local variables into four buckets.

    Returns::

        {
            "arrays":   {name: list},
            "pointers": {name: int},    # ints that look like indices
            "scalars":  {name: value},  # other plain values
            "other":    {name: value},  # dicts, tuples, custom objects …
        }
    """
    arrays: Dict[str, Any]   = {}
    pointers: Dict[str, Any] = {}
    scalars: Dict[str, Any]  = {}
    other: Dict[str, Any]    = {}

    for name, val in locals_dict.items():
        if name.startswith("_"):
            continue

        if isinstance(val, list):
            arrays[name] = val

        elif isinstance(val, int) and not isinstance(val, bool):
            if _looks_like_pointer(name):
                pointers[name] = val
            else:
                scalars[name] = val

        elif isinstance(val, (str, float, bool, type(None))):
            scalars[name] = val

        else:
            # tuple, dict, set, custom class …
            other[name] = val

    return {
        "arrays":   arrays,
        "pointers": pointers,
        "scalars":  scalars,
        "other":    other,
    }


# ---------------------------------------------------------------------------
# Pointer → array relationship inference
# ---------------------------------------------------------------------------

def find_array_pointers(
    arrays: Dict[str, list],
    pointers: Dict[str, int],
) -> Dict[str, Dict[str, int]]:
    """
    For each array, return the subset of pointer variables whose value is a
    valid index into that array (range [-1, len(array)]).

    Returns::

        {array_name: {ptr_name: ptr_value}}
    """
    result: Dict[str, Dict[str, int]] = {name: {} for name in arrays}

    for arr_name, arr in arrays.items():
        n = len(arr)
        for ptr_name, ptr_val in pointers.items():
            # -1 is a very common "not yet started" sentinel in LeetCode solutions
            if -1 <= ptr_val <= n:
                result[arr_name][ptr_name] = ptr_val

    return result

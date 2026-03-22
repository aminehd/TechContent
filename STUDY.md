# vizalgo — Study Guide (Q&A format)

Read through, cover the answers, test yourself.

---

## The full flow (memorize this)

```
@engine.show installs sys.settrace
    ↓
every line fires local_tracer → sets _trace_line
    ↓
engine.snap("desc") called
    ↓
walks call stack → collects all locals
    ↓
RenderConfig.extract() → calls .snapshot() on VizGrid/VizQueue
    ↓
Snapshot(line, description, duration, data) saved to engine.snapshots[]
    ↓
renderer.render(snapshots) → MP4 / Tkinter / JSON
```

---

## Q&A

**Q: When you call engine.snap("BFS from (0,0)") — who puts the line number on the snapshot?**

A: The local_tracer set by sys.settrace. It fires on every line before it executes,
   sets engine._trace_line. By the time snap() runs, the line number is already there.

---

**Q: What is sys.settrace?**

A: A Python built-in hook. You give it a function, Python calls it on every line,
   call, and return event. Used for debuggers, profilers, and our line-by-line tracer.

---

**Q: Which decorator installs sys.settrace?**

A: @engine.show. It wraps the function and installs the tracer when the function runs.

---

**Q: What are the two things @engine.show does?**

A: 1. Grabs the source code (via inspect.getsource) for the code panel
   2. Wraps the function to install sys.settrace on every call

---

**Q: What does @engine.solution do?**

A: Just two things:
   1. Resets engine.snapshots = [] before each run (clean slate per example)
   2. Resets _trace_line = 0

---

**Q: bfs is defined inside numIslands. Does @engine.show trace bfs lines too?**

A: Yes. The global_tracer checks co_qualname. If a called function's qualname starts
   with "numIslands.<locals>." it gets traced too. That's how bfs lines show up
   in the code panel even though @engine.show is on numIslands.

---

**Q: What is a Snapshot?**

A: A dataclass defined in vizalgo/core/event.py:

   @dataclass
   class Snapshot:
       description: str   # "BFS island 1 from (0,0)"
       duration:    float # how long this frame shows in the video
       line:        int   # which line of code is active
       data:        dict  # {grid: [[...]], queue: [...], count: 1}

   engine.snapshots is just a list of these. Pure data, no rendering.

---

**Q: How does RenderConfig know to call .snapshot() on VizGrid vs just storing an int?**

A: It uses hasattr:

   if hasattr(val, 'snapshot'):
       data[panel.key] = val.snapshot()  # VizGrid, VizQueue
   else:
       data[panel.key] = val             # plain int, list, etc.

   Any viz-aware object just needs a .snapshot() method. No inheritance needed.

---

**Q: What does VizGrid.snapshot() return?**

A: A plain list[list[int]] — a deep copy of the current grid state.
   This is what ends up in snapshot.data["grid"].

---

**Q: Why does snap() walk the entire call stack instead of just f_back?**

A: Because grid, queue, count are defined in numIslands but snap() is called from
   inside bfs. Walking up finds variables in all parent frames.

---

**Q: What are the micro-snapshots?**

A: When local_tracer fires on a line where snap() was NOT called, it adds a
   micro-snapshot with duration=line_speed (0.6s) and the last known data.
   This makes the code pointer animate line by line even between snap() calls.
   When snap() IS called on a line, it replaces the micro-snapshot with the full
   snap (duration=snap_speed, updated data).

---

**Q: What is RenderConfig?**

A: A config object that tells the engine which variables to extract from the call
   stack and how. You define it once per solution:

   engine.config = RenderConfig(panels=[
       GridPanel("grid"),    # find var named "grid", call .snapshot()
       QueuePanel("queue"),  # find var named "queue", call .snapshot()
       Counter("count"),     # find var named "count", store as-is
   ])

---

**Q: How are renderers swappable?**

A: All renderers inherit from BaseRenderer (ABC) with one method:

   def render(self, snapshots, output, **meta): ...

   snapshots[] is pure state. The renderer decides what to do with it.
   Same snapshots → MP4, Tkinter window, or JSON for the web.

---

**Q: What does the API return for GET /problems/lc200/frames?**

A: JSON with this shape:

   {
     "problem": "LC 200",
     "runs": [
       {
         "example": 1,
         "source_lines": ["def numIslands(raw_grid):", ...],
         "snapshots": [
           { "line": 3, "description": "", "duration": 0.6,
             "data": { "grid": [[...]], "queue": [], "count": 0 } },
           ...
         ]
       }
     ]
   }

---

**Q: How does the D3 frontend know which line to highlight?**

A: Each snapshot has a "line" integer. The frontend does:

   document.getElementById(`cl-${line}`).classList.add("active")

   The code panel is pre-built as one div per line with id="cl-{i}".

---

## File map

vizalgo/core/engine.py     — VizEngine: snap(), show(), solution(), render()
vizalgo/core/event.py      — Snapshot dataclass
vizalgo/core/state.py      — VizGrid, VizQueue (observable wrappers)
vizalgo/core/config.py     — RenderConfig, GridPanel, QueuePanel, Counter
vizalgo/renderers/pillow.py      — IslandsPillowRenderer → MP4
vizalgo/renderers/interactive.py — InteractiveRenderer → Tkinter
infra/backend/main.py      — FastAPI: /problems, /problems/{id}/frames
infra/web/index.html       — D3 frontend: grid + code + queue + controls
solutions/lc200_core.py    — example solution using the framework

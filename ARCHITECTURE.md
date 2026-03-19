# vizalgo — Architecture & Handoff

## The big picture

A Python framework that instruments algorithm solutions and renders them as videos,
interactive desktop apps, or streams JSON to a web frontend — without the solution
writer knowing anything about visualization.

---

## Core architecture

```
solution.py
  └── engine.snap("description")     ← only annotation needed
  └── @engine.solution / @engine.show ← decorators
  └── VizGrid / VizQueue              ← drop-in wrappers

Engine (sys.settrace)
  └── auto-captures every code line
  └── auto-captures state from call stack via RenderConfig
  └── produces: snapshots[]

snapshots[]  ←── pure state, no rendering
  { line, description, duration, data: {grid, queue, count} }

Renderers (swappable)
  ├── IslandsPillowRenderer → MP4
  ├── InteractiveRenderer   → Tkinter step-through window
  └── (JSON via API)        → D3 web frontend
```

---

## Writing a solution

```python
from vizalgo import VizEngine, RenderConfig, GridPanel, QueuePanel, Counter
from vizalgo.core.state import VizGrid, VizQueue

engine = VizEngine("LC 200", "Number of Islands")
engine.line_speed = 0.6   # seconds per code line
engine.snap_speed = 1.5   # seconds per state-change frame
engine.config = RenderConfig(panels=[
    GridPanel("grid"),
    QueuePanel("queue"),
    Counter("count"),
])

@engine.solution
@engine.show              # traces every line for code pointer
def numIslands(raw_grid):
    grid  = VizGrid(raw_grid)
    count = 0
    queue = VizQueue()

    def bfs(r, c):
        nonlocal count
        queue.push((r, c))
        grid[r][c] = 2
        engine.snap(f"BFS island {count} from ({r},{c})")  # ← only this
        while queue:
            cr, cc = queue.pop()
            grid[cr][cc] = 10 + count
            engine.snap(f"Marking ({cr},{cc})")
            for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                nr, nc = cr+dr, cc+dc
                if grid.valid(nr,nc) and grid[nr][nc] == 1:
                    grid[nr][nc] = 2
                    queue.push((nr,nc))
                    engine.snap(f"Enqueue ({nr},{nc})")
    ...
```

---

## Rendering

```python
from vizalgo.renderers.pillow      import IslandsPillowRenderer
from vizalgo.renderers.interactive import InteractiveRenderer

engine.run(numIslands, grid1)

# Video
engine.render(IslandsPillowRenderer(), output="videos/lc200_ex1.mp4")

# Interactive step-through (Tkinter window)
engine.render(InteractiveRenderer(scale=0.7))

# Both
engine.render(IslandsPillowRenderer(), output="videos/lc200_ex1.mp4")
engine.render(InteractiveRenderer(scale=0.7))
```

---

## How state auto-capture works

`engine.snap()` walks up the Python call stack and extracts variables by name:

```python
def snap(self, description="", **explicit_data):
    frame = inspect.currentframe().f_back
    all_locals = {}
    f = frame
    while f is not None:
        for k, v in f.f_locals.items():
            if k not in all_locals:
                all_locals[k] = v
        f = f.f_back
    data = self.config.extract(all_locals)  # finds grid, queue, count
```

`RenderConfig.extract()` calls `.snapshot()` on VizGrid/VizQueue to get clean copies.

---

## Line-by-line tracing

`@engine.show` installs `sys.settrace` and traces every line of the decorated function
AND all nested functions inside it:

```python
def global_tracer(frame, event, arg):
    if event == 'call':
        if frame.f_code is fn_code:
            return local_tracer
        # also trace bfs, dfs, etc. defined inside numIslands
        fq = getattr(frame.f_code, 'co_qualname', '')
        if fq.startswith(fn_qualname + '.<locals>.'):
            return local_tracer

# on each line: add micro-snapshot (0.6s) with last known state
# engine.snap() calls replace the micro-snap with a full snap (1.5s) + updated data
```

---

## Backend (FastAPI)

```python
# infra/backend/main.py
GET /problems              → list problems
GET /problems/{id}/frames  → all snapshots as JSON
POST /run                  → (future) run user code

# run locally:
python -m uvicorn infra.backend.main:app --port 8000

# deploy to Cloud Run (GCP vizalgo-490301):
gcloud run deploy vizalgo-api --source . --region us-central1
```

Snapshot JSON shape:
```json
{
  "line": 12,
  "description": "BFS island 1 from (0,0)",
  "duration": 1.5,
  "data": {
    "grid":  [[10,10,0],[0,0,0],[0,0,11]],
    "queue": [[0,1]],
    "count": 1
  }
}
```

---

## Web frontend (D3)

`infra/web/index.html` — single file, no build step.
- Fetches `/problems/lc200/frames` from the API
- Renders grid with D3 SVG + smooth color transitions
- Code panel with syntax highlighting + `►` line pointer
- Queue visualization + stats
- Prev / Next / Reset + keyboard arrows
- Example switcher dropdown

---

## File layout

```
vizalgo/
├── core/
│   ├── engine.py     ← VizEngine (snap, show, solution, render)
│   ├── state.py      ← VizGrid, VizQueue
│   ├── event.py      ← Snapshot dataclass
│   └── config.py     ← RenderConfig, GridPanel, QueuePanel, Counter
└── renderers/
    ├── __init__.py   ← BaseRenderer ABC
    ├── pillow.py     ← IslandsPillowRenderer → MP4
    └── interactive.py← InteractiveRenderer → Tkinter window

solutions/
└── lc200_core.py     ← clean solution using the framework

infra/
├── backend/main.py   ← FastAPI server
├── web/index.html    ← D3 frontend
└── pipeline/
    ├── produce.py    ← intro+examples+outro → final MP4
    └── upload.py     ← YouTube Data API v3 upload
```

---

## What's next

- `JSONRenderer` — export snapshots directly to file
- More problems using same framework (lc102, lc994)
- Deploy backend to Cloud Run, frontend to Firebase Hosting
- `POST /run` with sandboxed user code execution

"""
vizalgo backend — FastAPI

Local:
  uvicorn infra.backend.main:app --reload --port 8000

Cloud Run (future):
  gcloud run deploy vizalgo-api --source infra/backend --region us-central1

Endpoints:
  GET  /problems                    — list available problems
  GET  /problems/{id}/frames        — all snapshots as JSON (pre-generated)
  POST /run   (future)              — run user-submitted code, return frames
"""

import sys
import os
import json

# Make repo root importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, ROOT)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="vizalgo API", version="0.1.0")

# Allow Firebase frontend (any origin for now; lock down in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Problem registry — maps problem id → loader function
# ---------------------------------------------------------------------------

def _load_lc200():
    from vizalgo import VizEngine, RenderConfig, GridPanel, QueuePanel, Counter
    from vizalgo.core.state import VizGrid, VizQueue

    engine = VizEngine("LC 200", "Number of Islands")
    engine.line_speed = 0.6
    engine.snap_speed = 1.5
    engine.config = RenderConfig(panels=[
        GridPanel("grid"),
        QueuePanel("queue"),
        Counter("count"),
    ])

    @engine.solution
    @engine.show
    def numIslands(raw_grid):
        grid = VizGrid(raw_grid)
        rows, cols = grid.rows, grid.cols
        count = 0
        queue = VizQueue()

        def bfs(r, c):
            nonlocal count
            queue.push((r, c))
            grid[r][c] = 2
            engine.snap(f"BFS island {count} from ({r},{c})")
            while queue:
                cr, cc = queue.pop()
                grid[cr][cc] = 10 + count
                engine.snap(f"Marking ({cr},{cc}) as island {count}")
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = cr + dr, cc + dc
                    if grid.valid(nr, nc) and grid[nr][nc] == 1:
                        grid[nr][nc] = 2
                        queue.push((nr, nc))
                        engine.snap(f"Enqueue ({nr},{nc})")

        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 1:
                    count += 1
                    engine.snap(f"Found land at ({r},{c}) -> island {count}")
                    bfs(r, c)

        engine.snap(f"Done. {count} island(s)")
        return count

    examples = [
        [["1","1","0","0","0"],
         ["1","1","0","0","0"],
         ["0","0","1","0","0"],
         ["0","0","0","1","1"]],

        [["1","1","1"],
         ["0","1","0"],
         ["1","1","1"]],
    ]

    all_runs = []
    for i, grid in enumerate(examples):
        engine.run(numIslands, grid)
        all_runs.append({
            "example": i + 1,
            "snapshots": _serialize_snapshots(engine.snapshots),
            "source_lines": engine.source_lines,
        })

    return {
        "id":       "lc200",
        "problem":  "LC 200",
        "title":    "Number of Islands",
        "pattern":  ["BFS", "Grid"],
        "runs":     all_runs,
    }


PROBLEMS = {
    "lc200": _load_lc200,
}

PROBLEM_META = {
    "lc200": {"id": "lc200", "title": "Number of Islands", "difficulty": "Medium", "pattern": ["BFS", "Grid"]},
}

# Cache — computed once on first request
_cache: dict = {}


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def _serialize_snapshots(snapshots) -> list:
    result = []
    for s in snapshots:
        data = {}
        for k, v in s.data.items():
            if isinstance(v, (list, tuple, dict, int, float, str, bool, type(None))):
                data[k] = v
            else:
                data[k] = str(v)
        result.append({
            "line":        s.line,
            "description": s.description,
            "duration":    s.duration,
            "data":        data,
        })
    return result


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"status": "ok", "service": "vizalgo API"}


@app.get("/problems")
def list_problems():
    return {"problems": list(PROBLEM_META.values())}


@app.get("/problems/{problem_id}/frames")
def get_frames(problem_id: str):
    if problem_id not in PROBLEMS:
        raise HTTPException(status_code=404, detail=f"Unknown problem: {problem_id}")

    if problem_id not in _cache:
        print(f"  Computing frames for {problem_id}...")
        _cache[problem_id] = PROBLEMS[problem_id]()

    return _cache[problem_id]


# ---------------------------------------------------------------------------
# Future: run user code
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    code: str
    input: dict

@app.post("/run")
def run_code(req: RunRequest):
    # TODO: sandbox execution (gVisor / Cloud Run job)
    raise HTTPException(status_code=501, detail="User code execution not yet implemented")

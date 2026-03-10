# Google Onsite Interview Rounds - March 2026

## Round 1: Equal Area Cake Cut (Binary Search on Answer)
**Problem:** Given N square cakes on a 2D plane, find a horizontal line y=k such that total area above = total area below.
**Key Insight:** The difference between area above and area below is a monotonic function. Binary search on the y-range of the cakes.
**Precision:** Use `while right - left > 1e-9`.

## Round 2: Round-Robin Task Scheduler (Topological Sort / DAG)
**Problem:** Tasks 1..N. Each round, the scheduler iterates 1..N and picks up tasks if dependencies are met. Count total rounds.
**Optimal approach:** $O(N + E)$ using Topological Sort logic. 
- A task $i$ can be completed in round $R$.
- If $i$ depends on $j$, and $j$ was completed in round $R_{prev}$.
- If index $i > index j$: $i$ can potentially be done in the same round $R_{prev}$.
- If index $i < index j$: $i$ must wait until at least round $R_{prev} + 1$.

## Round 3: Garage Car Count (Line Sweep / Difference Array)
**Problem:** Given (start, end) tickets, return count of cars at each hour 0..N.
**Optimal approach:** $O(N + 	ext{tickets})$ using a Difference Array (Line Sweep). 
- `delta[start] += 1`
- `delta[end] -= 1`
- `result[i] = prefix_sum(delta)`
- This is the standard "Difference Array" pattern used for range updates.

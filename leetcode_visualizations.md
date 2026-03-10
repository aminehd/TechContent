# LeetCode Problem Visualizations

This file documents the solutions and corresponding terminal-based visualizations for several LeetCode problems.

---
---

## [1235. Maximum Profit in Job Scheduling](https://leetcode.com/problems/maximum-profit-in-job-scheduling/)
**Level:** Hard

### Problem Description
You have `n` jobs, where every job is scheduled to be done from `startTime[i]` to `endTime[i]`, obtaining a `profit[i]`. Find the maximum profit you can take such that there are no two jobs in the subset with overlapping time ranges.

### Explanation: Dynamic Programming + Binary Search
This is a classic Dynamic Programming problem with an optimization.

1.  **Combine and Sort:** The key first step is to combine the `startTime`, `endTime`, and `profit` arrays into a single list of jobs. Then, **sort these jobs by their `endTime`**.
2.  **DP State:** We define a `dp` array where `dp[i]` will store the maximum profit achievable considering only the jobs up to index `i` in our sorted list.
3.  **DP Logic:** As we iterate through the sorted jobs, for each `job i`, we have two choices:
    *   **Skip `job i`:** The profit is simply the maximum profit we could make before this job, which is `dp[i-1]`.
    *   **Take `job i`:** The profit is `profit[i]` plus the maximum profit from all compatible jobs that finished *before* `job i` started.
4.  **The Optimization:** To efficiently find the "maximum profit from compatible jobs", we use **binary search** on the `endTimes` of the jobs we've already processed. This allows us to find the latest job that doesn't overlap, and its corresponding max profit from our `dp` array, in `O(log n)` time.
5.  **Transition:** `dp[i]` becomes the `max(profit_if_skipped, profit_if_taken)`.

### Solution
```python
import bisect

def jobScheduling(startTime: list[int], endTime: list[int], profit: list[int]) -> int:
    jobs = sorted(zip(startTime, endTime, profit), key=lambda v: v[1])
    
    n = len(jobs)
    # dp[i] will store the max profit considering jobs up to index i-1
    dp = [0] * (n + 1)
    
    # Pre-extract sorted end times for binary search
    end_times = [job[1] for job in jobs]

    for i in range(n):
        start, end, p = jobs[i]

        # Profit if we skip the current job i.
        # This is simply the max profit up to the previous job.
        profit_if_skipped = dp[i]

        # Profit if we take the current job i.
        # We need to find the last job j that finishes at or before our start time.
        # bisect_right on end_times gives us the insertion point 'k'.
        # The max profit from all compatible jobs (0 to k-1) is stored in dp[k].
        prev_compatible_idx = bisect.bisect_right(end_times, start, hi=i)
        prev_profit = dp[prev_compatible_idx]
        profit_if_taken = p + prev_profit

        # The new max profit is the best of the two choices.
        dp[i + 1] = max(profit_if_skipped, profit_if_taken)
        
    return dp[n]
```

### Visualization
To see a step-by-step, animated explanation of this algorithm, run the visualizer we built for it.

**Path to Visualizer:** `job_scheduling_viz.py`
**Command:** `python3 job_scheduling_viz.py`

---
---

## [1882. Process Tasks Using Servers](https://leetcode.com/problems/process-tasks-using-servers/)
**Level:** Medium

### Problem Description
You have two arrays, `servers` (weights) and `tasks` (durations). Tasks arrive one per second. You must assign tasks to servers based on these rules:
1.  If any servers are free, choose the one with the **smallest weight**. If there's a tie, choose the one with the **smallest index**.
2.  If all servers are busy, wait until one becomes free. The task is then assigned to that server. If multiple servers free up at the same time, the standard priority rules (weight, then index) apply.

Return an array of the server indices assigned to each task.

### Explanation: Two-Heap Simulation
This is a classic simulation problem that is solved perfectly with **two min-heaps (priority queues)**.

1.  **`free_servers` heap:** Stores `(weight, index)` of available servers. This heap always keeps the "best" available server at the top, ready to be used.
2.  **`busy_servers` heap:** Stores `(free_time, index)` of servers currently processing a task. This heap always keeps the server that will finish its task *next* at the top.

The algorithm uses a `time` variable that can jump forward. It processes tasks in order, freeing up servers from the `busy_servers` heap as `time` advances. If no servers are free when a task arrives, it jumps `time` forward to the finish time of the next available server.

### Solution
```python
import heapq

def assignTasks(servers: list[int], tasks: list[int]) -> list[int]:
    # (weight, index)
    free_servers = [(servers[i], i) for i in range(len(servers))]
    heapq.heapify(free_servers)
    
    # (free_time, server_index)
    busy_servers = []
    
    res = [0] * len(tasks)
    time = 0
    task_idx = 0
    
    while task_idx < len(tasks):
        # The current time is at least the arrival time of the current task
        time = max(time, task_idx)
        
        # If no servers are free, we must jump time forward to when the
        # next server becomes available.
        if not free_servers:
            time = max(time, busy_servers[0][0])

        # Free up all servers that are done by the new 'time'
        while busy_servers and busy_servers[0][0] <= time:
            free_time, s_idx = heapq.heappop(busy_servers)
            heapq.heappush(free_servers, (servers[s_idx], s_idx))
            
        # Assign all tasks that have arrived by the current 'time'
        while free_servers and task_idx <= time and task_idx < len(tasks):
            s_weight, s_idx = heapq.heappop(free_servers)
            task_duration = tasks[task_idx]
            
            # The server will be busy until 'time' + task_duration
            heapq.heappush(busy_servers, (time + task_duration, s_idx))
            res[task_idx] = s_idx
            task_idx += 1
            
    return res
```

### Visualization
To see a step-by-step, animated explanation of this algorithm, run the visualizer we built for it.

**Path to Visualizer:** `cpu_scheduler_viz.py`
**Command:** `python3 cpu_scheduler_viz.py`

---
---

## [1055. Shortest Way to Form String](https://leetcode.com/problems/shortest-way-to-form-string/)
**Level:** Medium

### Problem Description
Given two strings `source` and `target`, return the minimum number of subsequences of `source` such that their concatenation equals `target`. If the task is impossible, return -1.

### Explanation
This problem can be solved with a greedy approach, and the greedy approach can be optimized with binary search.
1.  **Preprocessing:** First, we map each character in the `source` string to a sorted list of its indices. This allows us to quickly look up where each character appears. We also do a quick check to see if every character in `target` exists in `source` at all.
2.  **Greedy Search:** We iterate through the `target` string with a pointer `target_idx`. We also maintain a `source_idx` which represents the last-matched index in the `source` string.
3.  **Binary Search:** For each character in `target`, instead of linearly scanning `source`, we use binary search (`bisect_right`) on the pre-processed list of indices to find the *next available* index that is greater than our current `source_idx`.
4.  **New Subsequence:** If the binary search cannot find a valid index (meaning we're at the end of the `source` string), we know we must start a new subsequence. We increment our `count` and reset `source_idx` to `-1` to begin searching from the start of `source` again.

### Your Solution
This is the excellent, working solution you developed. It correctly uses a dictionary for the index map and `bisect_right` for the efficient search.
```python
from collections import defaultdict
from bisect import bisect_right

class Solution:
    def shortestWay(self, source: str, target: str) -> int:
        # Pre-check to see if all target chars are in source
        if any(char not in source for char in target):
            return -1
            
        indeces = defaultdict(list)
        for i, char in enumerate(source):
            indeces[char].append(i)

        i = 0
        source_idx = -1
        count = 1
        while i < len(target):
            current_char = target[i]
            available = indeces.get(current_char)

            # Find the insertion point for source_idx to find the next available index
            next_occurence = bisect_right(available, source_idx)
            
            if next_occurence == len(available):
                # No further index available in this pass, start a new subsequence
                source_idx = -1
                count += 1
                # Re-run the search for the same character with the reset source_idx
                next_occurence = bisect_right(available, source_idx)
            
            source_idx = available[next_occurence]
            i += 1
            
        return count
```

### Your Lesson Learnt
This is a great insight from your debugging process:
> A key part of breaking down the problem was using `print` statements to test the logic for when a new subsequence was needed (`if next_occurence == len(available)`). This helped find a bug where `source_idx` was being reset to `0` instead of `-1`. Resetting to `-1` is critical because it allows the binary search to correctly find a character at index `0` of the `source` string on the next pass.

### Visualization
To see a step-by-step, animated explanation of this algorithm, run the visualizer we built for it.

**Path to Visualizer:** `shortest_way_viz.py`
**Command:** `python3 shortest_way_viz.py`

---
---

## [1011. Capacity To Ship Packages Within D Days](https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/)
**Level:** Medium

### Problem Description
A conveyor belt has packages that must be shipped from one port to another within `days` days. The `ith` package has a weight of `weights[i]`. Each day, we can load the ship with packages in the order they appear on the conveyor belt. We cannot load more weight than the ship's maximum weight capacity.

Return the least weight capacity of the ship that will result in all the packages being shipped within `days` days.

### Explanation: Binary Search on the Answer
This is a classic problem that can be solved efficiently by "binary searching on the answer."

1.  **Define a Search Space:** The "answer" (the minimum capacity) must lie within a certain range.
    *   The *minimum possible capacity* is at least the weight of the heaviest single package (`max(weights)`).
    *   The *maximum possible capacity* would be to ship everything in one day (`sum(weights)`).
2.  **Binary Search:** We can binary search within this `[min_capacity, max_capacity]` range. For each `mid` capacity we test, we need to check if it's feasible.
3.  **`canShip` Helper Function:** We write a function that takes a test capacity `w` and checks if we can ship all packages within the allowed `days`. This is a simple linear scan: iterate through the weights, filling up one "day" at a time, and count how many days you need.
4.  **Narrowing the Search:**
    *   If `canShip(mid)` is `True`, it means this capacity works. It's a potential answer, but maybe we can do even better with a *smaller* capacity. So, we record `mid` as a potential answer and try the left half (`r = mid - 1`).
    *   If `canShip(mid)` is `False`, the capacity is too small. We must try a *larger* capacity, so we search the right half (`l = mid + 1`).

### Solution
```python
def shipWithinDays(self, weights: list[int], days: int) -> int:
    def canShip(capacity):
        days_needed = 1
        current_load = 0
        for w in weights:
            if current_load + w <= capacity:
                current_load += w
            else:
                days_needed += 1
                current_load = w
        return days_needed <= days
    
    # Define the search space for the capacity
    l, r = max(weights), sum(weights)
    ans = r
    
    while l <= r:
        mid = (l + r) // 2
        if canShip(mid):
            ans = mid
            r = mid - 1
        else:
            l = mid + 1
    return ans
```

### Visualization
To see a step-by-step, animated explanation of this algorithm, run the visualizer we built for it.

**Path to Visualizer:** `shipping_viz.py`
**Command:** `python3 shipping_viz.py`

---
---

## [1851. Minimum Interval to Include Each Query](https://leetcode.com/problems/minimum-interval-to-include-each-query/)
**Level:** Hard

### Problem Description
You are given a 2D integer array `intervals`, where `intervals[i] = [lefti, righti]` describes an interval, and an array `queries`. For each query `q`, find the length of the **smallest** interval that contains `q`. If no such interval exists, the answer is -1. The length of an interval `[left, right]` is `right - left + 1`.

### Explanation: Sweep-Line with Min-Heap
This is a classic "Sweep-Line" problem that is efficiently solved using a **min-heap**.

1.  **Sort Everything:** Sort the `intervals` by their start point. Sort the `queries` by their value, but keep track of their original indices.
2.  **Sweep and Process:** Iterate through the sorted queries. This simulates a "sweep line" moving across the number line.
3.  **Maintain Active Intervals:** As your sweep line moves to a query `q`, add all intervals that have now become active (i.e., `interval.start <= q`) into a min-heap. The min-heap will be prioritized by interval **length**, so the smallest interval is always at the top.
4.  **Remove Expired Intervals:** Before processing the query, remove any intervals from the top of the heap that have already ended (i.e., `interval.end < q`).
5.  **Get the Answer:** After adding active intervals and removing expired ones, the top of the min-heap is the smallest active interval that covers the current query `q`. Record its length as the answer for that query.

### Solution
```python
import heapq

def minInterval(self, intervals: list[list[int]], queries: list[int]) -> list[int]:
    intervals.sort()
    
    # Sort queries but keep original index
    sorted_queries = sorted([(q, i) for i, q in enumerate(queries)])
    
    res = [-1] * len(queries)
    min_heap = []  # Stores (interval_length, right_boundary)
    interval_idx = 0
    
    for q_val, original_index in sorted_queries:
        # Add all intervals that have started by the current query time
        while interval_idx < len(intervals) and intervals[interval_idx][0] <= q_val:
            left, right = intervals[interval_idx]
            heapq.heappush(min_heap, (right - left + 1, right))
            interval_idx += 1
        
        # Remove all intervals from the heap that have already ended
        while min_heap and min_heap[0][1] < q_val:
            heapq.heappop(min_heap)
        
        # The top of the heap is the smallest active interval
        if min_heap:
            res[original_index] = min_heap[0][0]
            
    return res
```

### Visualization
To see a step-by-step, animated explanation of this algorithm, run the visualizer we built for it.

**Path to Visualizer:** `min_interval_viz.py`
**Command:** `python3 min_interval_viz.py`

---
---

## [1801. Number of Orders in the Backlog](https://leetcode.com/problems/number-of-orders-in-the-backlog/)
**Level:** Medium

### Problem Description
You are given a 2D integer array `orders`, where each `orders[i] = [pricei, amounti, orderTypei]` denotes that `amounti` orders have been placed of type `orderTypei` at the price `pricei`. The `orderTypei` is:
- `0` if it is a batch of buy orders.
- `1` if it is a batch of sell orders.

When an order is placed, it is matched against the backlog:
- A **buy order** is matched against the sell order with the **smallest price**.
- A **sell order** is matched against the buy order with the **largest price**.

If a match occurs (e.g., `sell_price <= buy_price`), orders are executed, amounts are reduced, and fulfilled orders are removed. Any remaining part of an order is added to the backlog.

Return the total amount of orders in the backlog after placing all orders, modulo 10<sup>9</sup> + 7.

### Explanation: The Two-Heap Approach
This problem perfectly models a real-world order book and is solved efficiently using **two heaps (priority queues)**.

1.  **`sell_backlog` (Asks):** To match a buy order, we always need the sell order with the *lowest price*. A **Min-Heap** is the ideal data structure for this.
2.  **`buy_backlog` (Bids):** To match a sell order, we always need the buy order with the *highest price*. A **Max-Heap** is perfect for this. In Python, we simulate this by storing the *negative* of the price in a min-heap.

### Solution
```python
import heapq

def getNumberOfBacklogOrders(orders: list[list[int]]) -> int:
    MOD = 10**9 + 7
    sell_backlog, buy_backlog = [], []  # min-heap, max-heap

    for price, amount, order_type in orders:
        if order_type == 0:  # BUY order
            while amount > 0 and sell_backlog and sell_backlog[0][0] <= price:
                sell_price, sell_amount = heapq.heappop(sell_backlog)
                executed = min(amount, sell_amount)
                amount -= executed
                sell_amount -= executed
                if sell_amount > 0:
                    heapq.heappush(sell_backlog, [sell_price, sell_amount])
            if amount > 0:
                heapq.heappush(buy_backlog, [-price, amount])
        else:  # SELL order
            while amount > 0 and buy_backlog and -buy_backlog[0][0] >= price:
                buy_price_neg, buy_amount = heapq.heappop(buy_backlog)
                executed = min(amount, buy_amount)
                amount -= executed
                buy_amount -= executed
                if buy_amount > 0:
                    heapq.heappush(buy_backlog, [buy_price_neg, buy_amount])
            if amount > 0:
                heapq.heappush(sell_backlog, [price, amount])

    total_amount = sum(a for _, a in buy_backlog) + sum(a for _, a in sell_backlog)
    return total_amount % MOD
```

### Visualization
To see a step-by-step, animated explanation of this algorithm, run the visualizer we built for it.

**Path to Visualizer:** `backlog_viz.py`
**Command:** `python3 backlog_viz.py`

---
---

## [1712. Ways to Split Array Into Three Subarrays](https://leetcode.com/problems/ways-to-split-array-into-three-subarrays/)
**Level:** Medium

### Problem Description
A split of an integer array is good if the array is split into three non-empty contiguous subarrays (`left`, `mid`, `right`) such that `sum(left) <= sum(mid)` and `sum(mid) <= sum(right)`.

### Explanation
This solution uses **Prefix Sums** and **Binary Search** for an efficient `O(n log n)` runtime. We iterate through the first split point `i`, then use binary search on the prefix sum array to find the valid range of second split points `j`.

### Solution
```python
import bisect

def waysToSplit(nums: list[int]) -> int:
    n = len(nums)
    MOD = 10**9 + 7
    prefix_sum = [0] * (n + 1)
    for i in range(n):
        prefix_sum[i+1] = prefix_sum[i] + nums[i]

    count = 0
    for i in range(1, n - 1):
        left_sum = prefix_sum[i]
        
        j_min = bisect.bisect_left(prefix_sum, 2 * left_sum, lo=i + 1, hi=n)
        target_j_max = (prefix_sum[n] + left_sum) // 2
        j_max = bisect.bisect_right(prefix_sum, target_j_max, lo=j_min, hi=n)
        
        if j_max > j_min:
            count = (count + (j_max - j_min)) % MOD
            
    return count
```

### Visualization
To see a step-by-step explanation of this algorithm, run the visualizer we built for it.

**Path to Visualizer:** `split_array_viz.py`
**Command:** `python3 split_array_viz.py`

---
---

## [84. Largest Rectangle in Histogram](https://leetcode.com/problems/largest-rectangle-in-histogram/)
**Level:** Hard

### Problem Description
Given an array of integers `heights` representing the histogram's bar height where the width of each bar is 1, return the area of the largest rectangle in the histogram.

### Explanation: The Perspective Shift (Monotonic Stack)
A common mistake is to think of this problem in the same way as **Trapping Rain Water (LC 42)**. However, the perspective is different.

- **Trapping Rain Water (Looking UP):** At each index `i`, you want to find the **ceiling** (the maximum heights to the left and right). The water level is limited by the **shortest of the two maximums**.
- **Largest Rectangle (Looking DOWN/OUT):** For each bar at index `i`, you want to find its **floor** (the first bar to the left and right that is **shorter** than it). These two shorter bars define the width for which the current height can be maintained.

A **monotonic increasing stack** is the perfect tool for finding the "nearest smaller element" in $O(n)$ time.

### Solution
```python
def largestRectangleArea(heights: list[int]) -> int:
    # A monotonic increasing stack stores indices
    stack = []
    max_area = 0
    # Add a dummy zero at the end to force the stack to empty
    heights.append(0)
    
    for i, h in enumerate(heights):
        # If current height 'h' is smaller than the top of the stack,
        # the bar at 'stack[-1]' has found its RIGHT boundary.
        while stack and heights[stack[-1]] >= h:
            height = heights[stack.pop()]
            # The new top of the stack is the LEFT boundary.
            # If stack is empty, it means the bar at 'height' was the smallest so far.
            width = i if not stack else i - stack[-1] - 1
            max_area = max(max_area, height * width)
        
        stack.append(i)
        
    # Clean up (remove the dummy 0)
    heights.pop()
    return max_area
```

### Visualization
While we don't have a dedicated visualizer for this yet, you can think of it as a "cleanup" process. As we iterate, we build a "mountain" (the stack). Whenever we see a "valley" (a shorter bar), we must "flatten" the mountain by calculating the rectangles for all bars that are now blocked by this valley.

---
---

## [2050. Parallel Courses III](https://leetcode.com/problems/parallel-courses-iii/)
**Level:** Hard

### Problem Description
You are given an integer `n` courses (1 to `n`) and a 2D integer array `relations` (dependencies). Each course has a corresponding duration in the `time` array. You can study any number of courses at the same time as long as their prerequisites are met. Find the minimum months to complete all courses.

### Explanation: Longest Path in a DAG
This is the "big brother" of the Google scheduler question. While the Google version had a "round-robin" constraint, this version has courses with different durations.

Both are variations of finding the **longest path in a Directed Acyclic Graph (DAG)**.
- **Nodes:** Courses.
- **Edges:** Prerequisites.
- **Node Weights:** Duration of each course.
- **Wait Rule:** For any course `v`, it can only start after **ALL** its prerequisites `u` are finished. So, `v`'s finish time is `max(finish_times[u]) + duration[v]`.

We use **Kahn's Algorithm (Topological Sort)** to process nodes in the correct order.

### Solution
```python
from collections import deque, defaultdict

def minimumTime(n: int, relations: list[list[int]], time: list[int]) -> int:
    adj = defaultdict(list)
    in_degree = [0] * (n + 1)
    for u, v in relations:
        adj[u].append(v)
        in_degree[v] += 1
        
    # max_time[i] stores the earliest month course i is FINISHED
    max_time = [0] * (n + 1)
    queue = deque()
    
    # Initialize with starting courses (no prerequisites)
    for i in range(1, n + 1):
        if in_degree[i] == 0:
            queue.append(i)
            max_time[i] = time[i-1]
            
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            # Course v can start only after its slowest prerequisite u is done
            max_time[v] = max(max_time[v], max_time[u] + time[v-1])
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
                
    return max(max_time)
```

---
---

## Other Visualizations

This project contains several other algorithm visualizations.

### The Skyline Problem (LC 218)
- **`skyline_viz.py`**: Visualizes the full sweep-line algorithm, including the heap state and result construction.
- **`event_sorter_viz.py`**: A focused visualization that explains the "event sorting trick" used in the sweep-line algorithm.
- **Command:** `python3 skyline_viz.py` or `python3 event_sorter_viz.py`

### Brightest Position on Street (LC 2021)
- **`brightest_position_viz.py`**: A graphical visualization of the line sweep algorithm for this problem, showing a number line and brightness levels.
- **Command:** `python3 brightest_position_viz.py`

### Generic Animation Demos
- **`standalone_viz.py`**: A self-contained script demonstrating the `GridVisualizer` with a "flashy" replace animation.
- **Command:** `python3 standalone_viz.py`
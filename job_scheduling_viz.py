import os
import time
import re
import bisect

# --- GridVisualizer Class (self-contained) ---

def get_visible_len(s):
    """Calculates the visible length of a string, ignoring ANSI color codes."""
    return len(re.sub(r'\033\[[0-9;]*m', '', s))

class GridVisualizer:
    def __init__(self, rows, cols, cell_width=10, title="Grid Visualizer"):
        self.rows = rows
        self.cols = cols
        self.cell_width = cell_width
        self.title = title
        self.speed = 2.5
        self.grid_content = [['' for _ in range(cols)] for _ in range(rows)]
        self._arrays = {}
        self._texts = {}
        self._highlights = {}

    def place_array_in_row(self, name, data, grid_row, formatter=None):
        self._arrays[name] = {'data': data, 'row': grid_row, 'formatter': formatter}

    def place_text(self, name, text, row, col):
        self._texts[name] = {'text': text, 'row': row, 'col': col}

    def highlight_cell(self, array_name, index, color='yellow', ttl=1):
        if array_name in self._arrays and 0 <= index < len(self._arrays[array_name]['data']):
            row = self._arrays[array_name]['row']
            col = index
            self._highlights[(row, col)] = {'color': color, 'ttl': ttl}

    def _draw_to_grid(self, pointers={}):
        self.grid_content = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        
        for text_info in self._texts.values():
             r, c = text_info['row'], text_info['col']
             if 0 <= r < self.rows and 0 <= c < self.cols:
                self.grid_content[r][c] = text_info['text']

        for arr_name, arr_info in self._arrays.items():
            row = arr_info['row']
            # FIX: If the stored formatter is None, default to the 'str' function
            formatter = arr_info.get('formatter') or str
            for i, val in enumerate(arr_info['data']):
                if 0 <= i < self.cols:
                    self.grid_content[row][i] = formatter(val)
        
        for name, info in pointers.items():
            arr_name = info.get('array')
            if arr_name in self._arrays:
                row = self._arrays[arr_name]['row'] + 1
                index = info.get('index')
                if 0 <= row < self.rows and 0 <= index < self.cols:
                    self.grid_content[row][index] += f" \033[1;92m↑{name}\033[0m"
    
    def _update_highlights(self):
        for key in list(self._highlights.keys()):
            self._highlights[key]['ttl'] -= 1
            if self._highlights[key]['ttl'] <= 0:
                del self._highlights[key]

    def _render_grid(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{self.title}\n" + "=" * len(self.title))
        separator = "+" + ("-" * self.cell_width + "+") * self.cols
        print(separator)
        for r in range(self.rows):
            row_str_parts = []
            for c in range(self.cols):
                cell_content = self.grid_content[r][c]
                highlight = self._highlights.get((r,c))
                if highlight:
                    color_code = {'green': '42', 'yellow': '43', 'red': '41'}.get(highlight['color'], '47')
                    cell_content = f"\033[{color_code}m{cell_content}\033[0m"
                
                visible_len = get_visible_len(cell_content)
                padding_needed = self.cell_width - visible_len
                left_pad = padding_needed // 2
                right_pad = padding_needed - left_pad
                padded_content = ' ' * left_pad + cell_content + ' ' * right_pad
                row_str_parts.append(padded_content)
            print("|" + "|".join(row_str_parts) + "|")
            print(separator)

    def capture(self, message="", pointers={}, final=False):
        self.place_text('message', message, 0, 0)
        self._draw_to_grid(pointers=pointers)
        self._render_grid()
        if not final:
            self._update_highlights()
            time.sleep(self.speed)

# --- "Maximum Profit in Job Scheduling" Visualization ---

def visualize_job_scheduling(startTime, endTime, profit):
    
    # --- Setup ---
    jobs = sorted(zip(startTime, endTime, profit), key=lambda v: v[1])
    n = len(jobs)
    dp = [0] * (n + 1)
    
    # Extract sorted end times for binary search
    end_times = [job[1] for job in jobs]

    # --- Visualizer Setup ---
    viz = GridVisualizer(rows=11, cols=n, title="Job Scheduling DP + Binary Search")
    
    job_formatter = lambda j: f"({j[0]},{j[1]},{j[2]})"
    viz.place_array_in_row('jobs', jobs, 2, formatter=job_formatter)
    viz.place_array_in_row('dp', dp, 5)
    viz.place_array_in_row('ends', end_times, 8)
    
    viz.place_text('jobs_label', "Jobs (s,e,p):", 1, 0)
    viz.place_text('dp_label', "DP (Max Profit):", 4, 0)
    viz.place_text('ends_label', "End Times (for BS):", 7, 0)
    
    viz.capture(message="Sorted jobs by end time. Initialized DP array.")

    # --- Algorithm Execution ---
    for i in range(n):
        start, end, p = jobs[i]
        pointers = {'i': {'array': 'jobs', 'index': i}}
        viz.capture(message=f"Considering job {i}: (s:{start}, e:{end}, p:{p})", pointers=pointers)

        # Profit if we skip job i
        profit_if_skipped = dp[i]
        viz.highlight_cell('dp', i, 'yellow', 2)
        viz.capture(message=f"Profit if skipped = max profit so far = {profit_if_skipped}", pointers=pointers)

        # Profit if we take job i
        # Binary search for the last job that finishes before this one starts
        # We search for `start` in the `end_times` array up to the current job `i`.
        prev_job_idx = bisect.bisect_right(end_times, start, hi=i)
        
        # Animate the binary search
        viz.place_text('bs_label', f"BS for end <= {start}", 7, i)
        viz.highlight_cell('ends', prev_job_idx, 'red', 3)
        viz.capture(message=f"Binary search for last compatible job index, found k={prev_job_idx}", pointers=pointers)
        
        prev_profit = dp[prev_job_idx]
        viz.highlight_cell('dp', prev_job_idx, 'yellow', 2)
        viz.capture(message=f"Profit from compatible jobs is dp[{prev_job_idx}] = {prev_profit}", pointers=pointers)
        
        profit_if_taken = p + prev_profit
        viz.place_text('calc_label', f"Profit if taken = {p} + {prev_profit} = {profit_if_taken}", 9, 0)
        viz.capture(message="Calculating profit if job is taken...", pointers=pointers)
        
        # Update DP array
        dp[i + 1] = max(profit_if_skipped, profit_if_taken)
        viz._arrays['dp']['data'] = dp # Manually update data for viz
        viz.highlight_cell('dp', i + 1, 'green', 3)
        viz.capture(
            message=f"dp[{i+1}] = max({profit_if_skipped}, {profit_if_taken}) = {dp[i+1]}", 
            pointers=pointers
        )
        viz.place_text('calc_label', "", 9, 0) # Clear calculation

    viz.capture(message=f"Finished! Max profit is {dp[n]}", final=True)

if __name__ == "__main__":
    s = [1,2,3,3]
    e = [3,4,5,6]
    p = [50,10,40,70]
    visualize_job_scheduling(s, e, p)
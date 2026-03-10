import os
import time
import re
import heapq

# --- GridVisualizer Class (self-contained) ---

def get_visible_len(s):
    return len(re.sub(r'\033\[[0-9;]*m', '', s))

class GridVisualizer:
    def __init__(self, rows, cols, cell_width=12, title="Grid Visualizer"):
        self.rows = rows
        self.cols = cols
        self.cell_width = cell_width
        self.title = title
        self.speed = 2.0
        self.grid_content = [['' for _ in range(cols)] for _ in range(rows)]
        self._arrays = {}
        self._texts = {}
        self.highlight_grid = {}

    def place_array_in_row(self, name, data, grid_row):
        self._arrays[name] = {'data': data, 'row': grid_row}

    def place_text_in_cell(self, name, text, row, col):
        self._texts[name] = {'text': text, 'row': row, 'col': col}

    def highlight_cell(self, array_name, index, color='yellow', ttl=1):
        if array_name in self._arrays and 0 <= index < len(self._arrays[array_name]['data']):
            row = self._arrays[array_name]['row']
            col = index
            self.highlight_grid[(row, col)] = {'color': color, 'ttl': ttl}

    def _draw_to_grid(self, pointers={}):
        self.grid_content = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        
        for text_info in self._texts.values():
            self.grid_content[text_info['row']][text_info['col']] = text_info['text']

        for arr_name, arr_info in self._arrays.items():
            row = arr_info['row']
            for i, val in enumerate(arr_info['data']):
                if 0 <= i < self.cols:
                    # Custom formatting for tuples
                    if isinstance(val, tuple) or isinstance(val, list):
                        self.grid_content[row][i] = f"({val[0]},{val[1]})"
                    else:
                        self.grid_content[row][i] = str(val)
        
        for name, info in pointers.items():
            arr_name = info.get('array')
            if arr_name in self._arrays:
                row = self._arrays[arr_name]['row'] + 1
                index = info.get('index')
                if 0 <= row < self.rows and 0 <= index < self.cols:
                    self.grid_content[row][index] += f" \033[1;92m↑{name}\033[0m"

    def _update_highlights(self):
        for key in list(self.highlight_grid.keys()):
            self.highlight_grid[key]['ttl'] -= 1
            if self.highlight_grid[key]['ttl'] <= 0:
                del self.highlight_grid[key]

    def _render_grid(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{self.title}\n" + "=" * len(self.title))
        separator = "+" + ("-" * self.cell_width + "+") * self.cols
        print(separator)
        for r in range(self.rows):
            row_str_parts = []
            for c in range(self.cols):
                cell_content = self.grid_content[r][c]
                highlight = self.highlight_grid.get((r,c))
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
        self._texts['message'] = {'text': message, 'row': 0, 'col': 0}
        self._draw_to_grid(pointers=pointers)
        self._render_grid()
        if not final:
            self._update_highlights()
            time.sleep(self.speed)

# --- "Minimum Interval to Include Each Query" Visualization ---

def visualize_min_interval(intervals, queries):
    
    # --- Setup ---
    intervals.sort()
    
    # Keep track of original indices for queries
    sorted_queries = sorted([(query, i) for i, query in enumerate(queries)])
    
    res = [-1] * len(queries)
    min_heap = []
    interval_idx = 0

    # --- Visualizer Setup ---
    viz = GridVisualizer(rows=10, cols=max(len(intervals), len(queries)), title="Minimum Interval Sweep-Line")
    viz.place_array_in_row('intervals', intervals, grid_row=2)
    viz.place_array_in_row('queries', sorted_queries, grid_row=4)
    viz.place_array_in_row('heap', [], grid_row=6)
    viz.place_array_in_row('result', res, grid_row=8)
    
    viz.place_text_in_cell('intervals_label', "Intervals:", 1, 0)
    viz.place_text_in_cell('queries_label', "Queries:", 3, 0)
    viz.place_text_in_cell('heap_label', "Min-Heap (len, right):", 5, 0)
    viz.place_text_in_cell('result_label', "Result:", 7, 0)

    viz.capture(message="Sorted intervals and queries.")

    # --- Algorithm Execution ---
    for q_idx, (q_val, original_index) in enumerate(sorted_queries):
        message = f"Sweep line at query: {q_val}"
        pointers = {'q': {'array': 'queries', 'index': q_idx}}
        viz.capture(message=message, pointers=pointers)

        # 1. Add active intervals to heap
        while interval_idx < len(intervals) and intervals[interval_idx][0] <= q_val:
            left, right = intervals[interval_idx]
            heapq.heappush(min_heap, (right - left + 1, right))
            
            viz._arrays['heap']['data'] = sorted(min_heap)
            viz.highlight_cell('intervals', interval_idx, 'green', 2)
            viz.highlight_cell('heap', len(min_heap)-1, 'green', 2)
            viz.capture(
                message=f"Query {q_val} >= interval start {left}. Adding to heap.",
                pointers={'q': {'array': 'queries', 'index': q_idx}, 'i': {'array': 'intervals', 'index': interval_idx}})
            interval_idx += 1
        
        # 2. Remove expired intervals from heap
        while min_heap and min_heap[0][1] < q_val:
            viz.highlight_cell('heap', 0, 'red', 2)
            viz.capture(
                message=f"Top of heap ends at {min_heap[0][1]} < query {q_val}. Popping.",
                pointers={'q': {'array': 'queries', 'index': q_idx}})
            heapq.heappop(min_heap)
            viz._arrays['heap']['data'] = sorted(min_heap)
            viz.capture(
                message="Heap after popping expired interval.",
                pointers={'q': {'array': 'queries', 'index': q_idx}})

        # 3. Get result for current query
        if min_heap:
            res[original_index] = min_heap[0][0]
            viz.highlight_cell('heap', 0, 'yellow', 2)
            viz.highlight_cell('result', original_index, 'yellow', 2)
            viz.capture(
                message=f"Smallest active interval has length {res[original_index]}. Storing result.",
                pointers={'q': {'array': 'queries', 'index': q_idx}})
        else:
             viz.capture(
                message=f"No active interval for query {q_val}. Result is -1.",
                pointers={'q': {'array': 'queries', 'index': q_idx}})
            
    viz.capture(message="Algorithm finished.", final=True)


if __name__ == "__main__":
    intervals_input = [[1,4],[2,4],[3,6],[4,4]]
    queries_input = [2,3,4,5]
    visualize_min_interval(intervals_input, queries_input)

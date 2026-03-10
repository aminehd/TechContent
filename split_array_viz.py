import os
import time
import re
import bisect

# --- GridVisualizer Class (self-contained) ---

def get_visible_len(s):
    return len(re.sub(r'\033\[[0-9;]*m', '', s))

class GridVisualizer:
    def __init__(self, rows, cols, cell_width=7, title="Grid Visualizer"):
        self.rows = rows
        self.cols = cols
        self.cell_width = cell_width
        self.title = title
        self.speed = 2.0
        self.grid_content = [['' for _ in range(cols)] for _ in range(rows)]
        self.highlight_grid = [[None for _ in range(cols)] for _ in range(rows)]
        self._arrays = {}
        self._texts = {}

    def place_array_in_row(self, name, data, grid_row):
        self._arrays[name] = {'data': data, 'row': grid_row}

    def place_text_in_cell(self, name, text, row, col):
        self._texts[name] = {'text': text, 'row': row, 'col': col}

    def highlight_cell(self, row, col, color='yellow', ttl=1):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.highlight_grid[row][col] = {'color': color, 'ttl': ttl}

    def _draw_to_grid(self, pointers={}):
        self.grid_content = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        
        for text_info in self._texts.values():
             self.grid_content[text_info['row']][text_info['col']] = text_info['text']

        for arr_info in self._arrays.values():
            row = arr_info['row']
            for i, val in enumerate(arr_info['data']):
                if 0 <= i < self.cols:
                    self.grid_content[row][i] = str(val)
        
        for name, info in pointers.items():
            arr_name = info.get('array', 'prefix_sum') # Default to prefix_sum array
            arr_info = self._arrays.get(arr_name)
            if arr_info:
                pointer_row = arr_info['row'] + 1
                index = info['index']
                if 0 <= pointer_row < self.rows and 0 <= index < self.cols:
                    self.grid_content[pointer_row][index] += f" \033[1;92m↑{name}\033[0m"
    
    def _update_highlights(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.highlight_grid[r][c]:
                    self.highlight_grid[r][c]['ttl'] -= 1
                    if self.highlight_grid[r][c]['ttl'] <= 0:
                        self.highlight_grid[r][c] = None

    def _render_grid(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{self.title}\n" + "=" * len(self.title))
        separator = "+" + ("-" * self.cell_width + "+") * self.cols
        print(separator)
        for r in range(self.rows):
            row_str_parts = []
            for c in range(self.cols):
                cell_content = self.grid_content[r][c]
                highlight = self.highlight_grid[r][c]
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

# --- "Ways to Split Array Into Three Subarrays" Visualization ---

def visualize_split_array(nums):
    n = len(nums)
    MOD = 10**9 + 7
    
    # 1. Create Prefix Sum Array
    prefix_sum = [0] * (n + 1)
    for i in range(n):
        prefix_sum[i+1] = prefix_sum[i] + nums[i]

    # --- Visualizer Setup ---
    viz = GridVisualizer(rows=8, cols=n + 1, cell_width=5, title="Ways to Split Array")
    viz.place_array_in_row('nums', [""] + nums, grid_row=2) # Pad for alignment
    viz.place_array_in_row('prefix_sum', prefix_sum, grid_row=4)
    viz.place_text_in_cell('nums_label', "nums:", 1, 0)
    viz.place_text_in_cell('prefix_label', "Prefix Sum:", 3, 0)
    viz.place_text_in_cell('count_label', "Count:", 6, 0)

    viz.capture(message="Calculated prefix sum array.")

    count = 0
    
    # 2. Iterate through first split point 'i'
    for i in range(1, n - 1):
        left_sum = prefix_sum[i]
        viz._texts['count'] = {'text': f"{count}", 'row': 6, 'col': 1}
        viz.capture(
            message=f"i={i}: left_sum = {left_sum}",
            pointers={'i': {'index': i}}
        )

        # 3. Find j_min (lower bound for second split)
        # We need P[j] >= 2 * P[i]  =>  P[j] - P[i] >= P[i]
        target_j_min = 2 * left_sum
        # bisect_left finds first j where prefix_sum[j] is not less than target
        j_min = bisect.bisect_left(prefix_sum, target_j_min, lo=i + 1, hi=n)
        
        viz.highlight_cell(row=4, col=j_min, color='yellow', ttl=2)
        viz.capture(
            message=f"i={i}: Find j_min where P[j] >= 2*P[i]={target_j_min}. Found j_min={j_min}",
            pointers={'i': {'index': i}, 'j_min': {'index': j_min}}
        )
        
        # 4. Find j_max (upper bound for second split)
        # We need P[n] - P[j] >= P[j] - P[i]  =>  P[j] <= (P[n] + P[i]) / 2
        target_j_max = (prefix_sum[n] + left_sum) // 2
        # bisect_right finds insertion point, so we look for first element > target and go back one
        j_max = bisect.bisect_right(prefix_sum, target_j_max, lo=j_min, hi=n)

        viz.highlight_cell(row=4, col=j_max -1, color='yellow', ttl=2)
        viz.capture(
            message=f"i={i}: Find j_max where P[j] <= (P[n]+P[i])/2={target_j_max}. Found j_max={j_max}",
            pointers={'i': {'index': i}, 'j_min': {'index': j_min}, 'j_max-1': {'index': j_max-1}}
        )

        # 5. Add valid splits to count
        if j_max > j_min:
            num_splits = j_max - j_min
            count = (count + num_splits) % MOD
            viz._texts['count'] = {'text': f"{count}", 'row': 6, 'col': 1}
            for k in range(j_min, j_max):
                viz.highlight_cell(row=4, col=k, color='green', ttl=2)
            viz.capture(
                message=f"i={i}: Valid j range is [{j_min}, {j_max-1}]. Adding {num_splits} to count.",
                pointers={'i': {'index': i}}
            )

    viz.capture(message=f"Finished. Total good ways: {count}", final=True)


if __name__ == "__main__":
    # nums_input = [1,1,1]
    nums_input = [0,3,3]
    # nums_input = [3,2,1]
    visualize_split_array(nums_input)

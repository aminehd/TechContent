import os
import time
import re

# --- GridVisualizer Class (self-contained) ---

def get_visible_len(s):
    return len(re.sub(r'\033\[[0-9;]*m', '', s))

class GridVisualizer:
    def __init__(self, rows, cols, cell_width=8, title="Grid Visualizer"):
        self.rows = rows
        self.cols = cols
        self.cell_width = cell_width
        self.title = title
        self.speed = 1.0
        self.grid_content = [['' for _ in range(cols)] for _ in range(rows)]
        self._arrays = {}
        self._texts = {}
        self._highlights = {}

    def place_array_in_row(self, name, data, grid_row):
        self._arrays[name] = {'data': data, 'row': grid_row}

    def place_text_in_cell(self, name, text, row, col):
        self._texts[name] = {'text': text, 'row': row, 'col': col}

    def highlight_cell(self, array_name, index, color='yellow', ttl=1):
        if array_name in self._arrays and 0 <= index < len(self._arrays[array_name]['data']):
            row = self._arrays[array_name]['row']
            col = index
            self._highlights[(row, col)] = {'color': color, 'ttl': ttl}

    def _draw_to_grid(self, pointers={}):
        self.grid_content = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        
        for name, text_info in self._texts.items():
             self.grid_content[text_info['row']][text_info['col']] = str(text_info['text'])

        for arr_name, arr_info in self._arrays.items():
            row = arr_info['row']
            for i, val in enumerate(arr_info['data']):
                if 0 <= i < self.cols:
                    self.grid_content[row][i] = str(val)
        
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
        self._texts['message'] = {'text': message, 'row': 0, 'col': 0}
        self._draw_to_grid(pointers=pointers)
        self._render_grid()
        if not final:
            self._update_highlights()
            time.sleep(self.speed)

# --- "Capacity To Ship Packages Within D Days" Visualization ---

def visualize_shipping(weights, days):
    
    # --- Visualizer Setup ---
    viz = GridVisualizer(rows=12, cols=len(weights), title="Ship Packages within D Days")
    viz.place_array_in_row('weights', weights, grid_row=2)
    viz.place_text_in_cell('weights_label', "Weights:", 1, 0)
    viz.place_text_in_cell('ships_label', "Ships:", 4, 0)
    viz.place_text_in_cell('search_label', "Binary Search for Capacity:", 7, 0)

    # --- Algorithm ---
    l, r = max(weights), sum(weights)
    ans = r
    
    while l <= r:
        mid = (l + r) // 2
        
        # --- `canship` check visualization ---
        d_used = 1
        current_load = 0
        ships = [0] * days
        
        # Update binary search display
        viz.place_text_in_cell('l', f"l: {l}", 8, 0)
        viz.place_text_in_cell('r', f"r: {r}", 8, 2)
        viz.place_text_in_cell('mid', f"mid: {mid}", 8, 4)
        viz.place_text_in_cell('ans', f"ans: {ans}", 8, 6)
        viz.highlight_cell('weights', -1) # Clear old highlights
        
        viz.capture(message=f"Testing capacity w = {mid}...")
        
        possible = True
        for i, weight in enumerate(weights):
            if weight > mid:
                possible = False
                viz.highlight_cell('weights', i, 'red', 3)
                viz.capture(message=f"Impossible: weight {weight} > capacity {mid}")
                break

            if current_load + weight <= mid:
                current_load += weight
            else:
                d_used += 1
                current_load = weight

            if d_used > days:
                possible = False
                viz.highlight_cell('weights', i, 'red', 3)
                viz.capture(message=f"Impossible: requires more than {days} days.")
                break
            
            # Update ship visualization
            ships[d_used - 1] = current_load
            viz.place_array_in_row('ships', [f"{s}/{mid}" for s in ships], grid_row=5)
            viz.capture(
                message=f"Loading weight {weight}. Day {d_used}, Load: {current_load}/{mid}",
                pointers={'w': {'array': 'weights', 'index': i}}
            )

        if possible:
            viz.capture(message=f"SUCCESS: Capacity {mid} works in {d_used} days. Trying smaller...")
            ans = mid
            r = mid - 1
        else:
            viz.capture(message=f"FAILURE: Capacity {mid} is too small. Trying larger...")
            l = mid + 1
            
    viz.place_text_in_cell('ans', f"ans: {ans}", 8, 6)
    viz.capture(message=f"Finished! Optimal capacity is {ans}", final=True)


if __name__ == "__main__":
    weights_input = [1,2,3,4,5,6,7,8,9,10]
    days_input = 5
    visualize_shipping(weights_input, days_input)

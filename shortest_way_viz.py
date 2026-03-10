import os
import time
import re
import collections

# --- GridVisualizer Class (self-contained) ---

def get_visible_len(s):
    return len(re.sub(r'\033\[[0-9;]*m', '', s))

class GridVisualizer:
    def __init__(self, rows, cols, cell_width=5, title="Grid Visualizer"):
        self.rows = rows
        self.cols = cols
        self.cell_width = cell_width
        self.title = title
        self.speed = 1.5
        self.grid_content = [['' for _ in range(cols)] for _ in range(rows)]
        self._arrays = {}
        self._texts = {}
        self._highlights = {}

    def place_array_in_row(self, name, data, grid_row):
        self._arrays[name] = {'data': data, 'row': grid_row}

    def place_text(self, name, text):
        self._texts[name] = text

    def highlight_cell(self, array_name, index, color='yellow', ttl=1):
        if array_name in self._arrays and 0 <= index < len(self._arrays[array_name]['data']):
            row = self._arrays[array_name]['row']
            col = index
            self._highlights[(row, col)] = {'color': color, 'ttl': ttl}

    def _draw_to_grid(self, pointers={}):
        self.grid_content = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        
        for name, text_info in self._texts.items():
            r, c = text_info['row'], text_info['col']
            self.grid_content[r][c] = text_info['text']

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
        self.place_text('message', {'text': message, 'row': 0, 'col': 0})
        self._draw_to_grid(pointers=pointers)
        self._render_grid()
        if not final:
            self._update_highlights()
            time.sleep(self.speed)

# --- "Shortest Way to Form String" Visualization ---

def visualize_shortest_way(source, target):
    # --- Preprocessing ---
    char_indices = collections.defaultdict(list)
    for i, char in enumerate(source):
        char_indices[char].append(i)

    if any(c not in char_indices for c in target):
        print("Impossible to form target. Character not in source.")
        return

    # --- Visualizer Setup ---
    viz = GridVisualizer(rows=12, cols=max(len(source), len(target)), title="Shortest Way to Form String")
    viz.place_array_in_row('source', list(source), 1)
    viz.place_array_in_row('target', list(target), 4)

    # --- Algorithm Execution ---
    count = 1
    source_idx = -1
    target_idx = 0

    while target_idx < len(target):
        char_to_find = target[target_idx]
        indices_list = char_indices[char_to_find]

        viz.place_text('count_label', {'text': "Count:", 'row': 9, 'col': 0})
        viz.place_text('count_val', {'text': str(count), 'row': 9, 'col': 1})
        viz.place_text('s_idx_label', {'text': "source_idx:", 'row': 10, 'col': 0})
        viz.place_text('s_idx_val', {'text': str(source_idx), 'row': 10, 'col': 1})
        
        pointers = {
            'target': {'array': 'target', 'index': target_idx},
        }
        if source_idx != -1:
            pointers['source'] = {'array': 'source', 'index': source_idx}

        viz.capture(
            message=f"Looking for '{char_to_find}' in source with index > {source_idx}",
            pointers=pointers
        )

        # Binary search visualization
        low, high = 0, len(indices_list) - 1
        next_pos = -1
        
        while low <= high:
            mid = (low + high) // 2
            
            # Show binary search on the indices list
            viz.place_array_in_row('indices', indices_list, 7)
            viz.place_text('indices_label', {'text': f"Indices for '{char_to_find}':", 'row': 6, 'col': 0})

            viz.highlight_cell('indices', mid, 'yellow', 2)
            viz.capture(
                message=f"Binary searching... Is {indices_list[mid]} > {source_idx}?",
                pointers=pointers
            )

            if indices_list[mid] > source_idx:
                next_pos = mid
                high = mid - 1
            else:
                low = mid + 1
        
        if next_pos == -1:
            count += 1
            source_idx = -1
            viz.capture(message="Not found in rest of source. Starting new subsequence.", pointers=pointers)
            # Re-run loop for same target_idx
        else:
            source_idx = indices_list[next_pos]
            target_idx += 1
            pointers['source'] = {'array': 'source', 'index': source_idx}
            viz.highlight_cell('source', source_idx, 'green', 2)
            viz.capture(message=f"Found. Jumping source pointer to index {source_idx}.", pointers=pointers)
    
    viz.capture(message=f"Finished! Minimum subsequences: {count}", final=True)


if __name__ == "__main__":
    source_str = "abcbc"
    target_str = "abcbc"
    visualize_shortest_way(source_str, target_str)

import os
import time
import re

# --- All code is now in this single file ---

def get_visible_len(s):
    """Calculates the visible length of a string, ignoring ANSI color codes."""
    return len(re.sub(r'\033\[[0-9;]*m', '', s))

class GridVisualizer:
    """
    A self-contained visualizer that renders algorithm states on a true, cell-based grid.
    """
    def __init__(self, rows, cols, cell_width=7, title="Grid Visualizer"):
        self.rows = rows
        self.cols = cols
        self.cell_width = cell_width
        self.title = title
        self.speed = 1.0
        self.grid_content = [['' for _ in range(cols)] for _ in range(rows)]
        self.highlight_grid = [[None for _ in range(cols)] for _ in range(rows)]
        self._arrays = {}
        self._effects = []

    def place_array_in_row(self, name, data, grid_row):
        """Dedicates a grid row to display an array."""
        self._arrays[name] = {'data': data, 'row': grid_row}

    def highlight_cell(self, row, col, color='yellow', ttl=1):
        """Schedules a cell to be highlighted."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.highlight_grid[row][col] = {'color': color, 'ttl': ttl}

    def replace_value(self, array_name, index, new_value):
        """Replaces a value and triggers the 'falling value' animation."""
        if array_name not in self._arrays or not (0 <= index < len(self._arrays[array_name]['data'])):
            return

        arr_info = self._arrays[array_name]
        old_value = arr_info['data'][index]
        arr_info['data'][index] = new_value

        self._effects.append({
            'type': 'text',
            'text': f"\033[91m{old_value}\033[0m",
            'row': arr_info['row'] + 2,
            'col': index,
            'ttl': 2
        })
        self.highlight_cell(arr_info['row'], index, 'green', 2)

    def _draw_to_grid(self, message="", pointers={}):
        """Populates the internal grid_content with raw data strings."""
        self.grid_content = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        
        # Place message
        self.grid_content[0][0] = message

        # Place arrays
        for arr_info in self._arrays.values():
            row = arr_info['row']
            for i, val in enumerate(arr_info['data']):
                if 0 <= i < self.cols:
                    self.grid_content[row][i] = str(val)
        
        # Place pointers
        for name, index in pointers.items():
            # Assuming all pointers point to the first array for this simple model
            first_arr_name = next(iter(self._arrays))
            arr_info = self._arrays[first_arr_name]
            pointer_row = arr_info['row'] + 1
            if 0 <= pointer_row < self.rows and 0 <= index < self.cols:
                self.grid_content[pointer_row][index] += f" \033[1;92m↑{name}\033[0m"

        # Process effects
        for effect in self._effects:
            if effect['type'] == 'text':
                row, col = effect['row'], effect['col']
                if 0 <= row < self.rows and 0 <= col < self.cols:
                    self.grid_content[row][col] += effect['text']

    def _update_effects(self):
        """Updates the TTL of effects and highlights."""
        for r in range(self.rows):
            for c in range(self.cols):
                if self.highlight_grid[r][c]:
                    self.highlight_grid[r][c]['ttl'] -= 1
                    if self.highlight_grid[r][c]['ttl'] <= 0:
                        self.highlight_grid[r][c] = None
        
        self._effects = [eff for eff in self._effects if eff.get('ttl', 0) > 1]
        for eff in self._effects:
            eff['ttl'] -= 1

    def _render_grid(self):
        """Renders the grid with formatting."""
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
        """Renders a single frame."""
        self._draw_to_grid(message=message, pointers=pointers)
        self._render_grid()
        if not final:
            self._update_effects()
            time.sleep(self.speed)

# --- Algorithm is now in the same file ---

def standalone_demo(data, target):
    """
    Demonstrates the flashy animation using the self-contained GridVisualizer.
    """
    left, right = 0, len(data) - 1
    replacement_done = False

    viz = GridVisualizer(rows=8, cols=len(data), cell_width=7, title="Standalone Flashy Demo")
    viz.place_array_in_row('main_array', data, grid_row=2)
    viz.speed = 0.9

    while left < right:
        message = ""
        pointers = {'L': left, 'R': right}

        if right == 3 and not replacement_done:
            message = "Replacing value 99 with 5!"
            viz.replace_value(array_name='main_array', index=right, new_value=5)
            replacement_done = True
        else:
            current_sum = data[left] + data[right]
            message = f"L({data[left]}) + R({data[right]}) = {current_sum}"

        viz.capture(message=message, pointers=pointers)

        if data[left] + data[right] < target:
            left += 1
        else:
            right -= 1
    
    viz.capture(message="Finished", pointers={'L':left, 'R':right}, final=True)
    for _ in range(3): # Extra captures to let effects fade
        viz.capture(message="Finished", pointers={'L':left, 'R':right}, final=True)
    print("\nVisualization complete.")

if __name__ == "__main__":
    initial_data = [1, 2, 8, 99, 11, 14]
    target_sum = 15
    standalone_demo(initial_data, target_sum)

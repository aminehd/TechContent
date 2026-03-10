import os
import time
import re

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
        self.highlight_grid = [[None for _ in range(cols)] for _ in range(rows)]
        self._arrays = {}

    def place_array_in_row(self, name, data, grid_row):
        self._arrays[name] = {'data': data, 'row': grid_row}

    def highlight_cell(self, row, col, color='yellow', ttl=1):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.highlight_grid[row][col] = {'color': color, 'ttl': ttl}

    def _draw_to_grid(self, message="", pointers={}):
        self.grid_content = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        self.grid_content[0][0] = message

        for arr_name, arr_info in self._arrays.items():
            row = arr_info['row']
            for i, val in enumerate(arr_info['data']):
                if 0 <= i < self.cols:
                    # Custom formatter for different array types
                    if isinstance(val, tuple):
                        self.grid_content[row][i] = f"({val[0]}, {val[1]})"
                    else:
                        self.grid_content[row][i] = str(val)
        
        for name, info in pointers.items():
            arr_info = self._arrays.get(info['array'])
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
        self._draw_to_grid(message=message, pointers=pointers)
        self._render_grid()
        if not final:
            self._update_highlights()
            time.sleep(self.speed)

# --- Skyline Event Sorting Visualization ---

def visualize_event_sorting(buildings):
    """
    Visualizes the creation and sorting of events for the Skyline problem.
    """
    # --- Setup ---
    viz = GridVisualizer(rows=10, cols=10, cell_width=12, title="Skyline: The Event Sorting Trick")

    # Static Labels
    viz.grid_content[1][0] = "Unsorted:"
    viz.grid_content[4][0] = "Sorted:"
    
    # --- 1. Create Events ---
    events = []
    for L, R, H in buildings:
        # For this visualization, we only need the (x, height) part of the event
        events.append((L, -H)) # Start event
        events.append((R, H))  # End event
    
    viz.place_array_in_row('unsorted', events, grid_row=2)
    viz.capture(message="Generated events from buildings. (Start events have -Height)")

    # --- 2. Animate the Sort (using a simple insertion sort for clarity) ---
    sorted_events = []
    viz.place_array_in_row('sorted', sorted_events, grid_row=5)

    for i, event_to_insert in enumerate(events):
        viz.highlight_cell(row=2, col=i, color='yellow', ttl=3)
        message = f"Picking next event to sort: {event_to_insert}"
        viz.capture(message=message, pointers={'Ins': {'array': 'unsorted', 'index': i}})

        # Find insertion position
        j = 0
        while j < len(sorted_events) and sorted_events[j] <= event_to_insert:
            viz.highlight_cell(row=5, col=j, color='red', ttl=1)
            message = f"Comparing {event_to_insert} with {sorted_events[j]}..."
            pointers = {
                'Ins': {'array': 'unsorted', 'index': i},
                'Comp': {'array': 'sorted', 'index': j}
            }
            viz.capture(message=message, pointers=pointers)
            j += 1
        
        message = f"Found insertion spot for {event_to_insert} at index {j}"
        if j < len(sorted_events):
             viz.highlight_cell(row=5, col=j, color='green', ttl=2)
        viz.capture(message=message, pointers={'Ins': {'array': 'unsorted', 'index': i}})

        sorted_events.insert(j, event_to_insert)
        viz.capture(message=f"Inserted {event_to_insert}. List remains sorted.", pointers={})

    # Final view
    message="Sorting complete! Notice start events (-H) come before end events (H) at the same 'x'."
    viz.capture(message=message, final=True)
    print("\nDone.")


if __name__ == "__main__":
    # A simple set of buildings that shows all sorting cases
    # Two buildings start at the same time, one ends when another starts, etc.
    buildings_input = [[2, 9, 10], [3, 7, 15]]
    visualize_event_sorting(buildings_input)

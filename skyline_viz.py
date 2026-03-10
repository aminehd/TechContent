import os
import time
import re
import heapq

# --- GridVisualizer Class (copied from standalone_viz.py for self-containment) ---

def get_visible_len(s):
    """Calculates the visible length of a string, ignoring ANSI color codes."""
    return len(re.sub(r'\033\[[0-9;]*m', '', s))

class GridVisualizer:
    """
    A self-contained visualizer that renders algorithm states on a true, cell-based grid.
    """
    def __init__(self, rows, cols, cell_width=10, title="Grid Visualizer"):
        self.rows = rows
        self.cols = cols
        self.cell_width = cell_width
        self.title = title
        self.speed = 1.5
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

    def _draw_to_grid(self, message="", pointers={}):
        """Populates the internal grid_content with raw data strings."""
        self.grid_content = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        
        # Place message and other static text
        self.grid_content[0][0] = message

        # Place arrays
        for arr_info in self._arrays.values():
            row = arr_info['row']
            # Custom formatter for different array types
            for i, val in enumerate(arr_info['data']):
                if 0 <= i < self.cols:
                    if isinstance(val, tuple):
                        # Nicer formatting for heap/event tuples
                        self.grid_content[row][i] = f"({val[0]},{str(val[1])[:4]})"
                    else:
                        self.grid_content[row][i] = str(val)
        
        # Place pointers
        for name, index in pointers.items():
            # This logic assumes pointers point to the 'events' array
            if 'events' in self._arrays:
                arr_info = self._arrays['events']
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

# --- Skyline Algorithm Visualization ---

def visualize_skyline(buildings):
    """
    Computes and visualizes the skyline using a Sweep Line algorithm.
    """
    # 1. Create Events
    events = []
    for L, R, H in buildings:
        events.append((L, -H, R)) # Start event
        events.append((R, 0, 0))  # End event 
    events.sort()

    # --- Visualizer Setup ---
    viz = GridVisualizer(rows=12, cols=len(events), cell_width=12, title="Skyline Algorithm")
    viz.place_array_in_row('events', events, grid_row=2)
    viz.place_array_in_row('heap', [], grid_row=5)
    viz.place_array_in_row('result', [], grid_row=8)
    
    # Static Labels
    viz.grid_content[1][0] = "Events:"
    viz.grid_content[4][0] = "Max-Heap:"
    viz.grid_content[7][0] = "Result:"
    viz.grid_content[10][0] = "Sweep Line:"


    # --- Algorithm Execution ---
    max_heap = [(0, float('inf'))] # (neg_height, right_edge)
    viz._arrays['heap']['data'] = max_heap # Initial heap state
    
    result = []
    last_max_height = 0

    for i, (x, neg_h, R) in enumerate(events):
        
        message = f"Sweep line at x={x}. Processing event: ({x}, {neg_h}, {R})"
        viz._arrays['heap']['data'] = sorted(max_heap) # Keep heap display sorted
        viz.capture(message=message, pointers={'event': i})

        # 1. Pop expired buildings (Lazy Removal)
        while max_heap and max_heap[0][1] <= x:
            expired_building = heapq.heappop(max_heap)
            message = f"x={x}: Popping expired building {expired_building} from heap."
            viz._arrays['heap']['data'] = sorted(max_heap)
            viz.highlight_cell(row=5, col=0, color='red', ttl=2)
            viz.capture(message=message, pointers={'event': i})
            
        # 2. Process current event
        if neg_h != 0: # It's a start event
            heapq.heappush(max_heap, (neg_h, R))
            message = f"x={x}: Start event. Pushing ({-neg_h}, {R}) to heap."
            viz._arrays['heap']['data'] = sorted(max_heap)
            viz.highlight_cell(row=5, col=len(max_heap)-1, color='green', ttl=2)
            viz.capture(message=message, pointers={'event': i})
            
        # 3. Check for change in max height
        current_max_height = -max_heap[0][0]
        
        if current_max_height != last_max_height:
            message = f"x={x}: Max height changed from {last_max_height} to {current_max_height}. Appending point."
            result.append([x, current_max_height])
            last_max_height = current_max_height
            viz._arrays['result']['data'] = result
            viz.highlight_cell(row=8, col=len(result)-1, color='yellow', ttl=2)
            viz.capture(message=message, pointers={'event': i})

    viz.capture(message="Algorithm Finished.", final=True)
    print("\nFinal Skyline:", result)


if __name__ == "__main__":
    buildings_input = [[2,9,10], [3,7,15], [5,12,12], [15,20,10], [19,24,8]]
    visualize_skyline(buildings_input)

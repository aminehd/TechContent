import os
import time
import re

# --- GridVisualizer Class (self-contained) ---

def get_visible_len(s):
    """Calculates the visible length of a string, ignoring ANSI color codes."""
    return len(re.sub(r'\033\[[0-9;]*m', '', s))

class GridVisualizer:
    def __init__(self, rows, cols, cell_width=5, title="Grid Visualizer"):
        self.rows = rows
        self.cols = cols
        self.cell_width = cell_width
        self.title = title
        self.speed = 0.5
        self.grid_content = [['' for _ in range(cols)] for _ in range(rows)]
        self.highlight_grid = [[None for _ in range(cols)] for _ in range(rows)]
        self._arrays = {}
        self._texts = {}
        self._custom_cells = {} # For individual cell content not tied to arrays/text

    def place_array_in_row(self, name, data, grid_row):
        self._arrays[name] = {'data': data, 'row': grid_row}

    def place_text_in_cell(self, name, text, row, col):
        self._texts[name] = {'text': text, 'row': row, 'col': col}

    def place_custom_cell(self, row, col, content, color=None, ttl=1):
        """Places custom content in a specific cell, can have color and TTL."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self._custom_cells[(row, col)] = {'content': content, 'color': color, 'ttl': ttl}

    def highlight_cell(self, row, col, color='yellow', ttl=1):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.highlight_grid[row][col] = {'color': color, 'ttl': ttl}

    def _draw_to_grid(self, pointers={}):
        self.grid_content = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        
        # Place pre-defined texts
        for text_info in self._texts.values():
             self.grid_content[text_info['row']][text_info['col']] = text_info['text']

        # Place arrays
        for arr_name, arr_info in self._arrays.items():
            row = arr_info['row']
            for i, val in enumerate(arr_info['data']):
                if 0 <= i < self.cols:
                    if arr_name == 'events': # Special formatting for event tuples
                        self.grid_content[row][i] = f"({val[0]},{val[1]:+d})"
                    else:
                        self.grid_content[row][i] = str(val)
        
        # Place custom cells
        for (r, c), cell_info in self._custom_cells.items():
            content = cell_info['content']
            if cell_info['color']:
                color_code = {'green': '92', 'yellow': '93', 'red': '91', 'blue': '94'}.get(cell_info['color'], '97')
                content = f"\033[{color_code}m{content}\033[0m"
            self.grid_content[r][c] = content


        # Place pointers
        for name, info in pointers.items():
            arr_name = info.get('array')
            if arr_name and arr_name in self._arrays:
                arr_info = self._arrays[arr_name]
                pointer_row = arr_info['row'] + 1
                index = info['index']
                if 0 <= pointer_row < self.rows and 0 <= index < self.cols:
                    self.grid_content[pointer_row][index] += f" \033[1;92m↑{name}\033[0m"
            elif arr_name == 'street_viz': # Pointer for the street visual
                row = info.get('row', 2) # Default street row
                index = info['index']
                if 0 <= row + 1 < self.rows and 0 <= index < self.cols:
                    self.grid_content[row + 1][index] += f" \033[1;94m↑{name}\033[0m" # Blue pointer
    
    def _update_highlights_and_custom_cells(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.highlight_grid[r][c]:
                    self.highlight_grid[r][c]['ttl'] -= 1
                    if self.highlight_grid[r][c]['ttl'] <= 0:
                        self.highlight_grid[r][c] = None
        
        for key in list(self._custom_cells.keys()):
            self._custom_cells[key]['ttl'] -= 1
            if self._custom_cells[key]['ttl'] <= 0:
                del self._custom_cells[key]

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
                    color_code = {'green': '42', 'yellow': '43', 'red': '41', 'blue': '44'}.get(highlight['color'], '47')
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
        self._texts['message_display'] = {'text': message, 'row': 0, 'col': 0}
        self._draw_to_grid(pointers=pointers)
        self._render_grid()
        if not final:
            self._update_highlights_and_custom_cells()
            time.sleep(self.speed)

# --- "Brightest Position on Street" Visualization ---

def visualize_brightest_position(lights):
    """
    Visualizes the Brightest Position on Street problem using a Line Sweep algorithm.
    """
    # 1. Determine the coordinate range for visualization
    min_coord = min(pos - r for pos, r in lights) - 2
    max_coord = max(pos + r for pos, r in lights) + 2
    coord_range = max_coord - min_coord + 1
    
    # Map raw coordinates to grid columns
    def coord_to_col(coord):
        return coord - min_coord

    # 2. Create Events
    events = []
    for pos, r in lights:
        events.append((pos - r, 1))      # Coverage starts
        events.append((pos + r + 1, -1)) # Coverage ends
    events.sort()

    # --- Visualizer Setup ---
    viz = GridVisualizer(rows=12, cols=coord_range, cell_width=4, title="Brightest Position on Street")
    viz.speed = 0.3

    # Labels
    viz.place_text_in_cell('street_label', "Street:", 2, 0)
    viz.place_text_in_cell('events_label', "Events:", 6, 0)
    viz.place_text_in_cell('curr_bright_label', "Current Brightness:", 8, 0)
    viz.place_text_in_cell('max_bright_label', "Max Brightness:", 9, 0)
    viz.place_text_in_cell('best_pos_label', "Best Position:", 10, 0)

    # Place events array
    viz.place_array_in_row('events', events, grid_row=7)

    # Draw the initial street
    for c in range(coord_range):
        viz.place_custom_cell(row=3, col=c, content=str(min_coord + c)) # Coordinates
        viz.place_custom_cell(row=2, col=c, content='.', color='blue', ttl=float('inf')) # Street background

    # --- Algorithm Execution ---
    max_brightness = 0
    curr_brightness = 0
    best_pos = 0
    
    # Store the actual brightness for each position
    brightness_on_street = [0] * coord_range

    event_idx_ptr = 0
    while event_idx_ptr < len(events):
        x, change = events[event_idx_ptr]
        
        # Process all events at current x
        current_x_events = []
        while event_idx_ptr < len(events) and events[event_idx_ptr][0] == x:
            current_x_events.append(events[event_idx_ptr])
            event_idx_ptr += 1

        # Update brightness based on all events at this x-coordinate
        for cx, cchange in current_x_events:
            curr_brightness += cchange

        # Update actual brightness on the street visual
        # This is where the brightness in the interval (previous_x, x] changes
        # For simplicity, we just visualize brightness at current x.
        brightness_on_street[coord_to_col(x)] = curr_brightness

        # Capture the state
        message = f"Sweep line at x={x}. Change={sum(c for _,c in current_x_events)}. Current Brightness: {curr_brightness}"
        
        # Highlight current sweep position on street
        viz.place_custom_cell(row=2, col=coord_to_col(x), content='@', color='yellow', ttl=2)
        
        # Update dynamic text
        viz.place_text_in_cell('curr_bright_val', f"{curr_brightness}", 8, 1)
        
        # Check for max_brightness at the end of all events at the same coordinate
        if curr_brightness > max_brightness:
            max_brightness = curr_brightness
            best_pos = x
            viz.place_text_in_cell('max_bright_val', f"{max_brightness}", 9, 1)
            viz.place_text_in_cell('best_pos_val', f"{best_pos}", 10, 1)
            viz.highlight_cell(row=2, col=coord_to_col(best_pos), color='red', ttl=float('inf')) # Keep highlighted

        # For visualizing the range of brightness:
        # We need to apply brightness to all cells from prev_x up to x
        # This requires more complex state management in the visualizer.
        # For now, just mark the current sweep position and best_pos.
        
        viz.capture(message=message, pointers={'event': {'array': 'events', 'index': event_idx_ptr - 1 if event_idx_ptr > 0 else 0, 'row': 7}})
        
    viz.capture(message="Algorithm Finished. Final best position: " + str(best_pos), final=True)

if __name__ == "__main__":
    lights_input = [[-3,1], [0,2], [2,3]] # Example with negative coords
    #lights_input = [[1,1], [0,2], [2,3]]
    visualize_brightest_position(lights_input)

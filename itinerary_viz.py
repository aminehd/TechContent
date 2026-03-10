import os
import time
import re
import collections

# --- GridVisualizer Class (Full-featured version from standalone_viz.py) ---

def get_visible_len(s):
    return len(re.sub(r'\033\[[0-9;]*m', '', s))

class GridVisualizer:
    def __init__(self, rows, cols, cell_width=12, title="Grid Visualizer"):
        self.rows = rows
        self.cols = cols
        self.cell_width = cell_width
        self.title = title
        self.speed = 1.8
        self.grid_content = [['' for _ in range(cols)] for _ in range(rows)]
        self._arrays = {}
        self._texts = {}
        self.highlight_grid = [[None for _ in range(cols)] for _ in range(rows)]

    def place_array_in_row(self, name, data, grid_row):
        self._arrays[name] = {'data': data, 'row': grid_row}

    def place_text(self, name, text, row, col):
        self._texts[name] = {'text': str(text), 'row': row, 'col': col}

    def _draw_to_grid(self, pointers={}):
        self.grid_content = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        
        for text_info in self._texts.values():
            r, c = text_info['row'], text_info['col']
            if 0 <= r < self.rows and 0 <= c < self.cols:
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
        self.place_text('message', message, 0, 0)
        self._draw_to_grid(pointers=pointers)
        self._render_grid()
        if not final:
            self._update_highlights()
            time.sleep(self.speed)

# --- "Reconstruct Itinerary" Visualization (Grid Style) ---

def visualize_itinerary(tickets):
    # 1. Build the graph
    adj = collections.defaultdict(list)
    for src, dst in sorted(tickets, reverse=True):
        adj[src].append(dst)
    
    sorted_airports = sorted(adj.keys())

    # --- Visualizer Setup ---
    max_path_len = len(tickets) + 1
    viz = GridVisualizer(rows=15, cols=max_path_len, title="Reconstruct Itinerary (DFS)")
    
    # Static Labels
    viz.place_text('adj_header', "Adjacency List", 2, 0)
    viz.place_text('airport_header', "Airport", 3, 0)
    viz.place_text('tickets_header', "Available Tickets", 3, 1)

    stack_row = 5 + len(sorted_airports)
    result_row = stack_row + 2
    
    viz.place_text('stack_label', "Stack:", stack_row - 1, 0)
    viz.place_text('result_label', "Result (built backwards):", result_row - 1, 0)
    
    viz.place_array_in_row('stack', [], stack_row)
    viz.place_array_in_row('result', [], result_row)
    
    def update_adj_display(current_airport):
        """Helper to format and display the entire adjacency list."""
        for i, airport in enumerate(sorted_airports):
            is_top = (current_airport == airport)
            prefix = "> " if is_top else "  "
            viz.place_text(f"adj_{airport}_name", f"{prefix}{airport}", 4 + i, 0)
            viz.place_text(f"adj_{airport}_list", str(adj.get(airport, [])), 4 + i, 1)

    # --- Algorithm Execution ---
    result = []
    stack = ["JFK"]

    # Initial state
    viz._arrays['stack']['data'] = stack
    update_adj_display("JFK")
    viz.capture(message="Start at JFK. Push to stack.")

    while stack:
        current_airport = stack[-1]
        
        update_adj_display(current_airport)
        viz._arrays['stack']['data'] = list(stack)
        viz._arrays['result']['data'] = list(result)

        if current_airport in adj and adj[current_airport]:
            next_airport = adj[current_airport].pop()
            
            viz.capture(message=f"At {current_airport}, chose smallest path: {next_airport}.")
            
            stack.append(next_airport)
            viz._arrays['stack']['data'] = list(stack)
            update_adj_display(next_airport)
            viz.capture(message=f"Pushing {next_airport} to stack.")
        else:
            airport = stack.pop()
            result.append(airport)
            
            viz._arrays['stack']['data'] = list(stack)
            viz._arrays['result']['data'] = list(result)
            update_adj_display(stack[-1] if stack else None)
            viz.capture(message=f"Stuck at {airport}. Pop and add to result.")

    final_path = result[::-1]
    viz._arrays['result']['data'] = final_path
    viz.place_text('result_label', "Final Path (Reversed):", result_row - 1, 0)
    viz.capture(message=f"Finished. Final path: {final_path}", final=True)

if __name__ == "__main__":
    tickets_input = [["JFK","SFO"],["JFK","ATL"],["SFO","ATL"],["ATL","JFK"],["ATL","SFO"]]
    # graph is 
    # JFK -> SFO
    # JFK -> ATL
    # ATL -> JFK
    # ATL -> SFO
    # SFO -> ATL
    visualize_itinerary(tickets_input)
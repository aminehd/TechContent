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
        self.speed = 1.8
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
            self.grid_content[r][c] = str(text_info['text'])

        for arr_name, arr_info in self._arrays.items():
            row = arr_info['row']
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

# --- "Process Tasks Using Servers" Visualization ---

def visualize_cpu_scheduler(servers, tasks):
    
    # --- Visualizer Setup ---
    max_cols = max(len(servers), len(tasks))
    viz = GridVisualizer(rows=12, cols=max_cols, title="CPU Task Scheduler")
    
    # Formatters for heap tuples
    free_server_fmt = lambda s: f"(w:{s[0]}, i:{s[1]})"
    busy_server_fmt = lambda s: f"(t:{s[0]}, i:{s[1]})"
    
    # Place arrays and labels
    viz.place_array_in_row('tasks', tasks, 2)
    viz.place_array_in_row('free', [], 5, formatter=free_server_fmt)
    viz.place_array_in_row('busy', [], 8, formatter=busy_server_fmt)
    viz.place_array_in_row('ans', ['-'] * len(tasks), 10)
    
    viz.place_text('tasks_label', "Tasks (duration):", 1, 0)
    viz.place_text('free_label', "Free Servers (w, i):", 4, 0)
    viz.place_text('busy_label', "Busy Servers (free_t, i):", 7, 0)
    viz.place_text('ans_label', "Result (server index):", 9, 0)

    # --- Algorithm Execution ---
    free_servers = [(servers[i], i) for i in range(len(servers))]
    heapq.heapify(free_servers)
    busy_servers = []
    
    time = 0
    task_idx = 0
    ans = [0] * len(tasks)

    viz.place_array_in_row('free', sorted(free_servers), 5, formatter=free_server_fmt)
    viz.capture(message="Initialized. All servers are free.")

    while task_idx < len(tasks):
        # Master time variable moves to next task arrival if it's later
        time = max(time, task_idx)
        viz.place_text('time', f"Time: {time}", 0, viz.cols -1)

        # If no servers are free, jump time to the next moment a server becomes free
        if not free_servers:
            time = max(time, busy_servers[0][0])
            viz.place_text('time', f"Time: {time}", 0, viz.cols -1)
            viz.capture(message=f"No free servers. Jumping time to {time}.")

        # Free up all servers that are done by the new 'time'
        while busy_servers and busy_servers[0][0] <= time:
            free_time, s_idx = heapq.heappop(busy_servers)
            heapq.heappush(free_servers, (servers[s_idx], s_idx))
            
            viz._arrays['free']['data'] = sorted(free_servers)
            viz._arrays['busy']['data'] = sorted(busy_servers)
            viz.highlight_cell('busy', 0, 'green', 2)
            viz.capture(message=f"t={time}: Server {s_idx} is now free.")

        # Assign all tasks that have arrived by the current 'time'
        while free_servers and task_idx <= time and task_idx < len(tasks):
            s_weight, s_idx = heapq.heappop(free_servers)
            task_duration = tasks[task_idx]
            
            heapq.heappush(busy_servers, (time + task_duration, s_idx))
            ans[task_idx] = s_idx
            
            viz._arrays['free']['data'] = sorted(free_servers)
            viz._arrays['busy']['data'] = sorted(busy_servers)
            viz._arrays['ans']['data'] = ans
            viz.highlight_cell('tasks', task_idx, 'yellow', 2)
            viz.highlight_cell('free', 0, 'red', 2)
            viz.capture(
                message=f"t={time}: Assigning task {task_idx} to server {s_idx}.",
                pointers={'task': {'array': 'tasks', 'index': task_idx}}
            )
            task_idx += 1

    viz.capture(message="All tasks assigned.", final=True)

if __name__ == "__main__":
    s = [5,1,4,3,2]
    t = [2,1,3,1,5]
    visualize_cpu_scheduler(s, t)

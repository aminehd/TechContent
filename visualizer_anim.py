import os
import time
import re
from abc import ABC, abstractmethod

# --- UTILITY ---
def get_visible_len(s):
    return len(re.sub(r'\033\[[0-9;]*m', '', s))

# --- SCENE OBJECTS (Remain the same) ---

class SceneObject(ABC):
    def __init__(self, name, start_row, start_col):
        self.name = name
        self.start_row = start_row
        self.start_col = start_col
        self._keyframes = {}

    def set_state(self, time, **state_data):
        if time not in self._keyframes: self._keyframes[time] = {}
        self._keyframes[time].update(state_data)

    def _get_state_at(self, time):
        cumulative_state = {}
        relevant_times = sorted([t for t in self._keyframes if t <= time])
        for t in relevant_times:
            cumulative_state.update(self._keyframes[t])
        return cumulative_state

    @abstractmethod
    def render(self, grid_content, current_time):
        pass

class GridArray(SceneObject):
    def __init__(self, name, initial_data, start_row=0, start_col=0):
        super().__init__(name, start_row, start_col)
        self.set_state(0, data=list(initial_data), highlight={})

    def render(self, grid_content, current_time):
        state = self._get_state_at(current_time)
        if not state or 'data' not in state: return
        data, highlights = state.get('data', []), state.get('highlight', {})
        for i, val in enumerate(data):
            r, c = self.start_row, self.start_col + i
            if 0 <= r < len(grid_content) and 0 <= c < len(grid_content[0]):
                cell_val = str(val)
                if i in highlights:
                    color = highlights[i]
                    color_code = {'green': '42', 'yellow': '43', 'red': '41'}.get(color, '47')
                    cell_val = f"\033[{color_code}m{cell_val}\033[0m"
                grid_content[r][c] = cell_val

# --- NEW VIEW & ENGINE ARCHITECTURE ---

class View:
    """A self-contained panel that knows how to render itself completely."""
    def __init__(self, title, rows, cols, start_row, start_col, cell_width=8):
        self.title = title
        self.rows, self.cols = rows, cols
        self.start_row, self.start_col = start_row, start_col
        self.cell_width = cell_width
        self.objects = []
    
    def add_object(self, obj):
        self.objects.append(obj)

    def render(self, current_time):
        """Renders the entire view into a list of formatted strings."""
        # 1. Populate the view's internal data grid
        grid_content = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        for obj in self.objects:
            obj.render(grid_content, current_time)

        # 2. Build the string output for the entire view, including borders
        output_lines = []
        separator = "+" + ("-" * self.cell_width + "+") * self.cols
        title_str = f"+-- {self.title} "
        title_str += ('-' * (len(separator) - len(title_str)))

        output_lines.append(title_str)
        
        for r in range(self.rows):
            row_str_parts = []
            for c in range(self.cols):
                cell = grid_content[r][c]
                padding = self.cell_width - get_visible_len(cell)
                left_pad = padding // 2
                right_pad = padding - left_pad
                padded_content = ' ' * left_pad + cell + ' ' * right_pad
                row_str_parts.append(padded_content)
            output_lines.append("|" + "|".join(row_str_parts) + "|")
        
        output_lines.append(separator)
        return output_lines


class AnimationEngine:
    """A simplified engine that manages views and time."""
    def __init__(self, title="Animation Dashboard", default_speed=1.0):
        self.title = title
        self.default_speed = default_speed
        self.views = []
        self._max_time = 0

    def add_view(self, view):
        self.views.append(view)

    def run(self):
        max_times = [max(obj._keyframes.keys()) for v in self.views for obj in v.objects if obj._keyframes]
        self._max_time = max(max_times) if max_times else 0
        
        for t in range(self._max_time + 2):
            self._render_frame(t)
            time.sleep(self.default_speed)
        
        print("\nAnimation complete.")

    def _render_frame(self, current_time):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{self.title} (Time: {current_time})\n")

        # Create a canvas large enough for all views
        max_r = max((v.start_row + v.rows + 2 for v in self.views), default=1)
        canvas = ["" for _ in range(max_r)]

        # Ask each view to render itself and place its lines on the canvas
        for view in self.views:
            view_lines = view.render(current_time)
            for i, line in enumerate(view_lines):
                r = view.start_row + i
                if 0 <= r < max_r:
                    # Basic blitting, assuming views don't overlap horizontally
                    canvas[r] += ' ' * view.start_col + line

        for line in canvas:
            print(line)

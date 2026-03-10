import os
import time
import re
import heapq

# --- GridVisualizer Class (self-contained, adapted for character graphics) ---

class GridVisualizer:
    def __init__(self, rows, cols, title="Grid Visualizer"):
        self.rows = rows
        self.cols = cols
        # For character graphics, each cell IS a character
        self.cell_width = 1 
        self.title = title
        self.speed = 0.1 # Faster speed for a smoother sweep
        self.grid_content = [[' ' for _ in range(cols)] for _ in range(rows)]

    def place_char(self, row, col, char):
        """Places a single character on the grid."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.grid_content[row][col] = char

    def _render_grid(self):
        """Renders the grid. Note: No cell padding for this graphical mode."""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{self.title}\n" + "=" * len(self.title))
        # Invert rows for printing so (0,0) is bottom-left
        for r in range(self.rows - 1, -1, -1):
            print("".join(self.grid_content[r]))

    def capture(self):
        """Renders a single frame."""
        self._render_grid()
        time.sleep(self.speed)

# --- Graphical Skyline Algorithm Visualization ---

def visualize_skyline_graphic(buildings):
    """
    Computes and visualizes the skyline graphically.
    """
    if not buildings:
        return []

    # 1. Determine grid dimensions
    max_r = max(b[1] for b in buildings)
    max_h = max(b[2] for b in buildings)
    viz = GridVisualizer(rows=max_h + 2, cols=max_r + 4, title="Skyline: Graphical Sweep-Line")

    # 2. Draw initial buildings with a shaded character
    for l, r, h in buildings:
        for y in range(h):
            for x in range(l, r):
                viz.place_char(y, x, '░')

    # 3. Create and sort events
    events = []
    for L, R, H in buildings:
        events.append((L, -H, R))
        events.append((R, 0, 0))
    events.sort()

    # 4. Initialize sweep-line algorithm components
    max_heap = [(0, float('inf'))]
    result = [[0, 0]]
    last_max_height = 0
    
    # --- Animation Loop ---
    # We will "sweep" through every x coordinate, not just event points
    for x in range(max_r + 2):
        # Process all events at the current x coordinate
        while events and events[0][0] == x:
            x_event, neg_h, R_event = events.pop(0)
            
            # Pop expired buildings
            while max_heap and max_heap[0][1] <= x:
                heapq.heappop(max_heap)
            
            # If it's a start event, push to heap
            if neg_h != 0:
                heapq.heappush(max_heap, (neg_h, R_event))

        # Get current max height
        current_max_height = -max_heap[0][0]
        
        # If height changes, it's a new key point
        if current_max_height != last_max_height:
            # Add point only if it's not a duplicate x
            if result[-1][0] != x:
                result.append([x, current_max_height])
            else: # If same x, update height
                result[-1][1] = current_max_height
            last_max_height = current_max_height

        # --- Draw the visualization for this frame ---
        # Draw sweep line
        for y in range(max_h + 1):
            viz.place_char(y, x, '|')
        
        # Draw the "lit up" max height point on the skyline
        if current_max_height > 0:
            viz.place_char(current_max_height -1, x, '\033[91m█\033[0m') # Bright red block
        
        viz.capture()

        # Erase sweep line for the next frame by redrawing building
        for y in range(max_h + 1):
            # Check if there is a building at this spot to redraw
            is_building = False
            for l, r, h in buildings:
                if l <= x < r and y < h:
                    is_building = True
                    break
            viz.place_char(y, x, '░' if is_building else ' ')

    print("\nFinal Skyline Key Points:", result)


if __name__ == "__main__":
    buildings_input = [[2,9,10], [3,7,15], [5,12,12], [15,20,10], [19,24,8]]
    visualize_skyline_graphic(buildings_input)

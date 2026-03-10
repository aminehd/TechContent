import os
import time

def _clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def _render_frame(array, pointers={}, sub_arrays={}, highlights={}, lis_frame_data=None):
    """
    Renders a complete frame for various algorithm types.
    """
    if lis_frame_data:
        # --- LIS Visualization ---
        print("Input `nums`:")
        _render_array_line(array, pointers)
        print("\n`tails` array (smallest tail for LIS of length i+1):")
        
        tails_array = lis_frame_data.get('tails', [])
        highlight_index = lis_frame_data.get('highlight_idx', -1)
        
        _render_array_line(
            tails_array,
            highlight_idx=highlight_index,
            use_color=True # Use yellow for highlight
        )
        print(f"\n{lis_frame_data.get('action', '')}")
    else:
        # --- Default/Sort Visualization ---
        print("Main Array:")
        _render_array_line(array, pointers, highlights.get('main', -1))
        if sub_arrays:
            print("\nSub-arrays being merged:")
            sub_highlights = highlights.get('sub', [])
            for i, (name, sub_array) in enumerate(sub_arrays.items()):
                highlight_idx = sub_highlights[i] if i < len(sub_highlights) else -1
                print(f"{name:>8}: ", end="")
                _render_array_line(sub_array, highlight_idx=highlight_idx, use_color=True)

def _render_array_line(array, pointers={}, highlight_idx=-1, use_color=False):
    """Renders a single formatted array line with pointers."""
    if not array and highlight_idx == -1:
        print("[]")
        return

    array_str_parts = []
    for i, x in enumerate(array):
        part = f"{x:3}" # Increased padding for larger numbers
        if i == highlight_idx:
            color = "\033[93m" if use_color else "\033[92m" # Yellow for sub, Green for main
            part = f"{color}{part}\033[0m"
        array_str_parts.append(part)
    array_str = " │ ".join(array_str_parts)
    print(f"[{array_str}]")

    # --- Render Pointers ---
    line_length = len(array_str) + 20 # Add buffer for color codes
    indicator_line = [" "] * line_length
    name_line = [" "] * line_length
    for name, index in pointers.items():
        if 0 <= index < len(array):
            # Adjust position based on new padding
            pos = 2 + index * 6
            if 0 <= pos < line_length:
                indicator_line[pos] = "↑"
                name_line[pos] = name
    print("".join(indicator_line))
    print("".join(name_line))

class AlgorithmVisualizer:
    """
    A class to handle the visualization of algorithms in the terminal.
    """
    def __init__(self, title="Algorithm Visualization", description="", speed=0.5):
        self.title = title
        self.description = description
        self.speed = speed

    def capture(self, array, pointers={}, sub_arrays={}, highlights={}, lis_frame_data=None, final=False):
        """
        Captures and visualizes a single frame of the algorithm.
        """
        _clear_screen()
        print(f"{self.title}")
        print("=" * len(self.title))
        
        # Pass all potential data to the renderer
        _render_frame(array, pointers, sub_arrays, highlights, lis_frame_data)
        
        if self.description and not lis_frame_data:
            print(f"\n{self.description}")
        
        if not final:
            time.sleep(self.speed)



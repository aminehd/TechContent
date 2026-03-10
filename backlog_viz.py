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
        self.speed = 1.5
        self.grid_content = [['' for _ in range(cols)] for _ in range(rows)]
        self.highlight_grid = [[None for _ in range(cols)] for _ in range(rows)]
        self._arrays = {}
        self._texts = {}

    def place_array_in_row(self, name, data, grid_row):
        self._arrays[name] = {'data': data, 'row': grid_row}

    def place_text_in_cell(self, name, text, row, col):
        self._texts[name] = {'text': text, 'row': row, 'col': col}

    def highlight_cell(self, row, col, color='yellow', ttl=1):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.highlight_grid[row][col] = {'color': color, 'ttl': ttl}

    def _draw_to_grid(self):
        self.grid_content = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        
        for text_info in self._texts.values():
            self.grid_content[text_info['row']][text_info['col']] = text_info['text']

        for arr_info in self._arrays.values():
            row = arr_info['row']
            # Custom formatter for different array types
            for i, val in enumerate(arr_info['data']):
                if 0 <= i < self.cols:
                    # Format for heap tuples [price, amount] or [-price, amount]
                    if isinstance(val, list) and len(val) == 2:
                        price, amount = (abs(val[0]), val[1]) if val[0] < 0 else (val[0], val[1])
                        self.grid_content[row][i] = f"[{price},{amount}]"
                    else:
                        self.grid_content[row][i] = str(val)
    
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

    def capture(self, message="", final=False):
        self._texts['message'] = {'text': message, 'row': 0, 'col': 0}
        self._draw_to_grid()
        self._render_grid()
        if not final:
            self._update_highlights()
            time.sleep(self.speed)

# --- "Number of Orders in the Backlog" Visualization ---

def visualize_backlog(orders):
    MOD = 10**9 + 7
    sell_backlog, buy_backlog = [], []  # min-heap, max-heap

    # --- Visualizer Setup ---
    # Determine max width needed
    max_orders_in_heap = len(orders) 
    viz = GridVisualizer(rows=10, cols=max_orders_in_heap, title="Order Backlog Visualization")

    viz.place_text_in_cell('buy_label', "BUY Backlog (Max-Heap):", 2, 0)
    viz.place_text_in_cell('sell_label', "SELL Backlog (Min-Heap):", 5, 0)
    viz.place_text_in_cell('order_label', "Incoming Order:", 8, 0)

    # --- Algorithm Execution ---
    for price, amount, order_type in orders:
        order_str = f"[{price},{amount},{'BUY' if order_type==0 else 'SELL'}]"
        viz.place_text_in_cell('current_order', order_str, 8, 1)
        viz.capture(message=f"Processing new {order_str} order.")

        if order_type == 0:  # BUY order
            while amount > 0 and sell_backlog and sell_backlog[0][0] <= price:
                viz.highlight_cell(row=6, col=0, color='yellow', ttl=2)
                viz.highlight_cell(row=8, col=1, color='yellow', ttl=2)
                viz.capture(message=f"BUY {price} matches SELL {sell_backlog[0][0]}. Executing...")
                
                sell_price, sell_amount = heapq.heappop(sell_backlog)
                executed = min(amount, sell_amount)
                amount -= executed
                sell_amount -= executed
                
                if sell_amount > 0:
                    heapq.heappush(sell_backlog, [sell_price, sell_amount])
                
                viz.place_array_in_row('buy', sorted(buy_backlog, reverse=True), 3)
                viz.place_array_in_row('sell', sorted(sell_backlog), 6)
                viz.capture(message=f"Executed {executed} units. Remaining BUY amount: {amount}")

            if amount > 0:
                heapq.heappush(buy_backlog, [-price, amount])
                viz.place_array_in_row('buy', sorted(buy_backlog, reverse=True), 3)
                viz.capture(message=f"Adding remaining {amount} units to BUY backlog.")

        else:  # SELL order
            while amount > 0 and buy_backlog and -buy_backlog[0][0] >= price:
                viz.highlight_cell(row=3, col=0, color='yellow', ttl=2)
                viz.highlight_cell(row=8, col=1, color='yellow', ttl=2)
                viz.capture(message=f"SELL {price} matches BUY {-buy_backlog[0][0]}. Executing...")

                buy_price_neg, buy_amount = heapq.heappop(buy_backlog)
                executed = min(amount, buy_amount)
                amount -= executed
                buy_amount -= executed

                if buy_amount > 0:
                    heapq.heappush(buy_backlog, [buy_price_neg, buy_amount])

                viz.place_array_in_row('buy', sorted(buy_backlog, reverse=True), 3)
                viz.place_array_in_row('sell', sorted(sell_backlog), 6)
                viz.capture(message=f"Executed {executed} units. Remaining SELL amount: {amount}")
            
            if amount > 0:
                heapq.heappush(sell_backlog, [price, amount])
                viz.place_array_in_row('sell', sorted(sell_backlog), 6)
                viz.capture(message=f"Adding remaining {amount} units to SELL backlog.")

    # Final Calculation
    total_amount = sum(a for _, a in buy_backlog) + sum(a for _, a in sell_backlog)
    total_amount %= MOD
    viz.place_text_in_cell('final_count', f"Total in Backlog: {total_amount}", 8, 3)
    viz.capture(message="All orders processed.", final=True)

if __name__ == "__main__":
    # Example from LeetCode
    orders_input = [[10,5,0],[15,2,1],[25,1,1],[30,4,0]]
    # Example with more matches
    # orders_input = [[7,1000000000,1],[15,3,0],[5,99,0],[10,50,1]]
    visualize_backlog(orders_input)

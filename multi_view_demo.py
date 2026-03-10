from visualizer_anim import AnimationEngine, View, GridArray

def multi_view_demo():
    """
    Demonstrates the multi-view dashboard functionality of the AnimationEngine.
    """
    
    # --- 1. Setup the Engine ---
    engine = AnimationEngine(title="Multi-View Dashboard Demo")
    engine.default_speed = 1.2
    
    # --- 2. Create and Configure Views ---
    
    # View 1: Positioned at the top
    view1 = View(title="Perspective 1: An Array", rows=3, cols=5, start_row=1, start_col=2, cell_width=5)
    
    # View 2: Positioned below the first one
    view2 = View(title="Perspective 2: Another Array", rows=3, cols=8, start_row=8, start_col=2, cell_width=5)

    # --- 3. Create Scene Objects ---
    
    array_obj1 = GridArray(name='Array1', initial_data=[1, 2, 3, 4, 5], start_row=1, start_col=0)
    
    array_obj2 = GridArray(name='Array2', initial_data=[9, 8, 7, 6, 5, 4, 3, 2], start_row=1, start_col=0)

    # --- 4. Add Objects to their respective Views ---
    view1.add_object(array_obj1)
    view2.add_object(array_obj2)

    # --- 5. Add Views to the Engine ---
    engine.add_view(view1)
    engine.add_view(view2)

    # --- 6. Script the Animation (Populate Keyframes) ---
    time = 0
    
    time += 1 # Time 1
    array_obj1.set_state(time, highlight={0: 'yellow'})
    array_obj2.set_state(time, highlight={7: 'yellow'})

    time += 1 # Time 2
    array_obj1.set_state(time, data=[9, 2, 3, 4, 5], highlight={0: 'green'})
    array_obj2.set_state(time, data=[9, 8, 7, 6, 5, 4, 3, 9], highlight={7: 'green'})
    
    time += 1 # Time 3
    array_obj1.set_state(time, highlight={2: 'yellow'})
    array_obj2.set_state(time, highlight={4: 'yellow'})
    
    time += 1 # Time 4
    array_obj1.set_state(time, highlight={})
    array_obj2.set_state(time, highlight={})
    
    # --- 7. Run the Animation ---
    engine.run()


if __name__ == "__main__":
    multi_view_demo()

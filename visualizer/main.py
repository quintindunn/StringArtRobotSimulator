import logging
import sys
import threading
import time

from visualizer import Visualizer
from instructions import set_movement_methods, parse_multiline_str

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    visualizer: Visualizer = Visualizer(500, 500, pin_count=150, scale=2)

    visualizer_thread = threading.Thread(target=visualizer.run, daemon=True).start()

    set_movement_methods(visualizer.arm.arm_to_angle, visualizer.table.move_tbl_degrees)

    with open("horse.stringart", 'r') as f:
        data = f.read()
        instructions = parse_multiline_str(data)

    time.sleep(3)

    for instruction in instructions:
        while ((visualizer.arm.arm_movement_task is not None or visualizer.table.move_tbl_task is not None) and
               visualizer.running):
            pass
        if instruction and visualizer.running:
            visualizer.set_current_command(instruction.instruction)
            instruction.execute()

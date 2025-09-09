import time
import uasyncio as asyncio
from motor import Motor

# Define motors from class
MOTOR1 = Motor((8, 9))
MOTOR2 = Motor((10, 11))

def window_move(speed_direction, duration, pause=2):
    try:
        MOTOR1.enable()
        MOTOR2.enable()
        try:
            MOTOR1.speed(speed_direction)
            MOTOR2.speed(-(speed_direction))
        except Exception as e:
            print("call failed:", e)
        await asyncio.sleep(duration)
        MOTOR1.stop()
        MOTOR2.stop()
    finally:
        MOTOR1.stop()
        MOTOR2.stop()
        MOTOR1.disable()
        MOTOR2.disable()

def move_roof(prev_roof, roof_open):
    if prev_roof == roof_open:
        return
    system_log(f"Actuating roof. prev_roof = {prev_roof}, roof_open = {roof_open}")
    # Mapping of transitions
    transitions = {
        (0, 33):  (0.75, [0.3]),
        (33, 66): (0.75, [0.4]),
        (66, 99): (0.75, [0.6]),
        (33, 0):  (-0.25, [0.39]),
        (66, 33): (-0.25, [0.39]),
        (99, 66): (-0.25, [0.39]),
    }

    action = transitions.get((prev_roof, roof_open))
    if action:
        speed, duration = action
        window_move(speed, duration)
    else:
        system_log(f"Invalid inputs. Roof not actuated")
    
    return
        

# UP = 0.3, 0.4, 0.6 motor durations, speed 0.75
# DOWN = 0.39, 0.39, 0.39 motor durations, speed -0.25
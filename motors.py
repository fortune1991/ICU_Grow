import time
from logging import system_log
from motor import Motor

def window_move(speed_direction, duration):
    # Define motors from class
    MOTOR1 = Motor((8, 9))
    MOTOR2 = Motor((10, 11))
    try:
        MOTOR1.enable()
        MOTOR2.enable()
        try:
            MOTOR1.speed(speed_direction)
            MOTOR2.speed(-(speed_direction))
        except Exception as e:
            system_log(f"Motor call failed: {e}")
        time.sleep(duration)
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
        (0, 33):  (0.75, 0.30),
        (33, 66): (0.75, 0.45),
        (66, 99): (0.75, 0.60),
        (33, 0):  (-0.35, 0.30),
        (66, 33): (-0.35, 0.30),
        (99, 66): (-0.35, 0.30),
    }

    action = transitions.get((prev_roof, roof_open))
    if action:
        speed_direction, duration = action
        window_move(speed_direction, duration)
    else:
        system_log("Invalid inputs. Roof not actuated")
        

# UP = 0.3, 0.4, 0.6 motor durations, speed 0.75
# DOWN = 0.39, 0.39, 0.39 motor durations, speed -0.25
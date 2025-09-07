import time

def actuator_logic(
    temp_setpoint_low,
    temp_setpoint_high,
    rh_setpoint_low,
    rh_setpoint_high,
    prev_temp,
    prev_rh,
    prev_roof,
    last_change_time,
    roof_open,
    fan_on,
    heat_pad_on,
    temp_celc,
    rh,
    is_night
):
    # configuration
    roof_step = 25
    deadband = 0.5
    fan_on_delta = 2.0

    # Use previous actuator states as starting point
    new_roof_open = roof_open
    new_fan_on = fan_on
    new_heat_pad_on = heat_pad_on

    # --- Heating branch ---
    if temp_celc < temp_setpoint_low:
        new_roof_open = 0
        new_fan_on = False
        new_heat_pad_on = True
    else:
        # Cooling / roof modulation
        if temp_celc > (temp_setpoint_high + deadband):
            new_roof_open = min(100, roof_open + roof_step)  # CHANGED: use current roof_open, not prev_roof
        elif temp_celc < (temp_setpoint_high - deadband):
            new_roof_open = max(0, roof_open - roof_step)  # CHANGED: use current roof_open, not prev_roof
        # Else hold current roof position
        new_heat_pad_on = False

    # --- Humidity control ---
    if temp_setpoint_low <= temp_celc <= temp_setpoint_high and not new_heat_pad_on:
        if prev_rh is not None and rh > rh_setpoint_high and rh > prev_rh:
            new_fan_on = True
        elif rh < rh_setpoint_low:
            new_fan_on = False

    # Fan assist if roof fully open
    if new_roof_open == 100:
        if temp_celc > (temp_setpoint_high + fan_on_delta):
            new_fan_on = True
        elif temp_celc < temp_setpoint_high:
            new_fan_on = False

    # Extreme heat
    if temp_celc > 35:
        new_fan_on = True

    # Night override
    if is_night:
        new_roof_open = 0
        new_fan_on = False
        if temp_celc < (temp_setpoint_low - deadband):
            new_heat_pad_on = True
        elif temp_celc >= (temp_setpoint_low + deadband):
            new_heat_pad_on = False

    # --- UPDATE MEMORY ---
    prev_temp = temp_celc
    prev_rh = rh
    prev_roof = roof_open  # CHANGED: store previous roof value BEFORE updating
    last_change_time = time.localtime()

    # Return new actuator values separately
    return (
        prev_temp,
        prev_rh,
        prev_roof,        # memory value before update
        last_change_time,
        new_roof_open,    # new actuator state
        new_fan_on,
        new_heat_pad_on,
        temp_celc,
        rh,
    )

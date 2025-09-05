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

    # Default values
    new_roof_open = roof_open
    new_fan_on = fan_on
    new_heat_pad_on = heat_pad_on

    # Heating / Cooling Logic 
    if temp_celc > temp_setpoint_high:
        new_heat_pad_on = False

        if prev_roof < 100:
            new_roof_open = min(100, prev_roof + 25)
        else:
            new_roof_open = prev_roof

        # If temp still rising and roof is fully open, use fan
        if (prev_temp is not None and temp_celc >= prev_temp and prev_roof == 100) or temp_celc > 35:
            new_fan_on = True
        else:
            new_fan_on = False

    elif temp_celc < temp_setpoint_low:
        new_heat_pad_on = True
        new_roof_open = 0
        new_fan_on = False

    else:
        new_heat_pad_on = False
        new_fan_on = False
        # Roof stays as is to maintain equilibrium

    # Humidity Control (secondary)
    if (
        prev_rh is not None
        and rh > rh_setpoint_high
        and rh > prev_rh
        and not new_heat_pad_on
    ):
        new_fan_on = True

    elif rh < rh_setpoint_low and not new_heat_pad_on:
        new_fan_on = False

    # --- NEW NIGHT-TIME OVERRIDE ---
    if is_night:
        new_roof_open = 0
        new_fan_on = False

    # Apply changes to actuator states
    if (
        new_roof_open != roof_open
        or new_fan_on != fan_on
        or new_heat_pad_on != heat_pad_on
    ):
        # Set actuators here 
        roof_open = new_roof_open
        fan_on = new_fan_on
        heat_pad_on = new_heat_pad_on

        # Update previous state of roof
        prev_roof = roof_open

    # Update environmental memory
    prev_temp = temp_celc
    prev_rh = rh
    last_change_time = time.localtime()

    return (
        prev_temp, 
        prev_rh, 
        prev_roof, 
        last_change_time, 
        roof_open, 
        fan_on, 
        heat_pad_on,
        temp_celc, 
        rh, 
    )

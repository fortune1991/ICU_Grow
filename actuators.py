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
    # configuration variables
    roof_step = 25 # percent
    deadband = 0.5            
    fan_on_delta = 2.0             

    # start with current states
    new_roof_open = roof_open
    new_fan_on = fan_on
    new_heat_pad_on = heat_pad_on

    if prev_roof is None:
        prev_roof = roof_open

    # Heating
    if temp_celc < temp_setpoint_low:
        new_roof_open = 0
        new_fan_on = False
        new_heat_pad_on = True
        
    # Cooling    

    else:
        # Roof modulation ONLY around the cooling setpoint (temp_setpoint_high)
        # Opening if above high (+ deadband)
        # Closing if below high (- deadband)
        # Hold position while inside the deadband to avoid chatter
        
        if temp_celc > (temp_setpoint_high + deadband):
            new_roof_open = min(100, prev_roof + roof_step)
        elif temp_celc < (temp_setpoint_high - deadband):
            new_roof_open = max(0, prev_roof - roof_step)
        else:
            # Hold previous roof position
            new_roof_open = prev_roof

        # ensure heat pad is off when we're not in the cold branch
        new_heat_pad_on = False

    # Humidity control via fan - only allowed if temperature is in comfort band and heating isn't active
    if (temp_setpoint_low <= temp_celc <= temp_setpoint_high) and not new_heat_pad_on:
        if prev_rh is not None and rh > rh_setpoint_high and rh > prev_rh:
            new_fan_on = True
        elif rh < rh_setpoint_low:
            new_fan_on = False

    # Fan cooling assist when roof fully open
    # Turn fan ON if roof == 100 and temp > high + fan_on_delta
    # Turn fan OFF if temp drops back below high
    if new_roof_open == 100:
        if temp_celc > (temp_setpoint_high + fan_on_delta):
            new_fan_on = True
        elif temp_celc < temp_setpoint_high:
            new_fan_on = False

    # Extreme-heat override
    if temp_celc > 35:
        new_fan_on = True

    # Night override
    # Roof closed, fan off. These should never run at night.
    #    Add 1°C deadband for night-time heating:
    #      - turn heat pad ON if temp < (low - 1)
    #      - turn heat pad OFF if temp >= low
    if is_night:
        new_roof_open = 0
        new_fan_on = False
        if temp_celc < (temp_setpoint_low - deadband):
            new_heat_pad_on = True
        elif temp_celc >= (temp_setpoint_low + deadband):
            new_heat_pad_on = False

    # Apply actuator changes if anything changed
    if (
        new_roof_open != roof_open
        or new_fan_on != fan_on
        or new_heat_pad_on != heat_pad_on
    ):
        roof_open = new_roof_open
        fan_on = new_fan_on
        heat_pad_on = new_heat_pad_on
        prev_roof = roof_open

    # Update memory
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


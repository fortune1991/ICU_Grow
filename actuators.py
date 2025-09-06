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
    # Start with current states
    new_roof_open = roof_open
    new_fan_on = fan_on
    new_heat_pad_on = heat_pad_on

    # 1. Temperature control
    if temp_celc > temp_setpoint_high:
        new_heat_pad_on = False
        new_roof_open = min(100, prev_roof + 25)

    elif temp_celc < temp_setpoint_low:
        new_roof_open = max(0, prev_roof - 25)
        new_fan_on = False
        new_heat_pad_on = True if new_roof_open == 0 else False

    else:  # in comfort range
        new_heat_pad_on = False
        new_fan_on = False

    # 2. Humidity control (only active in comfort zone and if not heating)
    if (
        temp_setpoint_low <= temp_celc <= temp_setpoint_high
        and not new_heat_pad_on
    ):
        if prev_rh is not None and rh > rh_setpoint_high and rh > prev_rh:
            new_fan_on = True
        elif rh < rh_setpoint_low:
            new_fan_on = False

    # 3. Fan assist if roof maxed
    if temp_celc > temp_setpoint_high + 2 and new_roof_open == 100:
        new_fan_on = True

    # 4. Extreme heat override
    if temp_celc > 35:
        new_fan_on = True

    # 5. Night override (always last, with 1 °C heating deadband)
    if is_night:
        new_roof_open = 0
        new_fan_on = False
        if temp_celc < (temp_setpoint_low - 1):
            new_heat_pad_on = True
        elif temp_celc > temp_setpoint_low:
            new_heat_pad_on = False

    # Apply changes
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


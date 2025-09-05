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
    new_roof_open = roof_open
    new_fan_on = fan_on
    new_heat_pad_on = heat_pad_on

    # 1. Night override
    if is_night:
        new_roof_open = 0
        new_fan_on = False
        new_heat_pad_on = temp_celc < temp_setpoint_low
    else:
        # 2. Too hot
        if temp_celc > temp_setpoint_high:
            new_heat_pad_on = False
            new_roof_open = min(100, prev_roof + 25)

            if prev_temp is not None and temp_celc >= prev_temp and prev_roof == 100:
                new_fan_on = True
            else:
                new_fan_on = False

        # 3. Too cold
        elif temp_celc < temp_setpoint_low:
            new_roof_open = max(0, prev_roof - 25)
            new_fan_on = False
            new_heat_pad_on = True if new_roof_open == 0 else False

        # 4. Comfort zone
        else:
            new_heat_pad_on = False
            new_fan_on = False
            # roof stays as is

        # 5. Humidity control
        if (
            prev_rh is not None
            and rh > rh_setpoint_high
            and rh > prev_rh
            and not new_heat_pad_on
        ):
            new_fan_on = True
        elif rh < rh_setpoint_low and not new_heat_pad_on:
            new_fan_on = False

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


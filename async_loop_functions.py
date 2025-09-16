import uasyncio as asyncio
import network
import time
import utime
import machine

from actuators import actuator_logic
from alerts import high_temp_alert, goodnight_message
from breakout_ltr559 import BreakoutLTR559
from led import red_led_on, red_led_off, green_led_on, green_led_off
from logging import system_log, log
from motors import move_roof
from sensors import sensor
from utils import get_local_time, seconds_until
from weather import (
    get_weather_data,
    get_sunrise_hour,
    get_sunrise_time,
    get_sunset_time,
    get_temperature_at_hour,
    weather_message,
    api_url_gen,
)
from screen import (
    screen_temperature_inside,
    screen_temperature_outside,
    screen_humidity,
    screen_actuations,
)
import state


async def sensor_log(record_interval, cloud_upload_interval, csv_complete, actuator_update):
    """Call Sensor function to read current sensor values. Write current values to logs"""
    while True:
        for _ in range(cloud_upload_interval):
            try:
                (
                    state.temp_celc_current,
                    state.rh_current,
                    state.temp_celc_outside_current,
                    state.lux_current,
                    moisture_value,
                ) = await sensor()
                log(
                    state.temp_celc_current,
                    state.rh_current,
                    state.temp_celc_outside_current,
                    state.lux_current,
                    state.roof_open,
                    state.fan_on,
                    state.heat_pad_on,
                    state.cover_on,
                    state.is_night,
                )
            except Exception as e:
                print("Sensor log error (sensor log):", e)
                system_log(f"Sensor log error: {e}")
            await asyncio.sleep(record_interval)

        csv_complete.set()


async def temp_inside_display(button_a, button_b, button_x, button_y):
    """If button A pressed, show temp_inside screen. Refresh temp every 10s until another button pressed."""
    while True:
        if button_a.read():
            while button_a.read():
                await asyncio.sleep(0.01)
            await asyncio.sleep(0.05)

            while True:
                await screen_temperature_inside(
                    display,
                    BG,
                    WHITE,
                    ORANGE,
                    state.temp_celc_current,
                    25,
                    18,
                    27,
                )

                exit_pressed = False
                for _ in range(100):
                    if button_b.read() or button_x.read() or button_y.read():
                        exit_pressed = True
                        while button_b.read() or button_x.read() or button_y.read():
                            await asyncio.sleep(0.01)
                        await asyncio.sleep(0.05)
                        break
                    await asyncio.sleep(0.1)

                if exit_pressed:
                    break
        else:
            await asyncio.sleep(0.1)


async def temp_outside_display(button_a, button_b, button_x, button_y):
    """If button B pressed, show temp_outside screen. Refresh temp every 10s until another button pressed."""
    while True:
        if button_b.read():
            while button_b.read():
                await asyncio.sleep(0.01)
            await asyncio.sleep(0.05)

            while True:
                await screen_temperature_outside(
                    display,
                    BG,
                    WHITE,
                    ORANGE,
                    state.temp_celc_outside_current,
                    25,
                    14,
                    27,
                )

                exit_pressed = False
                for _ in range(100):
                    if button_a.read() or button_x.read() or button_y.read():
                        exit_pressed = True
                        while button_a.read() or button_x.read() or button_y.read():
                            await asyncio.sleep(0.01)
                        await asyncio.sleep(0.05)
                        break
                    await asyncio.sleep(0.1)

                if exit_pressed:
                    break

        else:
            await asyncio.sleep(0.1)


async def humidity_display(button_a, button_b, button_x, button_y):
    """If button X pressed, show humidity screen. Refresh every 10s until another button pressed."""
    while True:
        if button_x.read():
            while button_x.read():
                await asyncio.sleep(0.01)
            await asyncio.sleep(0.05)

            while True:
                await screen_humidity(
                    display,
                    BG,
                    WHITE,
                    ORANGE,
                    state.rh_current,
                    60,
                    55,
                    40,
                )

                exit_pressed = False
                for _ in range(100):
                    if button_a.read() or button_b.read() or button_y.read():
                        exit_pressed = True
                        while button_a.read() or button_b.read() or button_y.read():
                            await asyncio.sleep(0.01)
                        await asyncio.sleep(0.05)
                        break
                    await asyncio.sleep(0.1)

                if exit_pressed:
                    break

        else:
            await asyncio.sleep(0.1)


async def actuations_display(button_a, button_b, button_x, button_y):
    """If button Y pressed, show actuations screen. Refresh every 10s until another button pressed."""
    error_count = 2

    while True:
        if button_y.read():
            while button_y.read():
                await asyncio.sleep(0.01)
            await asyncio.sleep(0.05)

            while True:
                await screen_actuations(
                    display,
                    BG,
                    WHITE,
                    ORANGE,
                    state.fan_on,
                    state.roof_open,
                    state.heat_pad_on,
                    error_count,
                )

                exit_pressed = False
                for _ in range(100):
                    if button_a.read() or button_b.read() or button_x.read():
                        exit_pressed = True
                        while button_a.read() or button_b.read() or button_x.read():
                            await asyncio.sleep(0.01)
                        await asyncio.sleep(0.05)
                        break
                    await asyncio.sleep(0.1)

                if exit_pressed:
                    break

        else:
            await asyncio.sleep(0.1)


async def cloud_upload(csv_complete, actuator_update):
    """Upload past 24 hours of log data to the cloud. Delete data successfully uploaded from the logs."""
    while True:
        await csv_complete.wait()
        print("Uploading CSV to cloud...")
        system_log("Uploading CSV to cloud...")
        csv_complete.clear()
        actuator_update.set()


async def actuators(actuator_update, temp_alert):
    """Compare sensor values to state and actuate devices accordingly."""
    temp_setpoint_low = 15
    temp_setpoint_high = 25
    rh_setpoint_low = 40
    rh_setpoint_high = 70

    prev_temp = None
    prev_rh = None
    prev_roof = 0
    last_change_time = None
    hold_time = 1

    state.roof_open = 0
    state.fan_on = False
    state.heat_pad_on = False

    while True:
        await actuator_update.wait()
        actuator_update.clear()

        try:
            (
                state.temp_celc_current,
                state.rh_current,
                state.temp_celc_outside_current,
                state.lux_current,
                moisture_current,
            ) = await sensor()

        except Exception as e:
            print("Sensor log error (actuation):", e)
            system_log(f"Sensor log error: {e}")

        (
            prev_temp,
            prev_rh,
            prev_roof,
            last_change_time,
            state.roof_open,
            state.fan_on,
            state.heat_pad_on,
            state.temp_celc_current,
            state.rh_current,
        ) = actuator_logic(
            temp_setpoint_low,
            temp_setpoint_high,
            rh_setpoint_low,
            rh_setpoint_high,
            prev_temp,
            prev_rh,
            prev_roof,
            last_change_time,
            state.roof_open,
            state.fan_on,
            state.heat_pad_on,
            state.temp_celc_current,
            state.rh_current,
            state.is_night,
        )

        if state.cover_on:
            if state.roof_open != 0 or state.fan_on:
                state.roof_open = 0
                state.fan_on = False
                system_log("Cover detected: forced roof closed and fan off")

        move_roof(prev_roof, state.roof_open)

        if state.fan_on:
            green_led_on()
        else:
            green_led_off()

        if state.heat_pad_on:
            red_led_on()
        else:
            red_led_off()

        print(f"roof open: {state.roof_open}, fan on: {state.fan_on}, heat pad on: {state.heat_pad_on}")
        temp_alert.set()
        await asyncio.sleep(hold_time)


async def weather_check():
    """Update weather data once per day at 3 AM and store safely in state.py"""

    # Sleep until 3 AM first time
    await asyncio.sleep(seconds_until(3))

    while True:
        try:
            api_url = api_url_gen(state.latitude, state.longitude, state.timezone)
            data = get_weather_data(api_url)

            year, month, day, *_ = state.rtc.datetime()
            date = "{:04d}-{:02d}-{:02d}".format(year, month, day)

            if data:
                # Sunrise hour as str
                state.sunrise_hour = str(get_sunrise_hour(data))
                # Sunrise time as string (HH:MM)
                state.sunrise_time = get_sunrise_time(data)
                # Temperature at sunrise as float
                temp_at_sunrise = get_temperature_at_hour(data, state.sunrise_hour)
                state.temp_at_sunrise = float(temp_at_sunrise) if temp_at_sunrise is not None else None

                if state.temp_at_sunrise is not None:
                    print(
                        f"Weather data acquired. Sunrise is at {state.sunrise_time} on {date}. "
                        f"Temperature at sunrise is {state.temp_at_sunrise}°C"
                    )
                    system_log(
                        f"Weather data acquired. Sunrise is at {state.sunrise_time} on {date}. "
                        f"Temperature at sunrise is {state.temp_at_sunrise}°C"
                    )

                    # Send weather message
                    weather_message(15, state.temp_at_sunrise)

                    # Sunset timestamp as int
                    sunset_timestamp = get_sunset_time(data)
                    state.sunset_time = int(sunset_timestamp) if sunset_timestamp is not None else None

                    if state.sunset_time:
                        sunset_struct = utime.localtime(state.sunset_time)
                        year, month, day, hour, minute, second, weekday, yearday = sunset_struct
                        system_log(f"Sunset time is {hour}:{minute} on {date}")

            else:
                print("Weather API failed; retrying in 60 seconds")
                system_log("Weather API failed; retrying in 60 seconds")

        except Exception as e:
            print(f"Weather check error: {e}")
            system_log(f"Weather check error: {e}")

        # Sleep until 3 AM next day
        await asyncio.sleep(seconds_until(3))


async def temperature_alert(temp_alert, goodnight):
    while True:
        await temp_alert.wait()
        temp_alert.clear()

        high_temp_alert(
            state.temp_celc_current,
            state.temp_celc_outside_current,
            state.roof_open,
            state.fan_on,
        )
        goodnight.set()


async def goodnight_routine(goodnight):
    while True:
        await goodnight.wait()
        goodnight.clear()

        current_timestamp = time.mktime(time.localtime())
        local_tm = time.localtime(current_timestamp)
        year, month, day, *_ = local_tm
        current_date = f"{year:04d}-{month:02d}-{day:02d}"

        if state.is_night and current_date != state.last_goodnight_date:
            state.roof_open = 0
            state.fan_on = False
            goodnight_message()
            state.last_goodnight_date = current_date


async def cover_check(i2c):
    """Runs independently to keep is_night and cover_on up-to-date."""
    ltr = BreakoutLTR559(i2c)

    prev_is_night = None
    prev_cover_on = None

    while True:
        lux_records = []
        for _ in range(4):
            try:
                (
                    state.temp_celc_current,
                    state.rh_current,
                    state.temp_celc_outside_current,
                    lux,
                    moisture_value,
                ) = await sensor()
                lux_records.append(lux)
                await asyncio.sleep(1)
            except Exception as e:
                print("Lux sensor log error:", e)
                system_log(f"Lux sensor log error: {e}")

        dark = sum(lux_records) == 0
        current_timestamp = time.mktime(time.localtime())

        new_is_night = (current_timestamp > state.sunset_time) if state.sunset_time else dark
        new_cover_on = dark and not new_is_night

        if new_is_night != prev_is_night:
            prev_is_night = new_is_night

        if new_cover_on != prev_cover_on:
            prev_cover_on = new_cover_on

        state.is_night = new_is_night
        state.cover_on = new_cover_on

        await asyncio.sleep(30)

async def clock_sync():
    """
    Daily RTC sync routine at 3am.
    """
    seconds_until_3am = seconds_until(3)
    await asyncio.sleep(seconds_until_3am)

    while True:
        try:
            t = await get_local_time(state.timezone)
            struct_raw = t["struct_time"]

            # Ensure all are integers
            struct = tuple(int(x) for x in struct_raw[:6]) + (0, 0, -1)

            if not hasattr(state, "rtc") or state.rtc is None:
                state.rtc = machine.RTC()

            weekday = utime.localtime(time.mktime(struct))[6]
            state.rtc.datetime(
                (struct[0], struct[1], struct[2], weekday, struct[3], struct[4], struct[5], 0)
            )

            print("Clock synced")
            system_log("Clock synced")

        except Exception as e:
            print("Clock sync failed:", e)
            system_log(f"Clock sync failed: {e}")

        seconds_until_3am = seconds_until(3)
        await asyncio.sleep(seconds_until_3am)


async def wifi_watch(ssid, password, check_interval=10):
    """Periodically checks Wi-Fi connection and reconnects if dropped."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    while True:
        if not wlan.isconnected():
            print("Wi-Fi disconnected. Attempting reconnect...")
            system_log("Wi-Fi disconnected. Attempting reconnect...")
            wlan.connect(ssid, password)

            retry_count = 0
            while not wlan.isconnected() and retry_count < 5:
                await asyncio.sleep(2)
                retry_count += 1

            if wlan.isconnected():
                print("Wi-Fi reconnected")
                system_log("Wi-Fi reconnected")
            else:
                print("Wi-Fi reconnect failed")
                system_log("Wi-Fi reconnect failed")
        await asyncio.sleep(check_interval)

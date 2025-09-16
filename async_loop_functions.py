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
from stats import average, low, high
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

async def goodnight_routine(goodnight):
    while True:
        await goodnight.wait()
        goodnight.clear()
        try:
            current_timestamp = time.mktime(time.localtime())
            local_tm = time.localtime(current_timestamp)
            year, month, day, *_ = local_tm
            current_date = f"{year:04d}-{month:02d}-{day:02d}"

            if state.is_night and current_date != state.last_goodnight_date:
                state.roof_open = 0
                state.fan_on = False
                goodnight_message()
                state.last_goodnight_date = current_date

            state.clear_error("goodnight_routine")

        except Exception as e:
            print(f"Goodnight routine error: {e}")
            system_log(f"Goodnight routine error: {e}")
            state.add_error("goodnight_routine")
            # optional: short sleep to prevent tight error loop
            await asyncio.sleep(1)

async def temperature_alert(temp_alert, goodnight):
    while True:
        await temp_alert.wait()
        temp_alert.clear()

        try:
            if state.temp_celc_current is not None:
                if state.temp_celc_current > 30:  # High temperature threshold
                    print(f"High temperature alert! {state.temp_celc_current}°C")
                    system_log(f"High temperature alert! {state.temp_celc_current}°C")
                    await high_temp_alert(state.temp_celc_current)
                elif state.temp_celc_current < 5:  # Low temperature threshold
                    print(f"Low temperature warning! {state.temp_celc_current}°C")
                    system_log(f"Low temperature warning! {state.temp_celc_current}°C")
            
            # Clear error if everything went fine
            state.clear_error("temperature_alert")

        except Exception as e:
            print(f"Temperature alert failed: {e}")
            system_log(f"Temperature alert failed: {e}")
            state.add_error("temperature_alert")

        await asyncio.sleep(1)


async def sensor_log(csv_complete, actuator_update):
    while True:
        for _ in range(state.cloud_upload_interval):
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
                state.clear_error("sensor_log")
            except Exception as e:
                print("Sensor log error:", e)
                system_log(f"Sensor log error: {e}")
                state.add_error("sensor_log")
            await asyncio.sleep(state.record_interval)

        csv_complete.set()


async def cloud_upload(csv_complete, actuator_update):
    while True:
        await csv_complete.wait()
        try:
            print("Uploading CSV to cloud...")
            system_log("Uploading CSV to cloud...")
            
            # Simulate the upload process here
        
            
            # Clear CSV complete event and set actuator update event
            csv_complete.clear()
            actuator_update.set()

            # Clear any previous errors for cloud_upload
            state.clear_error("cloud_upload")

        except Exception as e:
            print(f"Cloud upload failed: {e}")
            system_log(f"Cloud upload failed: {e}")
            state.add_error("cloud_upload")

        await asyncio.sleep(1)


async def temp_inside_display(display, button_a, button_b, button_x, button_y, BG, WHITE, ORANGE):
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
                    state.temp_celc_average,
                    state.temp_celc_low,
                    state.temp_celc_high,
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


async def temp_outside_display(display, button_a, button_b, button_x, button_y, BG, WHITE, ORANGE):
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
                    state.temp_celc_outside_average,
                    state.temp_celc_outside_low,
                    state.temp_celc_outside_high,
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


async def humidity_display(display, button_a, button_b, button_x, button_y, BG, WHITE, ORANGE):
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
                    state.rh_average,
                    state.rh_low,
                    state.rh_high,
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


async def actuations_display(display, button_a, button_b, button_x, button_y, BG, WHITE, ORANGE):
    while True:
        if button_y.read():
            while button_y.read():
                await asyncio.sleep(0.01)
            await asyncio.sleep(0.05)

            while True:
                error_count = state.error_total()
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


async def actuators(actuator_update, temp_alert):
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
            state.clear_error("actuators")
        except Exception as e:
            print("Sensor log error (actuation):", e)
            system_log(f"Sensor log error (actuation): {e}")
            state.add_error("actuators")

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
    await asyncio.sleep(seconds_until(3))

    while True:
        try:
            api_url = api_url_gen(state.latitude, state.longitude, state.timezone)
            data = get_weather_data(api_url)

            year, month, day, *_ = state.rtc.datetime()
            date = "{:04d}-{:02d}-{:02d}".format(year, month, day)

            if data:
                state.sunrise_hour = str(get_sunrise_hour(data))
                state.sunrise_time = get_sunrise_time(data)
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
                    weather_message(15, state.temp_at_sunrise)

                    sunset_timestamp = get_sunset_time(data)
                    state.sunset_time = int(sunset_timestamp) if sunset_timestamp is not None else None

                    if state.sunset_time:
                        sunset_struct = utime.localtime(state.sunset_time)
                        year, month, day, hour, minute, second, weekday, yearday = sunset_struct
                        system_log(f"Sunset time is {hour}:{minute} on {date}")

                state.clear_error("weather_check")
            else:
                print("Weather API failed; retrying in 60 seconds")
                system_log("Weather API failed; retrying in 60 seconds")
                state.add_error("weather_check")

        except Exception as e:
            print(f"Weather check error: {e}")
            system_log(f"Weather check error: {e}")
            state.add_error("weather_check")

        await asyncio.sleep(seconds_until(3))


async def cover_check(i2c):
    ltr = BreakoutLTR559(i2c)
    prev_is_night = None
    prev_cover_on = None

    while True:
        try:
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
                    state.clear_error("cover_check")
                except Exception as e:
                    print("Lux sensor log error:", e)
                    system_log(f"Lux sensor log error: {e}")
                    state.add_error("cover_check")

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

        except Exception as e:
            print(f"Cover check failed: {e}")
            system_log(f"Cover check failed: {e}")
            state.add_error("cover_check")

        await asyncio.sleep(30)


async def clock_sync():
    seconds_until_3am = seconds_until(3)
    await asyncio.sleep(seconds_until_3am)

    while True:
        try:
            t = await get_local_time(state.timezone)
            struct_raw = t["struct_time"]
            struct = tuple(int(x) for x in struct_raw[:6]) + (0, 0, -1)

            if not hasattr(state, "rtc") or state.rtc is None:
                state.rtc = machine.RTC()

            weekday = utime.localtime(time.mktime(struct))[6]
            state.rtc.datetime(
                (struct[0], struct[1], struct[2], weekday, struct[3], struct[4], struct[5], 0)
            )

            print("Clock synced")
            system_log("Clock synced")
            state.clear_error("clock_sync")
            state.clear_error("start_clock_sync")

        except Exception as e:
            print("Clock sync failed:", e)
            system_log(f"Clock sync failed: {e}")
            state.add_error("clock_sync")

        seconds_until_3am = seconds_until(3)
        await asyncio.sleep(seconds_until_3am)


async def stats_check():
    while True:
        try:
            state.temp_celc_average = average("temp_celc")
            state.temp_celc_outside_average = average("temp_celc_outside")
            state.rh_average = average("rh")

            state.temp_celc_low = low("temp_celc")
            state.temp_celc_outside_low = low("temp_celc_outside")
            state.rh_low = low("rh")

            state.temp_celc_high = high("temp_celc")
            state.temp_celc_outside_high = high("temp_celc_outside")
            state.rh_high = high("rh")

            state.clear_error("stats_check")
        except Exception as e:
            print("Stats calcs failed:", e)
            system_log(f"Stats calcs failed: {e}")
            state.add_error("stats_check")

        await asyncio.sleep(10)
        

async def wifi_watch(ssid, password, check_interval=10):
    """Periodically checks Wi-Fi connection and reconnects if dropped."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    while True:
        try:
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

            # Clear any previous errors for Wi-Fi
            state.clear_error("wifi_watch")

        except Exception as e:
            print(f"Wi-Fi watch error: {e}")
            system_log(f"Wi-Fi watch error: {e}")
            state.add_error("wifi_watch")

        await asyncio.sleep(check_interval)


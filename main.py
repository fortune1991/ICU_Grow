import uasyncio as asyncio
import network
import time
import utime
import machine
from actuators import actuator_logic
from alerts import high_temp_alert, goodnight_message
from breakout_ltr559 import BreakoutLTR559
from led import red_led_on, red_led_off, green_led_on, green_led_off, blue_led_on, blue_led_off
from logging import system_log
from motors import move_roof
from picographics import PicoGraphics, DISPLAY_PICO_EXPLORER
from pimoroni_i2c import PimoroniI2C
from pimoroni import PICO_EXPLORER_I2C_PINS, Button
from screen import (
    title,
    clear_animation_area,
    start_screen,
    start_up_success,
    start_up_fail,
    screen_temperature_inside,
    screen_temperature_outside,
    screen_humidity,
    screen_actuations,
)
from sensors import sensor
from start import connect_wifi, start_timezone, start_location, start_clock_sync, start_weather_data
from weather import (
    get_weather_data,
    get_sunrise_hour,
    get_sunrise_time,
    get_sunset_time,
    get_temperature_at_hour,
    weather_message,
    api_url_gen,
)
from utils import get_local_time, load_config, seconds_until

# MODULE LEVEL DEFAULTS

record_interval = None
cloud_upload_interval = None

roof_open = 0
fan_on = False
irrigation_on = False

temp_celc_current = None
rh_current = None
temp_celc_outside_current = None
lux_current = None

last_goodnight_date = None
is_night = False
cover_on = False

timezone = None
latitude = None
longitude = None

config = load_config()
display = PicoGraphics(display=DISPLAY_PICO_EXPLORER)
i2c = PimoroniI2C(**PICO_EXPLORER_I2C_PINS) #explorer base

SSID = config["SSID"]
PASSWORD = config["PASSWORD"]

button_a = Button(12)
button_b = Button(13)
button_x = Button(14)
button_y = Button(15)

# Screen Colours
BG       = display.create_pen(15, 25, 35)
STEM     = display.create_pen(30, 160, 60)    
LEAF     = display.create_pen(50, 210, 100)   
BUD_BASE = display.create_pen(60, 180, 80)    
PETALS   = display.create_pen(240, 120, 160)  
CENTER   = display.create_pen(255, 230, 120)  
WHITE    = display.create_pen(255, 255, 255)
GREEN = display.create_pen(0, 255, 0)
RED = display.create_pen(255, 0, 0)
ORANGE = display.create_pen(255, 165, 0)


# Async applicatio
async def main():
    global record_interval, cloud_upload_interval
    global roof_open, fan_on, irrigation_on, heat_pad_on
    global temp_celc_current, rh_current, temp_celc_outside_current, lux_current
    global timezone, latitude, longitude
    global is_night, cover_on, last_goodnight_date, sunset_time

    try:
        # Start Screen
        screen_running = asyncio.Event()
        screen_running.set()
        asyncio.create_task(title(display, BG, GREEN))
        asyncio.create_task(start_screen(display, screen_running, BG, STEM, LEAF, BUD_BASE, PETALS, CENTER, GREEN))
        
        await asyncio.sleep(0.01)
        
        # Define constants and state
        
        record_interval = 5 #seconds
        cloud_upload_interval = 5 #sesnsor reads
        roof_open = 0
        fan_on = False
        irrigation_on = False
        heat_pad_on = False
        temp_celc_current = None
        rh_current = None
        temp_celc_outside_current = None
        lux_current = None
        last_goodnight_date = None
        is_night = False
        cover_on = False
        sunset_time = None

        # Wait for USB to become ready
        await asyncio.sleep(0.1)
        # Connect to Wi-Fi
        await connect_wifi()
        # Timezone
        timezone = await start_timezone()
        # Location
        latitude, longitude = await start_location()
        # Clock sync at start-up
        rtc = await start_clock_sync(timezone)
        # Aquire weather data
        sunrise_hour, sunrise_time, temp_at_sunrise, sunset_time = await start_weather_data(latitude, longitude, timezone, rtc)

        # UI / Screen
        print("Start-up routine successful")
        system_log("Start-up routine successful")
        # Stop flower animation before showing success
        screen_running.clear()
        clear_animation_area(display, BG)
        await asyncio.sleep(0.1)
        # Start Success Message
        await start_up_success(display, BG, WHITE, GREEN)
        await asyncio.sleep(5)
        await screen_temperature_inside(
                    display, BG, WHITE, ORANGE,
                    temp_celc_current,
                    25,  # average
                    18,  # low
                    27   # high
                )

    except Exception as e:
        print("Start-up routine failed:", e)
        system_log(f"Start-up routine failed: {e}")
        screen_running.clear()
        clear_animation_area(display, BG)
        await asyncio.sleep(0.1)
        # Show start-up fail
        await start_up_fail(display, BG, RED, GREEN)
        return # exit(1) ?

    # Define Asyncio events for main loop
    csv_complete = asyncio.Event()
    actuator_update = asyncio.Event()
    temp_alert = asyncio.Event()
    goodnight = asyncio.Event()

    # Start all tasks concurrently
    await asyncio.gather(
        sensor_log(record_interval, csv_complete, actuator_update),
        cloud_upload(csv_complete, actuator_update),
        actuators(actuator_update, temp_alert),
        weather_check(),
        temperature_alert(temp_alert, goodnight),
        goodnight_routine(goodnight),
        clock_sync(),
        cover_check(),
        wifi_watch(SSID, PASSWORD),
        temp_inside_display(),
        temp_outside_display(),
        humidity_display(),
        actuations_display(),
    )

async def sensor_log(record_interval, csv_complete, actuator_update):
    global roof_open, fan_on, heat_pad_on, is_night, cover_on, cloud_upload_interval
    while True:
        for _ in range(cloud_upload_interval):
            try:
                temp_celc, rh, temp_celc_outside, lux, moisture_value = await sensor()
                log(temp_celc, rh, temp_celc_outside, lux, roof_open, fan_on, heat_pad_on, cover_on, is_night)
            except Exception as e:
                print("Sensor log error (sensor log):", e)
                system_log(f"Sensor log error: {e}")
            await asyncio.sleep(record_interval)

        csv_complete.set()


async def temp_inside_display():
    """Poll button A, show inside temp every 10s until another button pressed."""
    global temp_celc_current

    while True:
        if button_a.read():
            # Debounce button A
            while button_a.read():
                await asyncio.sleep(0.01)
            await asyncio.sleep(0.05)

            # Enter timed refresh mode
            while True:
                await screen_temperature_inside(
                    display, BG, WHITE, ORANGE,
                    temp_celc_current,
                    25,  # average
                    18,  # low
                    27   # high
                )

                # Refresh every 10s, but check for exit every 0.1s
                exit_pressed = False
                for _ in range(100):
                    if button_b.read() or button_x.read() or button_y.read():
                        exit_pressed = True
                        # Debounce whichever button was pressed
                        while button_b.read() or button_x.read() or button_y.read():
                            await asyncio.sleep(0.01)
                        await asyncio.sleep(0.05)
                        break
                    await asyncio.sleep(0.1)

                if exit_pressed:
                    break
        else:
            await asyncio.sleep(0.1)
            

async def temp_outside_display():
    """Poll button A, show outside temp every 10s until another button pressed."""
    global temp_celc_current

    while True:
        if button_b.read():
            # Debounce button B
            while button_b.read():
                await asyncio.sleep(0.01)
            await asyncio.sleep(0.05)

            # Enter timed refresh mode
            while True:
                await screen_temperature_outside(
                display, BG, WHITE, ORANGE,
                temp_celc_outside_current,
                25,  # avg
                14,  # low
                27   # high
            )

                # Refresh every 10s, but check for exit every 0.1s
                exit_pressed = False
                for _ in range(100):
                    if button_a.read() or button_x.read() or button_y.read():
                        exit_pressed = True
                        # Debounce whichever button was pressed
                        while button_a.read() or button_x.read() or button_y.read():
                            await asyncio.sleep(0.01)
                        await asyncio.sleep(0.05)
                        break
                    await asyncio.sleep(0.1)

                if exit_pressed:
                    break

        else:
            await asyncio.sleep(0.1)


async def humidity_display():
    """Poll button A, show outside temp every 10s until another button pressed."""
    global temp_celc_current

    while True:
        if button_x.read():
            # Debounce button B
            while button_x.read():
                await asyncio.sleep(0.01)
            await asyncio.sleep(0.05)

            # Enter timed refresh mode
            while True:
                await screen_humidity(
                display, BG, WHITE, ORANGE,
                rh_current,
                60,  # avg
                55,  # low
                40   # high (your original numbers looked reversed; keep as needed)
            )

                # Refresh every 10s, but check for exit every 0.1s
                exit_pressed = False
                for _ in range(100):
                    if button_a.read() or button_b.read() or button_y.read():
                        exit_pressed = True
                        # Debounce whichever button was pressed
                        while button_a.read() or button_b.read() or button_y.read():
                            await asyncio.sleep(0.01)
                        await asyncio.sleep(0.05)
                        break
                    await asyncio.sleep(0.1)

                if exit_pressed:
                    break

        else:
            await asyncio.sleep(0.1)


async def actuations_display():
    """Poll button A, show outside temp every 10s until another button pressed."""
    global temp_celc_current
    
    error_count = 2

    while True:
        if button_y.read():
            # Debounce button B
            while button_y.read():
                await asyncio.sleep(0.01)
            await asyncio.sleep(0.05)

            # Enter timed refresh mode
            while True:
                await screen_actuations(
                display, BG, WHITE, ORANGE,
                fan_on, roof_open, heat_pad_on, error_count
            )

                # Refresh every 10s, but check for exit every 0.1s
                exit_pressed = False
                for _ in range(100):
                    if button_a.read() or button_b.read() or button_x.read():
                        exit_pressed = True
                        # Debounce whichever button was pressed
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
    while True:
        await csv_complete.wait()
        print("Uploading CSV to cloud...")
        system_log("Uploading CSV to cloud...")
        csv_complete.clear()
        actuator_update.set()

async def actuators(actuator_update, temp_alert):
    global temp_celc_current, rh_current, lux_current, temp_celc_outside_current, roof_open, fan_on, heat_pad_on, is_night, cover_on

    temp_setpoint_low = 15
    temp_setpoint_high = 25
    rh_setpoint_low = 40
    rh_setpoint_high = 70

    prev_temp = None
    prev_rh = None
    prev_roof = 0
    last_change_time = None
    hold_time = 1

    roof_open = 0
    fan_on = False
    heat_pad_on = False
   
    while True:
        await actuator_update.wait()
        actuator_update.clear()

        try:
            temp_celc_current, rh_current, temp_celc_outside_current, lux_current, moisture_current = await sensor()
    
        except Exception as e:
            print("Sensor log error (actuation):", e)
            system_log(f"Sensor log error: {e}")

        (
            prev_temp,
            prev_rh,
            prev_roof,
            last_change_time,
            roof_open,
            fan_on,
            heat_pad_on,
            temp_celc_current,
            rh_current,
        ) = actuator_logic(
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
            temp_celc_current,
            rh_current,
            is_night,
        )
        
        if cover_on:
            if roof_open != 0 or fan_on:
                roof_open = 0
                fan_on = False
                system_log("Cover detected: forced roof closed and fan off")

        # ACTUATIONS START BELOW
        # Roof
        move_roof(prev_roof, roof_open)
    
        # Fan
        if fan_on == True:
            green_led_on()
        elif fan_on == False:
            green_led_off()
        
        # Heat
        if heat_pad_on == True:
            red_led_on()
        elif heat_pad_on == False:
            red_led_off()
            
        # Watering
    
    
        print(f"roof open: {roof_open}, fan on: {fan_on}, heat pad on: {heat_pad_on}")
        temp_alert.set()
        await asyncio.sleep(hold_time)


async def weather_check():
    global sunset_time
    
    # Sleep until 3am next day
    seconds_until_3am = seconds_until(3)
    await asyncio.sleep(seconds_until_3am)
    
    while True:
        api_url = api_url_gen(latitude, longitude, timezone)
        data = get_weather_data(api_url)
        year, month, day, *_ = rtc.datetime()
        date = "{:04d}-{:02d}-{:02d}".format(year, month, day)
        
        if data is not None:
            sunrise_hour = get_sunrise_hour(data)
            sunrise_time = get_sunrise_time(data)
            temp_at_sunrise = get_temperature_at_hour(data, sunrise_hour)
            
            if temp_at_sunrise is not None:
                print(f"Weather data acquired. Sunrise is at {sunrise_time} on {date}. Temperature at sunrise is {temp_at_sunrise}°C")
                system_log(f"Weather data acquired. Sunrise is at {sunrise_time} on {date}. Temperature at sunrise is {temp_at_sunrise}°C")
                
                # Send weather message
                weather_message(15, temp_at_sunrise)
                
                # Update sunset time variable
                sunset_time = get_sunset_time(data)
                sunset_struct = utime.localtime(sunset_time)
                # Extract components
                year, month, day, hour, minute, second, weekday, yearday = sunset_struct
                system_log(f"Sunset time is {hour}:{minute} on {date}")
                
                # Sleep until 3am next day
                seconds_until_3am = seconds_until(3)
                await asyncio.sleep(seconds_until_3am)
                
            else:
                print("Weather API call failed, retrying in 60 seconds")
                system_log("Weather API call failed, retrying in 60 seconds")
                await asyncio.sleep(60)
                
        else:
            print("Weather API failed, retrying in 60 seconds")
            system_log("Weather API failed, retrying in 60 seconds")
            await asyncio.sleep(60)

async def temperature_alert(temp_alert, goodnight):
    while True:
        await temp_alert.wait()
        temp_alert.clear()

        global temp_celc_current, temp_celc_outside_current, roof_open, fan_on

        high_temp_alert(temp_celc_current, temp_celc_outside_current, roof_open, fan_on)
        goodnight.set()


async def goodnight_routine(goodnight):
    global roof_open, fan_on, last_goodnight_date, is_night

    while True:
        await goodnight.wait()
        goodnight.clear()

        current_timestamp = time.mktime(time.localtime())
        local_tm = time.localtime(current_timestamp)
        year, month, day, *_ = local_tm
        current_date = f"{year:04d}-{month:02d}-{day:02d}"

        # Only send goodnight once per day at night
        if is_night and current_date != last_goodnight_date:
            roof_open = 0
            fan_on = False
            goodnight_message()
            last_goodnight_date = current_date


async def cover_check():
    """Runs independently to keep is_night and cover_on up-to-date."""
    global is_night, cover_on, sunset_time
    ltr = BreakoutLTR559(i2c) # define lux sensor

    prev_is_night = None
    prev_cover_on = None

    while True:
        lux_records = []
        for _ in range(4):
            try:
                temp_celc, rh, temp_celc_outside, lux, moisture_value = await sensor()
                lux_records.append(lux)
                await asyncio.sleep(1)
            except Exception as e:
                print("Lux sensor log error:", e)
                system_log(f"Lux sensor log error: {e}")

        dark = (sum(lux_records) == 0)
    
        current_timestamp = time.mktime(time.localtime())

        new_is_night = (current_timestamp > sunset_time) if sunset_time else dark
        new_cover_on = (dark and not new_is_night)

        if new_is_night != prev_is_night:
            prev_is_night = new_is_night

        if new_cover_on != prev_cover_on:
            prev_cover_on = new_cover_on

        is_night = new_is_night
        cover_on = new_cover_on

        await asyncio.sleep(30)  # adjust frequency as needed


async def clock_sync():
    # Sleep until 3am next day
    seconds_until_3am = seconds_until(3)
    await asyncio.sleep(seconds_until_3am)
    while True:
        try:
            t = await get_local_time(timezone)
            struct = t["struct_time"]
            rtc = machine.RTC()
            weekday = utime.localtime(time.mktime(struct))[6]
            rtc.datetime(
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
    """
    Periodically checks Wi-Fi connection and reconnects if dropped.
    """
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


# Run the whole program
asyncio.run(main())

# NEXT
# Move async functions into loop.py? Clean up notes
# Write functions to calculate averages for screen
# write error_count function




# Cloud Infrastructure:

    # AWS IoT Core (optional but robust for secure device messaging via MQTT or HTTPS)
    # AWS Lambda (process/transform data)
    # DynamoDB (store time-series data in NoSQL format)
    # Amazon S3 (for long-term backup or CSV export) 
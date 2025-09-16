import uasyncio as asyncio

from alerts import high_temp_alert, goodnight_message
from logging import system_log
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

from async_loop_functions import (
    sensor_log,
    temp_inside_display,
    temp_outside_display,
    humidity_display,
    actuations_display,
    cloud_upload,
    actuators,
    weather_check,
    temperature_alert,
    goodnight_routine,
    cover_check,
    clock_sync,
    wifi_watch,
)
from async_startup_functions import (
    connect_wifi,
    start_timezone,
    start_location,
    start_clock_sync,
    start_weather_data,
)

from utils import get_local_time, load_config, seconds_until
import state
import machine
import time
import utime

# Set-up
config = load_config()
display = PicoGraphics(display=DISPLAY_PICO_EXPLORER)
i2c = PimoroniI2C(**PICO_EXPLORER_I2C_PINS)

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
GREEN    = display.create_pen(0, 255, 0)
RED      = display.create_pen(255, 0, 0)
ORANGE   = display.create_pen(255, 165, 0)


# Async application
async def main():
    try:
        # Start Screen
        screen_running = asyncio.Event()
        screen_running.set()
        asyncio.create_task(title(display, BG, GREEN))
        asyncio.create_task(
            start_screen(display, screen_running, BG, STEM, LEAF, BUD_BASE, PETALS, CENTER, GREEN)
        )

        await asyncio.sleep(0.01)

        # Define constants and state
        state.record_interval = 5  # seconds
        state.cloud_upload_interval = 5  # sensor reads
        state.roof_open = 0
        state.fan_on = False
        state.irrigation_on = False
        state.heat_pad_on = False
        state.temp_celc_current = None
        state.rh_current = None
        state.temp_celc_outside_current = None
        state.lux_current = None
        state.last_goodnight_date = None
        state.is_night = False
        state.cover_on = False

        # Wait for USB to become ready
        await asyncio.sleep(0.1)
        # Connect to Wi-Fi
        await connect_wifi()
        # Timezone
        state.timezone = await start_timezone()
        # Location
        state.latitude, state.longitude = await start_location()
        # Clock sync at start-up
        rtc = await start_clock_sync(state.timezone)
        state.rtc = rtc
        # Acquire weather data
        (
            state.sunrise_hour,
            state.sunrise_time,
            state.temp_at_sunrise,
            state.sunset_time,
        ) = await start_weather_data()

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
            display,
            BG,
            WHITE,
            ORANGE,
            state.temp_celc_current,
            25,  # average
            18,  # low
            27,  # high
        )

    except Exception as e:
        print("Start-up routine failed:", e)
        system_log(f"Start-up routine failed: {e}")
        screen_running.clear()
        clear_animation_area(display, BG)
        await asyncio.sleep(0.1)
        # Show start-up fail
        await start_up_fail(display, BG, RED, GREEN)
        return  # exit(1) ?

    # Define Asyncio events for main loop
    csv_complete = asyncio.Event()
    actuator_update = asyncio.Event()
    temp_alert = asyncio.Event()
    goodnight = asyncio.Event()

    # Start all tasks concurrently
    await asyncio.gather(
        sensor_log(state.record_interval, state.cloud_upload_interval, csv_complete, actuator_update),
        cloud_upload(csv_complete, actuator_update),
        actuators(actuator_update, temp_alert),
        weather_check(),
        temperature_alert(temp_alert, goodnight),
        goodnight_routine(goodnight),
        clock_sync(),
        cover_check(i2c),
        wifi_watch(SSID, PASSWORD),
        temp_inside_display(button_a, button_b, button_x, button_y),
        temp_outside_display(button_a, button_b, button_x, button_y),
        humidity_display(button_a, button_b, button_x, button_y),
        actuations_display(button_a, button_b, button_x, button_y),
    )

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
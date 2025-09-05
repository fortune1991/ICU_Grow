# Create async to recconect to Wi-Fi if dropped out

import uasyncio as asyncio
import network
import time
import utime
import machine
from actuators import actuator_logic
from alerts import high_temp_alert, goodnight_message
from location import get_location, get_timezone
from logging import log, system_log
from screen import screen
from sensors import sensor
from weather import (
    get_weather_data,
    get_sunrise_hour,
    get_sunset_time,
    get_temperature_at_hour,
    weather_message,
    api_url_gen,
)
from utils import get_local_time, load_config, seconds_until

# Module-level defaults

record_interval = None

roof_open = 0
fan_on = False
irrigation_on = False

temp_celc_current = None
rh_current = None
temp_celc_outside_current = None

last_goodnight_date = None
is_night = False
cover_on = False

timezone = None
latitude = None
longitude = None

config = load_config()


# Async application

async def main():
    global record_interval
    global roof_open, fan_on, irrigation_on, heat_pad_on
    global temp_celc_current, rh_current, temp_celc_outside_current
    global timezone, latitude, longitude
    global is_night, cover_on, last_goodnight_date, sunset_time

    try:
        # Define constants and state
        record_interval = 1
        roof_open = 0
        fan_on = False
        irrigation_on = False
        heat_pad_on = False
        temp_celc_current = None
        rh_current = None
        temp_celc_outside_current = None
        last_goodnight_date = None
        is_night = False
        cover_on = False
        sunset_time = None

        # Wait for USB to become ready (blocking during startup)
        time.sleep(0.1)

        # Connect to Wi-Fi
        SSID = config["SSID"]
        PASSWORD = config["PASSWORD"]

        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(SSID, PASSWORD)

        wifi_retries = 10
        for attempt in range(wifi_retries):
            if wlan.isconnected():
                break
            print("Connecting to Wi-Fi...")
            system_log("Connecting to Wi-Fi...")
            time.sleep(5)
        else:
            raise RuntimeError("Failed to connect to Wi-Fi after multiple attempts")

        print("Connected to Wi-Fi")
        system_log("Connected to Wi-Fi")
        
        # API-dependent variables
        api_retries = 3

        # Timezone
        print("Fetching Timezone")
        system_log("Fetching Timezone")
        for attempt in range(api_retries):
            try:
                timezone = get_timezone()
                print(f"Timezone acquired")
                system_log(f"Timezone acquired")
                break
            except Exception as e:
                print(f"Attempt {attempt+1} to get timezone failed: {e}")
                system_log(f"Attempt {attempt+1} to get timezone failed: {e}")
                time.sleep(2)
        else:
            raise RuntimeError("Failed to get timezone after multiple attempts")

        # Location
        print("Fetching Location")
        system_log("Fetching Location")
        for attempt in range(api_retries):
            try:
                latitude, longitude = get_location()
                print(f"Location acquired")
                system_log(f"Location acquired")
                break
            except Exception as e:
                print(f"Attempt {attempt+1} to get location failed: {e}")
                system_log(f"Attempt {attempt+1} to get location failed: {e}")
                time.sleep(2)
        else:
            raise RuntimeError("Failed to get location after multiple attempts")

        # Clock sync at start-up
        print("Syncing Pi Clock")
        system_log("Syncing Pi Clock")
        t = await get_local_time(timezone, retries=3, delay=0.2)
        struct = t["struct_time"]
        rtc = machine.RTC()
        weekday = utime.localtime(time.mktime(struct))[6]
        rtc.datetime(
            (struct[0], struct[1], struct[2], weekday, struct[3], struct[4], struct[5], 0)
        )
        print("Clock synced at startup")
        system_log("Clock synced at startup")
        
        # Aquire weather data
        for attempt in range(api_retries):
            try:
                api_url = api_url_gen(latitude, longitude, timezone)
                data = get_weather_data(api_url)
                
                if data is not None:
                    sunrise_hour = get_sunrise_hour(data)
                    temp_at_sunrise = get_temperature_at_hour(data, sunrise_hour)
                    
                    if temp_at_sunrise is not None:
                        print(f"Weather data acquired. Temperature at sunrise ({sunrise_hour}:00) is {temp_at_sunrise}°C")
                        system_log(f"Weather data acquired. Temperature at sunrise ({sunrise_hour}:00) is {temp_at_sunrise}°C")
                        
                        # Send weather message
                        weather_message(15, temp_at_sunrise)
                        break
                    
                        # Update sunset time variable
                        sunset_time = get_sunset_time(data)
                    
            except Exception as e:
                print(f"Attempt {attempt+1} to get weather data failed: {e}")
                system_log(f"Attempt {attempt+1} to get weather data failed: {e}")
                time.sleep(2)
        else:
            raise RuntimeError("Failed to get weather data after multiple attempts")

        # UI / Screen
        print("Hello, Pi Pico W!")
        system_log("Hello, Pi Pico W!")
        screen()

        print("Start-up routine successful")
        system_log("Start-up routine successful")

    except Exception as e:
        print("Start-up routine failed:", e)
        system_log(f"Start-up routine failed: {e}")
        return

    # Asyncio events
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
        cover_check(),  # NEW task for continuous cover/night detection
        wifi_watch(SSID, PASSWORD),
    )

async def sensor_log(record_interval, csv_complete, actuator_update):
    global roof_open, fan_on, heat_pad_on, is_night, cover_on
    while True:
        for _ in range(5):
            try:
                temp_celc, rh, temp_celc_outside, lux = sensor()
                log(temp_celc, rh, temp_celc_outside, lux, roof_open, fan_on, heat_pad_on, cover_on)
            except Exception as e:
                print("Sensor log error:", e)
                system_log(f"Sensor log error: {e}")
            await asyncio.sleep(record_interval)

        csv_complete.set()


async def refresh_screen(temp_celc, rh, lux):
    pass

async def cloud_upload(csv_complete, actuator_update):
    while True:
        await csv_complete.wait()
        print("Uploading CSV to cloud...")
        system_log("Uploading CSV to cloud...")
        csv_complete.clear()
        actuator_update.set()

async def actuators(actuator_update, temp_alert):
    global temp_celc_current, rh_current, temp_celc_outside_current, roof_open, fan_on, heat_pad_on, is_night, cover_on

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

        temp_celc_current, rh_current, temp_celc_outside_current, lux_current = sensor()

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
        
        if data is not None:
            sunrise_hour = get_sunrise_hour(data)
            temp_at_sunrise = get_temperature_at_hour(data, sunrise_hour)
            
            if temp_at_sunrise is not None:
                print(f"Weather data acquired. Temperature at sunrise ({sunrise_hour}:00) is {temp_at_sunrise}°C")
                system_log(f"Weather data acquired. Temperature at sunrise ({sunrise_hour}:00) is {temp_at_sunrise}°C")
                
                # Send weather message
                weather_message(15, temp_at_sunrise)
                
                # Update sunset time variable
                sunset_time = get_sunset_time(data)
                
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

    prev_is_night = None
    prev_cover_on = None

    while True:
        lux_records = []
        for _ in range(4):
            lux_records.append(sensor()[3])
            await asyncio.sleep(1)

        dark = (sum(lux_records) == 0)
    
        current_timestamp = time.mktime(time.localtime())

        new_is_night = (current_timestamp > sunset_time) if sunset_time else dark
        new_cover_on = (dark and not new_is_night)

        if new_is_night != prev_is_night:
            system_log(f"is_night changed: {new_is_night}")
            prev_is_night = new_is_night

        if new_cover_on != prev_cover_on:
            system_log(f"cover_on changed: {new_cover_on}")
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


## Once data is being recorded _> Cloud Infrastructure:

    # AWS IoT Core (optional but robust for secure device messaging via MQTT or HTTPS)
    # AWS Lambda (process/transform data)
    # DynamoDB (store time-series data in NoSQL format)
    # Amazon S3 (for long-term backup or CSV export) 
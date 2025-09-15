import uasyncio as asyncio
import network
import time
import utime
import machine
from location import get_location, get_timezone
from logging import system_log
from weather import (
    get_weather_data,
    get_sunrise_hour,
    get_sunrise_time,
    get_sunset_time,
    get_temperature_at_hour,
    weather_message,
    api_url_gen,
)
from utils import get_local_time, load_config

async def connect_wifi():
    config = load_config()
    SSID = config["SSID"]
    PASSWORD = config["PASSWORD"]

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    wifi_retries = 10 # Change back to 10
    for attempt in range(wifi_retries):
        if wlan.isconnected():
            break
        print("Connecting to Wi-Fi...")
        system_log("Connecting to Wi-Fi...")
        await asyncio.sleep(5)
    else:
        raise RuntimeError("Failed to connect to Wi-Fi after multiple attempts")

    print("Connected to Wi-Fi")
    system_log("Connected to Wi-Fi")
    return

async def start_clock_sync(timezone, api_retries=3, delay=0.2):
    print("Syncing Pi Clock")
    system_log("Syncing Pi Clock")
    t = await get_local_time(timezone, api_retries, delay)
    struct = t["struct_time"]
    rtc = machine.RTC()
    weekday = utime.localtime(time.mktime(struct))[6]
    rtc.datetime(
        (struct[0], struct[1], struct[2], weekday, struct[3], struct[4], struct[5], 0)
    )
    print("Clock synced at startup")
    system_log("Clock synced at startup")
    return rtc


async def start_timezone(api_retries=3):
    for attempt in range(api_retries):
        try:
            timezone = get_timezone()
            print(f"Timezone acquired")
            system_log(f"Timezone acquired")
            return timezone
        except Exception as e:
            print(f"Attempt {attempt+1} to get timezone failed: {e}")
            system_log(f"Attempt {attempt+1} to get timezone failed: {e}")
            await asyncio.sleep(2)
    else:
        raise RuntimeError("Failed to get timezone after multiple attempts")


async def start_location(api_retries=3):
    for attempt in range(api_retries):
        try:
            latitude, longitude = get_location()
            print(f"Location acquired")
            system_log(f"Location acquired")
            return latitude, longitude
        except Exception as e:
            print(f"Attempt {attempt+1} to get location failed: {e}")
            system_log(f"Attempt {attempt+1} to get location failed: {e}")
            await asyncio.sleep(2)
    else:
        raise RuntimeError("Failed to get location after multiple attempts")


async def start_weather_data(latitude, longitude, timezone, rtc, api_retries=3):
    for attempt in range(api_retries):
        try:
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
                    return sunrise_hour, sunrise_time, temp_at_sunrise, sunset_time

        except Exception as e:
            print(f"Attempt {attempt+1} to get weather data failed: {e}")
            system_log(f"Attempt {attempt+1} to get weather data failed: {e}")
            await asyncio.sleep(2)
    else:
        raise RuntimeError("Failed to get weather data after multiple attempts")



import uasyncio as asyncio
import network
import time
import utime
import machine
import state
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

    wifi_retries = 10
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

async def start_clock_sync(api_retries=3, delay=0.2):
    """
    Sync Pi RTC at startup.
    """
    t = await get_local_time(state.timezone)
    struct = t["struct_time"][:8]

    rtc = machine.RTC()
    rtc.datetime(tuple(int(x) for x in struct))
    state.rtc = rtc
    
    year, month, day, *_ = state.rtc.datetime()
    date = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    
    if year == 1970:
        print("Clock sync returned default time")
        system_log("Clock sync returned default timer")
        state.add_error("start_clock_sync")
        return rtc

    print("Clock synced at startup")
    system_log("Clock synced at startup")
    return rtc


async def start_timezone(api_retries=3):
    for attempt in range(api_retries):
        try:
            state.timezone = get_timezone()
            print(f"Timezone acquired")
            system_log(f"Timezone acquired")
            return state.timezone
        except Exception as e:
            print(f"Attempt {attempt+1} to get timezone failed: {e}")
            system_log(f"Attempt {attempt+1} to get timezone failed: {e}")
            await asyncio.sleep(2)
    else:
        raise RuntimeError("Failed to get timezone after multiple attempts")

async def start_location(api_retries=3):
    for attempt in range(api_retries):
        try:
            state.latitude, state.longitude = get_location()
            print(f"Location acquired")
            system_log(f"Location acquired")
            return state.latitude, state.longitude
        except Exception as e:
            print(f"Attempt {attempt+1} to get location failed: {e}")
            system_log(f"Attempt {attempt+1} to get location failed: {e}")
            await asyncio.sleep(2)
    else:
        raise RuntimeError("Failed to get location after multiple attempts")

async def start_weather_data(api_retries=3):
    for attempt in range(api_retries):
        try:
            api_url = api_url_gen(state.latitude, state.longitude, state.timezone)
            data = get_weather_data(api_url)
            year, month, day, *_ = state.rtc.datetime()
            date = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
            if data is None:
                raise ValueError("Weather API returned no data")

            # Type-safe assignments
            sunrise_hour = str(get_sunrise_hour(data))
            sunrise_time = str(get_sunrise_time(data))
            temp_at_sunrise = float(get_temperature_at_hour(data, sunrise_hour))
            sunset_time = int(get_sunset_time(data))  # timestamp

            # Assign to state
            state.sunrise_hour = sunrise_hour
            state.sunrise_time = sunrise_time
            state.temp_at_sunrise = temp_at_sunrise
            state.sunset_time = sunset_time

            print(
                f"Weather data acquired. Sunrise at {sunrise_time} on {date}. "
                f"Temperature at sunrise is {temp_at_sunrise}°C"
            )
            system_log(
                f"Weather data acquired. Sunrise at {sunrise_time} on {date}. "
                f"Temperature at sunrise is {temp_at_sunrise}°C"
            )

            # Send weather message
            weather_message(15, temp_at_sunrise)

            # Log sunset time
            sunset_struct = utime.localtime(sunset_time)
            year, month, day, hour, minute, second, weekday, yearday = sunset_struct
            system_log(f"Sunset time is {int(hour)}:{int(minute)} on {date}")

            return sunrise_hour, sunrise_time, temp_at_sunrise, sunset_time

        except Exception as e:
            print(f"Attempt {attempt+1} to get weather data failed: {e}")
            system_log(f"Attempt {attempt+1} to get weather data failed: {e}")
            await asyncio.sleep(2)

    else:
        raise RuntimeError("Failed to get weather data after multiple attempts")




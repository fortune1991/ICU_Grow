import urequests
import ujson
import utime
import time
from logging import system_log
from utils import load_config

def api_url_gen(latitude, longitude, timezone):
    return (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}"
        f"&hourly=temperature_2m"
        f"&daily=sunrise,sunset"
        f"&forecast_days=2"
        f"&timezone={timezone}"
    )

def get_weather_data(api_url, timeout=10):
    """
    Fetches weather data from the API (single attempt).
    Returns data on success, None on failure.
    """    
    response = None
    try:
        print(f"Calling Weather API")
        system_log("Calling Weather API")
        
        # Ping weather data API with timeout
        start_time = utime.ticks_ms()
        response = urequests.get(api_url)
        
        # Timeout check
        elapsed = utime.ticks_diff(utime.ticks_ms(), start_time)
        if elapsed > timeout * 1000:
            raise Exception(f"Timeout after {timeout}s")
        
        # Check HTTP status
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        data = response.json()
        return data
        
    except Exception as e:
        print(f"Weather API error: {e}")
        system_log(f"Weather API error: {e}")
        return None  
        
    finally:
        if response:
            response.close()

def get_sunrise_hour(data):
    sunrise = data['daily']['sunrise'][1].split("T")
    sunrise_time = sunrise[1]
    sunrise_hour = sunrise_time[:2]
    return sunrise_hour

def get_sunset_time(data):
    """
    Returns the sunset time as a timestamp in the same local time
    reference as get_local_time().
    """
    if data is not None:
        # Get current local date
        local_struct = time.localtime()

        # Extract sunset hour and minute from API (already in local timezone)
        sunset_str = data['daily']['sunset'][0]  # e.g., "2025-09-02T19:21"
        _, time_str = sunset_str.split("T")
        hour, minute = map(int, time_str.split(":")[:2])

        # Construct a tuple for sunset on the current local day
        sunset_tuple = (
            local_struct[0],  # year
            local_struct[1],  # month
            local_struct[2],  # day
            hour,             # hour
            minute,           # minute
            0,                # second
            0, 0, -1          # weekday, yearday, dst
        )

        # Convert to timestamp
        sunset_timestamp = time.mktime(sunset_tuple)
        return sunset_timestamp
    return None

def get_temperature_at_hour(data, target_hour):
    if not data:
        print("No data available")
        return None

    times = data['hourly']['time']
    temps = data['hourly']['temperature_2m'] # parallel list of temps

    for i, t in enumerate(times):
        # Extract hour from timestamp, e.g. '2025-07-07T06:00' -> '06'
        hour_str = t.split('T')[1][:2]
        if hour_str == target_hour:
            return temps[i+24]

    print(f"No temperature found for hour {target_hour}")
    return None

def weather_message(target_temp, temp_at_sunrise):
    if temp_at_sunrise is None:
        print("No temperature data; message not sent")
        return

    if temp_at_sunrise < target_temp:
        MESSAGE = (
            f"Hey Clare!\n\n"
            f"It's going to be chilly tonight... {temp_at_sunrise}°C 🥶\n"
            "Best put some blankets on those plant babies!"
        )

        try:
            response = urequests.post(
                "https://ntfy.sh/charitylane_greenhouse",
                data=MESSAGE.encode("utf-8"),
                headers={"Content-Type": "text/plain"},
            )
            response.close()
        except Exception as e:
            print("Error sending notification:", e)

    else:
        print("No message required; temperature above threshold")
import urequests
import ujson
import uasyncio as asyncio
import utime
import time
from location import get_timezone
from logging import system_log

def seconds_until(hour):
    # Calculate sleep time until 3am next day
    now = time.localtime()
    current_hour = now[3]  
    current_minute = now[4]
    current_second = now[5] 
    
    # If it's already past 'hour' today, sleep until 'hour' tomorrow
    if current_hour >= hour:
        hours_until_hour = (24 - current_hour) + hour
    else:
        hours_until_hour = hour - current_hour
    
    # Calculate total seconds to sleep
    seconds_until_hour = (hours_until_hour * 3600) - (current_minute * 60) - current_second
    
    return seconds_until_hour

def load_config():
    with open("config.json") as f:
        return ujson.load(f)

def save_update_id(update_id):
    with open("last_id.txt", "w") as f:
        f.write(str(update_id))

def load_update_id():
    try:
        with open("last_id.txt") as f:
            return int(f.read())
    except:
        return 0

async def get_local_time(timezone, retries=2, delay=2, timeout=10):
    """
    Async MicroPython version: fetches local time with fallback methods
    """
    response = None
    for attempt in range(1, retries + 1):
        try:
            # Get time from World Time API
            start_time = utime.ticks_ms()
            response = urequests.get(f"http://worldtimeapi.org/api/timezone/{timezone}")
            # Timeout exception
            if utime.ticks_diff(utime.ticks_ms(), start_time) > timeout * 1000:
                response.close()
                raise Exception(f"API timeout after {timeout} seconds")
            
            data = ujson.loads(response.text)
            
            datetime_str = data['datetime']
            utc_offset = data['utc_offset'] 

            # Parse UTC time
            year = int(datetime_str[0:4])
            month = int(datetime_str[5:7])
            day = int(datetime_str[8:10])
            hour = int(datetime_str[11:13])
            minute = int(datetime_str[14:16])
            second = int(datetime_str[17:19])
                        
            struct = (year, month, day, hour, minute, second, 0, 0, -1)
            timestamp = time.mktime(struct)

            print(f"Local time fetched successfully from World Time API")
            system_log(f"Local time fetched successfully from World Time API")
            return {"struct_time": struct, "timestamp": timestamp, "offset": utc_offset}

        except Exception as e:
            print(f"Attempt {attempt} to sync clock failed: {e}")
            system_log(f"Attempt {attempt} to sync clock failed: {e}")
            
            if attempt < retries:
                await asyncio.sleep(delay)
                delay *= 2
            else:
                # Zeroed Unix timestamp as a last resort
                print(f"World Time API failed. Returning default time")
                system_log(f"World Time API failed. Returning default time")
                struct = (1970, 1, 1, 0, 0, 0, 3, 1, 0)
                timestamp = time.mktime(struct)
                return {"struct_time": struct, "timestamp": timestamp, "offset": "+00:00"}
            
        finally:
            if response:
                response.close()
    
                    
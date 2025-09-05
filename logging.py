import uasyncio as asyncio
import time


def log(temp_celc, rh, temp_celc_outside, lux, roof_open, fan_on, heat_pad_on, cover_on):
    lt = time.localtime()
    timestamp = "{}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
        lt[0], lt[1], lt[2], lt[3], lt[4], lt[5]
    )
    line = f"{timestamp},{temp_celc:.2f},{rh:.2f},{temp_celc_outside:.2f},{lux:.2f},{roof_open},{fan_on},{heat_pad_on},{cover_on}\n"
    with open("data_log.csv", "a") as file:
        file.write(line)
        
def system_log(item):
    lt = time.localtime()
    timestamp = "{}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
        lt[0], lt[1], lt[2], lt[3], lt[4], lt[5]
    )
    line = f"{timestamp}: {item}\n"
    with open("system_log.csv", "a") as file:
        file.write(line)


 
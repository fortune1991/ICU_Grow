# State and Constant Values

# Constants
record_interval = 5 
cloud_upload_interval = 5
water_me_threshold = 25

# States
roof_open = 0
fan_on = False
irrigation_on = False
heat_pad_on = False

temp_celc_current = None
rh_current = None
temp_celc_outside_current = None
lux_current = None

temp_celc_average = None
temp_celc_outside_average = None
rh_average = None

temp_celc_low = None
temp_celc_outside_low = None
rh_low = None

temp_celc_high = None
temp_celc_outside_high = None
rh_high = None

last_goodnight_date = None
is_night = False
cover_on = False

timezone = None
latitude = None
longitude = None

sunset_time = None
sunrise_hour = None
sunrise_time = None
temp_at_sunrise = None

rtc = None

error_count = []

def add_error(name: str):
    if name not in error_count:
        error_count.append(name)


def clear_error(name: str):
    if name in error_count:
        error_count.remove(name)


def error_total() -> int:
    return len(error_count)

import urequests
import ujson
import time

# Global variables to track alerts
last_high_temp_alert_time = 0
alert_cooldown = 3600  # seconds (1 hour cooldown)

def high_temp_alert(temp_celc_current, temp_celc_outside_current, roof_open, fan_on):
    global last_high_temp_alert_time
    current_struct = time.localtime()
    current_time = time.mktime(current_struct)  # <-- convert to seconds

    # Only trigger if conditions met AND cooldown passed
    if temp_celc_current > 40:
        if current_time - last_high_temp_alert_time > alert_cooldown:
            MESSAGE = (
                f"Hey Clare!\n\n"
                f"RED ALERT! It's bloody cooking in here... 🥵 {temp_celc_current}°C!\n\n"
                "Remove those plant babies"
            )
            try:
                response = urequests.post(
                    "https://ntfy.sh/charitylane_greenhouse",
                    data=MESSAGE.encode("utf-8"),
                    headers={"Content-Type": "text/plain"},
                )
                response.close()
            except Exception as e:
                print("Error sending high_temp notification:", e)
                system_log(f"Error sending high_temp notification: {e}")

            print("Temperature Alert Message Sent")
            system_log("Temperature Alert Message Sent")
            last_high_temp_alert_time = current_time

def goodnight_message():
    MESSAGE = ("Goodnight!")
    try:
        response = urequests.post(
            "https://ntfy.sh/charitylane_greenhouse",
            data=MESSAGE.encode("utf-8"),
            headers={"Content-Type": "text/plain"},
        )
        response.close()
    except Exception as e:
        print("Error sending notification:", e)
    
    return


import urequests
import utime
import time
import ujson

def get_location():
    while True:
        response = None
        try:
            # Ping location API with Timeout
            response = urequests.get("http://ip-api.com/json/",timeout=5)
            
            # Check HTTP status
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            
            data = response.json()

            # Make sure keys exist before returning
            if "lat" in data and "lon" in data:
                return data["lat"], data["lon"]

        except Exception as e:
            print("Location request failed:", e)
            
        finally:
            if response:
                response.close()

        # Wait a bit before retrying, otherwise it hammers the API
        time.sleep(5)
        return


def get_timezone():
    while True:
        response = None
        try:
            #Ping Timezone API with Timeout
            response = urequests.get("http://ip-api.com/json/",timeout=5)
            
            # Check HTTP status
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            
            data = response.json()

            if "timezone" in data:
                return data["timezone"]

        except Exception as e:
            print("Timezone request failed:", e)
            
        finally:
            if response:
                response.close()

        time.sleep(5)
        return
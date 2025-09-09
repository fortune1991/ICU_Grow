from breakout_bme280 import BreakoutBME280
from breakout_ltr559 import BreakoutLTR559
from logging import system_log
from pimoroni_i2c import PimoroniI2C
from pimoroni import PICO_EXPLORER_I2C_PINS
from machine import Pin, ADC
from moisture import Moisture
from time import sleep
import onewire
import ds18x20

def sensor():
    """Set-up hardware connections"""
    i2c = PimoroniI2C(**PICO_EXPLORER_I2C_PINS) #explorer base
    bme = BreakoutBME280(i2c, address=0x76) # temp and rh
    ltr = BreakoutLTR559(i2c) # Lux
    external_thermometer = Pin(0, Pin.IN)
    one_wire_sensor = ds18x20.DS18X20(onewire.OneWire(external_thermometer)) # also part of external temperature sensor
    moisture = Moisture(5) # Pin number
    
    """Breakout Sensor Readings"""
    # TEMPERATURE AND RH INSIDE
    # read the BME280 sensor
    temp_celc, pressure, rh = get_temp(bme)
    
    # LIGHT
    lux = get_lux(ltr)
    
    # EXTERNAL TEMP
    # read the external thermometer
    temp_celc_outside = get_external_temp(one_wire_sensor)
    
    # Moisture
    moisture_value = get_moisture(moisture)
    
    print(f"temp_celc = {temp_celc}, rh = {rh}, temp_celc_outside = {temp_celc_outside}, lux = {lux}, moisture = {moisture_value}")
    
    return temp_celc, rh, temp_celc_outside, lux, moisture_value

def get_lux(ltr, no_reads=3, delay=0.1):
    """
    Discard the first `warmup_reads` readings from the LTR559
    to skip None/invalid values, then return the next valid lux.
    """
    
    for i in range(no_reads):
        ltr.get_reading()   # discard
        sleep(delay)
    
    # now trust readings
    reading = ltr.get_reading()
    if reading is not None:
        return reading[BreakoutLTR559.LUX]
    return float("inf")

def get_temp(bme, no_reads=3, delay=0.1):
    """
    Discard the first `warmup_reads` readings from the LTR559
    to skip None/invalid values, then return the next valid lux.
    """
    
    for i in range(no_reads):
        bme.read() # discard
        sleep(delay)
    # now trust readings
    temp_celc, pressure, rh = bme.read()
    if temp_celc is not None:
        return temp_celc, pressure, rh
    return None

def get_external_temp(one_wire_sensor, delay=0.1):
    external_temp = 0
    try:
        roms = one_wire_sensor.scan()
        sensor_count = len(roms)
        if sensor_count > 0:
            one_wire_sensor.convert_temp()
            sleep(0.8)
            for rom in roms:
                external_temp = one_wire_sensor.read_temp(rom)
                sleep(delay)

    except:
        system_log("Error reading external tempurature sensor")
        
    return external_temp

def get_moisture(moisture):
    # give it at least 1 second to count pulses
    sleep(1.2)
    return moisture.read()
    


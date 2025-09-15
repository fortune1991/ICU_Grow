from breakout_bme280 import BreakoutBME280
from breakout_ltr559 import BreakoutLTR559
from logging import system_log
from pimoroni_i2c import PimoroniI2C
from pimoroni import PICO_EXPLORER_I2C_PINS
from machine import Pin, ADC
from moisture import Moisture
import uasyncio as asyncio
import onewire
import ds18x20
import time

async def sensor():
    """Set-up hardware connections"""
    i2c = PimoroniI2C(**PICO_EXPLORER_I2C_PINS) #explorer base
    bme = BreakoutBME280(i2c, address=0x76) # temp and rh
    ltr = BreakoutLTR559(i2c) # Lux
    external_thermometer = Pin(0, Pin.IN)
    one_wire_sensor = ds18x20.DS18X20(onewire.OneWire(external_thermometer)) # also part of external temperature sensor
    moisture = Moisture(5) # Pin number
    pi_temp = ADC(4) # The internal temperature sensor is connected to ADC4
    
    # Convert raw ADC reading into voltage for Pi Temp
    temp_conversion_factor = 3.3 / 65535
    
    """Breakout Sensor Readings"""
    # TEMPERATURE AND RH INSIDE
    # read the BME280 sensor
    temp_celc, pressure, rh = (await get_temp(bme))
    
    # LIGHT
    lux = await get_lux(ltr)
    
    # EXTERNAL TEMP
    # read the external thermometer
    #temp_celc_outside = get_external_temp(one_wire_sensor)
    
    # read the Pi sensor
    outside_temp_reading = pi_temp.read_u16() * temp_conversion_factor
    # Formula from the RP2040 datasheet:
    temp_celc_outside = 27 - (outside_temp_reading - 0.706)/0.001721
    
    # Moisture
    moisture_value = await get_moisture(moisture)
    
    print(f"temp_celc = {temp_celc}, rh = {rh}, temp_celc_outside = {temp_celc_outside}, lux = {lux}, moisture = {moisture_value}")
    
    return temp_celc, rh, temp_celc_outside, lux, moisture_value

async def get_lux(ltr, no_reads=2, delay=0.1):
    """
    Discard the first `warmup_reads` readings from the LTR559
    to skip None/invalid values, then return the next valid lux.
    """
    
    for i in range(no_reads):
        ltr.get_reading()
        time.sleep(delay)
    
    # now trust readings
    reading = ltr.get_reading()
    if reading is not None:
        return reading[BreakoutLTR559.LUX]
    raise ValueError("Lux Sensor returned None") 
    

async def get_temp(bme, no_reads=2, delay=0.1):
    for _ in range(no_reads):
        bme.read()
        time.sleep(delay)

    reading = bme.read()
    
    # Always unpack safely
    temp_celc, pressure, rh, *rest = reading  # ignore extra values
    if temp_celc is not None and rh is not None:
        return temp_celc, pressure, rh

    raise ValueError("Environmental Sensor returned None")
    

async def get_external_temp(one_wire_sensor, delay=0.1):
    external_temp = 0
    
    roms = one_wire_sensor.scan()
    sensor_count = len(roms)
    if sensor_count > 0:
        one_wire_sensor.convert_temp()
        time.sleep(0.8)
        for rom in roms:
            external_temp = one_wire_sensor.read_temp(rom)
            time.sleep(delay)
    
    if external_temp is not None:
        return external_temp
    raise ValueError("External Temperature Sensor returned None") 
    
async def get_moisture(moisture,delay=1.2):
    # give it at least 1 second to count pulses
    await asyncio.sleep(delay)
    reading = moisture.read()
    if reading is not None:
        return reading
    raise ValueError("Moisture Sensor returned None")
    


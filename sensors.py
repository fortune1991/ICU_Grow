from breakout_bme280 import BreakoutBME280
from breakout_ltr559 import BreakoutLTR559
from pimoroni_i2c import PimoroniI2C
from pimoroni import PICO_EXPLORER_I2C_PINS
from machine import Pin, ADC
from moisture import Moisture
from time import sleep

def sensor():
    """Set-up hardware connections"""
    i2c = PimoroniI2C(**PICO_EXPLORER_I2C_PINS) #explorer base
    bme = BreakoutBME280(i2c, address=0x76) # temp and rh
    ltr = BreakoutLTR559(i2c) # Lux
    pi_temp = ADC(4) # The internal temperature sensor is connected to ADC4
    moisture = Moisture(5) # Pin number
    
    # Convert raw ADC reading into voltage
    temp_conversion_factor = 3.3 / 65535
    
    """Breakout Sensor Readings"""
    # TEMPERATURE AND RH INSIDE
    # read the BME280 sensor
    temp_celc, pressure, rh = get_temp(bme)
    
    # LIGHT
    lux = get_lux(ltr)
    
    # EXTERNAL TEMP
    # read the Pi sensor
    outside_temp_reading = pi_temp.read_u16() * temp_conversion_factor
    # Formula from the RP2040 datasheet:
    temp_celc_outside = 27 - (outside_temp_reading - 0.706)/0.001721
    
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

def get_moisture(moisture):
    # give it at least 1 second to count pulses
    sleep(1.2)
    return moisture.read()

    
    """
    Sensor Connections Old
    
    import dht

    # DHT Inside
    dht_pin = Pin(0)
    dht_sensor = dht.DHT22(dht_pin)

    # DHT Outside
    dht_outside_pin = Pin(1)
    dht_outside_sensor = dht.DHT22(dht_outside_pin)

    # LDR
    ldr_pin = Pin(26)
    ldr_sensor = ADC(ldr_pin)

    # Soil Moisture Sensor
    # ADD CODE HERE

    # Constants for LDR config
    GAMMA = 0.7
    RL10 = 50000.0
    R_FIXED = 10000.0  # 10 kΩ
    """
    
    """
    DHT Inside Sensor Reading

    try:
        dht_sensor.measure()

        temp_celc = dht_sensor.temperature()
        rh = dht_sensor.humidity()

        #print("Temperature: {:.2f} °C".format(temp_celc))
        #print("Humidity: {:.2f} %".format(rh))

    except Exception as e:
        print("Error reading DHT22:", str(e))
    """

    """
    DHT Outside Sensor Reading

    try:
        dht_outside_sensor.measure()

        temp_celc_outside = dht_outside_sensor.temperature()
        rh_outside = dht_outside_sensor.humidity()

        #print("Temperature: {:.2f} °C".format(temp_celc_outside))
        #print("Humidity: {:.2f} %".format(rh_outside))

    except Exception as e:
        print("Error reading DHT22:", str(e))
    """

    """LDR Reading
    try:
        ldr_sensor_value = ldr_sensor.read_u16()  # 0-65535 for 0-3.3V
        analogValue = ldr_sensor_value
        voltage = analogValue * 3.3 / 65535.0
        resistance = R_FIXED * voltage / (3.3 - voltage)

        # Check for valid resistance
        if resistance > 0:
            lux = pow((RL10 * pow(10, GAMMA)) / resistance, 1.0 / GAMMA)
            #print("Light Intensity: {:.2f} Lux".format(lux))
        else:
            print("Invalid resistance value, cannot compute lux.")

    except Exception as e:
        print("Error reading LDR:", str(e))
    """



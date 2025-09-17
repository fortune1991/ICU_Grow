from machine import Pin
import time

class Moisture:
    def __init__(self, pin_num, wet_point=0.7, dry_point=27.6):
        self.pin = Pin(pin_num, Pin.IN)
        self.count = 0
        self.reading = 0
        self.last_time = time.ticks_ms()
        self.wet_point = wet_point
        self.dry_point = dry_point

        # Interrupt to count pulses
        self.pin.irq(trigger=Pin.IRQ_RISING, handler=self._pulse)

    def _pulse(self, pin):
        self.count += 1

    def read(self):
        now = time.ticks_ms()
        elapsed = (now - self.last_time) / 1000  # seconds
        if elapsed >= 1.0:
            self.reading = self.count / elapsed
            self.count = 0
            self.last_time = now
        return self.reading

    @property
    def saturation(self):
        sat = (self.reading - self.dry_point) / (self.wet_point - self.dry_point)
        return max(0.0, min(1.0, sat))
     
def water_me(moisture_value, threshold):
    """Sensor when dry = 31 Sensor when wet = 7"""
    if moisture_value > threshold:
        return True
    
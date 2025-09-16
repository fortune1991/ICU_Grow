from machine import Pin

def red_led_on():
    red_led = Pin(1, Pin.OUT)
    red_led.value(1)
    
def red_led_off():
    red_led = Pin(1, Pin.OUT)
    red_led.value(0)

def green_led_on():
    red_led = Pin(2, Pin.OUT)
    red_led.value(1)
    
def green_led_off():
    red_led = Pin(2, Pin.OUT)
    red_led.value(0)
    
def blue_led_on():
    red_led = Pin(3, Pin.OUT)
    red_led.value(1)

def blue_led_off():
    red_led = Pin(3, Pin.OUT)
    red_led.value(0)



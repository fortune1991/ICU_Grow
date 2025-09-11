# https://www.instructables.com/Raspberry-Pi-Pico-Pico-Explorer-Workout/

# This example lets you plug a BME280 breakout into your Pico Explorer and make a little indoor weather station, with barometer style descriptions.

import uasyncio as asyncio
import time
import math
from picographics import PicoGraphics, DISPLAY_PICO_EXPLORER

async def title(display, BG, GREEN):
    """
    Animated flower growth screen.
    Stops automatically if `screen_running` is set False.
    """    
    # Clear Screen
    display.set_pen(BG)
    display.clear()
    await asyncio.sleep(2)
    
    # Title
    display.set_pen(GREEN)
    display.text("ICU Grow", 40, 10, 200, 4)
    display.update()
    
def clear_animation_area(display, BG, top_y=40):
    """
    Clears only the area below the title, leaving the title intact.
    
    :param display: PicoGraphics display object
    :param BG: background pen color
    :param top_y: the y-coordinate where the animation starts
    """
    width, height = display.get_bounds()
    display.set_pen(BG)
    display.rectangle(0, top_y, width, height - top_y)
    display.update()
    
    
async def start_screen(display, screen_running, BG, STEM, LEAF, BUD_BASE, PETALS, CENTER, GREEN):
    """
    Animated flower growth screen.
    Stops automatically if `screen_running` is set False.
    """
    await asyncio.sleep(2)
    
    plant_height = 0
    max_height = 110
    stem_x = 120
    stem_base = 210
    stem_width = 3

    leaf_stages = [
        {"y": 55, "side": -1, "max_size": 10},
        {"y": 70, "side": 1,  "max_size": 12},
        {"y": 85, "side": -1, "max_size": 14},
        {"y": 100, "side": 1, "max_size": 14},
    ]

    def draw_filled_leaf(x, y, size, flip=False):
        for dx in range(-size, size + 1):
            height = int(math.sqrt(size**2 - dx**2) * 0.6)
            for dy in range(-height, height + 1):
                display.pixel(x + dx if not flip else x - dx, y + dy)

    def draw_flower(x, y, growth):
        bud_size = int(5 + growth * 0.5)
        max_size = 28
        if bud_size > max_size:
            bud_size = max_size

        display.set_pen(BUD_BASE)
        display.circle(x, y, bud_size)

        if bud_size > 10:
            display.set_pen(PETALS)
            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                px = int(x + math.cos(rad) * (bud_size + 5))
                py = int(y + math.sin(rad) * (bud_size + 5))
                display.circle(px, py, bud_size // 3)

        if bud_size > 12:
            display.set_pen(CENTER)
            display.circle(x, y, bud_size // 3)
    
    while screen_running.is_set():
        # Draw stem
        display.set_pen(STEM)
        for h in range(plant_height):
            offset = int(4 * math.sin(h / 25))
            display.rectangle(stem_x + offset - stem_width // 2, stem_base - h, stem_width, 1)

        # Leaves
        for leaf in leaf_stages:
            if plant_height > leaf["y"]:
                growth = min((plant_height - leaf["y"]) // 3, leaf["max_size"])
                if growth > 0:
                    display.set_pen(LEAF)
                    draw_filled_leaf(
                        stem_x + (leaf["side"] * (10 + growth // 2)),
                        stem_base - leaf["y"],
                        growth,
                        flip=(leaf["side"] < 0),
                    )

        # Flower
        if plant_height > max_height * 0.6:
            growth_progress = (plant_height - max_height * 0.6) / (max_height * 0.4)
            draw_flower(stem_x, stem_base - max_height, growth_progress * 50)

        display.update()

        # Growth speed
        if plant_height < max_height:
            plant_height += 3
            await asyncio.sleep(0.05)
        else:
            await asyncio.sleep(1.5)
            plant_height = 0
            
    # Clear Screen when exiting start-up screen
    clear_animation_area(display, BG)
    await asyncio.sleep(1)
    
async def start_up_success(display, BG, WHITE, GREEN):
    """
    Flashing success message without background corruption.
    """
    await asyncio.sleep(1)
    
    # Flash message
    for _ in range(3):
        # Draw Title and Message
        display.set_pen(GREEN)
        display.text("ICU Grow", 40, 10, 200, 4)
        display.set_pen(WHITE)
        display.text("Startup Successful", 40, 50, 200, 4)
        display.update()
        await asyncio.sleep(0.5)
        # Flash effect (rectangle over message)
        display.set_pen(BG)
        display.rectangle(40, 50, 200, 60)
        display.update()
        await asyncio.sleep(0.5)

    # Final message
    display.set_pen(GREEN)
    display.text("ICU Grow", 40, 10, 200, 4)
    display.set_pen(WHITE)
    display.text("Startup Successful", 40, 50, 200, 4)
    display.update()
    

async def start_up_fail(display, BG, RED, GREEN):
    """
    Flashing fail message without background corruption.
    """    
    await asyncio.sleep(1)

    # Flash message
    for _ in range(3):
        # Draw Title and Message
        display.set_pen(GREEN)
        display.text("ICU Grow", 40, 10, 200, 4)
        display.set_pen(RED)
        display.text("Startup FAILED", 40, 50, 200, 4)
        display.update()
        await asyncio.sleep(0.5)
        # Flash effect (rectangle over message)
        display.set_pen(BG)
        display.rectangle(40, 50, 200, 60)
        display.update()
        await asyncio.sleep(0.5)

    # Final message
    display.set_pen(GREEN)
    display.text("ICU Grow", 40, 10, 200, 4)
    display.set_pen(RED)
    display.text("Startup FAILED", 40, 50, 200, 4)
    display.update()

# Placeholder functions
def screen_current():
    pass

def screen_average():
    pass

    
"""
import time
from breakout_bme280 import BreakoutBME280
from pimoroni_i2c import PimoroniI2C
from pimoroni import PICO_EXPLORER_I2C_PINS
from picographics import PicoGraphics, DISPLAY_PICO_EXPLORER

# set up the hardware
display = PicoGraphics(display=DISPLAY_PICO_EXPLORER)
i2c = PimoroniI2C(**PICO_EXPLORER_I2C_PINS)
bme = BreakoutBME280(i2c, address=0x76)

# lets set up some pen colours to make drawing easier
TEMPCOLOUR = display.create_pen(0, 0, 0)  # this colour will get changed in a bit
WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)
RED = display.create_pen(255, 0, 0)
GREY = display.create_pen(125, 125, 125)


# converts the temperature into a barometer-type description and pen colour
def describe_temperature(temperature):
    global TEMPCOLOUR
    if temperature < 10:
        description = "very cold"
        TEMPCOLOUR = display.create_pen(0, 255, 255)
    elif 10 <= temperature < 20:
        description = "cold"
        TEMPCOLOUR = display.create_pen(0, 0, 255)
    elif 20 <= temperature < 25:
        description = "temperate"
        TEMPCOLOUR = display.create_pen(0, 255, 0)
    elif 25 <= temperature < 30:
        description = "warm"
        TEMPCOLOUR = display.create_pen(255, 255, 0)
    elif temperature >= 30:
        description = "very warm"
        TEMPCOLOUR = display.create_pen(255, 0, 0)
    else:
        description = ""
        TEMPCOLOUR = display.create_pen(0, 0, 0)
    return description


# converts pressure into barometer-type description
def describe_pressure(pressure):
    if pressure < 970:
        description = "storm"
    elif 970 <= pressure < 990:
        description = "rain"
    elif 990 <= pressure < 1010:
        description = "change"
    elif 1010 <= pressure < 1030:
        description = "fair"
    elif pressure >= 1030:
        description = "dry"
    else:
        description = ""
    return description


# converts humidity into good/bad description
def describe_humidity(humidity):
    if 40 < humidity < 60:
        description = "good"
    else:
        description = "bad"
    return description


while True:
    display.set_pen(BLACK)
    display.clear()

    # read the sensors
    temperature, pressure, humidity = bme.read()
    # pressure comes in pascals which is a reight long number, lets convert it to the more manageable hPa
    pressurehpa = pressure / 100

    # draw a thermometer/barometer thingy
    display.set_pen(GREY)
    display.circle(190, 190, 40)
    display.rectangle(180, 45, 20, 140)

    # switch to red to draw the 'mercury'
    display.set_pen(RED)
    display.circle(190, 190, 30)
    thermometerheight = int(120 / 30 * temperature)
    if thermometerheight > 120:
        thermometerheight = 120
    if thermometerheight < 1:
        thermometerheight = 1
    display.rectangle(186, 50 + 120 - thermometerheight, 10, thermometerheight)

    # drawing the temperature text
    display.set_pen(WHITE)
    display.text("temperature:", 10, 10, 240, 3)
    display.set_pen(TEMPCOLOUR)
    display.text("{:.1f}".format(temperature) + "C", 10, 30, 240, 5)
    display.set_pen(WHITE)
    display.text(describe_temperature(temperature), 10, 60, 240, 3)

    # and the pressure text
    display.text("pressure:", 10, 90, 240, 3)
    display.text("{:.0f}".format(pressurehpa) + "hPa", 10, 110, 240, 5)
    display.text(describe_pressure(pressurehpa), 10, 140, 240, 3)

    # and the humidity text
    display.text("humidity:", 10, 170, 240, 3)
    display.text("{:.0f}".format(humidity) + "%", 10, 190, 240, 5)
    display.text(describe_humidity(humidity), 10, 220, 240, 3)

    # time to update the display
    display.update()

    # waits for 1 second and clears to BLACK
    time.sleep(1)
"""

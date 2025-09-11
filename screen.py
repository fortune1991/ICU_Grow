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
    display.set_pen(RED)
    display.text("Startup FAILED", 40, 50, 200, 4)
    display.update()

def screen_temperature_inside(display, BG, WHITE, temp_celc_current, temp_celc_average, temp_celc_low, temp_celc_high):
    clear_animation_area(display, BG)

def screen_temperature_outside(temp_celc_outside_current, temp_celc_outside_average, temp_celc_outside_low, temp_celc_outside_high):
    pass

def screen_temperature_humidity(rh_current, rh_average, rh_low, rh_high):
    pass

def screen_actuations():
    pass




# TESTING

async def main():
    display = PicoGraphics(display=DISPLAY_PICO_EXPLORER)

    # Screen Colours
    BG       = display.create_pen(15, 25, 35)     # deep background
    STEM     = display.create_pen(30, 160, 60)    # stem green
    LEAF     = display.create_pen(50, 210, 100)   # leaf green
    BUD_BASE = display.create_pen(60, 180, 80)    # green bud base
    PETALS   = display.create_pen(240, 120, 160)  # petals (pink)
    CENTER   = display.create_pen(255, 230, 120)  # yellow centre
    WHITE    = display.create_pen(255, 255, 255)
    GREEN = display.create_pen(0, 255, 0)
    RED = display.create_pen(255, 0, 0)
    
    await start_up_success(display, BG, WHITE, GREEN)

# Run the event loop
asyncio.run(main())


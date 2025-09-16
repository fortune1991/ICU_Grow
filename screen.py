import uasyncio as asyncio
import time
import math
from picographics import PicoGraphics, DISPLAY_PICO_EXPLORER

def fmt_degrees(value):
        try:
            return f"{value:.1f}°C"
        except (TypeError, ValueError):
            return "N/A"

def fmt_percent(value):
        try:
            return f"{value:.0f}%"
        except (TypeError, ValueError):
            return "N/A"

async def title(display, BG, GREEN):
    """
    Animated flower growth screen.
    Stops automatically if `screen_running` is set False.
    """    
    # Clear Screen
    display.set_pen(BG)
    display.clear()
    await asyncio.sleep(0.1)
    
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
    
async def menu(display, BG, WHITE, ORANGE):
    clear_animation_area(display, BG)
    # Title
    display.set_pen(WHITE)
    display.text("Menu", 40, 45, 200, 3)
    # A button
    display.set_pen(ORANGE)
    display.text(f"Press A for: ", 40, 75, 200, 2)
    display.set_pen(WHITE)
    display.text(f"Temperature (inside)", 40, 90, 200, 2)
    # B button
    display.set_pen(ORANGE)
    display.text(f"Press B for: ", 40, 120, 200, 2)
    display.set_pen(WHITE)
    display.text(f"Temperature (outside)", 40, 135, 200, 2)
    # X button
    display.set_pen(ORANGE)
    display.text(f"Press X for: ", 40, 165, 200, 2)
    display.set_pen(WHITE)
    display.text(f"Humidity", 40, 180, 200, 2)
    # Y button
    display.set_pen(ORANGE)
    display.text(f"Press Y for: ", 40, 195, 200, 2)
    display.set_pen(WHITE)
    display.text(f"Actuations and Errors", 40, 210, 200, 2)
    
    display.update()
    await asyncio.sleep(0.5)
    
    
async def start_screen(display, screen_running, BG, STEM, LEAF, BUD_BASE, PETALS, CENTER, GREEN):
    """
    Memory-light animated flower growth.
    Redraws stem, leaves, and flower each frame.
    Stops if `screen_running` is cleared.
    """
    await asyncio.sleep(0.1)

    max_height = 110
    stem_x = 120
    stem_base = 210
    stem_width = 3

    # Leaf positions relative to stem
    leaf_stages = [
        {"y": 55, "side": -1, "max_size": 10},
        {"y": 70, "side": 1,  "max_size": 12},
        {"y": 85, "side": -1, "max_size": 14},
        {"y": 100, "side": 1, "max_size": 14},
    ]

    def draw_leaf(x, y, size, flip=False):
        step = 2  # reduces pixel count, saves memory
        for dx in range(-size, size + 1, step):
            height = int(math.sqrt(size**2 - dx**2) * 0.6)
            for dy in range(-height, height + 1, step):
                display.pixel(x + (-dx if flip else dx), y + dy)

    def draw_flower(x, y, growth):
        bud_size = min(int(5 + growth * 0.5), 28)
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

    plant_height = 0

    while screen_running.is_set():
        # Clear only animation area (optional, keep stem redraw simple)
        width, height = display.get_bounds()
        display.set_pen(BG)
        display.rectangle(0, 40, width, height - 40)

        # Draw stem
        display.set_pen(STEM)
        for h in range(plant_height):
            offset = int(4 * math.sin(h / 25))
            display.rectangle(stem_x + offset - stem_width // 2, stem_base - h, stem_width, 1)

        # Draw leaves
        display.set_pen(LEAF)
        for leaf in leaf_stages:
            if plant_height > leaf["y"]:
                growth = min((plant_height - leaf["y"]) // 3, leaf["max_size"])
                if growth > 0:
                    draw_leaf(stem_x + (leaf["side"] * (10 + growth // 2)),
                              stem_base - leaf["y"],
                              growth,
                              flip=(leaf["side"] < 0))

        # Draw flower bud
        if plant_height > max_height * 0.6:
            growth_progress = (plant_height - max_height * 0.6) / (max_height * 0.4)
            draw_flower(stem_x, stem_base - max_height, growth_progress * 50)

        display.update()

        # Increment growth
        if plant_height < max_height:
            plant_height += 6
            await asyncio.sleep(0.05)  # growth speed
        else:
            await asyncio.sleep(0.5)
            plant_height = 0


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


async def screen_temperature_inside(display, BG, WHITE, ORANGE, temp_celc_current, temp_celc_average, temp_celc_low, temp_celc_high):
    clear_animation_area(display, BG)
    # Title
    display.set_pen(WHITE)
    display.text("Temperature (Inside)", 40, 50, 200, 3)
    # Current label
    display.set_pen(ORANGE)
    display.text(f"Current: ", 40, 105, 200, 2)
    # Current value
    display.set_pen(WHITE)
    display.text(fmt_degrees(temp_celc_current), 132, 105, 200, 2)
    # Average label
    display.set_pen(ORANGE)
    display.text(f"Average: ", 40, 130, 200, 2)
    # Average value
    display.set_pen(WHITE)
    display.text(fmt_degrees(temp_celc_average), 132, 130, 200, 2)
    # Low label
    display.set_pen(ORANGE)
    display.text(f"Low: ", 40, 155, 200, 2)
    # Low value
    display.set_pen(WHITE)
    display.text(fmt_degrees(temp_celc_low), 90, 155, 200, 2)
    # High label
    display.set_pen(ORANGE)
    display.text(f"High: ", 40, 180, 200, 2)
    # High value
    display.set_pen(WHITE)
    display.text(fmt_degrees(temp_celc_high), 90, 180, 200, 2)
    
    display.update()
    await asyncio.sleep(0.5)
    

async def screen_temperature_outside(display, BG, WHITE, ORANGE, temp_celc_outside_current, temp_celc_outside_average, temp_celc_outside_low, temp_celc_outside_high):
    clear_animation_area(display, BG)
    # Title
    display.set_pen(WHITE)
    display.text("Temperature (Outside)", 40, 50, 200, 3)
    # Current label
    display.set_pen(ORANGE)
    display.text(f"Current: ", 40, 105, 200, 2)
    # Current value
    display.set_pen(WHITE)
    display.text(fmt_degrees(temp_celc_outside_current), 132, 105, 200, 2)
    # Average label
    display.set_pen(ORANGE)
    display.text(f"Average: ", 40, 130, 200, 2)
    # Average value
    display.set_pen(WHITE)
    display.text(fmt_degrees(temp_celc_outside_average), 132, 130, 200, 2)
    # Low label
    display.set_pen(ORANGE)
    display.text(f"Low: ", 40, 155, 200, 2)
    # Low value
    display.set_pen(WHITE)
    display.text(fmt_degrees(temp_celc_outside_low), 90, 155, 200, 2)
    # High label
    display.set_pen(ORANGE)
    display.text(f"High: ", 40, 180, 200, 2)
    # High value
    display.set_pen(WHITE)
    display.text(fmt_degrees(temp_celc_outside_high), 90, 180, 200, 2)
    
    display.update()
    await asyncio.sleep(0.5)

async def screen_humidity(display, BG, WHITE, ORANGE, rh_current, rh_average, rh_low, rh_high):
    clear_animation_area(display, BG)
    # Title
    display.set_pen(WHITE)
    display.text("Humidity (Inside)", 40, 50, 200, 3)
    # Current label
    display.set_pen(ORANGE)
    display.text(f"Current: ", 40, 105, 200, 2)
    # Current value
    display.set_pen(WHITE)
    display.text(fmt_percent(rh_current), 132, 105, 200, 2)
    # Average label
    display.set_pen(ORANGE)
    display.text(f"Average: ", 40, 130, 200, 2)
    # Average value
    display.set_pen(WHITE)
    display.text(fmt_percent(rh_average), 132, 130, 200, 2)
    # Low label
    display.set_pen(ORANGE)
    display.text(f"Low: ", 40, 155, 200, 2)
    # Low value
    display.set_pen(WHITE)
    display.text(fmt_percent(rh_low), 90, 155, 200, 2)
    # High label
    display.set_pen(ORANGE)
    display.text(f"High: ", 40, 180, 200, 2)
    # High value
    display.set_pen(WHITE)
    display.text(fmt_percent(rh_high), 90, 180, 200, 2)
    
    display.update()
    await asyncio.sleep(0.5)


async def screen_actuations(display, BG, WHITE, ORANGE, fan_on, roof_open, heat_pad_on, error_count):
    clear_animation_area(display, BG)
    # Title
    display.set_pen(WHITE)
    display.text("Actuations and Errors", 40, 50, 200, 3)
    # Fan label
    display.set_pen(ORANGE)
    display.text(f"Fan: ", 40, 105, 200, 2)
    # Fan value
    display.set_pen(WHITE)
    display.text(f"{'on' if fan_on else 'off'}", 84, 105, 200, 2)
    # Roof label
    display.set_pen(ORANGE)
    display.text(f"Roof Opening: ", 40, 130, 200, 2)
    # Roof value
    display.set_pen(WHITE)
    display.text(fmt_percent(roof_open), 185, 130, 200, 2)
    # Heating label
    display.set_pen(ORANGE)
    display.text(f"Heating: ", 40, 155, 200, 2)
    # Heating value
    display.set_pen(WHITE)
    display.text(f"{'on' if heat_pad_on else 'off'}", 127, 155, 200, 2)
    # Error label
    display.set_pen(ORANGE)
    display.text(f"Errors: ", 40, 180, 200, 2)
    # Error value
    display.set_pen(WHITE)
    display.text(f"{error_count}", 117, 180, 200, 2)
    
    display.update() 
    await asyncio.sleep(0.5)


# TESTING

"""
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
    ORANGE = display.create_pen(255, 165, 0)
    
    screen_running = asyncio.Event()
    screen_running.set()
    
    await title(display, BG, GREEN)
    await screen_temperature_inside(display, BG, WHITE, ORANGE, 25, 24, 18, 28)

# Run the event loop
asyncio.run(main())
"""




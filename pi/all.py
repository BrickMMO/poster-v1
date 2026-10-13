#!/usr/bin/env python3
import time
from rpi_ws281x import PixelStrip, Color
from smbus2 import SMBus
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106, ssd1306
from luma.core.render import canvas
import brickpi3

# LED grid
GRID_COUNT = 256
GRID_PIN = 18
GRID_DMA = 10
GRID_CHANNEL = 0

# LED strip
STRIP_COUNT = 60  # Change if your strip has a different count
STRIP_PIN = 19
STRIP_DMA = 11
STRIP_CHANNEL = 1

# OLEDs and multiplexer
TCA_ADDRESS = 0x70
OLED_ADDRESS = 0x3C

# EV3 motor
MOTOR_PORT = brickpi3.BrickPi3.PORT_A


def test_leds(name, count, pin, dma, channel):
    print(f"\nTesting {name}...")
    leds = PixelStrip(
        count, pin, 800000, dma, False, 40, channel
    )
    leds.begin()

    try:
        for color in [
            Color(255, 0, 0),
            Color(0, 255, 0),
            Color(0, 0, 255),
        ]:
            for i in range(count):
                leds.setPixelColor(i, color)
            leds.show()
            time.sleep(1)

    finally:
        for i in range(count):
            leds.setPixelColor(i, Color(0, 0, 0))
        leds.show()

    print(f"{name}: PASS")


def select_oled_channel(channel):
    with SMBus(1) as bus:
        bus.write_byte(TCA_ADDRESS, 1 << channel)


def test_oled(name, channel, driver, width, height):
    print(f"\nTesting {name}...")
    select_oled_channel(channel)

    serial = i2c(port=1, address=OLED_ADDRESS)
    oled = driver(serial, width=width, height=height)

    try:
        with canvas(oled) as draw:
            draw.text((0, 0), name, fill="white")
            draw.text((0, 16), "Display working", fill="white")
            if height >= 64:
                draw.text((0, 32), "Hardware test", fill="white")
                draw.text((0, 48), time.strftime("%H:%M:%S"),
                          fill="white")
        time.sleep(3)
    finally:
        oled.clear()

    print(f"{name}: PASS")


def test_motor():
    print("\nTesting EV3 motor on Port A...")
    bp = brickpi3.BrickPi3()

    try:
        bp.set_motor_power(MOTOR_PORT, 30)
        time.sleep(2)
        bp.set_motor_power(MOTOR_PORT, 0)
    finally:
        bp.set_motor_power(MOTOR_PORT, 0)
        bp.reset_all()

    print("EV3 motor: PASS")


try:
    print("Starting hardware tests.")

    test_leds(
        "LED strip", STRIP_COUNT,
        STRIP_PIN, STRIP_DMA, STRIP_CHANNEL
    )

    test_leds(
        "LED grid", GRID_COUNT,
        GRID_PIN, GRID_DMA, GRID_CHANNEL
    )

    test_oled("Battery OLED", 0, sh1106, 128, 32)
    test_oled("Second OLED", 7, ssd1306, 128, 64)

    test_motor()

    print("\nAll hardware tests completed.")

except KeyboardInterrupt:
    print("\nTest interrupted.")

except Exception as error:
    print(f"\nTEST FAILED: {error}")
    raise

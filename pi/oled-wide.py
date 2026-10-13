#!/usr/bin/env python3

import time
from smbus2 import SMBus
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas

TCA_ADDRESS = 0x70
OLED_ADDRESS = 0x3C
CHANNEL = 0

# Select TCA9548A channel 0
bus = SMBus(1)
bus.write_byte(TCA_ADDRESS, 1 << CHANNEL)
bus.close()

serial = i2c(port=1, address=OLED_ADDRESS)
oled = sh1106(serial, width=128, height=32)

try:
    while True:
        with canvas(oled) as draw:
            draw.text((0, 0), "Battery OLED", fill="white")
            draw.text((0, 12), "Display working!", fill="white")
            draw.text((0, 24), time.strftime("%H:%M:%S"), fill="white")
        time.sleep(1)

except KeyboardInterrupt:
    oled.clear()
    print("OLED test stopped.")

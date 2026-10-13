#!/usr/bin/env python3
import time
from smbus2 import SMBus
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas

TCA_ADDRESS = 0x70
OLED_ADDRESS = 0x3C
CHANNEL = 7

bus = SMBus(1)
bus.write_byte(TCA_ADDRESS, 1 << CHANNEL)
bus.close()

serial = i2c(port=1, address=OLED_ADDRESS)
oled = ssd1306(serial, width=128, height=64)

try:
    while True:
        with canvas(oled) as draw:
            draw.text((0, 0), "Second OLED", fill="white")
            draw.text((0, 16), "SSD1306 128x64", fill="white")
            draw.text((0, 32), "Channel 7", fill="white")
            draw.text((0, 48), time.strftime("%H:%M:%S"), fill="white")
        time.sleep(1)
except KeyboardInterrupt:
    oled.clear()
    print("OLED test stopped.")

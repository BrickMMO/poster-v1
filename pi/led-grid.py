#!/usr/bin/env python3

import time
import random
from rpi_ws281x import PixelStrip, Color

LED_COUNT = 256
LED_PIN = 18
DMA = 10
CHANNEL = 0

grid = PixelStrip(
    LED_COUNT,
    LED_PIN,
    dma=DMA,
    channel=CHANNEL
)

grid.begin()

try:
    while True:
        for i in range(LED_COUNT):
            choice = random.choice([1, 2, 3])

            if choice == 1:
                grid.setPixelColor(i, Color(0, 5, 1))
            elif choice == 2:
                grid.setPixelColor(i, Color(5, 1, 5))
            else:
                grid.setPixelColor(i, Color(0, 1, 5))

        grid.show()
        print("LED grid updated")
        time.sleep(1)

except KeyboardInterrupt:
    print("Turning off grid...")

finally:
    for i in range(LED_COUNT):
        grid.setPixelColor(i, Color(0, 0, 0))

    grid.show()
    print("Done.")

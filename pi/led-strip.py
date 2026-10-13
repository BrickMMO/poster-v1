
#!/usr/bin/env python3
import time
from rpi_ws281x import PixelStrip, Color

LED_COUNT = 150  # Change to your strip's actual LED count
LED_PIN = 19    # GPIO10, physical pin 19
LED_FREQ_HZ = 800000
LED_DMA = 11
LED_BRIGHTNESS = 40
LED_INVERT = False
LED_CHANNEL = 1

strip = PixelStrip(
    LED_COUNT,
    LED_PIN,
    LED_FREQ_HZ,
    LED_DMA,
    LED_INVERT,
    LED_BRIGHTNESS,
    LED_CHANNEL
)

strip.begin()

try:
    while True:
        for color in [
            Color(10, 0, 0),
            Color(0, 10, 0),
            Color(0, 0, 10)
        ]:
            for i in range(strip.numPixels()):
                strip.setPixelColor(i, color)
            strip.show()
            time.sleep(1)

except KeyboardInterrupt:
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
    print("Strip test stopped.")

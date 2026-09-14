from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas
from PIL import Image, ImageDraw, ImageFont
import time
import random

device = sh1106(
    i2c(port=1, address=0x3C),
    width=128,
    height=32
)

font = ImageFont.load_default()

battery = 82

while True:

    # Randomly change battery level
    battery += random.choice([-2, -1, 1, 2])

    # Keep it between 10% and 99%
    battery = max(10, min(99, battery))

    with canvas(device) as draw:

        # -------------------------
        # Battery
        # -------------------------

        # Battery outline
        draw.rectangle(
            (1, 1, 85, 29),
            outline="white"
        )

        # Battery terminal
        draw.rectangle(
            (86, 10, 90, 21),
            fill="white"
        )

        # Filled portion
        fill_width = int(80 * battery / 100)

        if fill_width > 0:
            draw.rectangle(
                (4, 4, 4 + fill_width, 26),
                fill="white"
            )

        # -------------------------
        # Percentage
        # -------------------------

        text = f"{battery}%"

        text_image = Image.new("1", (32, 16), 0)
        text_draw = ImageDraw.Draw(text_image)

        text_draw.text(
            (1, 1),
            text,
            font=font,
            fill=1
        )

        # Scale percentage vertically
        text_image = text_image.resize(
            (32, 32),
            Image.Resampling.NEAREST
        )

        draw.bitmap(
            (94, 0),
            text_image,
            fill="white"
        )

    # Slowly change the battery level
    time.sleep(random.uniform(0.5, 0.8))
#!/usr/bin/env python3
"""
Firebase Real-time Control System for k107

Firebase variables:
    lights-1
    fans-1
    rooms-1
    display

Threads:
    Generic -> OLED Screen 0 battery animation
    Fans    -> OLED Screen 7 fan animation
    Rooms   -> 8 x 32 LED grid
"""

import firebase_admin
from firebase_admin import credentials, db

import time
import sys
import threading
import random
import smbus2
import math

from rpi_ws281x import PixelStrip, Color

from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.oled.device import ssd1306
from luma.core.render import canvas

from PIL import Image, ImageDraw, ImageFont


# --------------------------------------------------
# Firebase
# --------------------------------------------------

FIREBASE_PATH = 'k107'
SERVICE_ACCOUNT_KEY = 'serviceAccountKey.json'

state = {
    'lights-1': None,
    'fans-1': None,
    'rooms-1': None,
    'display': None
}


# --------------------------------------------------
# TCA9548A / I2C
# --------------------------------------------------

TCA_ADDRESS = 0x70
OLED_ADDRESS = 0x3C

i2c_lock = threading.Lock()


def select_tca_channel(channel):

    bus = smbus2.SMBus(1)

    bus.write_byte(
        TCA_ADDRESS,
        channel
    )

    bus.close()


# --------------------------------------------------
# Firebase Functions
# --------------------------------------------------

def initialize_firebase():

    try:

        firebase_admin.get_app()

    except ValueError:

        try:

            cred = credentials.Certificate(
                SERVICE_ACCOUNT_KEY
            )

            firebase_admin.initialize_app(
                cred,
                {
                    'databaseURL':
                    'https://brickmmoposter-default-rtdb.firebaseio.com'
                }
            )

            print(
                'Firebase initialized successfully'
            )

        except FileNotFoundError:

            print(
                f'Error: {SERVICE_ACCOUNT_KEY} not found'
            )

            sys.exit(1)

        except Exception as e:

            print(
                f'Firebase initialization error: {e}'
            )

            sys.exit(1)


def on_variable_change(variable_name):

    def callback(message):

        value = message.data

        state[variable_name] = value

        timestamp = time.strftime(
            '%Y-%m-%d %H:%M:%S'
        )

        print(
            f'[{timestamp}] '
            f'{variable_name} changed to: {value}'
        )

    return callback


def setup_listeners():

    variables = [
        'lights-1',
        'fans-1',
        'rooms-1',
        'display'
    ]

    for var_name in variables:

        ref = db.reference(
            f'{FIREBASE_PATH}/{var_name}'
        )

        initial_value = ref.get()

        state[var_name] = initial_value

        print(
            f'Initial {var_name}: '
            f'{initial_value}'
        )

        ref.listen(
            on_variable_change(var_name)
        )

        print(
            f'Listener set up for {var_name}'
        )


# --------------------------------------------------
# Generic Thread
# --------------------------------------------------

def generic():

    print(
        'Thread Started: Generic'
    )

    with i2c_lock:

        select_tca_channel(0x01)

        device = sh1106(
            i2c(
                port=1,
                address=OLED_ADDRESS
            ),
            width=128,
            height=32
        )

    font = ImageFont.load_default()

    battery = 82

    while True:

        with i2c_lock:

            select_tca_channel(0x01)

            battery += random.choice(
                [-2, -1, 1, 2]
            )

            battery = max(
                10,
                min(99, battery)
            )

            with canvas(device) as draw:

                draw.rectangle(
                    (1, 1, 85, 29),
                    outline="white"
                )

                draw.rectangle(
                    (86, 10, 90, 21),
                    fill="white"
                )

                fill_width = int(
                    80 * battery / 100
                )

                if fill_width > 0:

                    draw.rectangle(
                        (
                            4,
                            4,
                            4 + fill_width,
                            26
                        ),
                        fill="white"
                    )

                text = f'{battery}%'

                text_image = Image.new(
                    "1",
                    (32, 16),
                    0
                )

                text_draw = ImageDraw.Draw(
                    text_image
                )

                text_draw.text(
                    (1, 1),
                    text,
                    font=font,
                    fill=1
                )

                text_image = text_image.resize(
                    (32, 32),
                    Image.Resampling.NEAREST
                )

                draw.bitmap(
                    (94, 0),
                    text_image,
                    fill="white"
                )

        time.sleep(
            random.uniform(
                0.5,
                0.8
            )
        )


# --------------------------------------------------
# Fans Thread
# --------------------------------------------------

def fans():

    print(
        'Thread Started: Fans'
    )

    with i2c_lock:

        select_tca_channel(0x80)

        device = ssd1306(
            i2c(
                port=1,
                address=OLED_ADDRESS
            ),
            width=128,
            height=64
        )

    font = ImageFont.load_default()

    angle = 0

    left_percent = 20
    right_percent = 35

    left_direction = 1
    right_direction = -1

    while True:

        with i2c_lock:

            select_tca_channel(0x80)

            if state['fans-1']:

                left_percent += left_direction
                right_percent += right_direction

                if left_percent >= 40:
                    left_direction = -1

                if left_percent <= 20:
                    left_direction = 1

                if right_percent >= 40:
                    right_direction = -1

                if right_percent <= 20:
                    right_direction = 1

                with canvas(device) as draw:

                    draw.rectangle(
                        (0, 0, 63, 63),
                        outline="white"
                    )

                    draw.rectangle(
                        (64, 0, 127, 63),
                        outline="white"
                    )

                    fan_display = [
                        (32, 22, left_percent),
                        (96, 22, right_percent)
                    ]

                    for cx, cy, percent in fan_display:

                        draw.ellipse(
                            (
                                cx - 17,
                                cy - 17,
                                cx + 17,
                                cy + 17
                            ),
                            outline="white"
                        )

                        for i in range(4):

                            a = (
                                angle +
                                (i * math.pi / 2)
                            )

                            x1 = (
                                cx +
                                int(
                                    math.cos(a) * 3
                                )
                            )

                            y1 = (
                                cy +
                                int(
                                    math.sin(a) * 3
                                )
                            )

                            x2 = (
                                cx +
                                int(
                                    math.cos(a + 0.4) * 14
                                )
                            )

                            y2 = (
                                cy +
                                int(
                                    math.sin(a + 0.4) * 14
                                )
                            )

                            draw.line(
                                (
                                    x1,
                                    y1,
                                    x2,
                                    y2
                                ),
                                fill="white",
                                width=3
                            )

                        draw.ellipse(
                            (
                                cx - 3,
                                cy - 3,
                                cx + 3,
                                cy + 3
                            ),
                            fill="white"
                        )

                        text = f'{percent}%'

                        bbox = draw.textbbox(
                            (0, 0),
                            text,
                            font=font
                        )

                        text_width = (
                            bbox[2] - bbox[0]
                        )

                        draw.text(
                            (
                                cx - text_width // 2,
                                47
                            ),
                            text,
                            font=font,
                            fill="white"
                        )

                angle += 0.3

                if angle >= math.pi * 2:
                    angle -= math.pi * 2

            else:

                left_percent = 0
                right_percent = 0

                with canvas(device) as draw:

                    draw.rectangle(
                        (0, 0, 63, 63),
                        outline="white"
                    )

                    draw.rectangle(
                        (64, 0, 127, 63),
                        outline="white"
                    )

                    fan_display = [
                        (32, 22, 0),
                        (96, 22, 0)
                    ]

                    for cx, cy, percent in fan_display:

                        draw.ellipse(
                            (
                                cx - 17,
                                cy - 17,
                                cx + 17,
                                cy + 17
                            ),
                            outline="white"
                        )

                        for i in range(4):

                            a = i * math.pi / 2

                            x1 = (
                                cx +
                                int(math.cos(a) * 3)
                            )

                            y1 = (
                                cy +
                                int(math.sin(a) * 3)
                            )

                            x2 = (
                                cx +
                                int(math.cos(a + 0.4) * 14)
                            )

                            y2 = (
                                cy +
                                int(math.sin(a + 0.4) * 14)
                            )

                            draw.line(
                                (
                                    x1,
                                    y1,
                                    x2,
                                    y2
                                ),
                                fill="white",
                                width=3
                            )

                        draw.ellipse(
                            (
                                cx - 3,
                                cy - 3,
                                cx + 3,
                                cy + 3
                            ),
                            fill="white"
                        )

                        text = f'{percent}%'

                        bbox = draw.textbbox(
                            (0, 0),
                            text,
                            font=font
                        )

                        text_width = (
                            bbox[2] - bbox[0]
                        )

                        draw.text(
                            (
                                cx - text_width // 2,
                                47
                            ),
                            text,
                            font=font,
                            fill="white"
                        )

        time.sleep(0.1)


# --------------------------------------------------
# Rooms Thread
# --------------------------------------------------

def rooms():

    print(
        'Thread Started: Rooms'
    )

    LED_COUNT = 256
    LED_PIN = 18

    grid = PixelStrip(
        LED_COUNT,
        LED_PIN,
        dma=10,
        channel=0
    )

    grid.begin()

    while True:

        if state['rooms-1']:

            for i in range(LED_COUNT):

                # random choose 1, 2, 3
                choice = random.choice([1, 2, 3])
                if choice == 1:
                    grid.setPixelColor(
                        i,
                        Color(0, 5, 1)
                    )
                elif choice == 2:
                    grid.setPixelColor(
                        i,
                        Color(5, 1, 5)
                    )
                else:
                    grid.setPixelColor(
                        i,
                        Color(0, 1, 5)
                    )

            grid.show()

            time.sleep(1)

        else:

            # Turn entire grid off
            for i in range(LED_COUNT):

                grid.setPixelColor(
                    i,
                    Color(0, 0, 0)
                )

            grid.show()

        time.sleep(0.1)

def lights():

    print('Lights test started')

    LED_COUNT = 150
    LED_PIN = 19

    strip = PixelStrip(
        LED_COUNT,
        LED_PIN,
        dma=11,
        channel=1
    )

    strip.begin()

    # Clear the strip first
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

    time.sleep(1)

    # Turn entire strip red
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(1, 0, 0))

    strip.show()

    while True:
        time.sleep(1)

# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    print('Firebase k107 Control System')
    print('=' * 50)

    initialize_firebase()

    setup_listeners()

    print(
        'All listeners active. '
        'Monitoring for changes...'
    )

    print('Press Ctrl+C to stop\n')

    # Generic
    generic_thread = threading.Thread(
        target=generic,
        daemon=True
    )

    generic_thread.start()

    print('Generic thread running.')

    # Fans
    fans_thread = threading.Thread(
        target=fans,
        daemon=True
    )

    fans_thread.start()

    print('Fans thread running.')

    # Rooms
    rooms_thread = threading.Thread(
        target=rooms,
        daemon=True
    )

    rooms_thread.start()

    print('Rooms thread running.')

    # Lights
    lights_thread = threading.Thread(
        target=lights,
        daemon=True
    )

    lights_thread.start()

    print('Lights thread running.')

    try:

        while True:

            time.sleep(1)

    except KeyboardInterrupt:

        print(
            'Shutting down...'
        )

        firebase_admin.delete_app(
            firebase_admin.get_app()
        )

        print(
            'Firebase connection closed'
        )

        sys.exit(0)


if __name__ == '__main__':

    main()

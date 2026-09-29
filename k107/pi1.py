#!/usr/bin/env python3
"""
Firebase Real-time Control System for k107

Firebase variables:
    lights-1
    fans-1
    room-1
    display

Threads:
    Generic -> OLED Screen 0 battery animation
    Fans    -> OLED Screen 7 fan animation
"""

import firebase_admin
from firebase_admin import credentials, db

import time
import sys
import threading
import random
import smbus2
import math
import brickpi3

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
    'room-1': None,
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

            print(
                'Please provide your Firebase service account key file'
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
        'room-1',
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

    # Create Screen 0
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

                # Battery level
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

                # Percentage
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
                    (
                        32,
                        32
                    ),
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

    # Initialize BrickPi3
    try:

        BP = brickpi3.BrickPi3()

        print(
            'BrickPi3 initialized for motors'
        )

    except Exception as e:

        print(
            f'Error initializing BrickPi3: {e}'
        )

        BP = None

    # Create Screen 7
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

            # ------------------------------------------
            # FANS ON
            # ------------------------------------------

            if state['fans-1']:

                # Control motors at 50% speed
                if BP is not None:

                    BP.set_motor_power(
                        BP.PORT_B,
                        25
                    )

                    BP.set_motor_power(
                        BP.PORT_C,
                        25
                    )

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

                    # Left box
                    draw.rectangle(
                        (0, 0, 63, 63),
                        outline="white"
                    )

                    # Right box
                    draw.rectangle(
                        (64, 0, 127, 63),
                        outline="white"
                    )

                    fan_display = [
                        (
                            32,
                            22,
                            left_percent
                        ),
                        (
                            96,
                            22,
                            right_percent
                        )
                    ]

                    for cx, cy, percent in fan_display:

                        # Fan housing
                        draw.ellipse(
                            (
                                cx - 17,
                                cy - 17,
                                cx + 17,
                                cy + 17
                            ),
                            outline="white"
                        )

                        # Fan blades
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
                                    math.cos(
                                        a + 0.4
                                    ) * 14
                                )
                            )

                            y2 = (
                                cy +
                                int(
                                    math.sin(
                                        a + 0.4
                                    ) * 14
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

                        # Fan center
                        draw.ellipse(
                            (
                                cx - 3,
                                cy - 3,
                                cx + 3,
                                cy + 3
                            ),
                            fill="white"
                        )

                        # Center percentage under fan
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

                # Rotate fans
                angle += 0.3

                if angle >= math.pi * 2:

                    angle -= math.pi * 2

            # ------------------------------------------
            # FANS OFF
            # ------------------------------------------

            else:

                # Stop motors
                if BP is not None:

                    BP.set_motor_power(
                        BP.PORT_B,
                        0
                    )

                    BP.set_motor_power(
                        BP.PORT_C,
                        0
                    )

                left_percent = 0
                right_percent = 0

                with canvas(device) as draw:

                    # Left box
                    draw.rectangle(
                        (0, 0, 63, 63),
                        outline="white"
                    )

                    # Right box
                    draw.rectangle(
                        (64, 0, 127, 63),
                        outline="white"
                    )

                    fan_display = [
                        (
                            32,
                            22,
                            0
                        ),
                        (
                            96,
                            22,
                            0
                        )
                    ]

                    for cx, cy, percent in fan_display:

                        # Fan housing
                        draw.ellipse(
                            (
                                cx - 17,
                                cy - 17,
                                cx + 17,
                                cy + 17
                            ),
                            outline="white"
                        )

                        # Stationary fan blades
                        for i in range(4):

                            a = (
                                i * math.pi / 2
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
                                    math.cos(
                                        a + 0.4
                                    ) * 14
                                )
                            )

                            y2 = (
                                cy +
                                int(
                                    math.sin(
                                        a + 0.4
                                    ) * 14
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

                        # Fan center
                        draw.ellipse(
                            (
                                cx - 3,
                                cy - 3,
                                cx + 3,
                                cy + 3
                            ),
                            fill="white"
                        )

                        # Center 0%
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
# Main
# --------------------------------------------------

def main():

    print(
        'Firebase k107 Control System'
    )

    print(
        '=' * 50
    )

    initialize_firebase()

    setup_listeners()

    print(
        'All listeners active. '
        'Monitoring for changes...'
    )

    print(
        'Press Ctrl+C to stop\n'
    )

    # Start Generic thread
    generic_thread = threading.Thread(
        target=generic,
        daemon=True
    )

    generic_thread.start()

    print(
        'Generic thread running.'
    )

    # Start Fans thread
    fans_thread = threading.Thread(
        target=fans,
        daemon=True
    )

    fans_thread.start()

    print(
        'Fans thread running.'
    )

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


# --------------------------------------------------
# Start Program
# --------------------------------------------------

if __name__ == '__main__':

    main()
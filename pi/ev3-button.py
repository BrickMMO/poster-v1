import brickpi3
import time

BP = brickpi3.BrickPi3()

print("Watching S1...")
print("Press and release the button.")

try:
    while True:
        value = BP.get_sensor(BP.PORT_1)

        print("S1:", value)

        time.sleep(0.2)

except KeyboardInterrupt:
    print("\nStopped.")

finally:
    BP.reset_all()
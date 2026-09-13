import brickpi3
import time

BP = brickpi3.BrickPi3()

BP.set_motor_power(BP.PORT_A, 50)

time.sleep(2)

BP.set_motor_power(BP.PORT_A, 0)

BP.reset_all()
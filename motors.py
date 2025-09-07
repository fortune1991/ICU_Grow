import time
from motor import Motor

def motor_1_forward(seconds):
    MOTOR1 = Motor((8, 9))
    MOTOR1.full_positive()
    time.sleep(seconds)
    MOTOR1.stop()

def motor_1_backward(seconds):
    MOTOR1 = Motor((8, 9))
    MOTOR1.full_negative()
    time.sleep(seconds)
    MOTOR1.stop()

def motor_2_forward(seconds):
    MOTOR2 = Motor((10, 11))
    MOTOR2.full_positive()
    time.sleep(seconds)
    MOTOR2.stop()

def motor_2_backward(seconds):
    MOTOR2 = Motor((10, 11))
    MOTOR2.full_negative()
    time.sleep(seconds)
    MOTOR2.stop()
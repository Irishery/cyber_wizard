import serial
from config import ARDUINO_PORT, SERVO_PIN


class HardwareControl:
    def __init__(self):
        self.ser = serial.Serial(ARDUINO_PORT, 9600)

    def move_servo(self, angle):
        command = f"{SERVO_PIN}:{angle}\n"
        self.ser.write(command.encode())

    def close(self):
        self.ser.close()

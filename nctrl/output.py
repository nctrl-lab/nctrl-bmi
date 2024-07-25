import glob
import time
import serial
import numpy as np

from nctrl.utils import tprint

class Laser:
    def __init__(self, port=None):
        if port is None:
            available_ports = glob.glob('/dev/ttyACM*')
            if available_ports:
                port = available_ports[0]
            else:
                raise ValueError("No suitable port found in /dev/ttyACM*")

        tprint(f'Setting output to Laser on port {port}')
        self.ser = serial.Serial(port=port, baudrate=2000000, timeout=0)
        self.ser.flushInput()
        self.ser.flushOutput()
        self.duration = 500

    def __call__(self, y):
        if isinstance(y, int) and y == 1:
            try:
                self.ser.write(b'a')
            except Exception as e:
                print(f"Error writing to serial port: {e}")
        elif isinstance(y, (list, np.ndarray)) and len(y) > 1:
            y_uint16 = np.packbits(y[0].astype(np.uint8)).view(np.uint16)
            self.ser.write(b'p' + y_uint16.tobytes())

    def __repr__(self):
        return f'Laser(port={self.ser.port}, duration={self.duration})'
    
    def on(self):
        self.ser.write(b'e')
        tprint('nctrl.output.Laser.on: Laser on')
        self.print_serial()
    
    def off(self):
        self.ser.write(b'E')
        tprint('nctrl.output.Laser.off: Laser off')
        self.print_serial()
    
    def set_duration(self, duration):
        self.duration = duration
        if not isinstance(duration, int) or duration < 0:
            raise ValueError("Duration (ms) must be a non-negative integer")
        self.ser.write(f'd{duration}'.encode())
        tprint(f'nctrl.output.Laser.set_duration: Setting duration to {duration} ms')
        self.print_serial()
    
    def print_serial(self):
        while True:
            output = self.ser.readline().decode().strip()
            if output:
                tprint(f'nctrl.output.Laser.from_serial: {output}')
                break
            time.sleep(0.1)  # Wait a bit before trying again

    def close(self):
        self.ser.close()
        tprint('nctrl.output.Laser.close: Laser closed')
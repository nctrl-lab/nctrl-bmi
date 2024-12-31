import serial
import glob
import time


class Teensy:
    def __init__(self):
        self.ser = None
        self.i_try = 0
        self.start_time = 0

        with self:
            self.start()
    
    def start(self):
        self.start_time = time.monotonic()
        self.i_try = 0
        self.open()
        for _ in range(3):
            try:
                self.run()
            except Exception as e:
                print(f"\nError: {e}")
                self.close()
                self.open()
    
    def run(self):
        while True:
            self.i_try += 1
            self.ser.write(b'1')
            elapsed = time.monotonic() - self.start_time
            status = f"\rTry {self.i_try} at {elapsed:.2f} s"
            print(status, end="", flush=True)
            time.sleep(0.5)

    def __exit__(self, *_):
        self.close()
        
    def open(self):
        start_time = time.monotonic()
        port = self.find_port()
        self.ser = serial.Serial(
            port=port,
            baudrate=2000000,
            timeout=0,
            write_timeout=0,
            inter_byte_timeout=0
        )
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        elapsed = time.monotonic() - start_time
        print(f"Opened Teensy on {port} in {elapsed:.2f}s")
    
    def close(self):
        if self.ser:
            try:
                port = self.ser.port
                self.ser.close()
                self.ser = None
                print(f"Closed Teensy on {port}")
            except Exception as e:
                print(f"Error closing Teensy: {e}")

    @staticmethod
    def find_port():
        ports = glob.glob('/dev/ttyACM*')
        if not ports:
            raise ValueError("No suitable port found in /dev/ttyACM*")
        return ports[0]


if __name__ == "__main__":
    teensy = Teensy()
    teensy.start()
    teensy.close()
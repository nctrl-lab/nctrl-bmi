import serial
import glob
import time


class Teensy:
    def __init__(self):
        self.ser = None
        with self:
            self.start()
    
    def start(self):
        i_try = 0
        start_time = time.monotonic()
        try:
            while True:
                i_try += 1
                self.ser.write(b'1')
                elapsed = time.monotonic() - start_time
                status = f"\rTry {i_try} at {elapsed:.2f}s"
                print(status, end="", flush=True)
                time.sleep(0.5)
        except Exception as e:
            print(f"\nError: {e}")

    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self, *_):
        self.close()
        
    def open(self):
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
        print(f"Opened Teensy on {port}")
    
    def close(self):
        if self.ser:
            port = self.ser.port
            self.ser.close()
            self.ser = None
            print(f"Closed Teensy on {port}")

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
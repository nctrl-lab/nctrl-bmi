import glob
import time
import serial
import logging
import numpy as np

logger = logging.getLogger(__name__)

class Laser:
    """
    A class to control a laser device via serial communication.

    This class provides methods to initialize, control, and manage a laser device
    connected through a serial port.

    Attributes:
        ser (serial.Serial): Serial connection to the laser device.
        duration (int): Duration of the laser pulse in milliseconds.

    Args:
        port (str, optional): The serial port to connect to. If None, it will
            attempt to find an available port automatically.
    """

    def __init__(self, port=None):
        """
        Initialize the Laser object.

        If no port is specified, it attempts to find an available port
        automatically from /dev/ttyACM*.

        Args:
            port (str, optional): The serial port to connect to.

        Raises:
            ValueError: If no suitable port is found when port is None.
        """
        if port is None:
            available_ports = glob.glob('/dev/ttyACM*')
            if not available_ports:
                raise ValueError("No suitable port found in /dev/ttyACM*")
            port = available_ports[0]

        logger.info(f'Setting output to Laser on port {port}')
        self.ser = serial.Serial(port=port, baudrate=2000000, timeout=0, write_timeout=0, inter_byte_timeout=0)
        self.ser.flushInput()
        self.ser.flushOutput()
        self.duration = 500

    def __call__(self, y):
        """
        Callable method to control the laser based on input.

        Args:
            y (int or array-like): Control signal for the laser.
                If y is 1, it triggers the laser.
                If y is an array-like object, it sends a more complex command.
        """
        if isinstance(y, int) and y == 1:
            if self.duration < 25:
                self._write_serial(b'1')
            else:
                self._write_serial(b'a')
        elif isinstance(y, (list, np.ndarray)) and len(y) > 1:
            y_uint16 = np.packbits(y[0].astype(np.uint8)).view(np.uint16)
            self._write_serial(b's' + y_uint16.tobytes())

    def __repr__(self):
        """
        Return a string representation of the Laser object.

        Returns:
            str: A string representation of the Laser object.
        """
        return f'Laser(port={self.ser.port}, duration={self.duration})'
    
    def on(self):
        """Turn the laser on."""
        self._write_serial(b'e')
        logger.info('Laser on')
        self._print_serial()
    
    def off(self):
        """Turn the laser off."""
        self._write_serial(b'E')
        logger.info('Laser off')
        self._print_serial()
    
    def set_duration(self, duration):
        """
        Set the duration of the laser pulse.

        Args:
            duration (int): Duration of the laser pulse in milliseconds.

        Raises:
            ValueError: If duration is not a non-negative integer.
        """
        if not isinstance(duration, int) or duration < 0:
            raise ValueError("Duration (ms) must be a non-negative integer")
        self.duration = duration
        self._write_serial(f'd{duration}'.encode())
        logger.info(f'Setting duration to {duration} ms')
        self._print_serial()
    
    def _print_serial(self):
        """
        Print the serial output from the laser device.

        This method reads from the serial port and prints any output received.
        """
        while True:
            output = self.ser.readline().decode().strip()
            if output:
                logger.info(output)
                break
            time.sleep(0.1)  # Wait a bit before trying again

    def _write_serial(self, data):
        """
        Write data to the serial port.

        Args:
            data (bytes): The data to be written to the serial port.
        """
        try:
            self.ser.write(data)
        except Exception as e:
            tprint(f"Error writing to serial port: {e}")

    def close(self):
        """Close the serial connection to the laser device."""
        self.ser.close()
        tprint('nctrl.output.Laser.close: Laser closed')
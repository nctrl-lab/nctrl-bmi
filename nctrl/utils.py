import logging
import numpy as np
import subprocess

from spiketag.utils.utils import EventEmitter

logger = logging.getLogger(__name__)

def kill_existing_processes():
    try:
        subprocess.run(["fuser", "-k", "/dev/xillybus_fet_clf_32"], check=True)
        logger.info("Successfully killed existing processes.")
    except subprocess.CalledProcessError:
        logger.warning("Failed to kill existing processes. Continuing anyway.")
    except FileNotFoundError:
        logger.warning("fuser command not found. Make sure it's installed.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")


class CircularBuffer:
    """
    A fast circular buffer implementation using numpy arrays.
    Optimized version that minimizes array operations and copies.

    Parameters
    ----------
    size : int or tuple
        Size of the buffer. If tuple, creates a 2D array of shape size.
        For 1D buffer, pass an integer size.

    Attributes
    ----------
    buffer : ndarray
        The underlying numpy array storing the data
    length : int
        Length of the first dimension of the buffer
    size : int or tuple
        Original size parameter used to create the buffer
    index : int
        Current position in the circular buffer

    Methods
    -------
    __call__()
        Returns the buffer contents in chronological order
    __getitem__(index)
        Access buffer elements relative to current position
    __setitem__(index, value) 
        Set buffer elements relative to current position
    roll(shift=-1)
        Rotate buffer position by shift steps
    step(shift=-1)
        Rotate buffer and zero the new positions
    """
    def __init__(self, size):
        self.buffer = np.zeros(size, dtype=np.int16)
        self.length = size[0] if isinstance(size, tuple) else size
        self.size = size
        self.index = 0
        
    def __call__(self):
        if self.index == self.length - 1:
            return self.buffer
        result = np.empty_like(self.buffer)
        np.concatenate((self.buffer[self.index+1:], self.buffer[:self.index+1]), out=result)
        return result

    def min(self):
        return np.min(self())

    def max(self):
        return np.max(self())

    def __getitem__(self, index):
        if isinstance(index, tuple):
            if isinstance(index[0], slice):
                start = 0 if index[0].start is None else index[0].start
                stop = self.length if index[0].stop is None else index[0].stop
                step = 1 if index[0].step is None else index[0].step
                idx = np.mod(np.arange(start, stop, step) + self.index + 1, self.length)
                return self.buffer[idx, index[1]]
            else:
                idx = (self.index + index[0] + 1) % self.length
                return self.buffer[idx, index[1]]
            
        return self.buffer[(self.index + index + 1) % self.length]

    def __setitem__(self, index, value):
        if isinstance(index, tuple):
            self.buffer[(self.index + index[0] + 1) % self.length, index[1]] = value
        else:
            self.buffer[(self.index + index + 1) % self.length] = value
    
    def __len__(self):
        return self.length
    
    def __repr__(self):
        return f"CircularBuffer(size={self.size})"

    def roll(self, shift=-1):
        self.index = (self.index - shift) % self.length
    
    def step(self, steps=1):
        """Rotate buffer by step positions and zero the new positions.
        
        Efficiently zeros out elements and updates buffer position in a single pass.
        Handles both positive and negative shifts with clear, vectorized operations.
        
        Parameters
        ----------
        steps : int, default 1
            Number of positions to rotate buffer. Positive steps move forward,
            negative steps move backward.
        """
        start_idx = self.index + (1 if steps > 0 else -1)
        end_idx = self.index + steps + (1 if steps > 0 else -1)
        step = 1 if steps > 0 else -1
        
        indices = np.unique(np.mod(np.arange(start_idx, end_idx, step), self.length))

        self.buffer[indices] = 0
        self.index = (self.index + steps) % self.length


class FastBinner(EventEmitter):
    """
    A fast binning implementation for neural spike data using circular buffers.
    
    This class efficiently bins neural spikes into time windows, supporting both
    single-unit and multi-unit configurations. It uses an optimized CircularBuffer
    implementation for minimal memory operations.

    Parameters
    ----------
    bin_size : float
        Size of each time bin in seconds
    n_id : int
        Number of neural units to track
    n_bin : int 
        Number of time bins to maintain in the buffer
    i_id : int, optional
        If specified, only track spikes from this unit ID
    sampling_rate : int, optional
        Recording sampling rate in Hz, defaults to 25000

    Attributes
    ----------
    count_vec : CircularBuffer
        Circular buffer storing spike counts, shape (n_bin, n_id) or (n_bin,)
    time_to_bin : float
        Conversion factor from timestamp to bin number
    last_bin : int
        Index of the last updated time bin
    """
    def __init__(self, bin_size, n_id, n_bin, id=None, sampling_rate=25000, exclude_first_unit=False):
        super().__init__()
        self.bin_size = bin_size
        self.N = n_id
        self.B = n_bin
        self.id = int(id) if id is not None else None
        buffer_size = (self.B, self.N) if self.id is None else self.B
        self.count_vec = CircularBuffer(size=buffer_size)
        self.time_to_bin = 1.0 / (self.bin_size * sampling_rate)
        self.last_bin = 0
        self.exclude_first_unit = exclude_first_unit
    
    def input(self, bmi_output, type='individual_spike'):
        """
        Process an input spike and update the appropriate bin count.

        Parameters
        ----------
        bmi_output : object
            Object containing spike timestamp and unit ID information
        """
        current_bin = int(bmi_output.timestamp * self.time_to_bin)
        spk_id = int(bmi_output.spk_id)
        
        if current_bin != self.last_bin:
            self.emit('decode', X=self.output)
            self.count_vec.step(steps=current_bin - self.last_bin)
            self.last_bin = current_bin

        if self.id is None:
            self.count_vec[-1, spk_id] += 1
        elif self.id == spk_id:
            self.count_vec[-1] += 1
    
    @property
    def output(self):
        """
        Get the current state of all bins.

        Returns
        -------
        ndarray
            Array of spike counts across all bins
        """
        if self.exclude_first_unit:
            return self.count_vec()[:, 1:]
        else:
            return self.count_vec()

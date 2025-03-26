import numpy as np
import logging
logger = logging.getLogger(__name__)
log_format = '%(asctime)s %(name)-15s %(levelname)-8s %(message)s'
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(console_handler)

from spiketag.analysis import Decoder

from .utils import CircularBuffer

class FrThreshold(Decoder):
    def __init__(self, t_window=0.001, unit_id=0, nspike=1e6):
        super().__init__(t_window)
        self.unit_id = unit_id
        self.nspike = nspike
        self.is_active = False
        self.active_count = 0

    def fit(self, unit_id=None, nspike=None):
        if unit_id is not None:
            logger.info(f'Setting unit_id to {unit_id}')
            self.unit_id = unit_id
        if nspike is not None:
            logger.info(f'Setting nspike to {nspike}')
            self.nspike = nspike

    def predict(self, X):
        # X is output from Binner
        # X.shape = B # B bins
        unit_spike_count = X.sum(axis=0)
        
        if unit_spike_count >= self.nspike:
            if not self.is_active:
                self.is_active = True
                self.active_count = 0
                return 1
            else:
                self.active_count += 1
                if self.active_count >= X.shape[0]:
                    self.active_count = 0
                    return 1
        else:
            self.is_active = False
            self.active_count = 0
        
        return 0

class DynamicFrThreshold(FrThreshold):
    def __init__(self, t_window=0.001, unit_id=0, nspike=1e6):
        super().__init__(t_window, unit_id, nspike)
        self.direction = 'up'
        self.target_fr = 100
        self.bin_size = 0.1
        self.B_bins_ = 10
        self.B2_bins = 100

    def fit(self, unit_id=None, target_fr=None, bin_size=None, B_bins=None, B2_bins=None, direction='up'):
        if unit_id is not None:
            self.unit_id = unit_id
        if target_fr is not None:
            self.target_fr = target_fr
        if bin_size is not None:
            self.bin_size = bin_size
        if B_bins is not None: # duration for laser execution
            self.B_bins_ = B_bins
        if B2_bins is not None: # duration for monitoring
            self.B2_bins = B2_bins
        if direction is not None:
            if direction == 'up' or direction == 'down':
                self.direction = direction
            else:
                raise ValueError(f"Invalid direction: {direction}. Must be 'up' or 'down'.")
        
        self.buffer = CircularBuffer(self.B2_bins)
        self.n_fire = int(self.target_fr * self.bin_size * self.B2_bins) # for example, 0.2 Hz * 0.1 s * 600 bins = 12 spikes
    
    def set_nspike(self):
        """
        Determine optimal spike threshold using binary search.
        
        Finds the minimum threshold that results in firing rate below target rate.
        Uses boolean operations and vectorized calculations for efficiency.
        
        Notes
        -----
        The algorithm:
        1. Binary searches through possible thresholds 
        2. For each threshold, finds contiguous blocks above threshold
        3. Calculates expected firing rate from block durations
        4. Sets threshold to maintain target firing rate (self.n_fire)
        """
        left, right = np.max([1, self.buffer.min()]), self.buffer.max() + 1
        
        while left < right:
            threshold = (left + right) // 2
            
            threshold_comp = self.buffer() >= threshold if self.direction == 'up' else self.buffer() <= threshold
            threshold_mask = np.concatenate(([0], threshold_comp, [0]))
            block_start = np.where(~threshold_mask[:-1] & threshold_mask[1:])[0]
            
            if len(block_start) == 0:
                if self.direction == 'up':
                    right = threshold
                else:
                    left = threshold + 1
                continue
                
            block_end = np.where(threshold_mask[:-1] & ~threshold_mask[1:])[0]
            fire_count = np.ceil((block_end - block_start) / self.B_bins_).sum()

            if self.direction == 'up':
                if fire_count >= self.n_fire:
                    left = threshold + 1
                else:
                    right = threshold
            else:
                if fire_count >= self.n_fire:
                    right = threshold
                else:
                    left = threshold + 1

        nspike = left - 1 if self.direction == 'up' else left
        if nspike != self.nspike:
            self.nspike = nspike
            logger.info(f'Setting nspike to {nspike}')

    def predict(self, X):
        unit_spike_count = X.sum()
        self.buffer[-1] = unit_spike_count
        
        if not self.buffer.ready:
            self.buffer.step()
            return 0
            
        self.set_nspike()
        self.buffer.step()

        # Determine if spike count meets threshold based on direction
        threshold_met = (unit_spike_count >= self.nspike if self.direction == 'up' 
                        else unit_spike_count <= self.nspike)

        if threshold_met:
            if not self.is_active:
                self.is_active = True
                self.active_count = 0
                return 1
            
            self.active_count += 1
            if self.active_count >= self.B_bins_:
                self.active_count = 0
                return 1
        else:
            self.is_active = False
            self.active_count = 0

        return 0


class Spikes(Decoder):
    def __init__(self, t_window=0.001, unit_ids=None):
        super().__init__(t_window)
        self.unit_ids = unit_ids if unit_ids is not None else []

    def fit(self, unit_ids):
        # output up to 16 channels
        self.unit_ids = unit_ids[:16] if len(unit_ids) > 16 else unit_ids
    
    def predict(self, X):
        return X[-1, self.unit_ids] > 0 if self.unit_ids else 0


class SingleSpike(Decoder):
    def __init__(self, t_window=0.001, unit_id=0):
        super().__init__(t_window)
        self.unit_id = unit_id

    def fit(self, unit_id=None):
        if unit_id is not None:
            logger.info(f'Setting unit_id to {unit_id}')
            self.unit_id = unit_id

    def predict(self, X):
        if X.spk_id == self.unit_id:
            return 1


class Print(Decoder):
    """
    A decoder that prints the input every 100 calls.

    This decoder is primarily used for debugging and monitoring purposes.
    It prints the input X every 100 calls to the predict method.
    """
    def __init__(self, t_window=0.001):
        super().__init__(t_window)
        self.count = 0

    def fit(self):
        pass

    def predict(self, X):
        if X.spk_id:
            self.count += 1
            if self.count % 100 == 0:
                timestamp_ms = X.timestamp / 25000
                logger.info(f"\033[1m\033[32m{timestamp_ms:.2f}ms:\033[0m \033[34mGroup {X.grp_id}\033[0m \033[35mSpike {X.spk_id}\033[0m", end='\r', flush=True)

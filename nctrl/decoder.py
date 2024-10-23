import logging
logger = logging.getLogger(__name__)

from spiketag.analysis import Decoder

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
        # X.shape = [B, N] # B bins, N units
        unit_spike_count = X[:, self.unit_id].sum()
        
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
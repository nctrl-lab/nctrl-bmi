from spiketag.analysis import Decoder
from nctrl.utils import tprint

class FrThreshold(Decoder):
    def __init__(self, t_window=0.1, unit_id=0, nspike=1e6):
        super(FrThreshold, self).__init__(t_window)
        self.unit_id = unit_id
        self.nspike = nspike
        self.is_active = False

    def fit(self, unit_id=None, nspike=None):
        if unit_id is not None:
            tprint(f'Setting unit_id to {unit_id}')
            self.unit_id = unit_id
        if nspike is not None:
            tprint(f'Setting nspike to {nspike}')
            self.nspike = nspike

    def predict(self, X):
        # X is output from Binner
        # X.shape = [B, N] # B bins, N units
        unit_spike_count = X[:, self.unit_id].sum()
        if self.is_active:
            if unit_spike_count < self.nspike:
                self.is_active = False
                return 0
            else:
                return 0
        else:
            if unit_spike_count >= self.nspike:
                self.is_active = True
                return 1
            else:
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
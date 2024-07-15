from spiketag.analysis import Decoder
from .unit import Unit

class FrThreshold(Decoder):
    def __init__(self, unit_id=0, thres=1e6):
        super(FrThreshold, self).__init__()
        self.unit_id = unit_id
        self.thres = thres

    def fit(self, unit_id=None, thres=None):
        if unit_id is not None:
            self.unit_id = unit_id
        if thres is not None:
            self.thres = thres

    def predict(self, X):
        # X is output from Binner
        # X.shape = [B, N] # B bins, N units
        return 1 if X[:, self.unit_id].sum() >= self.thres else 0
    

class Spikes(Decoder):
    def __init__(self, unit_ids=None):
        super().__init__()
        self.unit_ids = unit_ids if unit_ids is not None else []

    def fit(self, unit_ids):
        # output up to 16 channels
        self.unit_ids = unit_ids[:16] if len(unit_ids) > 16 else unit_ids
    
    def predict(self, X):
        return X[-1, self.unit_ids] > 0 if self.unit_ids else 0
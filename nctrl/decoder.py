from spiketag.analysis import Decoder
from .unit import Unit

class FrThreshold(Decoder):
    def __init__(self):
        super(FiringRate, self).__init__()

    def fit(self, unit_id=0, thres=1e6):
        self.unit_id = unit_id
        self.thres = thres

    def predict(self, X):
        # X is output from Binner
        # X.shape = [B, N] # B bins, N units

        if X[:, self.unit_id].sum() > self.thres:
            return 1
        else:
            return 0
    

class Spikes(Decoder):
    def __init__(self):
        super().__init__()
        self.idx = None
    
    def fit(self, unit_ids):
        # output up to 16 channels
        self.unit_ids = unit_ids[:16] if len(unit_ids) > 16 else unit_ids
    
    def predict(self, X):
        return X[-1, self.unit_ids] > 0


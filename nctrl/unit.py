import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class Unit():
    def __init__(self):
        pass

    def load(self, spike_file='./spktag/model.pd'):
        self.spike_file = spike_file
        df = pd.read_pickle(self.spike_file)

        n_unit = int(df['spike_id'].max())
        self.n_unit = n_unit
        self.spike_time = np.zeros(n_unit, dtype=object)
        self.spike_fr = np.zeros(n_unit)
        self.spike_group = np.zeros(n_unit, dtype=int)
        
        duration = (df['frame_id'].iloc[-1] - df['frame_id'].iloc[0]) / 25000

        for i_unit in range(n_unit):
            in_unit = df['spike_id'] == (i_unit + 1)
            if sum(in_unit) == 0:
                continue
            self.spike_group[i_unit] = df['group_id'][np.argwhere(in_unit.to_numpy())[0, 0]]
            self.spike_time[i_unit] = df['frame_id'][in_unit].to_numpy() / 25000
            self.spike_fr[i_unit] = sum(in_unit) / duration

    def plot(self):
        f = plt.figure()
        gs = gridspec.GridSpec(self.n_unit, 3, wspace = 0.3, hspace=0.3)
        # col1: fr, col2: autocorrelogram, col3: waveform


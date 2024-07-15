import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from spiketag.core import CCG

class Unit():
    def __init__(self, bin_size=0.1):
        self.bin_size = bin_size

    def load(self, spike_file='./spktag/model.pd'):
        self.spike_file = spike_file
        df = pd.read_pickle(self.spike_file)

        self.start_time = df['frame_id'].iloc[0] / 25000
        self.end_time = df['frame_id'].iloc[-1] / 25000
        self.duration = self.end_time - self.start_time
        self.time_bin = np.arange(self.start_time, self.end_time, self.bin_size)

        n_unit = int(df['spike_id'].max())
        self.n_unit = n_unit

        in_unit = df['spike_id'] > 0
        self.spk_time = df['frame_id'][in_unit].to_numpy().astype(int)
        self.spk_id = df['spike_id'][in_unit].to_numpy().astype(int) - 1
        self.ccg = CCG(self.spk_time, self.spk_id)

        self.spike_time = np.zeros(n_unit, dtype=object)
        self.spike_fr = np.zeros(n_unit)
        self.spike_group = np.zeros(n_unit, dtype=int)

        for i_unit in range(n_unit):
            in_unit = df['spike_id'] == (i_unit + 1)
            if np.any(in_unit):
                self.spike_group[i_unit] = df['group_id'][np.argwhere(in_unit.to_numpy())[0, 0]]
                self.spike_time[i_unit] = df['frame_id'][in_unit].to_numpy() / 25000
                self.spike_fr[i_unit] = np.sum(in_unit) / self.duration

    def plot(self):
        f = plt.figure()
        gs = gridspec.GridSpec(self.n_unit, 1, wspace = 0.3, hspace=0.3)
        # col1: fr, col2: autocorrelogram, col3: temporal pattern

        for i_unit in range(self.n_unit):
            gs_unit = gridspec.GridSpecFromSubplotSpec(2, 2, subplot_spec=gs[i_unit], wspace=0.1, hspace=0.1, height_ratios=[1, 1])
            ax1 = f.add_subplot(gs_unit[0, 0])
            ax2 = f.add_subplot(gs_unit[0, 1])
            ax3 = f.add_subplot(gs_unit[1, :])

            # firing rate plot
            spike_hist = np.histogram(self.spike_time[i_unit], self.time_bin)[0] / self.bin_size
            spike_conv = np.convolve(spike_hist, np.ones(10) / 10, 'valid')
            ax1.hist(spike_conv, bins=np.arange(0, max(spike_conv)+1), color='black')
            ax1.set_ylabel('Hz')
            ax1.set_xlim(0, max(spike_conv))

            mean_spike_conv = np.mean(spike_conv)
            median_spike_conv = np.median(spike_conv)
            percentile_80 = np.percentile(spike_conv, 80)
            percentile_90 = np.percentile(spike_conv, 90)
            ax1.axvline(median_spike_conv, color='g', linestyle='dashed', linewidth=1, label='Median')
            ax1.axvline(percentile_80, color='b', linestyle='dashed', linewidth=1, label='80th Percentile')
            ax1.axvline(percentile_90, color='y', linestyle='dashed', linewidth=1, label='90th Percentile')
            ax1.set_title(f'Unit {i_unit + 1} ({self.spike_fr[i_unit]:.2f} Hz)')

            # autocorrelogram
            ax2.bar(np.arange(-25, 25), self.ccg[i_unit, i_unit], color='black', width=1)
            ax2.set_xlim(-25, 25)
            if i_unit == 0:
                ax2.set_title('autocorrelogram')

            # temporal pattern
            time_bin_midpoints = (self.time_bin[:-1] + self.time_bin[1:]) / 2
            missing_points = len(self.time_bin) - len(spike_conv)
            start_pt = missing_points // 2
            end_pt = -start_pt+1 if missing_points % 2 == 0 else -start_pt
            middle_bins = time_bin_midpoints[start_pt:end_pt]
            ax3.plot(middle_bins, spike_conv, color='black')
            ax3.set_ylabel('Hz')
            ax3.set_xlim(self.time_bin[0], self.time_bin[-1])

            mean_spike_conv = np.mean(spike_conv)
            print(f'{"="*20} Unit: {i_unit + 1} {"="*20}')
            print(f'{"Mean:":<20} {mean_spike_conv:.2f} Hz')
            print(f'{"Median:":<20} {median_spike_conv:.2f} Hz')
            print(f'{"80th Percentile:":<20} {percentile_80:.2f} Hz')
            print(f'{"90th Percentile:":<20} {percentile_90:.2f} Hz')
            print(f'{"="*49}')

        plt.tight_layout()
        plt.show()

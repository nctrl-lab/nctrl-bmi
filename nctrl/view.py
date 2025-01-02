# GUIs for visualizing firing rate, and features.

import numpy as np
from scipy import signal
from spiketag.view import line_view
from spiketag.view.color_scheme import palette


class fr_view(line_view):
    def __init__(self, fs=25e3):
        super().__init__()

        self.unfreeze()

        self._fs = fs
        self._time_tick = 1
        self._spike_time = np.array([])

    def add_data(self, spk_time=None):
        self._spike_time = np.append(self._spike_time, spk_time)
        self._draw()
    
    def set_data(self, spk_times=None):
        self._spike_time = spk_times
        self._draw()
    
    def _convolve(self):
        times = self._spike_time / int(self._fs * self._time_tick)
        print(times)
        counts = np.bincount(times.astype(int)) * int(1/self._time_tick)
        kernel = signal.gaussian(20, std=5) # should be half gaussian
        kernel = kernel[10:]
        kernel /= kernel.sum()
        fr =  signal.convolve(counts, kernel, mode='same')
        return fr
    
    def _draw(self):
        poses = []
        colors = []

        rate = self._convolve()
        x = np.arange(1, rate.shape[0] + 1)
        y = rate
        color = np.hstack((palette[1], 1))
        pos = np.column_stack((x, y))
        poses.append(pos)
        colors.append(color)

        super().set_data(poses, colors)



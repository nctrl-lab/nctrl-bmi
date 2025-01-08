# GUIs for visualizing firing rate, and features.

import numpy as np
from scipy import signal
from vispy import scene

import matplotlib as mpl


class LineView(scene.SceneCanvas):
    def __init__(self):
        super().__init__(keys=None)
        self.unfreeze()
        
        # Initialize grid and view
        self.grid = self.central_widget.add_grid(margin=10)
        self.view = self.grid.add_view(row=0, col=1)
        self.view.camera = 'panzoom'
        
        # Initialize line collections
        self.lines = []
        self.line_colors = mpl.colormaps.get_cmap('Set3').colors
        
        self._setup_axes()
        self.freeze()

    def _setup_axes(self, axis_color=(0,1,1,0.8)):
        axis_props = {
            'text_color': axis_color,
            'axis_color': axis_color,
            'tick_color': axis_color
        }
        
        self.xaxis = scene.AxisWidget(orientation='bottom', **axis_props)
        self.yaxis = scene.AxisWidget(orientation='left', **axis_props)
        
        self.xaxis.stretch = (0.9, 0.1)
        self.yaxis.stretch = (0.1, 0.9)
        
        self.grid.add_widget(self.xaxis, row=1, col=1)
        self.grid.add_widget(self.yaxis, row=0, col=0)
        
        self.xaxis.link_view(self.view)
        self.yaxis.link_view(self.view)
    
    def set_data(self, positions):
        """Set line data and update view
        
        Parameters
        ----------
        positions : array-like
            List of position arrays for each line
        """
        self.clear()
        
        n_colors = len(self.line_colors)
        
        for i, pos in enumerate(positions):
            line = scene.visuals.Line(
                pos=pos,
                color=self.line_colors[i % n_colors],
                width=2
            )
            self.view.add(line)
            self.lines.append(line)
            
        self.view.camera.set_range()
    
    def clear(self):
        """Remove all lines from view"""
        for line in self.lines:
            line.parent = None
        self.lines.clear()

# class fr_view(line_view):
#     def __init__(self, fs=25e3):
#         super().__init__()

#         self.unfreeze()

#         self._fs = fs
#         self._time_tick = 1
#         self._spike_time = np.array([])

#     def add_data(self, spk_time=None):
#         self._spike_time = np.append(self._spike_time, spk_time)
#         self._draw()
    
#     def set_data(self, spk_times=None):
#         self._spike_time = spk_times
#         self._draw()
    
#     def _convolve(self):
#         times = self._spike_time / int(self._fs * self._time_tick)
#         print(times)
#         counts = np.bincount(times.astype(int)) * int(1/self._time_tick)
#         kernel = signal.gaussian(20, std=5) # should be half gaussian
#         kernel = kernel[10:]
#         kernel /= kernel.sum()
#         fr =  signal.convolve(counts, kernel, mode='same')
#         return fr
    
#     def _draw(self):
#         poses = []
#         colors = []

#         rate = self._convolve()
#         x = np.arange(1, rate.shape[0] + 1)
#         y = rate
#         color = np.hstack((palette[1], 1))
#         pos = np.column_stack((x, y))
#         poses.append(pos)
#         colors.append(color)

#         super().set_data(poses, colors)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    view = LineView()
    view.show()
    app.exec_()
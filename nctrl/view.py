from vispy import scene
import matplotlib as mpl
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5 import QtCore

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
        self.n_colors = len(self.line_colors)
        
        self._setup_axes()
        self.freeze()

    def _setup_axes(self, axis_color=(1, 1, 1, 0.8)):
        axis_props = {
            'text_color': axis_color,
            'axis_color': axis_color,
            'tick_color': axis_color
        }
        
        self.xaxis = scene.AxisWidget(orientation='bottom', **axis_props)
        self.yaxis = scene.AxisWidget(orientation='left', **axis_props)
        
        # Configure axes
        self.xaxis.stretch = (0.9, 0.1)
        self.yaxis.stretch = (0.1, 0.9)
        
        # Add to grid and link views
        self.grid.add_widget(self.xaxis, row=1, col=1)
        self.grid.add_widget(self.yaxis, row=0, col=0)
        self.xaxis.link_view(self.view)
        self.yaxis.link_view(self.view)
    
    def set_data(self, positions, colors=None, width=1):
        """Set line data and update view
        
        Parameters
        ----------
        positions : array-like
            List of position arrays for each line
        colors : array-like, optional
            List of colors for each line. If None, cycles through colors.
        """
        self.clear()
        
        for i, pos in enumerate(positions):
            line_color = colors[i] if colors else self.line_colors[i % self.n_colors]
            self.lines.append(
                scene.visuals.Line(pos=pos, color=line_color, width=width, parent=self.view.scene)
            )
            
        self.view.camera.set_range()

    def clear(self):
        """Remove all lines from view"""
        for line in self.lines:
            line.parent = None
        self.lines.clear()


class FrView(LineView):
    def __init__(self, bin_size=5.0):
        super().__init__()

        self.unfreeze()
        self.bin_size = bin_size
        self.freeze()

    def set_data(self, data):
        if data.ndim == 1:
            data = data.reshape(-1, 1)

        x = np.arange(data.shape[0]) * self.bin_size
        y = data / self.bin_size

        positions = [np.column_stack((x, y[:, i])) for i in range(y.shape[1])]
        super().set_data(positions)


class FrGUI(QWidget):

    def __init__(self):
        super().__init__()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)

        self.btn = QPushButton('Start')
        self.btn.setCheckable(True) 
        self.btn.toggled.connect(self.start)

        self.plot = FrView()

        layout_main = QVBoxLayout()
        layout_main.addWidget(self.btn)
        layout_main.addWidget(self.plot.native)
        self.setLayout(layout_main)

        self.data = None
        self.time = 0

    def set_data(self, pos):
        self.data = pos
    
    def update(self):
        self.plot.set_data(self.data[self.time:self.time+360])
        self.time += 1

    def start(self, state):
        if state:
            self.timer.start(1000)
        else:
            self.timer.stop()

if __name__ == '__main__':
    import numpy as np
    from PyQt5.QtWidgets import QApplication

    data = np.random.randn(100000)

    app = QApplication([])
    gui = FrGUI()
    gui.set_data(data)
    gui.show()
    app.exec_()
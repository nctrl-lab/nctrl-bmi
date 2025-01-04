import os
import sys

import matplotlib.pyplot as plt

from PyQt5.QtCore import Qt, QThread, QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../nctrl')))

from view import fr_view
from spiketag.base import CLU

class GUI(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.update_interval = 2000 # unit: ms
        
        self.fr = fr_view()
        self.start_btn = QPushButton('start')
        self.start_btn.setCheckable(True)
        self.start_btn.clicked.connect(self.start)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.start_btn)
        self.layout.addWidget(self.fr.native)
        self.setLayout(self.layout)

    def start(self):
        if self.start_btn.isChecked():
            print('start')
            self.timer.start(self.update_interval)
        else:
            print('stop')
            self.timer.stop()
    
    def update(self):
        self.fr.set_data(spk_times=gen_spikes())

def gen_spikes():
    import numpy as np
    iti = np.random.gamma(25000*5, 1/5, (100,))
    # print(iti)
    return np.cumsum(iti)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = GUI()
    gui.show()
    sys.exit(app.exec_())
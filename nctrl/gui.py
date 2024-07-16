import sys

from spiketag.view import raster_view
from spiketag.utils import Timer

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QApplication, QPushButton, QSplitter, QGridLayout, QVBoxLayout, QHBoxLayout, QFormLayout, QSpinBox, QDoubleSpinBox


class nctrl_gui(QWidget):

    def __init__(self, nctrl=None):
        super().__init__()

        if nctrl:
            self.nctrl = nctrl

            self.view_timer = QtCore.QTimer(self)
            self.view_timer.timeout.connect(self.view_update)
            self.update_interval = 60
            
        else:
            self.nctrl = None

        self.init_gui()

    def init_gui(self, t_window=5e-3, view_window=10):
        
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.darkGray)
        p.setColor(self.foregroundRole(), Qt.white)
        self.setPalette(p)

        # stream button: shows the current neural data
        self.stream_btn = QPushButton("Stream Off")
        self.stream_btn.setCheckable(True)
        self.stream_btn.toggled.connect(self.stream_toggle)

        # bmi button: reacts to the current neural data
        self.bmi_btn = QPushButton("BMI Off")
        self.bmi_btn.setCheckable(True)
        self.bmi_btn.toggled.connect(self.bmi_toggle)

        # decoder settings
        self.unit_btn = QSpinBox()
        self.unit_btn.setRange(1, 100)
        self.unit_btn.setValue(1)

        self.fr_btn = QDoubleSpinBox()
        self.fr_btn.setRange(1.0, 100.0)
        self.fr_btn.setValue(1.0)
        self.fr_btn.setSingleStep(0.1)

        layout_setting = QFormLayout()
        layout_setting.addRow("Unit", self.unit_btn)
        layout_setting.addRow("FR Threshold", self.fr_btn)

        layout_btn = QGridLayout()
        layout_btn.addWidget(self.stream_btn, 0, 0)
        layout_btn.addWidget(self.bmi_btn, 1, 0)
        layout_btn.addLayout(layout_setting, 2, 0)

        layout_left = QVBoxLayout()
        layout_left.addLayout(layout_btn)
        leftside = QWidget()
        leftside.setLayout(layout_left)

        # there will be a raster view
        if self.nctrl:
            self.raster_view = raster_view(n_units=self.nctrl.bmi.fpga.n_units+1, t_window=t_window, view_window=view_window)
        else:
            self.raster_view = raster_view(n_units=10, t_window=t_window, view_window=view_window)

        layout_right = QVBoxLayout()
        layout_right.addWidget(self.raster_view.native)
        rightside = QWidget()
        rightside.setLayout(layout_right)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(leftside)
        splitter.addWidget(rightside)

        layout_main = QHBoxLayout()
        layout_main.addWidget(splitter)
        self.setLayout(layout_main)
    
    def bmi_toggle(self, checked):
        if checked:
            if not self.stream_btn.isChecked():
                self.stream_btn.setChecked(True)
                self.stream_toggle(True)
            self.bmi_btn.setText('BMI On')
            self.bmi_btn.setStyleSheet("background-color: green")

            # set decoder
            unit_id = self.unit_btn.value()
            thres = self.fr_btn.value()
            self.nctrl.set_decoder(decoder='fr', unit_id=unit_id, thres=thres)

            self.nctrl.output.on()
        else:
            self.bmi_btn.setText('BMI Off')
            self.bmi_btn.setStyleSheet("background-color: white")

            self.nctrl.output.off()

    def stream_toggle(self, checked):
        if checked:
            self.stream_btn.setText('Stream On')
            self.stream_btn.setStyleSheet("background-color: green")
            self.nctrl.bmi.start(gui_queue=False)
            self.view_timer.start(self.update_interval)
        else:
            self.stream_btn.setText('Stream Off')
            self.stream_btn.setStyleSheet("background-color: white")
            self.nctrl.bmi.stop()
            self.view_timer.stop()

    def view_update(self):
        with Timer('update', verbose=False):
            if self.nctrl:
                self.raster_view.update_fromfile()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = nctrl_gui()
    gui.show()
    sys.exit(app.exec_())
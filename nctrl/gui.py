import sys

from spiketag.view import raster_view
from spiketag.utils import Timer

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QApplication, QPushButton, QSplitter, QGridLayout, QVBoxLayout, QHBoxLayout, QFormLayout, QSpinBox, QDoubleSpinBox, QRadioButton, QLabel, QComboBox


class nctrl_gui(QWidget):

    def __init__(self, nctrl=None):
        super().__init__()
        self.setWindowTitle('NCtrl')

        if nctrl:
            self.nctrl = nctrl

            self.view_timer = QtCore.QTimer(self)
            self.view_timer.timeout.connect(self.view_update)
            self.update_interval = 60
            
        else:
            self.nctrl = None
            self.view_timer = None

        self.bin_size = 0.00004
        self.init_gui()

    def init_gui(self, t_window=10e-3, view_window=1):
        
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

        self.bin_menu = QComboBox()
        self.bin_menu.addItem("0.0004") # 10 frames
        self.bin_menu.addItem("0.001") # 25 frames
        self.bin_menu.addItem("0.010") # 250 frames
        self.bin_menu.addItem("0.100") # 2500 frames
        self.bin_menu.currentIndexChanged.connect(self.bin_toggle)

        self.B_btn = QSpinBox()
        self.B_btn.setRange(1, 100)
        self.B_btn.setValue(10)
        self.B_btn.setSingleStep(1)
        self.B_btn.valueChanged.connect(self.update_fr)

        self.nspike_btn = QSpinBox()
        self.nspike_btn.setRange(1, 100)
        self.nspike_btn.setValue(1)
        self.nspike_btn.setSingleStep(1)
        self.nspike_btn.valueChanged.connect(self.update_fr)

        self.fr_btn = QDoubleSpinBox()
        self.fr_btn.setRange(0.0, 100.0)
        self.fr_btn.setValue(1.0)
        self.fr_btn.setSingleStep(0.1)
        self.fr_btn.setSuffix(" Hz")
        self.fr_btn.setEnabled(False)

        self.laser_duration_btn = QComboBox()
        self.laser_duration_btn.addItem("1")
        self.laser_duration_btn.addItem("5")
        self.laser_duration_btn.addItem("10")
        self.laser_duration_btn.addItem("100")
        self.laser_duration_btn.addItem("500")
        self.laser_duration_btn.currentIndexChanged.connect(self.laser_duration_toggle)
        self.laser_duration_btn.setCurrentIndex(1)  # Set default to "5"

        layout_setting = QFormLayout()
        layout_setting.addRow("Unit ID", self.unit_btn)
        layout_setting.addRow("Bin size (s)", self.bin_menu)
        layout_setting.addRow("Bin count", self.B_btn)
        layout_setting.addRow("Spike count", self.nspike_btn)
        layout_setting.addRow("Fr", self.fr_btn)
        layout_setting.addRow("Laser duration (ms)", self.laser_duration_btn)

        layout_btn = QGridLayout()
        layout_btn.addWidget(self.bmi_btn, 0, 0)
        layout_btn.addWidget(self.stream_btn, 1, 0)
        layout_btn.addLayout(layout_setting, 2, 0)

        self.bin_menu.setCurrentIndex(3)
        self.bin_menu.currentIndexChanged.emit(3)

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
        '''
        BMI: enable output
        '''
        if checked:
            # start bmi
            bin_size = self.bin_size
            B_bins = self.B_btn.value()
            unit_id = self.unit_btn.value()
            nspike = self.nspike_btn.value()

            if self.nctrl:
                self.nctrl.output.on()
                self.nctrl.bmi.set_binner(bin_size=bin_size, B_bins=B_bins)
                self.nctrl.set_decoder(decoder='fr', unit_id=unit_id, nspike=nspike)
                self.nctrl.bmi.start(gui_queue=False)

            self.bmi_btn.setText('BMI On')
            self.bmi_btn.setStyleSheet("background-color: green")
        else:
            if self.stream_btn.isChecked():
                self.stream_btn.setChecked(False)
                self.stream_toggle(False)

            self.bmi_btn.setText('BMI Off')
            self.bmi_btn.setStyleSheet("background-color: white")

            if self.nctrl:
                self.nctrl.output.off()
                self.nctrl.bmi.stop()

    def stream_toggle(self, checked):
        '''
        Stream: starts to collect neural data
        '''
        if checked:
            if not self.bmi_btn.isChecked():
                self.bmi_btn.setChecked(True)
                self.bmi_toggle(True)

            if self.view_timer:
                self.view_timer.start(self.update_interval)

            self.stream_btn.setText('Stream On')
            self.stream_btn.setStyleSheet("background-color: green")
        else:
            if self.view_timer:
                self.view_timer.stop()

            self.stream_btn.setText('Stream Off')
            self.stream_btn.setStyleSheet("background-color: white")

    def view_update(self):
        with Timer('update', verbose=False):
            if self.nctrl:
                self.raster_view.update_fromfile(filename=self.nctrl.bmi.fetfile, n_items=8, last_N=20000)

    def bin_toggle(self):
        '''
        Bin size: set the bin size
        '''
        self.bin_size = float(self.bin_menu.currentText())
        self.update_fr()

    def laser_duration_toggle(self):
        '''
        Laser duration: set the laser duration
        '''
        self.laser_duration = int(self.laser_duration_btn.currentText())
        if self.nctrl:
            self.nctrl.output.set_duration(self.laser_duration)
    
    def update_fr(self):
        self.fr_btn.setValue(self.nspike_btn.value() / self.bin_size / self.B_btn.value())

    def closeEvent(self, event):
        '''
        Handle actions when the window is closing
        '''
        if self.nctrl:
            if self.stream_btn.isChecked():
                self.stream_toggle(False)
            if self.bmi_btn.isChecked():
                self.bmi_toggle(False)
            self.nctrl.output.close()
            self.nctrl.bmi.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = nctrl_gui()
    gui.show()
    sys.exit(app.exec_())
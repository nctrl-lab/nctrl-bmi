import sys
import numpy as np
import logging

logger = logging.getLogger(__name__)
log_format = '%(asctime)s %(name)-15s %(levelname)-8s %(message)s'
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(console_handler)

try:
    from spiketag.view import raster_view
    from spiketag.utils import Timer
    SPIKETAG_AVAILABLE = True
except ImportError:
    SPIKETAG_AVAILABLE = False
    print("spiketag module not found. Some features will be disabled.")

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QPushButton,
    QSplitter,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QRadioButton,
    QLabel,
    QComboBox,
    QListWidget
)


class NCtrlGUI(QWidget):
    def __init__(self, nctrl=None):
        super().__init__()

        self.setWindowTitle('NCtrl')
        self.nctrl = nctrl
        self.view_timer = QtCore.QTimer(self) if nctrl else None
        if self.view_timer:
            self.view_timer.timeout.connect(self.view_update)
            self.update_interval = 500

        # Parameters
        self.decoder = None
        self.bin_size = 0.00004
        self.B_bins = 1
        self.nspike = 1

        self.init_gui()

    def init_gui(self, t_window=10e-3, view_window=1):
        if SPIKETAG_AVAILABLE:
            self.setup_raster_view(t_window, view_window)
        self.setup_ui()

    def setup_ui(self):
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.darkGray)
        p.setColor(self.foregroundRole(), Qt.white)
        self.setPalette(p)

        # start buttons
        self.bmi_btn = QPushButton("BMI Off")
        self.bmi_btn.setToolTip("Toggle Brain-Machine Interface")
        self.bmi_btn.setCheckable(True)
        self.bmi_btn.toggled.connect(self.bmi_toggle)
        self.bmi_btn.setMinimumSize(100, 50)

        self.stream_btn = QPushButton("Stream Off")
        self.stream_btn.setToolTip("Toggle streaming of neural data. This will also turn on BMI.")
        self.stream_btn.setCheckable(True)
        self.stream_btn.toggled.connect(self.stream_toggle)
        self.stream_btn.setMinimumSize(100, 50)

        self.layout_start = QHBoxLayout()
        self.layout_start.addWidget(self.bmi_btn)
        self.layout_start.addWidget(self.stream_btn)

        # decoder settings
        self.decoder_fr_btn = QRadioButton("FR")
        self.decoder_spikes_btn = QRadioButton("Spikes")
        self.decoder_single_btn = QRadioButton("Single Spike")
        self.decoder_print_btn = QRadioButton("Print")

        self.decoder_fr_btn.toggled.connect(self.decoder_changed)
        self.decoder_spikes_btn.toggled.connect(self.decoder_changed)
        self.decoder_single_btn.toggled.connect(self.decoder_changed)
        self.decoder_print_btn.toggled.connect(self.decoder_changed)
        
        self.layout_decoder = QHBoxLayout()
        self.layout_decoder.addWidget(self.decoder_fr_btn)
        self.layout_decoder.addWidget(self.decoder_single_btn)
        self.layout_decoder.addWidget(self.decoder_spikes_btn)
        self.layout_decoder.addWidget(self.decoder_print_btn)

        # decoder settings
        self.layout_setting = QFormLayout()
        self.layout_setting.setVerticalSpacing(5)
        self.decoder_fr_btn.click()

        # laser settings
        self.laser_duration_btn = QComboBox()
        self.laser_duration_btn.addItems(["1", "2", "5", "10", "20", "50", "100", "200", "500"])
        self.laser_duration_btn.currentIndexChanged.connect(self.laser_duration_toggle)
        self.laser_duration_btn.setCurrentIndex(6)

        self.laser_latency_btn = QComboBox()
        self.laser_latency_btn.addItems(["0", "10", "20", "50", "100", "200", "500"])
        self.laser_latency_btn.currentIndexChanged.connect(self.laser_latency_toggle)
        self.laser_latency_btn.setCurrentIndex(3)

        self.layout_laser = QFormLayout()
        self.layout_laser.addRow("Laser duration (ms)", self.laser_duration_btn)
        self.layout_laser.addRow("Laser latency (ms)", self.laser_latency_btn)

        # main layout
        layout_btn = QGridLayout()
        layout_btn.addLayout(self.layout_start, 0, 0)
        layout_btn.addLayout(self.layout_decoder, 1, 0)
        layout_btn.addLayout(self.layout_setting, 2, 0)
        layout_btn.addLayout(self.layout_laser, 3, 0)
        layout_btn.setVerticalSpacing(10)

        layout_left = QVBoxLayout()
        layout_left.addLayout(layout_btn)
        leftside = QWidget()
        leftside.setLayout(layout_left)
        
        layout_right = QVBoxLayout()
        if SPIKETAG_AVAILABLE:
            layout_right.addWidget(self.raster_view.native)
        else:
            layout_right.addWidget(QLabel("Raster view not available (spiketag module not found)"))
        rightside = QWidget()
        rightside.setLayout(layout_right)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(leftside)
        splitter.addWidget(rightside)

        layout_main = QHBoxLayout()
        layout_main.addWidget(splitter)
        self.setLayout(layout_main)

    def setup_raster_view(self, t_window, view_window):
        if SPIKETAG_AVAILABLE:
            n_units = self.nctrl.bmi.fpga.n_units + 1 if self.nctrl else 10
            self.raster_view = raster_view(n_units=n_units, t_window=t_window, view_window=view_window)

    def bmi_toggle(self, checked):
        if checked:
            if self.nctrl:
                self.nctrl.output.on()

                # Decoder settings
                if self.decoder == 'fr':
                    unit_id = int(self.unit_selector.selectedItems()[0].text())
                    self.nctrl.bmi.set_fr_binner()
                    self.nctrl.bmi.set_binner(bin_size=self.bin_size, B_bins=self.B_bins)
                    self.nctrl.set_decoder(decoder=self.decoder, unit_id=unit_id, nspike=self.nspike)
                    logger.info(f"Fr BMI: bin size {self.bin_size} s, Bin number {self.B_bins}")
                    logger.info(f"Unit ID: {unit_id}, threshold {self.nspike_btn.value()}")
                    logger.info(f"Laser duration: {self.laser_duration} ms")
                elif self.decoder == 'spikes':
                    self.nctrl.bmi.set_fr_binner()
                    self.nctrl.bmi.set_binner(bin_size=self.bin_size, B_bins=self.B_bins)
                    unit_ids = np.array([int(item.text()) for item in self.unit_selector.selectedItems()], dtype=int)
                    self.nctrl.set_decoder(decoder=self.decoder, unit_ids=unit_ids)
                elif self.decoder == 'single':
                    unit_id = int(self.unit_selector.selectedItems()[0].text())
                    self.nctrl.set_decoder(decoder=self.decoder, unit_id=unit_id)
                    logger.info(f"Single spike BMI: Unit ID {unit_id}")
                    logger.info(f"Laser duration: {self.laser_duration} ms")
                elif self.decoder == 'print':
                    self.nctrl.set_decoder(decoder=self.decoder)
                    logger.info('Printing BMI messages')
                
                logger.info('Starting BMI')
                self.nctrl.bmi.start(gui_queue=False)
            self.update_button_state(self.bmi_btn, 'BMI On', "green")

            for i in range(self.layout_setting.count()):
                item = self.layout_setting.itemAt(i).widget()
                if item:
                    item.setEnabled(False)

        else:
            if self.nctrl:
                self.nctrl.output.off()
                self.nctrl.bmi.stop()
            if self.stream_btn.isChecked():
                self.stream_btn.setChecked(False)
            logger.info('Stopping BMI')
            self.update_button_state(self.bmi_btn, 'BMI Off', "white")

            for i in range(self.layout_setting.count()):
                item = self.layout_setting.itemAt(i).widget()
                if item:
                    item.setEnabled(True)

    def stream_toggle(self, checked):
        if checked:
            if not self.bmi_btn.isChecked():
                self.bmi_btn.setChecked(True)
            if self.view_timer:
                self.view_timer.start(self.update_interval)
            self.update_button_state(self.stream_btn, 'Stream On', "green")
        else:
            if self.view_timer:
                self.view_timer.stop()
            self.update_button_state(self.stream_btn, 'Stream Off', "white")
    
    def update_button_state(self, button, text, color):
        button.setText(text)
        button.setStyleSheet(f"background-color: {color}")

    def view_update(self):
        if self.nctrl and SPIKETAG_AVAILABLE:
            self.raster_view.update_fromfile(filename=self.nctrl.bmi.fetfile, n_items=8, last_N=20000)
    
    def decoder_changed(self):
        if hasattr(self, 'layout_setting'):
            while self.layout_setting.rowCount() > 0:
                self.layout_setting.removeRow(0)
        else:
            self.layout_setting = QFormLayout()

        if self.decoder_fr_btn.isChecked():
            self.decoder = 'fr'
            self.set_fr_layout()
            logger.info('FR decoder selected')
        elif self.decoder_single_btn.isChecked():
            self.decoder = 'single'
            self.set_single_layout()
            logger.info('Single spike decoder selected')
        elif self.decoder_spikes_btn.isChecked():
            self.decoder = 'spikes'
            self.set_spikes_layout()
            logger.info('Spikes decoder selected')
        elif self.decoder_print_btn.isChecked():
            self.decoder = 'print'
            self.set_print_layout()
            logger.info('Print decoder selected')

        if hasattr(self, 'settings_widget'):
            self.settings_widget.setLayout(self.layout_setting)
    
    # FR decoder setting
    def set_fr_layout(self):
        n_unit = self.nctrl.n_units if self.nctrl else 10

        self.unit_selector = QListWidget()
        self.unit_selector.setSelectionMode(QListWidget.SingleSelection)
        for i in range(1, n_unit + 1):  # Up to 16 units
            self.unit_selector.addItem(f"{i}")
        self.unit_selector.setToolTip("Select a unit to generate spikes.")

        self.bin_menu = QComboBox()
        self.bin_menu.addItems(["0.0004", "0.001", "0.010", "0.100"])
        self.bin_menu.currentIndexChanged.connect(self.bin_toggle)

        self.B_btn = QSpinBox(minimum=1, maximum=100, value=10)
        self.nspike_btn = QSpinBox(minimum=1, maximum=100, value=1)

        self.fr_btn = QLabel("1.0 Hz")

        for spin in [self.B_btn, self.nspike_btn]:
            spin.valueChanged.connect(self.update_fr)
        
        # Set default values
        self.bin_menu.setCurrentIndex(3)
        self.B_btn.setValue(10)
        self.nspike_btn.setValue(1)

        self.layout_setting.addRow("Unit ID", self.unit_selector)
        self.layout_setting.addRow("Bin size (s)", self.bin_menu)
        self.layout_setting.addRow("Bin count", self.B_btn)
        self.layout_setting.addRow("Spike count", self.nspike_btn)
        self.layout_setting.addRow("Fr", self.fr_btn)

    def bin_toggle(self):
        self.bin_size = float(self.bin_menu.currentText())
        self.update_fr()

    def update_fr(self):
        self.nspike = self.nspike_btn.value()
        self.B_bins = self.B_btn.value()
        self.fr_btn.setText(f"{self.nspike / self.bin_size / self.B_bins:.2f} Hz")

    # Single spike decoder setting
    def set_single_layout(self):
        n_unit = self.nctrl.n_units if self.nctrl else 10
        self.unit_selector = QListWidget()
        self.unit_selector.setSelectionMode(QListWidget.SingleSelection)
        for i in range(1, n_unit + 1):  # Up to 16 units
            self.unit_selector.addItem(f"{i}")
        self.unit_selector.setToolTip("Select a unit to generate spikes.")
        self.layout_setting.addRow("Unit ID", self.unit_selector)

    # Spikes decoder setting
    def set_spikes_layout(self):
        n_unit = self.nctrl.n_units if self.nctrl else 10
        self.unit_selector = QListWidget()
        self.unit_selector.setSelectionMode(QListWidget.MultiSelection)
        for i in range(1, n_unit + 1):  # Up to 16 units
            self.unit_selector.addItem(f"{i}")
        self.unit_selector.setToolTip("Select units to generate spikes.")

        self.bin_size = 0.0004
        self.B_bins = 1
        self.nspike = 1

        self.layout_setting.addRow("Unit ID", self.unit_selector)

    # Print decoder setting
    def set_print_layout(self):
        info_label = QLabel("Print decoder doesn't require any settings.")
        self.layout_setting.addRow(info_label)

    # Laser duration setting
    def laser_duration_toggle(self):
        self.laser_duration = int(self.laser_duration_btn.currentText())
        logger.info(f"Laser duration: {self.laser_duration} ms")
        if self.nctrl:
            self.nctrl.output.set_duration(self.laser_duration)

    def laser_latency_toggle(self):
        self.laser_latency = int(self.laser_latency_btn.currentText())
        logger.info(f"Laser latency: {self.laser_latency} ms")
        if self.nctrl:
            self.nctrl.output.set_latency(self.laser_latency)
    
    def closeEvent(self, event):
        if self.nctrl:
            self.stream_btn.setChecked(False)
            self.bmi_btn.setChecked(False)
            self.nctrl.output.close()
            self.nctrl.bmi.close()
        event.accept()

if __name__ == "__main__":
    logger.info('Starting GUI')
    app = QApplication(sys.argv)
    gui = NCtrlGUI()
    gui.show()
    sys.exit(app.exec_())
    logger.info('Exiting GUI')
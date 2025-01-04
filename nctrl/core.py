import os
import sys
import numpy as np
import logging
from PyQt5.QtWidgets import QApplication

logger = logging.getLogger(__name__)

from spiketag.base import probe
from spiketag.realtime import BMI

from .decoder import *
from .output import Laser
from .gui import NCtrlGUI
from .utils import kill_existing_processes, FastBinner


class NCtrl:
    """
    Neural Control (NCtrl) class for managing BMI, decoders, and outputs.

    This class initializes and manages the components necessary for a Brain-Machine Interface (BMI) system,
    including probe file loading, BMI initialization, decoder setting, and output management.

    Attributes:
        prbfile (str): Path to the probe file.
        prb (spiketag.base.probe): Probe object.
        bmi (spiketag.realtime.BMI): BMI object.
        dec (Union[FrThreshold, Spikes]): Decoder object.
        output (Callable): Output function (e.g., Laser).
        gui (nctrl_gui): GUI object for the NCtrl system.

    Args:
        prbfile (str, optional): Path to the probe file. If None, attempts to find one.
        fetfile (str, optional): Path to the feature file. Defaults to './fet.bin'.
        output_type (str, optional): Type of output. Defaults to 'laser'.
        output_port (str, optional): Port for the output device.
    """
    def __init__(self, prbfile=None, fetfile='./fet.bin', output_type='laser', output_port=None):
        self.set_logger()
        self.set_probe(prbfile)
        self.set_output(output_type, output_port)
        self.set_bmi(fetfile)
    
    def set_logger(self):
        log_format = '%(asctime)s %(name)-15s %(levelname)-8s %(message)s'
        logging.basicConfig(filename='bmi.log',
                            filemode='w',
                            level=logging.INFO,
                            format=log_format,
                            force=True)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(console_handler)

    def set_probe(self, prbfile):
        def _find_probe_file(prbfile):
            """Find a suitable probe file."""
            if prbfile and os.path.isfile(prbfile):
                return prbfile

            directories = ['.', os.path.expanduser('~/Work/probe-files')]
            for directory in directories:
                prb_files = [f for f in os.listdir(directory) if f.endswith('.prb')]
                if prb_files:
                    return os.path.join(directory, prb_files[0])
            return None

        self.prbfile = _find_probe_file(prbfile)
        if not self.prbfile:
            raise FileNotFoundError('nctrl.NCtrl: No probe file found. Please provide a probe file.')

        logger.info(f'Loading probe file {self.prbfile}')
        self.prb = probe()
        self.prb.load(self.prbfile)

    def set_bmi(self, fetfile):
        logger.info('Loading BMI')
        for attempt in range(2):
            try:
                self.bmi = NCtrlBMI(prb=self.prb, fetfile=fetfile, output=self.output)
                self.n_units = self.bmi.fpga.n_units
                return
            except Exception as e:
                if attempt == 0:
                    logger.error(f"Error initializing BMI: {e}")
                    logger.error("Attempting to kill existing processes and retry...")
                    kill_existing_processes()
                else:
                    raise

    def set_decoder(self, decoder='fr', **kwargs):
        """
        Set the decoder for the BMI system.

        Args:
            decoder (str, optional): Type of decoder to use.
                'fr': FrThreshold
                'spikes': Spikes
                'singleSpike': SingleSpike
            **kwargs: Additional arguments to pass to the decoder's fit method.
        """
        decoder_map = {
            'fr': (FrThreshold, 'binner'),
            'single': (SingleSpike, 'spike'),
            'dynamic': (DynamicFrThreshold, 'binner'),
            'print': (Print, 'spike')
        }
        decoder_class, mode = decoder_map.get(decoder, (FrThreshold, 'binner'))

        self.dec = decoder_class()
        self.dec.fit(**kwargs)
        self.bmi.mode = mode
        self.bmi.output = self.output
        self.bmi.set_decoder(dec=self.dec)

        if mode == 'binner':
            @self.bmi.binner.connect
            def on_decode(X):
                y = self.dec.predict(X)
                self.output(y)
    
    def set_output(self, output_type='laser', output_port=None):
        """
        Set the output type for the BMI system.

        Args:
            output_type (str, optional): Type of output to use. Defaults to 'laser'.
            output_port (str, optional): Port for the output device.
        """
        if output_type == 'laser':
            self.output = Laser(output_port)

    def show(self):
        """Display the GUI for the NCtrl system."""
        app = QApplication(sys.argv)
        self.gui = NCtrlGUI(nctrl=self)
        self.gui.show()
        app.exec_()


class NCtrlBMI(BMI):
    def __init__(self, prb, fetfile, ttlport=None, mode='binner', output=None):
        super().__init__(prb, fetfile, ttlport)
        self.mode = mode
        self.output = output
        self.fr_binner = None

    def BMI_core_func(self, gui_queue, model=None):
        self.model = model
        while True:
            bmi_output = self.read_bmi()

            if self.mode == 'binner':
                self.binner.input(bmi_output)
                if self.fr_binner is not None:
                    self.fr_binner.input(bmi_output)
            elif self.mode == 'spike':
                y = self.dec.predict(bmi_output)
                self.output(y)
                
    def set_binner(self, bin_size, B_bins, id=None):
        N_units = self.fpga.n_units + 1 # The unit #0, no matter from which group, is always noise
        self.binner = FastBinner(bin_size, N_units, B_bins, id)
        logger.info(
            f'BMI binner: {B_bins} bins ' + 
            (f'{N_units} units, each bin is {bin_size} seconds' if id is None else f'for unit {id}')
        )
    
    def set_fr_binner(self, bin_size=5, B_bins=360, id=None):
        n_units = self.fpga.n_units + 1
        self.fr_binner = FastBinner(bin_size, n_units, B_bins, id)
        logger.info(
            f'BMI fr binner: {B_bins} bins ' + 
            (f'{n_units} units, each bin is {bin_size} seconds' if id is None else f'for unit {id}')
        )
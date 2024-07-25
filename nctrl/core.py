import os
import sys
import subprocess
from PyQt5.QtWidgets import QApplication

from spiketag.base import probe
from spiketag.realtime import BMI

from nctrl.decoder import FrThreshold, Spikes
from nctrl.output import Laser
from nctrl.gui import nctrl_gui
from nctrl.utils import tprint


class NCtrl():
    def __init__(self,
                 prbfile=None,
                 fetfile='./fet.bin',
                 output_type='laser',
                 output_port='/dev/ttyACM0',
                 ):

        self.prbfile = self.find_probe_file(prbfile)
        if self.prbfile:
            tprint(f'Loading probe file {self.prbfile}')
            self.prb = probe()
            self.prb.load(self.prbfile)
        else:
            raise FileNotFoundError('nctrl.NCtrl: No probe file found. Please provide a probe file.')

        # set input
        tprint(f'Loading BMI')

        try:
            self.bmi = BMI(prb=self.prb, fetfile=fetfile)
        except Exception as e:
            tprint(f"Error initializing BMI: {e}")
            tprint("Attempting to kill existing processes and retry...")
            try:
                subprocess.run(["fuser", "-k", "/dev/xillybus_fet_clf_32"], check=True)
                tprint("Successfully killed existing processes.")
            except subprocess.CalledProcessError:
                tprint("Failed to kill existing processes. Continuing anyway.")
            except FileNotFoundError:
                tprint("fuser command not found. Make sure it's installed.")
            self.bmi = BMI(prb=self.prb, fetfile=fetfile)

        # set output
        self.set_output(output_type, output_port)
    
    def find_probe_file(self, prbfile):
        if prbfile and os.path.isfile(prbfile):
            return prbfile

        prb_files = [f for f in os.listdir('.') if f.endswith('.prb')]
        if prb_files:
            return prb_files[0]

        prb_folder = os.path.expanduser('~/Work/probe-files')
        prb_files = [f for f in os.listdir(prb_folder) if f.endswith('.prb')]
        if prb_files:
            return os.path.join(prb_folder, prb_files[0])
        return None

    def set_decoder(self, decoder='fr', **kwargs):
        if decoder == 'fr':
            self.dec = FrThreshold()
            self.dec.fit(**kwargs)
            self.bmi.set_decoder(dec=self.dec)
        elif decoder == 'spikes':
            self.dec = Spikes()
            self.dec.fit(**kwargs)
            self.bmi.set_decoder(dec=self.dec)
        
        self.bmi.binner._reset()
        
        # bmi.binner is an eventemitter that will run this function when a new bin is ready
        @self.bmi.binner.connect
        def on_decode(X):
            y = self.dec.predict(X)
            self.output(y)
    
    def set_output(self, output_type='laser', output_port=None):
        if output_type == 'laser':
            self.output = Laser(output_port)
    
    def show(self):
        app = QApplication(sys.argv)
        self.gui = nctrl_gui(nctrl=self)
        self.gui.show()
        app.exec_()
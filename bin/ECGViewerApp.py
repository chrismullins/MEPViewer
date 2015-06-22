#!/usr/bin/env python

import argparse
import os
import sys
import time

from PyQt4 import QtGui, QtCore
# Since posix symlinks are not supported on windows, let's
# explicitly update sys.path.
try:
    import ecgviewerqt as ecg
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
    import ecgviewerqt as ecg

#---------------------------------------------------------------------------
class ECGViewerParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


app = None
MainWindow = None
ui = None
#---------------------------------------------------------------------------
def fileLoadSequence():
    f = showDialog()
    r = ecg.SpikeReader.reader(str(f.name))
    ecgplot = ui.graphicsView.getPlotItem()
    ecg_signal = r.GetECGSignal()
    ecgplot.plot(ecg_signal, pen=(255,255,255,200))

#---------------------------------------------------------------------------
def showDialog():
        fname = QtGui.QFileDialog.getOpenFileName()
        f = open(fname, 'r')
        return f

#---------------------------------------------------------------------------
if __name__ == '__main__':

    parser = ECGViewerParser()

    parser.add_argument("--version", action="version",
        version="%(prog)s {}".format(ecg.__version__))

    parser.add_argument("-v", "--verbose", dest="verbose_count",
        action="count", default=0,
        help="increases log verbosity for each occurence.")

    # parser.add_argument("-i", "--inputFile", dest="filename",
    #      required=False, type=argparse.FileType('r'))

    parser.add_argument("-i", "--inputFile", dest="filename",
        required=False, type=argparse.FileType('r'))

    arguments = parser.parse_args(sys.argv[1:])

    # if arguments.verbose_count == 0:
    #     arguments.verbose_count = ecg.VERBOSE

    # ecg.StartUI(inputFile=arguments.filename,
    #          verbose=arguments.verbose_count)

    import sys
    app = ecg.gui.QtGui.QApplication(sys.argv)
    MainWindow = ecg.gui.QtGui.QMainWindow()
    ui = ecg.gui.Ui_MainWindow()
    ui.setupUi(MainWindow)
    ui.actionExit.triggered.connect(app.quit)
    ui.actionLoad.triggered.connect(fileLoadSequence)
    MainWindow.show()
    sys.exit(app.exec_())

    
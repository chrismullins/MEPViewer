#!/usr/bin/env python

import argparse
import os
import sys
import time
import pyqtgraph as pg

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



class MEPAppController(object):

    def __init__(self):
        self.app = None
        self.MainWindow = None
        self.ui = None
        self.signal_logic = None
        self.ecg_signal = None
        self.ecgplot = None
        self.currentFile = None
        self.startApp()

    #---------------------------------------------------------------------------
    def annotateSignal(self):
        #global signal_logic
        signal_trigger_minmax_dict = self.signal_logic.reportTriggersAndResponses()
        for trigger, minmaxlist in signal_trigger_minmax_dict.items():
            triggerItem = pg.ArrowItem(angle=90, tipAngle=30, baseAngle=-30, headLen=40, tailLen=None)
            triggerItem.setPos(trigger,0)
            self.ecgplot.addItem(triggerItem)
            minItem = pg.ArrowItem(angle=90, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush=None)
            minItem.setPos(minmaxlist[0][0],minmaxlist[0][1])
            self.ecgplot.addItem(minItem)
            maxItem = pg.ArrowItem(angle=-90, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush=None)
            maxItem.setPos(minmaxlist[1][0],minmaxlist[1][1])
            self.ecgplot.addItem(maxItem)


    #---------------------------------------------------------------------------
    def fileLoadSequence(self):
        self.currentFile = self.showDialog()
        r = ecg.SpikeReader.reader(str(self.currentFile.name))
        self.ecgplot = self.ui.graphicsView.getPlotItem()
        self.ecg_signal = r.GetECGSignal()
        #global signal_logic
        self.signal_logic = ecg.ECGLogic.ECGLogic(self.ecg_signal)
        self.ecgplot.plot(self.signal_logic.timesteps, self.ecg_signal, pen=(255,255,255,200))
        #annotateSignal()

    #---------------------------------------------------------------------------
    def showDialog(self):
            fname = QtGui.QFileDialog.getOpenFileName()
            f = open(fname, 'r')
            return f

    def startApp(self):
        self.app = ecg.gui.QtGui.QApplication(sys.argv)
        self.MainWindow = ecg.gui.QtGui.QMainWindow()
        self.ui = ecg.gui.Ui_MainWindow()
        self.ui.setupUi(self.MainWindow)
        self.ui.actionExit.triggered.connect(self.app.quit)
        self.ui.actionExit.setShortcut('Ctrl+X')
        self.ui.actionLoad.triggered.connect(self.fileLoadSequence)
        self.ui.actionLoad.setShortcut('Ctrl+O')
        self.ui.actionAnnotate_Min_Max.triggered.connect(self.annotateSignal)
        self.ui.actionAnnotate_Min_Max.setShortcut('Ctrl+A')
        self.ecgplot = self.ui.graphicsView.getPlotItem()
        self.ecgplot.showGrid(x=True, y=True, alpha=0.6)
        vb = self.ecgplot.getViewBox()
        vb.setMouseMode(pg.ViewBox.RectMode)
        self.MainWindow.showMaximized()
        pg.setConfigOption('leftButtonPan', False)
        sys.exit(self.app.exec_())

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

    mep_controller = MEPAppController()

    # if arguments.verbose_count == 0:
    #     arguments.verbose_count = ecg.VERBOSE

    # ecg.StartUI(inputFile=arguments.filename,
    #          verbose=arguments.verbose_count)

    # app = ecg.gui.QtGui.QApplication(sys.argv)
    # MainWindow = ecg.gui.QtGui.QMainWindow()
    # ui = ecg.gui.Ui_MainWindow()
    # ui.setupUi(MainWindow)
    # ui.actionExit.triggered.connect(app.quit)
    # ui.actionExit.setShortcut('Ctrl+X')
    # ui.actionLoad.triggered.connect(fileLoadSequence)
    # ui.actionLoad.setShortcut('Ctrl+O')
    # ui.actionAnnotate_Min_Max.triggered.connect(annotateSignal)
    # ui.actionAnnotate_Min_Max.setShortcut('Ctrl+A')
    # ecgplot = ui.graphicsView.getPlotItem()
    # ecgplot.showGrid(x=True, y=True, alpha=0.6)
    # vb = ecgplot.getViewBox()
    # vb.setMouseMode(pg.ViewBox.RectMode)
    # MainWindow.showMaximized()
    # pg.setConfigOption('leftButtonPan', False)
    # sys.exit(app.exec_())

    
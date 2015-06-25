#!/usr/bin/env python

import argparse
import os
import sys
import time
import pyqtgraph as pg
import numpy as np

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

#---------------------------------------------------------------------------
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

    def clearScene(self):
        self.ecgplot.clear()
        self.signal_logic = None
        self.ecg_signal = None
        self.currentFile = None

    def annotateSignal(self):
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

    def fileLoadSequence(self):
        self.currentFile = self.showDialog()
        r = ecg.SpikeReader.reader(str(self.currentFile.name))
        self.ecgplot = self.ui.graphicsView.getPlotItem()
        self.ecg_signal = r.GetECGSignal()
        self.signal_logic = ecg.ECGLogic.ECGLogic(self.ecg_signal)
        self.ecgplot.plot(self.signal_logic.timesteps, self.ecg_signal, pen=(255,255,255,200))

    def showDialog(self):
            fname = QtGui.QFileDialog.getOpenFileName()
            f = open(fname, 'r')
            return f

    def writeToCSV(self):
            outputPath = QtGui.QFileDialog.getSaveFileName( \
                directory=os.path.dirname(str(self.currentFile.name)), \
                caption="Save Response as CSV"
                )
            if outputPath:
                np.savetxt(str(outputPath), \
                    np.vstack([
                    np.hstack(arr.reshape(-1,1) for arr in \
                        [self.signal_logic.getTriggerTimePoints(), \
                         self.signal_logic.getTriggerMins(), \
                         self.signal_logic.getTriggerMaxs(), \
                         self.signal_logic.getTriggerMeans(), \
                         self.signal_logic.getTriggerP2Ps()]), \
                        np.array([0,0,0,0,self.signal_logic.getFinalAverage()])]), \
                    header="trigger,min,max,mean,peak2peak,finalAverage", delimiter=",", \
                    fmt="%.5e")

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
        self.ui.actionCSV.triggered.connect(self.writeToCSV)
        self.ui.actionCSV.setShortcut('Ctrl+S')
        self.ui.actionClear_Scene.triggered.connect(self.clearScene)
        self.ui.actionClear_Scene.setShortcut('Ctrl+W')
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

    parser.add_argument("-i", "--inputFile", dest="filename",
        required=False, type=argparse.FileType('r'))

    arguments = parser.parse_args(sys.argv[1:])

    mep_controller = MEPAppController()
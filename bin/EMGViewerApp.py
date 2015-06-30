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
    import emgviewerqt as emg
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
    import emgviewerqt as emg

#---------------------------------------------------------------------------
class EMGViewerParser(argparse.ArgumentParser):
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
        self.emg_signal = None
        self.emgplot = None
        self.currentFile = None
        self.annotated = False
        self.plotDataItem = None
        self.view = None
        self.vLine = None
        self.hLine = None
        self.originalMousePressEvent = None
        self.startApp()

    def clearScene(self):
        self.emgplot.clear()
        self.signal_logic = None
        self.emg_signal = None
        self.currentFile = None
        self.annotated = False

    def annotateSignal(self):
        if not self.annotated:
            signal_trigger_minmax_dict = self.signal_logic.reportTriggersAndResponses()
            for trigger, minmaxlist in signal_trigger_minmax_dict.items():
                triggerItem = pg.ArrowItem(angle=90, tipAngle=30, baseAngle=-30, headLen=40, tailLen=None)
                triggerItem.setPos(trigger,0)
                self.emgplot.addItem(triggerItem)
                minItem = pg.ArrowItem(angle=90, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush=None)
                minItem.setPos(minmaxlist[0][0],minmaxlist[0][1])
                self.emgplot.addItem(minItem)
                maxItem = pg.ArrowItem(angle=-90, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush=None)
                maxItem.setPos(minmaxlist[1][0],minmaxlist[1][1])
                self.emgplot.addItem(maxItem)
            self.annotated = True
        else:
            print("Already annotated! Load a new file.")
        return

    def fileLoadSequence(self):
        self.currentFile = self.showDialog()
        r = emg.SpikeReader.reader(str(self.currentFile.name))
        self.emgplot = self.ui.graphicsView.getPlotItem()
        self.emg_signal = r.GetEMGSignal()
        self.signal_logic = emg.EMGLogic.EMGLogic(self.emg_signal)
        self.plotDataItem = self.emgplot.plot(self.signal_logic.timesteps, self.emg_signal, pen=(255,255,255,200))
        # self.plotDataItem.sigClicked.connect(self.clicked)
        # self.plotDataItem.sigClicked.emit(self)
        return

    def addTrigger(self,ev):
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.emgplot.addItem(self.vLine, ignoreBounds=True)
        self.emgplot.addItem(self.hLine, ignoreBounds=True)
        self.MainWindow.mousePressEvent = self.plotClicked
        self.emgplot.scene().sigMouseMoved.connect(self.mouseMovedAddTrigger)

    def plotClicked(self,ev):
        view = self.emgplot.getViewBox()
        self.emgplot.removeItem(self.vLine)
        self.emgplot.removeItem(self.hLine)
        trigger_time, response_minmax = self.signal_logic.addTriggerTimepoint( \
            float(view.mapSceneToView(ev.pos()).x()))
        self.annotateMinMax(trigger_time, response_minmax)
        self.MainWindow.mousePressEvent = self.originalMousePressEvent
        self.emgplot.scene().sigMouseMoved.disconnect()
        return

    def annotateMinMax(self, trigger_time, minmaxlist):
        triggerItem = pg.ArrowItem(angle=90, tipAngle=30, baseAngle=-30, headLen=40, tailLen=None)
        triggerItem.setPos(trigger_time,0)
        self.emgplot.addItem(triggerItem)
        minItem = pg.ArrowItem(angle=90, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush=None)
        minItem.setPos(minmaxlist[0][0],minmaxlist[0][1])
        self.emgplot.addItem(minItem)
        maxItem = pg.ArrowItem(angle=-90, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush=None)
        maxItem.setPos(minmaxlist[1][0],minmaxlist[1][1])
        self.emgplot.addItem(maxItem)

    def mouseMovedAddTrigger(self, evt):
        #pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        pos = evt
        if self.emgplot.sceneBoundingRect().contains(pos):
            mousePoint = self.view.mapSceneToView(pos)
            index = int(mousePoint.x())
            #if index > 0 and index < len(data1):
            #   label.setText("<span style='font-size: 12pt'>x=%0.1f,   <span style='color: red'>y1=%0.1f</span>,   <span style='color: green'>y2=%0.1f</span>" % (mousePoint.x(), data1[index], data2[index]))
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

    def showDialog(self):
            fname = QtGui.QFileDialog.getOpenFileName()
            f = open(fname, 'r')
            return f

    def writeToCSV(self):
            outputPath = QtGui.QFileDialog.getSaveFileName( \
                directory=os.path.dirname(str(self.currentFile.name)), \
                caption="Save Response as CSV"
                )
            if self.annotated:
                if outputPath:
                    np.savetxt(str(outputPath), \
                        np.vstack([
                        np.hstack(arr.reshape(-1,1) for arr in \
                            [self.signal_logic.getTriggerTimePoints(), \
                             self.signal_logic.getTriggerMins(), \
                             self.signal_logic.getTriggerMaxs(), \
                             self.signal_logic.getTriggerMeans(), \
                             self.signal_logic.getTriggerP2Ps()]),
                              \
                            np.array([0,0,0,0,self.signal_logic.getFinalAverage()])]), \
                        header="trigger,min,max,mean,peak2peak,finalAverage", delimiter=",", \
                        fmt="%.5e")
            else:
                print("Annotate first, then save it out!")
            return

    def startApp(self):
        self.app = emg.gui.QtGui.QApplication(sys.argv)
        self.MainWindow = emg.gui.QtGui.QMainWindow()
        self.ui = emg.gui.Ui_MainWindow()
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
        self.ui.actionManually_Add_Trigger.triggered.connect(self.addTrigger)
        self.ui.actionManually_Add_Trigger.setShortcut('Ctrl++')
        self.emgplot = self.ui.graphicsView.getPlotItem()
        self.emgplot.showGrid(x=True, y=True, alpha=0.6)
        self.originalMousePressEvent = self.MainWindow.mousePressEvent
        vb = self.emgplot.getViewBox()
        vb.setMouseMode(pg.ViewBox.RectMode)
        self.view = self.emgplot.getViewBox()
        self.MainWindow.showMaximized()
        pg.setConfigOption('leftButtonPan', False)
        sys.exit(self.app.exec_())

#---------------------------------------------------------------------------
if __name__ == '__main__':

    parser = EMGViewerParser()

    parser.add_argument("--version", action="version",
        version="%(prog)s {}".format(emg.__version__))

    parser.add_argument("-v", "--verbose", dest="verbose_count",
        action="count", default=0,
        help="increases log verbosity for each occurence.")

    parser.add_argument("-i", "--inputFile", dest="filename",
        required=False, type=argparse.FileType('r'))

    arguments = parser.parse_args(sys.argv[1:])

    mep_controller = MEPAppController()
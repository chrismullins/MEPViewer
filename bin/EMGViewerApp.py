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
        # For addTrigger manually
        self.vLine = None
        self.hLine = None
        self.originalMousePressEvent = None

        # For tracking annotations
        self.triggerAnnotationList = []
        self.minAnnotationList = []
        self.maxAnnotationList = []

        self.startApp()

    def clearScene(self):
        self.emgplot.clear()
        self.signal_logic = None
        self.emg_signal = None
        self.currentFile = None
        self.annotated = False

    def autoAnnotateSignal(self):
        """ Detect and annotate the trigger points, min and max points on the plot.
        """
        if len(self.triggerAnnotationList) > 0:
            # Delete all of the annotations
            for item in self.triggerAnnotationList:
                self.emgplot.removeItem(item)
            for item in self.minAnnotationList:
                self.emgplot.removeItem(item)
            for item in self.maxAnnotationList:
                self.emgplot.removeItem(item)
            self.triggerAnnotationList = []
            self.minAnnotationList = []
            self.maxAnnotationLst = []
        if self.ui.comboBox.currentText() == "PAS":
            for trigger_time, minmaxtuple in self.signal_logic.trigger_dict.items():
                self.placeTriggerArrow(trigger_time)
                self.placeUpArrow(minmaxtuple.minTime, minmaxtuple.minValue)
                self.placeDownArrow(minmaxtuple.maxTime, minmaxtuple.maxValue)
        elif self.ui.comboBox.currentText() == "Cortical Silent Period":
            for trigger_time, csptuple in self.signal_logic.trigger_dict.items():
                self.placeTriggerArrow(trigger_time)
                self.placeUpArrow(csptuple.cspStartTime, csptuple.cspStartValue)
                self.placeDownArrow(csptuple.cspEndTime, csptuple.cspEndValue)
        self.annotated = True

    def placeTriggerArrow(self, trigger_time):
        """ Place a trigger arrow (solid, upward) point on the 
        x-axis at the specified area.
        """
        triggerItem = pg.ArrowItem(angle=90, tipAngle=30, baseAngle=-30, headLen=40, tailLen=None)
        triggerItem.setPos(trigger_time,0)
        self.triggerAnnotationList.append(triggerItem)
        self.emgplot.addItem(triggerItem)
        return

    def placeUpArrow(self, x_pos, y_pos):
        """ Place a single unfilled upward arrow on the plot.
        """
        minItem = pg.ArrowItem(angle=90, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush=None)
        minItem.setPos(x_pos, y_pos)
        self.minAnnotationList.append(minItem)
        self.emgplot.addItem(minItem)
        return

    def placeDownArrow(self, x_pos, y_pos):
        """ Place a single unfilled upward arrow on the plot.
        """
        maxItem = pg.ArrowItem(angle=-90, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush=None)
        maxItem.setPos(x_pos, y_pos)
        self.maxAnnotationList.append(maxItem)
        self.emgplot.addItem(maxItem)
        return

    def fileLoadSequence(self):
        """ Load a signal from a selected file, and show the plot.
        """
        self.currentFile = self.showDialog()
        r = emg.SpikeReader.reader(str(self.currentFile.name))
        self.emgplot = self.ui.graphicsView.getPlotItem()
        self.emg_signal = r.GetEMGSignal()
        if self.ui.comboBox.currentText() == "PAS":
            self.signal_logic = emg.EMGLogic.EMGLogic(emg_signal=self.emg_signal, \
                trigger_threshold=self.ui.pas_trigger_threshold_spinbox.value(), \
                window_begin=self.ui.pas_response_delay_spinbox.value(), \
                window_end=self.ui.pas_response_delay_spinbox.value() + self.ui.pas_response_window_spinbox.value())
        elif self.ui.comboBox.currentText() == "Cortical Silent Period":
            self.signal_logic = emg.CSPLogic.CSPLogic(self.emg_signal)
        self.plotDataItem = self.emgplot.plot(self.signal_logic.timesteps, self.emg_signal, pen=(255,255,255,200))
        self.ui.lineEdit.setText(self.currentFile.name)
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
        trigger_time = self.signal_logic.addTriggerTimepoint( \
            float(view.mapSceneToView(ev.pos()).x()))
        minmaxtuple = self.signal_logic.trigger_dict[trigger_time]
        self.annotateTriggerPoint(trigger_time)
        self.annotateMinPoint(minmaxtuple.minTime, minmaxtuple.minValue)
        self.annotateMaxPoint(minmaxtuple.maxTime, minmaxtuple.maxValue)

        self.MainWindow.mousePressEvent = self.originalMousePressEvent
        self.emgplot.scene().sigMouseMoved.disconnect()
        return

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

    def modeChanged(self):
        print self.ui.comboBox.currentText()

    def pasParametersChanged(self):
        """ Let the signal_logic update its internal dict of triggers/min and maxs
        each time we change a parameter.  This is fast so it doesn't really matter.
        Alternatively, we could put this step off until asked to plot it.
        """
        self.signal_logic.updateParameters(threshold=self.ui.pas_trigger_threshold_spinbox.value(), \
                begin=self.ui.pas_response_delay_spinbox.value(), \
                end=self.ui.pas_response_delay_spinbox.value() + self.ui.pas_response_window_spinbox.value())


    def writeToCSV(self):
        """ Write the data from this session to CSV.
        """
        outputPath = QtGui.QFileDialog.getSaveFileName( \
            directory=os.path.dirname(str(self.currentFile.name)), \
            caption="Save Response as CSV"
            )
        if self.annotated:
            self.signal_logic.writeInfoToCSV(str(outputPath))
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
        self.ui.actionAnnotate_Min_Max.triggered.connect(self.autoAnnotateSignal)
        self.ui.actionAnnotate_Min_Max.setShortcut('Ctrl+A')
        self.ui.actionCSV.triggered.connect(self.writeToCSV)
        self.ui.actionCSV.setShortcut('Ctrl+S')
        self.ui.actionClear_Scene.triggered.connect(self.clearScene)
        self.ui.actionClear_Scene.setShortcut('Ctrl+W')
        self.ui.actionManually_Add_Trigger.triggered.connect(self.addTrigger)
        self.ui.actionManually_Add_Trigger.setShortcut('Ctrl++')
        self.ui.comboBox.activated.connect(self.modeChanged)
        self.ui.pas_response_delay_spinbox.valueChanged.connect(self.pasParametersChanged)
        self.ui.pas_response_window_spinbox.valueChanged.connect(self.pasParametersChanged)
        self.ui.pas_trigger_threshold_spinbox.valueChanged.connect(self.pasParametersChanged)
        self.emgplot = self.ui.graphicsView.getPlotItem()
        self.emgplot.showGrid(x=True, y=True, alpha=0.6)
        self.ui.dockWidget.setMinimumWidth(220)
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
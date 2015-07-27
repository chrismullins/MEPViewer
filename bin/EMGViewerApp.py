#!/usr/bin/env python

import argparse
import os
import sys
import time
import pyqtgraph as pg
import numpy as np
import collections

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
        self.signal_logics = []
        self.emgSignalDict = dict()
        self.emgplot = None
        self.currentFiles = []
        self.currentFileDict = dict()
        self.additionalLineEdits = []
        self.annotated = False
        self.plotDataItems = []
        self.view = None
        # For addTrigger manually
        self.vLine = None
        self.hLine = None
        self.originalMousePressEvent = None

        # For tracking annotations
        self.triggerAnnotationList = []
        self.minAnnotationList = []
        self.maxAnnotationList = []
        self.regionAnnotationList = collections.deque()

        # Keep track of additional plots
        self.lower_plot = None
        self.signal_legend = None

        # Keep track of additional files
        self.FileWidgetTuple = collections.namedtuple('FileWidgetTuple', 'checkbox lineedit label color')
        self.fileWidgetTupleDict = dict()
        self.plotDataDict = dict()
        self.signalLogicDict = dict()
        self.colorOrder = [(255,255,255),(255,255,0), (255,0,255), (0, 255, 255)]

        # Keep track of additional widgets
        self.savedatadialogWidget = None

        self.startApp()

    def clearScene(self):
        self.emgplot.clear()
        self.signal_logics = []
        self.emg_signals = []
        self.emgSignalDict.clear()
        self.currentFiles = []
        self.currentFileDict.clear()
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
        if self.ui.comboBox.currentText() == "PAS" or self.ui.comboBox.currentText() == "Paired Pulse":
            trigger_times = []
            peak2peaks = []
            for fname, ftuple in self.fileWidgetTupleDict.iteritems():
                for trigger_time, minmaxtuple in self.signalLogicDict[fname].trigger_dict.items():
                    if ftuple.checkbox.isChecked():
                        self.placeTriggerArrow(trigger_time)
                        self.placeUpArrow(minmaxtuple.minTime, minmaxtuple.minValue)
                        trigger_times.append(trigger_time)
                        peak2peaks.append(minmaxtuple.peak2peak)
                        self.placeDownArrow(minmaxtuple.maxTime, minmaxtuple.maxValue)
                        if self.lower_plot:
                            self.lower_plot.plot(self.signalLogicDict[fname].getTriggerTimePoints(), \
                                self.signalLogicDict[fname].getTriggerP2Ps(), \
                                #pen=(200,200,200), symbolBrush=(255,0,0), symbolPen='w')
                                #pen=self.colorOrder[len(self.currentFiles)-1], symbolBrush=(255,0,0), symbolPen='w')
                                pen=self.fileWidgetTupleDict[fname].color, symbolBrush=(255,0,0), symbolPen='w')
        elif self.ui.comboBox.currentText() == "Cortical Silent Period":
            for fname, ftuple in self.fileWidgetTupleDict.iteritems():
                for trigger_time, csptuple in self.signalLogicDict[fname].trigger_dict.items():
                    if ftuple.checkbox.isChecked():
                        self.placeTriggerArrow(trigger_time)
                        self.placeUpArrow(csptuple.cspStartTime, csptuple.cspStartValue)
                        self.placeDownArrow(csptuple.cspEndTime, csptuple.cspEndValue)
                        if self.lower_plot:
                            self.lower_plot.plot(self.signalLogicDict[fname].getTriggerTimePoints(), \
                                self.signalLogicDict[fname].getCSPDurations(), \
                                pen=self.fileWidgetTupleDict[fname].color, symbolBrush=(255,0,0), symbolPen='w')
        elif self.ui.comboBox.currentText() == "Recruitment Curve":
            trigger_times = []
            peak2peaks = []
            for fname, ftuple in self.fileWidgetTupleDict.iteritems():
                if ftuple.checkbox.isChecked():
                    for trigger_time, minmaxtuple in self.signalLogicDict[fname].trigger_dict.items():
                        self.placeTriggerArrow(trigger_time)
                        self.placeUpArrow(minmaxtuple.minTime, minmaxtuple.minValue)
                        trigger_times.append(trigger_time)
                        peak2peaks.append(minmaxtuple.peak2peak)
                        self.placeDownArrow(minmaxtuple.maxTime, minmaxtuple.maxValue)
                    if self.lower_plot:
                        intensity_arr, means_arr, stddev_arr = self.signalLogicDict[fname].getMeanMEPReadings()
                        self.lower_plot.plot(intensity_arr, means_arr, \
                            pen=None, symbolBrush=(255,0,0), symbolPen='w')
                        err = pg.ErrorBarItem(x=intensity_arr, y=means_arr, top=stddev_arr, bottom=stddev_arr, beam=0.5)
                        self.lower_plot.addItem(err)
                        # plot sigmoid
                        sig_x, sig_y = self.signalLogicDict[fname].getSigmoidFit()
                        self.lower_plot.plot(sig_x,sig_y,pen=self.fileWidgetTupleDict[fname].color)
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
        minItem = pg.ArrowItem(angle=90, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush=(0,200,0), pen='w')
        minItem.setPos(x_pos, y_pos)
        self.minAnnotationList.append(minItem)
        self.emgplot.addItem(minItem)
        return

    def placeDownArrow(self, x_pos, y_pos):
        """ Place a single unfilled upward arrow on the plot.
        """
        maxItem = pg.ArrowItem(angle=-90, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush=(0,200,0), pen='w')
        maxItem.setPos(x_pos, y_pos)
        self.maxAnnotationList.append(maxItem)
        self.emgplot.addItem(maxItem)
        return

    def fileLoadSequence(self):
        """ Load a signal from a selected file, and show the plot.
        """
        recentFile = self.showDialog()
        self.currentFileDict[recentFile.name] = recentFile
        r = emg.SpikeReader.reader(str(recentFile.name))
        self.emgSignalDict[recentFile.name] = r.GetEMGSignal()
        self.createSignalLogic(filename=recentFile.name, emg_signal=self.emgSignalDict[recentFile.name])
        self.setSignalLogicMode()
        if len(self.currentFileDict) > 1:
            additionalLineEdit = self.addFileWidgets(fid=recentFile)
            self.additionalLineEdits.append(additionalLineEdit)
        else:
            self.ui.fileLineEdit1.setText(recentFile.name)
            widgetTuple = self.FileWidgetTuple(checkbox=self.ui.fileCheckbox1, lineedit=self.ui.fileLineEdit1, label=self.ui.fileLabel1, color=self.colorOrder[len(self.currentFileDict)-1])
            self.fileWidgetTupleDict[recentFile.name] = widgetTuple
        plotDataItem = self.emgplot.plot(self.signalLogicDict[recentFile.name].timesteps, self.emgSignalDict[recentFile.name], \
            #pen=(255,255,255,200), \
            pen=self.fileWidgetTupleDict[recentFile.name].color, \
            name=os.path.basename(str(recentFile.name)))
        self.plotDataDict[recentFile.name] = plotDataItem
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
        if len(self.currentFileDict) > 0:
            self.setSignalLogicMode()

    def setSignalLogicMode(self):
        self.setPASParameters(False)
        self.setCSPParameters(False)
        self.setRCParameters(False)
        for fname, signal_logic in self.signalLogicDict.iteritems():
            if self.ui.comboBox.currentText() == "PAS":
                self.signalLogicDict[fname] = emg.EMGLogic.EMGLogic(emg_signal=self.emgSignalDict[fname], \
                    trigger_threshold=self.ui.pas_trigger_threshold_spinbox.value(), \
                    window_begin=self.ui.pas_response_delay_spinbox.value(), \
                    window_end=self.ui.pas_response_delay_spinbox.value() + self.ui.pas_response_window_spinbox.value(), \
                    paired_pulse=False)
                self.setPASParameters(True)
            elif self.ui.comboBox.currentText() == "Paired Pulse":
                self.signalLogicDict[fname] = emg.EMGLogic.EMGLogic(emg_signal=self.emgSignalDict[fname], \
                    trigger_threshold=self.ui.pas_trigger_threshold_spinbox.value(), \
                    window_begin=self.ui.pas_response_delay_spinbox.value(), \
                    window_end=self.ui.pas_response_delay_spinbox.value() + self.ui.pas_response_window_spinbox.value(), \
                    paired_pulse=True)
                self.setPASParameters(True)
            elif self.ui.comboBox.currentText() == "Cortical Silent Period":
                self.signalLogicDict[fname] = emg.CSPLogic.CSPLogic(emg_signal=self.emgSignalDict[fname], \
                    trigger_threshold=self.ui.csp_trigger_threshold_spinbox.value(), \
                    window_begin=self.ui.csp_response_delay_spinbox.value(), \
                    window_end=self.ui.csp_response_delay_spinbox.value() + self.ui.csp_response_window_spinbox.value(), \
                    csp_threshold=self.ui.csp_csp_threshold_spinbox.value())
                self.setCSPParameters(True)
            elif self.ui.comboBox.currentText() == "Recruitment Curve":
                self.signalLogicDict[fname] = emg.RCLogic.RCLogic(emg_signal=self.emgSignalDict[fname], \
                    trigger_threshold=self.ui.rc_trigger_threshold_spinbox.value(), \
                    window_begin=self.ui.rc_response_delay_spinbox.value(), \
                    window_end=self.ui.rc_response_delay_spinbox.value() + self.ui.rc_response_window_spinbox.value(), \
                    fid=self.currentFileDict[fname])
                self.setRCParameters(True)
        return

    def createSignalLogic(self, filename, emg_signal):
        if self.ui.comboBox.currentText() == "PAS":
            self.signal_logics.append(emg.EMGLogic.EMGLogic(emg_signal=emg_signal, \
                trigger_threshold=self.ui.pas_trigger_threshold_spinbox.value(), \
                window_begin=self.ui.pas_response_delay_spinbox.value(), \
                window_end=self.ui.pas_response_delay_spinbox.value() + self.ui.pas_response_window_spinbox.value(), \
                paired_pulse=False))
        elif self.ui.comboBox.currentText() == "Paired Pulse":
            self.signal_logics.append(emg.EMGLogic.EMGLogic(emg_signal=emg_signal, \
                trigger_threshold=self.ui.pas_trigger_threshold_spinbox.value(), \
                window_begin=self.ui.pas_response_delay_spinbox.value(), \
                window_end=self.ui.pas_response_delay_spinbox.value() + self.ui.pas_response_window_spinbox.value(), \
                paired_pulse=True))
        elif self.ui.comboBox.currentText() == "Cortical Silent Period":
            self.signal_logics.append(emg.CSPLogic.CSPLogic(emg_signal=emg_signal, \
                trigger_threshold=self.ui.csp_trigger_threshold_spinbox.value(), \
                window_begin=self.ui.csp_response_delay_spinbox.value(), \
                window_end=self.ui.csp_response_delay_spinbox.value() + self.ui.csp_response_window_spinbox.value(), \
                csp_threshold=self.ui.csp_csp_threshold_spinbox.value()))
        elif self.ui.comboBox.currentText() == "Recruitment Curve":
            self.signal_logics.append(emg.RCLogic.RCLogic(emg_signal=emg_signal, \
                trigger_threshold=self.ui.rc_trigger_threshold_spinbox.value(), \
                window_begin=self.ui.rc_response_delay_spinbox.value(), \
                window_end=self.ui.rc_response_delay_spinbox.value() + self.ui.rc_response_window_spinbox.value(), \
                fid=self.currentFileDict[filename]))
        # Quick hack to just return the one we created. Fix this.
        self.signalLogicDict[filename] = self.signal_logics[-1]
        return self.signal_logics[-1]


    def setCSPParameters(self, enabled):
        self.ui.csp_show_csp_window_checkbox.setEnabled(enabled)
        self.ui.csp_csp_threshold_spinbox.setEnabled(enabled)
        self.ui.csp_trigger_threshold_spinbox.setEnabled(enabled)
        self.ui.csp_response_delay_spinbox.setEnabled(enabled)
        self.ui.csp_response_window_spinbox.setEnabled(enabled)
        self.ui.csp_duration_vs_time_checkbox.setEnabled(enabled)

    def setPASParameters(self, enabled):
        self.ui.pas_trigger_threshold_spinbox.setEnabled(enabled)
        self.ui.pas_response_delay_spinbox.setEnabled(enabled)
        self.ui.pas_response_window_spinbox.setEnabled(enabled)
        self.ui.pas_show_mep_amplitude_checkbox.setEnabled(enabled)

    def setRCParameters(self, enabled):
        self.ui.rc_trigger_threshold_spinbox.setEnabled(enabled)
        self.ui.rc_response_delay_spinbox.setEnabled(enabled)
        self.ui.rc_response_window_spinbox.setEnabled(enabled)
        self.ui.rc_show_rc_checkbox.setEnabled(enabled)


    def pasParametersChanged(self):
        """ Let the signal_logic update its internal dict of triggers/min and maxs
        each time we change a parameter.  This is fast so it doesn't really matter.
        Alternatively, we could put this step off until asked to plot it.
        """
        for i in range(len(self.signal_logics)):
            self.signal_logics[i].updateParameters(threshold=self.ui.pas_trigger_threshold_spinbox.value(), \
                   begin=self.ui.pas_response_delay_spinbox.value(), \
                    end=self.ui.pas_response_delay_spinbox.value() + self.ui.pas_response_window_spinbox.value())

    def cspParametersChanged(self):
        """ Let the signal_logic update its internal dict of triggers and csp durations
        each time we change a parameters.
        """
        for fname, signal_logic in self.signalLogicDict.iteritems():
            self.signalLogicDict[fname].updateParameters(trigger_threshold=self.ui.csp_trigger_threshold_spinbox.value(), \
                begin=self.ui.csp_response_delay_spinbox.value(), \
                end=self.ui.csp_response_delay_spinbox.value() + self.ui.csp_response_window_spinbox.value(), \
                csp_threshold=self.ui.csp_csp_threshold_spinbox.value())

    def rcParametersChanged(self):
        """ Let the signal_logic update its internal dict of triggers and associated parameters.
        """
        for fname, signal_logic in self.signalLogicDict.iteritems():
            self.signalLogicDict[fname].updateParameters(trigger_threshold =self.ui.rc_trigger_threshold_spinbox.value(), \
                begin=self.ui.rc_response_delay_spinbox.value(), \
                end=self.ui.rc_response_delay_spinbox.value() + self.ui.rc_response_window_spinbox.value(), \
                filename=self.currentFileDict[fname])


    def writeToCSV(self):
        """ Write the data from this session to CSV.
        """
        for fname, ftuple in self.fileWidgetTupleDict.iteritems():
            if ftuple.checkbox.isChecked():
                outputPath = QtGui.QFileDialog.getSaveFileName( \
             directory=os.path.dirname(str(fname)), \
             caption="Save {} as CSV".format(os.path.basename(str(fname))))
                self.signalLogicDict[fname].writeInfoToCSV(str(outputPath))

    def cspLowerPlotChanged(self):
        if self.ui.csp_duration_vs_time_checkbox.isChecked():
            self.ui.graphicsView.nextRow()
            self.lower_plot = self.ui.graphicsView.addPlot(title="CSP Duration vs Trigger Time")
            self.lower_plot.setLabel('left', "Silent Period Duration", units='s')
            self.lower_plot.setLabel('bottom', "Time", units='s')
        else:
            self.ui.graphicsView.removeItem(self.lower_plot)
            self.lower_plot = None

    def cspShowWindowChanged(self):
        pass
        # if self.ui.csp_show_csp_window_checkbox.isChecked():
        #     for trigger_time, csptuple in self.signal_logic.trigger_dict.items():
        #         lr = pg.LinearRegionItem([csptuple.windowBeginTime, csptuple.windowEndTime])
        #         lr.setZValue(-10)
        #         self.regionAnnotationList.append(lr)
        #         self.emgplot.addItem(lr)
        # else:
        #     while True:
        #         try:
        #             self.emgplot.removeItem(self.regionAnnotationList.pop())
        #         except IndexError:
        #             break

    def rcShowRCFitChanged(self):
        if self.ui.rc_show_rc_checkbox.isChecked():
            self.ui.graphicsView.nextRow()
            self.lower_plot = self.ui.graphicsView.addPlot(title="Recruitment Curve: Average MEP Amplitude vs Intensity")
            self.lower_plot.setLabel('left', "Average MEP Amplitude", units='mV')
            self.lower_plot.setLabel('bottom', "Trigger Intensity", units='\%\ of machine output')
        else:
            self.ui.graphicsView.removeItem(self.lower_plot)
            self.lower_plot = None

    def pasShowMEPAmpChanged(self):
        if self.ui.pas_show_mep_amplitude_checkbox.isChecked():
            self.ui.graphicsView.nextRow()
            self.lower_plot = self.ui.graphicsView.addPlot(title="MEP Amplitude vs Trigger Time")
            self.lower_plot.setLabel('left', "MEP Amplitude", units='mV')
            self.lower_plot.setLabel('bottom', "Time", units='s')
        else:
            self.ui.graphicsView.removeItem(self.lower_plot)
            self.lower_plot = None

    def addFileWidgets(self, fid):
        fileLineEdit = emg.gui.QtGui.QLineEdit(self.ui.dockWidgetContents)
        fileLineEdit.setReadOnly(True)
        # Called by add file dialog, so currentFiles is already updated
        fileLineEdit.setObjectName("fileLineEdit{}".format(len(self.currentFileDict)))
        fileLineEdit.setText(fid.name)
        self.ui.file_mode_layout.addWidget(fileLineEdit, len(self.currentFileDict)+1, 1, 1, 1)
        fileLabel = emg.gui.QtGui.QLabel(self.ui.dockWidgetContents)
        fileLabel.setObjectName("fileLabel{}".format(len(self.currentFileDict)))
        fileLabel.setText("File {}:".format(len(self.currentFileDict)))
        self.ui.file_mode_layout.addWidget(fileLabel, len(self.currentFileDict)+1, 0, 1, 1)
        fileCheckbox = emg.gui.QtGui.QCheckBox(self.ui.dockWidgetContents)
        fileCheckbox.setText("")
        fileCheckbox.setChecked(True)
        fileCheckbox.setObjectName("fileCheckbox{}".format(len(self.currentFileDict)))
        self.ui.file_mode_layout.addWidget(fileCheckbox,len(self.currentFileDict)+1, 2, 1, 1)
        fileCheckbox.stateChanged.connect(self.updatePlot)
        widgetTuple = self.FileWidgetTuple(checkbox=fileCheckbox, lineedit=fileLineEdit, label=fileLabel, \
            color=self.colorOrder[len(self.currentFileDict)-1])
        self.fileWidgetTupleDict[fid.name] = widgetTuple
        return

    def updatePlot(self):
        self.emgplot.clear()
        self.emgplot.legend.items = []
        for fname, ftuple in self.fileWidgetTupleDict.iteritems():
            if ftuple.checkbox.isChecked():
                self.plotDataDict[fname] = self.emgplot.plot(self.signalLogicDict[fname].timesteps, self.signalLogicDict[fname].emg_signal, \
                    #pen=(255,255,255,200), \
                    pen=self.fileWidgetTupleDict[fname].color, \
            name=os.path.basename(str(fname)))
            else:
                pass

    def startApp(self):
        self.app = emg.gui.QtGui.QApplication(sys.argv)
        self.MainWindow = emg.gui.QtGui.QMainWindow()
        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
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
        self.ui.pas_show_mep_amplitude_checkbox.stateChanged.connect(self.pasShowMEPAmpChanged)
        self.ui.csp_csp_threshold_spinbox.valueChanged.connect(self.cspParametersChanged)
        self.ui.csp_response_delay_spinbox.valueChanged.connect(self.cspParametersChanged)
        self.ui.csp_response_window_spinbox.valueChanged.connect(self.cspParametersChanged)
        self.ui.csp_trigger_threshold_spinbox.valueChanged.connect(self.cspParametersChanged)
        self.ui.csp_duration_vs_time_checkbox.stateChanged.connect(self.cspLowerPlotChanged)
        self.ui.csp_show_csp_window_checkbox.stateChanged.connect(self.cspShowWindowChanged)
        self.ui.rc_trigger_threshold_spinbox.valueChanged.connect(self.rcParametersChanged)
        self.ui.rc_response_delay_spinbox.valueChanged.connect(self.rcParametersChanged)
        self.ui.rc_response_window_spinbox.valueChanged.connect(self.rcParametersChanged)
        self.ui.rc_show_rc_checkbox.stateChanged.connect(self.rcShowRCFitChanged)
        self.ui.command_annotate_button.clicked.connect(self.autoAnnotateSignal)
        self.ui.fileCheckbox1.stateChanged.connect(self.updatePlot)
        self.setCSPParameters(False)
        self.setRCParameters(False)
        self.emgplot = self.ui.graphicsView.addPlot(title="EMG Signal")
        self.emgplot.showGrid(x=True, y=True, alpha=0.6)
        self.plotLegend = self.emgplot.addLegend()
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
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


app = None
MainWindow = None
ui = None
signal_logic = None
ecgplot = None

#---------------------------------------------------------------------------
def annotateSignal():
    #trigger_indices, trigger_coords = signal_logic.findTriggers()
    # text = pg.TextItem(html='<div style="text-align: center"><span style="color: #FFF;">This is the</span><br><span style="color: #FF0; font-size: 16pt;">PEAK</span></div>', anchor=(-0.3,1.3), border='w', fill=(0, 0, 255, 100))
    # ecgplot.addItem(text)
    # text.setPos(0, 5)
    #a1 = pg.ArrowItem(angle=-160, tipAngle=60, headLen=40, tailLen=40, tailWidth=20, pen={'color': 'w', 'width': 3})
    # a2 = pg.ArrowItem(angle=-120, tipAngle=30, baseAngle=20, headLen=40, tailLen=40, tailWidth=8, pen=None, brush='y')
    # Use a3 style for min and max?
    # a3 = pg.ArrowItem(angle=-60, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush=None)
    a4 = pg.ArrowItem(angle=90, tipAngle=30, baseAngle=-30, headLen=40, tailLen=None)
    # a2.setPos(10,0)
    # a3.setPos(20,0)
    a4.setPos(10,0)
    ecgplot.addItem(a4)
    # p.addItem(a2)
    # p.addItem(a3)
    # p.addItem(a4)
    # p.setRange(QtCore.QRectF(-20, -10, 60, 20))
    global signal_logic
    #global ecgplot
    signal_trigger_minmax_dict = signal_logic.reportTriggersAndResponses()
    for trigger, minmaxlist in signal_trigger_minmax_dict.items():
        triggerItem = pg.ArrowItem(angle=90, tipAngle=30, baseAngle=-30, headLen=40, tailLen=None)
        triggerItem.setPos(trigger,0)
        ecgplot.addItem(triggerItem)
        minItem = pg.ArrowItem(angle=90, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush=None)
        minItem.setPos(minmaxlist[0][0],minmaxlist[0][1])
        ecgplot.addItem(minItem)
        maxItem = pg.ArrowItem(angle=-90, tipAngle=30, baseAngle=20, headLen=40, tailLen=None, brush=None)
        maxItem.setPos(minmaxlist[1][0],minmaxlist[1][1])
        ecgplot.addItem(maxItem)


#---------------------------------------------------------------------------
def fileLoadSequence():
    f = showDialog()
    r = ecg.SpikeReader.reader(str(f.name))
    ecgplot = ui.graphicsView.getPlotItem()
    ecg_signal = r.GetECGSignal()
    #ecgplot.plot(ecg_signal, pen=(255,255,255,200))
    global signal_logic
    signal_logic = ecg.ECGLogic.ECGLogic(ecg_signal)
    ecgplot.plot(signal_logic.timesteps, ecg_signal, pen=(255,255,255,200))
    annotateSignal()

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
    ui.actionExit.setShortcut('Ctrl+X')
    ui.actionLoad.triggered.connect(fileLoadSequence)
    ui.actionLoad.setShortcut('Ctrl+O')
    #global ecgplot
    ecgplot = ui.graphicsView.getPlotItem()
    # show both x and y grids
    ecgplot.showGrid(x=True, y=True, alpha=0.6)
    # enable the zoom box thing
    vb = ecgplot.getViewBox()
    vb.setMouseMode(pg.ViewBox.RectMode)

    MainWindow.showMaximized()
    pg.setConfigOption('leftButtonPan', False)
    sys.exit(app.exec_())

    
# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\P\MEPApp\Qt\ECGViewerQt\Resources\EMGViewerGUI.ui'
#
# Created: Tue Jul 07 12:30:45 2015
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1062, 897)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.graphicsView = PlotWidget(self.centralwidget)
        self.graphicsView.setObjectName(_fromUtf8("graphicsView"))
        self.gridLayout.addWidget(self.graphicsView, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1062, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuSave = QtGui.QMenu(self.menuFile)
        self.menuSave.setObjectName(_fromUtf8("menuSave"))
        self.menuActions = QtGui.QMenu(self.menubar)
        self.menuActions.setObjectName(_fromUtf8("menuActions"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.dockWidget = QtGui.QDockWidget(MainWindow)
        self.dockWidget.setObjectName(_fromUtf8("dockWidget"))
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))
        self.gridLayout_3 = QtGui.QGridLayout(self.dockWidgetContents)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.gridLayout_2 = QtGui.QGridLayout()
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.label_2 = QtGui.QLabel(self.dockWidgetContents)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout_2.addWidget(self.label_2, 1, 0, 1, 1)
        self.label = QtGui.QLabel(self.dockWidgetContents)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)
        self.comboBox = QtGui.QComboBox(self.dockWidgetContents)
        self.comboBox.setObjectName(_fromUtf8("comboBox"))
        self.comboBox.addItem(_fromUtf8(""))
        self.comboBox.addItem(_fromUtf8(""))
        self.comboBox.addItem(_fromUtf8(""))
        self.gridLayout_2.addWidget(self.comboBox, 0, 1, 1, 1)
        self.lineEdit = QtGui.QLineEdit(self.dockWidgetContents)
        self.lineEdit.setReadOnly(True)
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.gridLayout_2.addWidget(self.lineEdit, 1, 1, 1, 1)
        self.gridLayout_3.addLayout(self.gridLayout_2, 0, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_3.addItem(spacerItem, 1, 0, 1, 1)
        self.dockWidget.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dockWidget)
        self.actionLoad = QtGui.QAction(MainWindow)
        self.actionLoad.setObjectName(_fromUtf8("actionLoad"))
        self.actionCSV = QtGui.QAction(MainWindow)
        self.actionCSV.setObjectName(_fromUtf8("actionCSV"))
        self.actionExit = QtGui.QAction(MainWindow)
        self.actionExit.setObjectName(_fromUtf8("actionExit"))
        self.actionAnnotate_Min_Max = QtGui.QAction(MainWindow)
        self.actionAnnotate_Min_Max.setObjectName(_fromUtf8("actionAnnotate_Min_Max"))
        self.actionClear_Scene = QtGui.QAction(MainWindow)
        self.actionClear_Scene.setObjectName(_fromUtf8("actionClear_Scene"))
        self.actionManually_Add_Trigger = QtGui.QAction(MainWindow)
        self.actionManually_Add_Trigger.setObjectName(_fromUtf8("actionManually_Add_Trigger"))
        self.menuSave.addAction(self.actionCSV)
        self.menuFile.addAction(self.actionLoad)
        self.menuFile.addAction(self.menuSave.menuAction())
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuActions.addAction(self.actionAnnotate_Min_Max)
        self.menuActions.addAction(self.actionClear_Scene)
        self.menuActions.addSeparator()
        self.menuActions.addAction(self.actionManually_Add_Trigger)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuActions.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.menuFile.setTitle(_translate("MainWindow", "File", None))
        self.menuSave.setTitle(_translate("MainWindow", "Save", None))
        self.menuActions.setTitle(_translate("MainWindow", "Actions", None))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar", None))
        self.label_2.setText(_translate("MainWindow", "Current File:", None))
        self.label.setText(_translate("MainWindow", "Mode: ", None))
        self.comboBox.setItemText(0, _translate("MainWindow", "PAS", None))
        self.comboBox.setItemText(1, _translate("MainWindow", "Paired Pulse", None))
        self.comboBox.setItemText(2, _translate("MainWindow", "Cortical Silent Period", None))
        self.lineEdit.setPlaceholderText(_translate("MainWindow", "Load a .smr file.", None))
        self.actionLoad.setText(_translate("MainWindow", "Load", None))
        self.actionCSV.setText(_translate("MainWindow", "CSV", None))
        self.actionExit.setText(_translate("MainWindow", "Exit", None))
        self.actionAnnotate_Min_Max.setText(_translate("MainWindow", "Annotate Min/Max", None))
        self.actionClear_Scene.setText(_translate("MainWindow", "Clear Scene", None))
        self.actionManually_Add_Trigger.setText(_translate("MainWindow", "Manually Add Trigger", None))

from pyqtgraph import PlotWidget

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())


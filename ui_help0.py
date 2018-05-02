# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_help0.ui'
#
# Created: Fri Mar 08 20:18:09 2013
#      by: PyQt4 UI code generator 4.9.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Help0(object):
    def setupUi(self, Help0):
        Help0.setObjectName(_fromUtf8("Help0"))
        Help0.resize(600, 400)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Help0.sizePolicy().hasHeightForWidth())
        Help0.setSizePolicy(sizePolicy)
        Help0.setMinimumSize(QtCore.QSize(400, 300))
        Help0.setMaximumSize(QtCore.QSize(1000, 640))
        self.verticalLayout = QtGui.QVBoxLayout(Help0)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setMargin(2)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.textBrowser = QtGui.QTextBrowser(Help0)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.textBrowser.sizePolicy().hasHeightForWidth())
        self.textBrowser.setSizePolicy(sizePolicy)
        #self.textBrowser.setSource(QtCore.QUrl(_fromUtf8("file:help1.html")))
        #self.textBrowser.setSource(QtCore.QUrl('file:///C:/Users/alper78/.qgis/python/plugins/GeolocatePhotos/help1.html'))
        #plugin_dir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/geolocatephotos"
        #self.textBrowser.setSource(QtCore.QUrl('file:///' + plugin_dir + '/help1.html'))
        self.textBrowser.setObjectName(_fromUtf8("textBrowser"))
        self.verticalLayout.addWidget(self.textBrowser)
        self.okButton = QtGui.QPushButton(Help0)
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.verticalLayout.addWidget(self.okButton)

        self.retranslateUi(Help0)
        QtCore.QMetaObject.connectSlotsByName(Help0)

    def retranslateUi(self, Help0):
        Help0.setWindowTitle(QtGui.QApplication.translate("Help0", "General help", None, QtGui.QApplication.UnicodeUTF8))
        self.okButton.setText(QtGui.QApplication.translate("Help0", "Ok", None, QtGui.QApplication.UnicodeUTF8))


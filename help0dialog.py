# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Help0Dialog
                                 A QGIS plugin
 Geolocate Photos according to the time
                             -------------------
        begin                : 2016-09-15
        copyright            : (C) 2016 by Mattia Campeggi
        email                : campeggi92@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
#from qgis.gui import *

#from datetime import datetime
#from datetime import timedelta

#import os.path, re
#import EXIF
#import geolocatephotos_utils as utils

#from ui_geolocatephotos import Ui_GeolocatePhotos
from ui_help0 import Ui_Help0


# create the dialog


class Help0Dialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_Help0()
        self.ui.setupUi(self)

        
        QObject.connect(self.ui.okButton, SIGNAL("clicked()"), self.close)

        plugin_dir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/geolocatephotos"
        self.ui.textBrowser.setSource(QtCore.QUrl('file:///' + plugin_dir + '/help0.html'))


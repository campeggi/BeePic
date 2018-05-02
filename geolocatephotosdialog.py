# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeolocatePhotosDialog
                                 A QGIS plugin
 Geolocate Photos according to time
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
from osgeo import ogr
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from fractions import Fraction
from datetime import datetime
from datetime import timedelta

import os.path, re
import EXIF
import geolocatephotos_utils as utils

from ui_beepic import Ui_BeePic
from help0dialog import Help0Dialog
from help1dialog import Help1Dialog


# create the dialog


class GeolocatePhotosDialog(QtGui.QDialog):
    def __init__(self, iface):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_BeePic()
        self.ui.setupUi(self)
        # Save reference to the QGIS interface
        self.iface = iface

        QObject.connect( self.ui.ButtonRefresh, SIGNAL( "clicked()" ), self.chooseLayer )
        QObject.connect( self.ui.comboBoxPoints, SIGNAL("currentIndexChanged(QString)"), self.chooseField )
        QObject.connect( self.ui.comboBoxFields, SIGNAL("currentIndexChanged(QString)"), self.showImageInfo )
        QObject.connect( self.ui.BrowseInFolder, SIGNAL( "clicked()" ), self.selectInputDir )
        QObject.connect( self.ui.inputFolder, SIGNAL("textChanged(QString)"), self.listImages )
        QObject.connect( self.ui.comboBoxFilters, SIGNAL("currentIndexChanged(QString)"), self.listImages )
        QObject.connect( self.ui.comboBoxFields, SIGNAL("currentIndexChanged(QString)"), self.showImageInfo )
        QObject.connect( self.ui.listWidget, SIGNAL( "itemSelectionChanged()" ), self.showImageInfo )
        QObject.connect( self.ui.spinBoxDelay, SIGNAL( "valueChanged(int)" ), self.showImageInfo )
        QObject.connect( self.ui.editFieldTimeFormat, SIGNAL("textChanged(QString)"), self.showImageInfo )
        QObject.connect( self.ui.editImageTimeFormat, SIGNAL("textChanged(QString)"), self.showImageInfo )
        QObject.connect( self.ui.checkShowPosition, SIGNAL( "stateChanged(int)" ), self.showMarker )
        QObject.connect( self.ui.BrowseOutput, SIGNAL( "clicked()" ), self.selectOutputFile )
        #QObject.connect( self.ui.cancelButton, SIGNAL("clicked()"), self.deleteMarker )
        QObject.connect( self.ui.cancelButton, SIGNAL("clicked()"), self.uncheckShowPosition )
        QObject.connect( self.ui.cancelButton, SIGNAL("clicked()"), self.close )
        #QObject.connect( self.ui.okButton, SIGNAL("clicked()"), self.deleteMarker )
        QObject.connect( self.ui.okButton, SIGNAL("clicked()"), self.go )
        QObject.connect( self.ui.helpButton, SIGNAL("clicked()"), self.showHelp0 )
        QObject.connect( self.ui.ButtonHelp1, SIGNAL("clicked()"), self.showHelp1 )
        QObject.connect( self.ui.ButtonHelp2, SIGNAL("clicked()"), self.showHelp1 )
        QObject.connect( self.ui.radioButton, SIGNAL("clicked()"), self.showImageInfo )
        QObject.connect( self.ui.radioButton_2, SIGNAL("clicked()"), self.showImageInfo )

        filterList = ['Images JPEG, TIFF, RAW','JPEG JFIF (.jpg .jpeg .JPG .JPEG)', 'PNG (.png .PNG)',
        'TIFF (.tif .tiff .TIF .TIFF)', 'RAW (.DNG .ARW .CRW .DCR .ERW .MRW .NEF .ORF .PEF .RAF .X3F)', 'all files']
        self.ui.comboBoxFilters.addItems(filterList)     

        self.chooseLayer()


    def chooseLayer( self ):
        layerList = []     # crea una lista vuota
        self.ui.comboBoxPoints.clear()     # svuota la lista del combo box
        layerList = self.getLayerNames()     # a layerList assegna il risultato della procedura getLayerNames()
        self.ui.comboBoxPoints.addItems(layerList)     # aggiunge layerList al combo box
        return

    def getLayerNames( self ):
        layermap = QgsMapLayerRegistry.instance().mapLayers()   # assegna a layermap l'insieme dei layers caricati
        layerLst = []
        for i, layer in layermap.iteritems():
            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QGis.Point:    # considera solo i layers vettoriali di punti
                layerLst.append( unicode( layer.name() ) )   # prende il nome di ogni layer e lo aggiunge alla lista layerLst
        return layerLst

    def chooseField( self ):
        fieldList = []     # crea una lista vuota
        self.ui.comboBoxFields.clear()     # svuota la lista del combo box
        fieldList = self.getFieldNames()     # a fieldList assegna il risultato della procedura getFieldNames()
        self.ui.comboBoxFields.addItems(fieldList)     # aggiunge fieldList al combo box
        return

    def getFieldNames( self ):
        fieldLst = []
        layermap = QgsMapLayerRegistry.instance().mapLayers()
        for i, layer in layermap.iteritems():
            if layer.type() == QgsMapLayer.VectorLayer and layer.name() == self.ui.comboBoxPoints.currentText():
               if layer.isValid():
                    fields = layer.dataProvider().fields()
                    for field in fields:
                        fieldLst.append(field.name())
                     
                    
                     
        return fieldLst


    def selectInputDir( self ):
        inputDir = QFileDialog.getExistingDirectory( self,
                               self.tr( "Select directory with images" ),
                               utils.lastPhotosDir() )
        if not inputDir:
            return

        self.ui.inputFolder.setText( inputDir )

        utils.setLastPhotosDir( inputDir )


    def listImages( self ):
        self.ui.listWidget.clear()
        inputFold = self.ui.inputFolder.text()
        workDir = QDir( inputFold )
        workDir.setFilter( QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot )

        if self.ui.comboBoxFilters.currentText() == 'Images JPEG, TIFF, RAW':
            # nameFilter = QStringList() << "*.jpg" << "*.jpeg" << "*.JPG" << "*.JPEG"
            nameFilter = ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG', '*.tif', '*.tiff', '*.TIF', '*.TIFF', '*.DNG', '*.ARW', '*.CRW', '*.DCR', '*.ERW', '*.MRW', '*.NEF', '*.ORF', '*.PEF', '*.RAF', '*.X3F']
            workDir.setNameFilters( nameFilter )

        elif self.ui.comboBoxFilters.currentText() == 'JPEG JFIF (.jpg .jpeg .JPG .JPEG)':
            # nameFilter = QStringList() << "*.jpg" << "*.jpeg" << "*.JPG" << "*.JPEG"
            nameFilter = ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']
            workDir.setNameFilters( nameFilter )

        elif self.ui.comboBoxFilters.currentText() == 'PNG (.png .PNG)':
            # nameFilter = QStringList() << "*.png" << "*.PNG"
            nameFilter = ['*.png', '*.PNG']
            workDir.setNameFilters( nameFilter )

        elif self.ui.comboBoxFilters.currentText() == 'TIFF (.tif .tiff .TIF .TIFF)':
            # nameFilter = QStringList() << "*.tif" << "*.tiff" << "*.TIF" << "*.TIFF"
            nameFilter = ['*.tif', '*.tiff', '*.TIF', '*.TIFF']
            workDir.setNameFilters( nameFilter )

        elif self.ui.comboBoxFilters.currentText() == 'RAW (.DNG .ARW .CRW .DCR .ERW .MRW .NEF .ORF .PEF .RAF .X3F)':
            # nameFilter = QStringList() << 
            nameFilter = ['*.DNG', '*.ARW', '*.CRW', '*.DCR', '*.ERW', '*.MRW', '*.NEF', '*.ORF', '*.PEF', '*.RAF', '*.X3F']
            workDir.setNameFilters( nameFilter )

        self.inputFiles = workDir.entryList()
        #if self.inputFiles.count() == 0:
        #    QMessageBox.warning( self, self.tr( "No images found" ), self.tr( "There are no supported images in this directory. Please select another one." ) )
        #    self.inputFiles = None
        #    return

        # imageList = []
        # imagesList = self.inputFiles
        # for file in self.inputFiles:
        #     imageList.append(file)           
        self.ui.listWidget.addItems(self.inputFiles)
        return
    
    def convert_to_degress(self, value):
      """Helper function to convert the GPS coordinates stored in the EXIF to degress in float format"""
      d = float(Fraction(str(value.values[0])))
      m = float(Fraction(str(value.values[1]))) 
      s = float(Fraction(str(value.values[2])))

      return d + (m / 60.0) + (s / 3600.0)        
        
    def showImageInfo( self ):
        self.ui.textBrowser.clear()
        # workDirSelect = QDir( self.ui.inputFolder.text() )
        # workDirSelect.setFilter( QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot )
        # selection = self.ui.listWidget.selectedItems()
        # nameSelect = [ selection[0] ]
        # workDirSelect.setNameFilters( [nameSelect] )
        # selectedFiles = workDirSelect.entryList()
        
        layerName = self.ui.comboBoxPoints.currentText()
        if layerName == '':
            self.ui.textBrowser.append('Calculated coordinates: !!! select a reference layer of points !!!')
            return
        fieldName = self.ui.comboBoxFields.currentText()
        if fieldName == '':
            self.ui.textBrowser.append('Calculated coordinates: !!! select the reference time field !!!')
            return

        dt1,k1 = self.prova()
        
        try: 
            dt1 = dt1.toPyDateTime()
        except:
            self.ui.textBrowser.append('This field does not contain a valid date ' )
                
        self.ui.textBrowser.append('First point date and time: ' + str(dt1))
        fieldTimeFormat = str( self.ui.editFieldTimeFormat.text() )
               
        try:
            dt1b = datetime.strptime(str(dt1), fieldTimeFormat)            
        except:
            self.ui.textBrowser.append('!!! Wrong field or datetime format !!!')            
            return
        
        selectedFiles = self.ui.listWidget.selectedItems()
        
        if len(selectedFiles) == 0:
            return

        self.ui.textBrowser.append(' ')
        firstImageName = 'File name: ' + selectedFiles[0].text()  
        # self.ui.textBrowser.insertPlainText('Image name: ' firstImageName)
        self.ui.textBrowser.append( firstImageName )
                    
        path = os.path.abspath( unicode( QFileInfo( self.ui.inputFolder.text() + "/" + selectedFiles[0].text() ).absoluteFilePath() ) )
        photoFile = open( path, "rb" )
        exifTags = EXIF.process_file( photoFile, details=False )
        #a = get_exif(photoFile)
        photoFile.close()
        
        if exifTags.has_key( "GPS GPSLongitude" ) and exifTags.has_key( "GPS GPSLatitude" ):
            
            gpslon =  exifTags[ "GPS GPSLongitude" ] 
            gpslat =  exifTags[ "GPS GPSLatitude" ]
              
            lon = self.convert_to_degress(gpslon)
            lat = self.convert_to_degress(gpslat)
            self.ui.textBrowser.append('Coordinates in exif data: ' + str(lon) + 'E ' + str(lat) +' N' )
            
        else:
            self.ui.textBrowser.append('Coordinates in exif data: Absent' )
        
        
      
        
        newImgDate = 0
        if exifTags.has_key( "EXIF DateTimeOriginal" ):
            imgDateStr = str( exifTags[ "EXIF DateTimeOriginal" ] )
            self.ui.textBrowser.append('Exif date and time: ' + imgDateStr)
            imgDateFormat = str( self.ui.editImageTimeFormat.text() )
            #self.ui.textBrowser.append('Exif datetime format: ' + imgDateFormat)
            try:
                imgDate = datetime.strptime(imgDateStr, imgDateFormat)
                #self.ui.textBrowser.append('Converted date and time: ' + str(imgDate).strip('[]'))
            except:
                self.ui.textBrowser.append('!!! Wrong image datetime format !!!')
                return
            delay = int( self.ui.spinBoxDelay.value() )
            newImgDate = imgDate + timedelta(seconds=delay)
            self.ui.textBrowser.append('Converted and updated date and time: ' + str(newImgDate).strip('[]'))

        else:
            self.ui.textBrowser.append('!!! This image has no exif datetime !!!')
            return

        if newImgDate < dt1b:
            self.ui.textBrowser.append('!!! This image was taken before starting track !!!')
            return
        
        if newImgDate == 0:
            self.ui.textBrowser.append('Calculated coordinates: !!! something is wrong !!!')
        else:
            x,y,preTrack,postTrack = self.getxy( newImgDate )
            self.ui.textBrowser.append(' ')
            self.ui.textBrowser.append('Calculated coordinates: ' + str(x) + 'E ' + str(y) + 'N')
            #self.ui.textBrowser.append('time previous point: ' + str(pretime))
            #self.ui.textBrowser.append('time nexy point: ' + str(postime))
            #self.ui.textBrowser.append('x previous point: ' + str(prex))
            #self.ui.textBrowser.append('x nexy point: ' + str(postx))
            #self.ui.textBrowser.append('step: ' + str(step))

        # show point on the map
        if self.ui.checkShowPosition.isChecked():
            if self.markerLayer.featureCount() == 0:
                # add a point with x,y coordinates
                marker = QgsFeature()
                if self.ui.radioButton.isChecked():
                  if exifTags.has_key( "GPS GPSLongitude" ) and exifTags.has_key( "GPS GPSLatitude" ):
                      x = float(lon)
                      y = float(lat)
                  else:
                      QMessageBox.warning( self, self.tr( "No GPS Coordinates" ), self.tr( "There are no GPS coordinates for this photo " ) )    
                marker.setGeometry( QgsGeometry.fromPoint(QgsPoint(x,y)) )
                self.markerProvider.addFeatures( [ marker ] )
                # update layer's extent when new features have been added
                # because change of extent in provider is not propagated to the layer
                self.markerLayer.updateExtents()
                self.iface.mapCanvas().refresh()   # refresh the map
            else:
                # shift the point to x,y coordinates
                if self.ui.radioButton.isChecked():
                  if exifTags.has_key( "GPS GPSLongitude" ) and exifTags.has_key( "GPS GPSLatitude" ):
                      x = float(lon)
                      y = float(lat)
                  else:
                      QMessageBox.warning( self, self.tr( "No GPS Coordinates" ), self.tr( "There are no GPS coordinates for this photo " ) )    
                geom = QgsGeometry.fromPoint(QgsPoint(x,y))
                self.markerProvider.changeGeometryValues({ 1 : geom })
                # update layer's extent
                self.markerLayer.updateExtents()
                self.iface.mapCanvas().refresh()   # refresh the map
        return


    def showMarker(self):
        layermap = QgsMapLayerRegistry.instance().mapLayers()
        if self.ui.checkShowPosition.isChecked():
            for i, layer in layermap.iteritems():
                if layer.type() == QgsMapLayer.VectorLayer and layer.name() == self.ui.comboBoxPoints.currentText():
                    referenceLayer = layer
                    break
            # create layer
            self.markerLayer = QgsVectorLayer("Point", "image_position", "memory")
            self.markerLayer.setCrs( referenceLayer.crs() )
            self.markerProvider = self.markerLayer.dataProvider()
            # add layer to the registry and show it
            QgsMapLayerRegistry.instance().addMapLayer(self.markerLayer)
            legend = self.iface.legendInterface()  # access the legend
            legend.setLayerVisible(self.markerLayer, True)  # show the layer
            #legend.isLayerVisible(markerLayer)   # check if markerLayer is visible (true or false)
            self.showImageInfo()   # show again image info in the text browser and marker on the map
        else:
            try:
                # remove and delete layer
                QgsMapLayerRegistry.instance().removeMapLayers( [self.markerLayer.id()] )
                #self.deleteMarker()
            except:
                return
        return
    
    def uncheckShowPosition(self):
        self.ui.checkShowPosition.setChecked(0)
        return
        
    def deleteMarker(self):
        try:
            QgsMapLayerRegistry.instance().removeMapLayers( [self.markerLayer.id()] )
            return
        except:
            return
             

    def prova( self ):
        
        layermap = QgsMapLayerRegistry.instance().mapLayers()
        for i, layer in layermap.iteritems():
            if layer.type() == QgsMapLayer.VectorLayer and layer.name() == self.ui.comboBoxPoints.currentText():
                provider = layer.dataProvider()
                IDdatetimeField = [provider.fieldNameIndex( self.ui.comboBoxFields.currentText() )]
                for f in layer.getFeatures():
                    map = f.attributes()
                    fieldvalue=f[self.ui.comboBoxFields.currentText()]                                        
                    for  value in map:                         
                         return fieldvalue, str(IDdatetimeField)

        
    def getxy( self, imgtime ):
        layermap = QgsMapLayerRegistry.instance().mapLayers()
        for i, layer in layermap.iteritems():
            if layer.type() == QgsMapLayer.VectorLayer and layer.name() == self.ui.comboBoxPoints.currentText():
                provider = layer.dataProvider()
                IDdatetimeField = [provider.fieldNameIndex( self.ui.comboBoxFields.currentText() )]
                fieldTimeFormat = str( self.ui.editFieldTimeFormat.text() )
                
                for feat in layer.getFeatures():
                    point = feat.geometry().asPoint()
                    map = feat.attributes()
                    if feat.id() == 0:
                            fieldvalue=feat[self.ui.comboBoxFields.currentText()]
                            fieldvalue = fieldvalue.toPyDateTime()                            
                            time1 = datetime.strptime(str(fieldvalue), fieldTimeFormat)
                            x1 = point.x()
                            y1 = point.y()
                    fieldvalue=feat[self.ui.comboBoxFields.currentText()]
                    fieldvalue = fieldvalue.toPyDateTime()                   
                    time2 = datetime.strptime(str(fieldvalue), fieldTimeFormat)
                    x2 = point.x()
                    y2 = point.y()
                    if time1 > imgtime:
                            xImg = 0
                            yImg = 0
                            pre = 1
                            post = 0
                            #case = 1                            
                            return xImg,yImg,pre,post
                    elif time2 == imgtime:
                            pre = 0
                            post = 0
                            #case = 2
                            return x2,y2,pre,post
                    elif time2 > imgtime:
                            xImg = (imgtime-time1).total_seconds()/(time2-time1).total_seconds()*(x2-x1)+x1
                            yImg = (imgtime-time1).total_seconds()/(time2-time1).total_seconds()*(y2-y1)+y1
                            pre = 0
                            post = 0                           
                            #case = 3
                            return xImg,yImg,pre,post
                    time1 = time2
                    x1 = x2
                    y1 = y2                   
                xImg = 0
                yImg = 0
                pre = 0
                post = 1
                step = 4
                return xImg,yImg,pre,post


    def selectOutputFile( self ):
        # prepare dialog parameters
        settings = QSettings()
        lastDir = utils.lastShapefileDir()
        shpFilter =  "Shapefiles (*.shp *.SHP)" 

        fileDialog = QgsEncodingFileDialog( self, self.tr( "Select output shapefile" ), lastDir, shpFilter )        
        fileDialog.setFileMode( QFileDialog.AnyFile )
        fileDialog.setAcceptMode( QFileDialog.AcceptSave )
        fileDialog.setConfirmOverwrite( True )

        if not fileDialog.exec_() == QDialog.Accepted:
          return

        outputFile = fileDialog.selectedFiles()[0]
        self.outputEncoding = fileDialog.encoding()
           
        utils.setLastShapefileDir( outputFile )
        self.ui.lineEditOutput.setText( outputFile )


    def showHelp0( self ):
        self.help0dlg = Help0Dialog()
        self.help0dlg.show()
        return

    def showHelp1( self ):
        self.help1dlg = Help1Dialog()
        self.help1dlg.show()
        return


    def go( self ):

        self.ui.textBrowser.clear()

        if len(self.inputFiles) == 0:
            QMessageBox.warning( self, self.tr( "No images found" ), self.tr( "There are no supported images in this directory. Please select another one." ) )
            self.inputFiles = None
            return

        outputFileName = self.ui.lineEditOutput.text() + '.shp'
       
        if outputFileName == '':
            QMessageBox.warning( self, self.tr( "No output file" ), self.tr( "Please insert output shapefile." ) )
            return

        layerName = self.ui.comboBoxPoints.currentText()
        if layerName == '':
            QMessageBox.warning( self, self.tr( "No reference points" ), self.tr( "Please select a layer with reference points." ) )
            return
        layermap = QgsMapLayerRegistry.instance().mapLayers()
        for i, layer in layermap.iteritems():
            if layer.type() == QgsMapLayer.VectorLayer and layer.name() == self.ui.comboBoxPoints.currentText():
                referenceLayer = layer
                break
        
        fieldName = self.ui.comboBoxFields.currentText()
        if fieldName == '':
            QMessageBox.warning( self, self.tr( "No field" ), self.tr( "Please select a field with date and time of the reference points." ) )
            return
        
        fieldTimeFormat = str( self.ui.editFieldTimeFormat.text() )
        dt1,k1 = self.prova()
        
        try: 
            dt1 = dt1.toPyDateTime()
            dt1b = datetime.strptime(str(dt1), fieldTimeFormat)
        except:
            QMessageBox.warning( self, self.tr( "Bad datetime" ), self.tr( "The datetime of the reference points is wrong! Please correct the format or select another field." ) )
            return
       
        self.ui.progressBar.setMinimum(0)
        self.ui.progressBar.setMaximum(len(self.inputFiles))
        progr = 0

        delay = int( self.ui.spinBoxDelay.value() )
        
        shapeFields = QgsFields()
        shapeFields.append(QgsField("image_ID", QVariant.Int))
        shapeFields.append(QgsField("filename", QVariant.String))
        shapeFields.append(QgsField("x", QVariant.Double))
        shapeFields.append(QgsField("y", QVariant.Double))
        shapeFields.append(QgsField("altitude", QVariant.Double))
        shapeFields.append(QgsField("datetime", QVariant.String))
        shapeFields.append(QgsField("filepath", QVariant.String))
        
        crs = referenceLayer.crs()
        shapeFileWriter = QgsVectorFileWriter( outputFileName, "utf-8", shapeFields, QGis.WKBPoint, crs, "ESRI Shapefile" )
                                
        georefImages = 0
        imageNoDatetime = 0
        imageBadDatetime = 0
        preImages = 0
        postImages = 0
        
        
        # create .kml
        if self.ui.checkKml.isChecked():
            self.createkml(outputFileName)
            
        for imageName in self.inputFiles:

            # get image datetime in exif
            path = os.path.abspath( unicode( QFileInfo( self.ui.inputFolder.text() + "/" + imageName ).absoluteFilePath() ) )
            photoFile = open( path, "rb" )
            exifTags = EXIF.process_file( photoFile, details=False )
            photoFile.close()
            self.ui.textBrowser.append(imageName + ': ')
            #newImgDate = 0
            
            if exifTags.has_key( "GPS GPSAltitude" ):
              altitude = str(exifTags[ "GPS GPSAltitude" ]) 
            else:
              altitude = 0
              
            if exifTags.has_key( "EXIF DateTimeOriginal" ):
                imgDateStr = str( exifTags[ "EXIF DateTimeOriginal" ] )
                
                imgDateFormat = str( self.ui.editImageTimeFormat.text() )
                imgDate = datetime.strptime(imgDateStr, imgDateFormat) 
                                   
        
                try:                    
                    imgDate = datetime.strptime(imgDateStr, imgDateFormat)                    
                    newImgDate = imgDate + timedelta(seconds=delay)
                    x,y,preTrack,postTrack = self.getxy( newImgDate )
                    
                    if self.ui.radioButton.isChecked():
                           if exifTags.has_key( "GPS GPSLongitude" ) and exifTags.has_key( "GPS GPSLatitude" ):  
                                gpslon =  exifTags[ "GPS GPSLongitude" ] 
                                gpslat =  exifTags[ "GPS GPSLatitude" ]
              
                                lon = self.convert_to_degress(gpslon)
                                lat = self.convert_to_degress(gpslat)
                            
                                preTrack = 0
                                postTrack = 0
                            
                                x = float(lon)
                                y = float(lat)
                           else:
                                self.ui.textBrowser.insertPlainText('This photo has not Gps Coordinates, i am using the calculated coordinates')
                    

                    if preTrack == 1:
                        preImages = preImages + 1
                        self.ui.textBrowser.insertPlainText('taken before the reference points')
                    elif postTrack == 1:
                        postImages = postImages + 1
                        self.ui.textBrowser.insertPlainText('taken after the reference points')
                    else:
                        imagePoint = QgsFeature()
                                                                                                     
                        imagePoint.setGeometry( QgsGeometry.fromPoint(QgsPoint(x,y)) )
                        georefImages = georefImages + 1                       
                        imagePoint.setAttributes([georefImages,imageName, x, y, altitude, str(newImgDate), path])                                                                                 
                        shapeFileWriter.addFeature(imagePoint)
                       
                        # update layer's extent when new features have been added
                        # because change of extent in provider is not propagated to the layer
                        #layer.updateExtents()
                        self.ui.textBrowser.insertPlainText(str(x) + 'E ' + str(y) + 'N')
                        #self.ui.textBrowser.append( str(georefImages) + " " + str(newImgDate) + " " + str(path) )
                        # add placemark to .kml
                        if self.ui.checkKml.isChecked():
                            self.writekmlpoint(imageName,x,y,path)
                except:
                    imageBadDatetime = imageBadDatetime + 1
                    self.ui.textBrowser.insertPlainText('! Wrong image datetime format !')
            else:
                imageNoDatetime = imageNoDatetime + 1
                self.ui.textBrowser.insertPlainText('! This image has no exif datetime !')
                
            progr = progr + 1
            self.ui.progressBar.setValue(progr)
            self.ui.textBrowser.verticalScrollBar().setValue(self.ui.textBrowser.verticalScrollBar().maximum())
            
        del shapeFileWriter
        haveShape = True

        # close .kml
        if self.ui.checkKml.isChecked():
            self.closekml()

        #self.ui.textBrowser.clear()
        self.ui.textBrowser.append(' ')
        if georefImages == 1:
            self.ui.textBrowser.append( '1 image has been geolocate' )
        else:
            self.ui.textBrowser.append( str(georefImages) + ' images have been geolocated' )
        if imageNoDatetime != 0:
            if imageNoDatetime == 1:
                self.ui.textBrowser.append( '1 file has no DateTimeOriginal exif tag' )
            else:
                self.ui.textBrowser.append( str(imageNoDatetime) + ' files have no DateTimeOriginal exif tag' )
        if imageBadDatetime != 0:
            if imageBadDatetime == 1:
                self.ui.textBrowser.append( '1 file has wrong datetime format' )
            else:
                self.ui.textBrowser.append( str(imageBadDatetime) + ' files have wrong datetime format' )
        if preImages != 0:
            if preImages == 1:
                self.ui.textBrowser.append( '1 image was taken before the first reference points' )
            else:
                self.ui.textBrowser.append( str(preImages) + ' images were taken before the first reference points' )
        if postImages != 0:
            if postImages == 1:
                self.ui.textBrowser.append( '1 image was taken after the last reference points' )
            else:
                self.ui.textBrowser.append( str(postImages) + ' images were taken after the last reference points' )

        if georefImages > 0:
            photoLayer = QgsVectorLayer( outputFileName, QFileInfo( outputFileName ).baseName(), "ogr" ) 
            QgsMapLayerRegistry.instance().addMapLayer( photoLayer )
           

        self.ui.textBrowser.verticalScrollBar().setValue(self.ui.textBrowser.verticalScrollBar().maximum())
        return


    def createkml(self,outputFileName):
        outputkmlName = outputFileName.replace(".shp", "-kml.kml")
        self.outkml = open(outputkmlName,'w')
        self.outkml.write('''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
	<name>''' + os.path.basename(str(outputkmlName)) + '''</name>
	<Style id="sn_camera">
		<IconStyle>
			<Icon><href>http://maps.google.com/mapfiles/kml/shapes/camera.png</href></Icon>
			<hotSpot x="0.5" y="0" xunits="fraction" yunits="fraction"/><scale>0.7</scale>
		</IconStyle>
		<LabelStyle><scale>0.4</scale></LabelStyle>
		<ListStyle></ListStyle>
	</Style>
	<StyleMap id="msn_camera">
		<Pair><key>normal</key><styleUrl>#sn_camera</styleUrl></Pair>
		<Pair><key>highlight</key><styleUrl>#sh_camera</styleUrl></Pair>
	</StyleMap>
	<Style id="sh_camera">
		<IconStyle>
			<scale>1.18182</scale>
			<Icon><href>http://maps.google.com/mapfiles/kml/shapes/camera.png</href></Icon>
			<hotSpot x="0.5" y="0" xunits="fraction" yunits="fraction"/>
		</IconStyle>
		<LabelStyle><scale>0.5</scale></LabelStyle>
		<ListStyle></ListStyle>
	</Style>
	<Folder>
		<name>geolocated_photos</name>''')
        return

    def writekmlpoint(self,imageName,x,y,path):
        self.outkml.write('''
		<Placemark>
			<name>''' + imageName + '''</name>
			<description><![CDATA[<img src="file:///''' + path.replace(".JPG", ".jpg") + '''"/>]]></description>
			<styleUrl>#msn_camera</styleUrl>
			<Point><coordinates>''' + str(x) + ''',''' + str(y) + ''',0</coordinates></Point>
		</Placemark>''')
        return

    def closekml(self):
        self.outkml.write('''
	</Folder>
</Document>
</kml>''')
        self.outkml.close()
        return






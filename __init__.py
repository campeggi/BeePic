# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BeePic
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
 This script initializes the plugin, making it known to QGIS.
"""




def classFactory(iface):
    # load GeolocatePhotos class from file GeolocatePhotos
    from geolocatephotos import BeePic
    return BeePic(iface)

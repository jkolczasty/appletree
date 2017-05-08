#!/usr/bin/env python3
#
#       Copyright 2017+ Jakub Kolasa <jkolczasty@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#
# __author__ = 'Jakub Kolasa <jkolczasty@gmail.com'>
#

# noinspection PyBroadException

import os
import traceback
import sys

__QT = 4 if os.environ.get('USE_QT4') == '1' else 5

if __QT == 5:
    try:
        from PyQt5 import Qt, QtGui, QtCore, QtWidgets
    except:
        __QT = 4

if __QT == 4:
    try:
        from PyQt4 import Qt, QtGui, QtCore, QtWidgets
    except:
        print("Could not find PyQt5 or PyQt4.")
        sys.exit(1)


FontDB = None


def initFonts():
    global FontDB
    FontDB = Qt.QFontDatabase()
    FontDB.addApplicationFont("fonts/fontawesome-webfont.ttf")


def loadQImageFix(path):
    try:
        f = Qt.QFile(path)
        if not f.open(Qt.QFile.ReadOnly):
            print("loadQImageFix(): could not open file:", path)
            return None

        data = f.readAll()
        f.close()
        del f

        image = Qt.QPixmap()
        image.loadFromData(data)
        data.clear()
        del data
        return image

    except Exception as e:
        print("Exception:", e.__class__.__name__, e)
        traceback.print_exc()
        return None

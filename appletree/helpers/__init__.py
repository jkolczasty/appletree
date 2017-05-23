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

from appletree.gui.qt import Qt
from uuid import uuid4
import os.path


# dummy translations
def T(*args):
    return args[0]


def genuid():
    return str(uuid4())


def getIcon(name):
    fn = os.path.join("icons", name + ".png")
    return Qt.QIcon(fn)


def getIconSvg(name):
    fn = os.path.join("icons", name + ".svg")
    return Qt.QIcon(fn)


def getIconImage(name):
    fn = os.path.join("icons", name + ".png")
    return Qt.QImage(fn)


def getIconPixmap(name):
    fn = os.path.join("icons", name + ".png")
    return Qt.QPixmap(fn, "PNG")


def messageDialog(title, message, details=None, OkCancel=False, icon=None):
    msg = Qt.QMessageBox()
    if icon:
        msg.setIcon(icon)
    else:
        msg.setIcon(Qt.QMessageBox.Information)

    msg.setText(message)
    msg.setWindowTitle(title)
    if details:
        msg.setDetailedText(details)
    if OkCancel:
        msg.setStandardButtons(Qt.QMessageBox.Ok | Qt.QMessageBox.Cancel)
    else:
        msg.setStandardButtons(Qt.QMessageBox.Ok)

    return msg.exec_() == Qt.QMessageBox.Ok

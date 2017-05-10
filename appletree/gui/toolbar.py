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
from appletree.helpers import getIcon
from weakref import ref


class Toolbar(Qt.QToolBar):
    def __init__(self, win):
        Qt.QToolBar.__init__(self, win)
        self.win = ref(win)

    def _add(self, name, icon, shortcut, callback):
        if icon.__class__.__name__ != "QIcon":
            _icon = getIcon(icon)
        else:
            _icon = icon

        a = Qt.QAction(_icon, name, self.win())
        a.triggered.connect(callback)
        if shortcut:
            a.setShortcut(shortcut)
        self.addAction(a)

    def add(self, items):
        for item in items:
            self._add(**item)

    def addWithSeparatorLeft(self, items):
        self.addSeparator()
        for item in items:
            self._add(**item)

    def addButton(self, name, icon, callback, shortcut=None):
        button = Qt.QAction(icon, name, self.win())
        if shortcut:
            button.setShortcut(shortcut)
        button.triggered.connect(callback)
        self.addAction(button)

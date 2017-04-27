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

from appletree.plugins.base import ATPlugin
from appletree.gui.qt import Qt


class TestPlugin(ATPlugin):
    def initialize(self):
        win = self.win()

        win.toolbar.addWithSeparatorLeft(
            [dict(name='Hello', icon=self.getIcon('toolbar'), shortcut='CTRL+A', callback=self.on_toolbar_hello),
             ])

    def on_toolbar_hello(self):
        # msg = Qt.QMessageBox()
        # msg.setIcon(Qt.QMessageBox.Information)
        #
        # msg.setText("Plugin Test")
        # msg.setInformativeText("This is simple plugin example for AppleTree")
        # msg.setWindowTitle("Plugin Test")
        # msg.setDetailedText("AppleTree is awsome!")
        # msg.setStandardButtons(Qt.QMessageBox.Ok)
        # # msg.buttonClicked.connect(msgbtn)
        #
        # msg.exec_()
        dialog = self.preferencesDialog("Some title", "Some text")
        dialog.addSimpleInput("input1", "some input", "somevalue")
        dialog.exec_()

    def on_plugin_menu(self):
        msg = Qt.QMessageBox()
        msg.setIcon(Qt.QMessageBox.Information)

        msg.setText("Plugin Test")
        msg.setInformativeText("You just clicked my plugin's menu item? ;-)")
        msg.setWindowTitle("Plugin Test")
        msg.setDetailedText("AppleTree is awsome!")
        msg.setStandardButtons(Qt.QMessageBox.Ok)
        # msg.buttonClicked.connect(msgbtn)

        msg.exec_()

FACTORY = TestPlugin

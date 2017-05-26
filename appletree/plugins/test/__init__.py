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
import time


class ProgressDialog(Qt.QProgressDialog):

    def __init__(self, win, cancelcb=None, *args):
        super(ProgressDialog, self).__init__(parent=win)
        self.setModal(True)
        self.setLabelText("Please wait...")
        self.cancelcb = cancelcb
        self.setRange(0, 100)
        self.setAutoClose(False)
        self.setAutoReset(False)
        self._cancebutton = Qt.QPushButton(self)
        self._cancebutton.setText("Cancel")
        self.setCancelButton(self._cancebutton)


class TestPlugin(ATPlugin):
    def buildToolbarApplication(self, toolbar):
        toolbar.addWithSeparatorLeft(
            [dict(name='Hello', icon=self.getIcon('plugin'), shortcut='CTRL+T', callback=self.on_toolbar_hello),
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
        d = ProgressDialog(self.win())
        d.show()
        c = 0
        while c < 100:
            d.setValue((c/100)*100)
            Qt.QApplication.processEvents()
            if d.wasCanceled():
                print("CANCEL! ABORT!")
            c += 1
            time.sleep(0.1)

        d.destroy()

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

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


import logging
import signal
import sys

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    print("Loading appletree.qui.qt")
    from appletree.gui.qt import initFonts, initQtApplication
    APP = initQtApplication()
    from appletree.gui.progressdialog import ProgressDialog

    ProgressDialog.create(0)
    ProgressDialog.progress(10)
    print("Loading appletree.helpers")
    from appletree.helpers import getIcon
    ProgressDialog.progress(20)
    print("Loading appletree.application")
    from appletree.application import App
    ProgressDialog.progress(30)

    APP.setApplicationName("AppleTree")
    APP.setWindowIcon(getIcon('app'))
    initFonts()
    app = App()
    ProgressDialog.done()
    app.show()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(APP.exec_())

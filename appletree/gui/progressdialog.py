#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from __future__ import absolute_import
from __future__ import print_function

# __author__ = 'Jakub Kolasa <jakub@arker.pl'>

from appletree.gui.qt import Qt
from appletree.helpers import T
_progress = None


class ProgressDialog(Qt.QProgressDialog):
    def __init__(self, win, cancelcb=None, showcancel=False, *args):
        super(ProgressDialog, self).__init__(parent=win)
        self.setModal(True)
        self.setLabelText("Please wait...")
        self.cancelcb = cancelcb
        self.setRange(0, 100)
        self.setAutoClose(False)
        self.setAutoReset(False)
        if showcancel:
            self.setCancelButtonText(T("Cancel"))

            if cancelcb:
                self._cancebutton = Qt.QPushButton(self)
                self._cancebutton.setText("Cancel")
                self.setCancelButton(self._cancebutton)
        else:
            self.setCancelButtonText("")
        self.reset()

    @staticmethod
    def create(delay=1, win=None):
        global _progress

        if not _progress:
            _progress = ProgressDialog(win)
        _progress.setMinimumDuration(delay*1000)

    @staticmethod
    def progress(value):
        global _progress
        if not _progress:
            ProgressDialog.create()

        _progress.setValue(value)

    @staticmethod
    def done():
        global _progress
        if not _progress:
            return

        progress = _progress
        _progress = None

        progress.reset()
        progress.hide()
        progress.destroy()

    @staticmethod
    def yield_():
        Qt.QApplication.processEvents()

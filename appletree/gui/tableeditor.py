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


import os
from appletree.gui.qt import QTVERSION, Qt, QtCore, loadQImageFix
from appletree.helpers import T, genuid, messageDialog
from .editor import Editor, EDITORS


class TableEditor(Editor):
    prevModified = False
    model = None
    has_images = False

    # def __init__(self, win, project, docid, docname):
    #     super(TableEditor, self).__init__(win, project, docid, docname)

    def createEditorWidget(self):
        self.editor = Qt.QTableView(parent=self)
        self.model = Qt.QStandardItemModel(self.editor)
        self.editor.setModel(self.model)
        self.editor.setItemDelegate(Qt.QItemDelegate(self.editor))
        # self.editor.cursorPositionChanged.connect(self.on_cursor_possition_changed)

        # docbody = self.project.doc.getDocumentBody(self.docid)

        self.model.insertColumn(0)
        self.model.insertColumn(1)
        self.model.insertColumn(2)
        # font = Qt.QFont("Courier")
        # font.setPointSize(14)
        # self.editor.setFont(font)
        # self.doc.setModified(False)

        self.editor.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self.on_contextmenu_event)

        return self.editor

    def destroy(self, *args):
        super(TableEditor, self).destroy(*args)
        self.log.info("Destroy")

    def setModified(self, modified):
        # self.doc.setModified(modified)
        # # NOTE: change also self.prevModified?
        # self.prevModified = None
        # self.on_text_changed()
        pass

    def getBody(self):
        return None

    def on_toolbar_editor_action(self, name):
        return None

    def on_contextmenu_event(self, point):
        menu = Qt.QMenu()

        action = Qt.QAction(T("Append row above"), menu)
        action.triggered.connect(self.on_contextmenu_insertrowabove)
        menu.addAction(action)

        action = Qt.QAction(T("Insert row below"), menu)
        action.triggered.connect(self.on_contextmenu_insertrowbelow)
        menu.addAction(action)

        menu.exec_(self.editor.mapToGlobal(point))
        del menu

    def on_contextmenu_insertrowabove(self):
        if self.model.rowCount() == 0:
            return self.on_contextmenu_insertrowbelow()

        indexes = self.editor.selectedIndexes()
        if not indexes:
            return
        index = indexes[0]

        self.model.insertRow(index.row())

    def on_contextmenu_insertrowbelow(self):
        if self.model.rowCount() == 0:
            return self.model.insertRow(0)

        indexes = self.editor.selectedIndexes()
        if not indexes:
            return
        index = indexes[0]

        self.model.insertRow(index.row()+1)


EDITORS['table'] = TableEditor

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


from appletree.gui.qt import QTVERSION, Qt, QtCore
from appletree.helpers import T
from appletree.gui.utils import ObjectCallbackWrapperRef
from .editor import Editor, EDITORS
from io import StringIO
import csv


class TableEditor(Editor):
    prevModified = False
    model = None
    has_images = False

    def createEditorWidget(self):
        self.editor = Qt.QTableView(parent=self)
        self.model = Qt.QStandardItemModel(self.editor)
        self.editor.setModel(self.model)
        self.editor.setItemDelegate(Qt.QItemDelegate(self.editor))

        docbody = self.project.doc.getDocumentBody(self.docid)
        self.putBody(docbody)

        self.editor.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self.on_contextmenu_event)

        return self.editor

    def destroy(self, *args):
        super(TableEditor, self).destroy(*args)
        self.log.info("Destroy")

    def setModified(self, modified):
        pass

    def getBody(self):
        ios = StringIO()
        cs = csv.writer(ios)

        for r in range(0, self.model.rowCount()):
            row = []
            for c in range(0, self.model.columnCount()):
                row.append(self.model.data(self.model.index(r, c)))

            cs.writerow(row)

        return ios.getvalue()

    def putBody(self, body):
        ios = StringIO(body)
        cs = csv.reader(ios)
        for r in cs:
            items = [Qt.QStandardItem(s) for s in r]
            self.model.appendRow(items)

    def on_toolbar_editor_action(self, name):
        return None

    def on_contextmenu_event(self, point):
        menu = Qt.QMenu()

        if self.model.rowCount() > 0:
            action = Qt.QAction(T("Insert row above"), menu)
            action.triggered.connect(ObjectCallbackWrapperRef(self, 'insertRowInPosition', 0))
            menu.addAction(action)

        action = Qt.QAction(T("Insert row below"), menu)
        action.triggered.connect(ObjectCallbackWrapperRef(self, 'insertRowInPosition', 1))
        menu.addAction(action)

        if self.model.columnCount() > 0:
            action = Qt.QAction(T("Insert column on the left"), menu)
            action.triggered.connect(ObjectCallbackWrapperRef(self, 'insertColInPosition', 0))
            menu.addAction(action)

        action = Qt.QAction(T("Insert column on the right"), menu)
        action.triggered.connect(ObjectCallbackWrapperRef(self, 'insertColInPosition', 1))
        menu.addAction(action)

        menu.exec_(self.editor.mapToGlobal(point))
        del menu

    def insertRowInPosition(self, pos, *args):
        if self.model.rowCount() == 0:
            return self.model.insertRow(0)

        indexes = self.editor.selectedIndexes()
        if not indexes:
            return
        index = indexes[0]

        self.model.insertRow(index.row()+pos)

    def insertColInPosition(self, pos, *args):
        if self.model.columnCount() == 0:
            return self.model.insertColumn(0)

        indexes = self.editor.selectedIndexes()
        if not indexes:
            return
        index = indexes[0]

        self.model.insertColumn(index.column() + pos)


EDITORS['table'] = TableEditor

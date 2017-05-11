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
from weakref import ref
from appletree.gui.qt import Qt
from appletree.helpers import getIcon
from collections import OrderedDict

EDITORS = OrderedDict()


class Editor(Qt.QWidget):
    prevModified = False
    has_images = False

    def __init__(self, win, project, docid, docname):
        Qt.QWidget.__init__(self)
        self.project = project
        self.log = logging.getLogger("at.editor")
        self.win = ref(win)
        self.ignorechanges = False

        self.docid = docid
        self.docname = docname
        h1 = Qt.QVBoxLayout()
        splitter = Qt.QSplitter()

        self.setLayout(h1)
        h1.addWidget(splitter)

        self.editor = self.createEditorWidget()
        # self.loadEditor()

        self.elements = None
        self.elementsroot = None

        # elements = Qt.QTreeWidget(self)
        # # elements.setMaximumWidth(200)
        # # elements.setFixedWidth(200)
        # # elements.setMinimumWidth(100)
        # elements.setBaseSize(100, 100)
        # elements.adjustSize()
        # # elements.setSizePolicy(Qt.QSizePolicy.MinimumExpanding,Qt.QSizePolicy.MinimumExpanding)
        #
        # # elements.setFixedWidth(200)
        # elements.setHeaderHidden(True)
        # elementsroot = elements.invisibleRootItem()
        #
        # elementstype = Qt.QTreeWidgetItem(elementsroot, [T("Attachements"), "attachements"])
        # elementstype.setIcon(0, getIcon("attachments"))
        # elementstype.setExpanded(True)
        #
        # elementstype = Qt.QTreeWidgetItem(elementsroot, [T("Images"), "images"])
        # elementstype.setIcon(0, getIcon("attachments"))
        # elementstype.setExpanded(True)
        #
        # self.elements = elements
        # self.elementsroot = elementsroot

        # self._addElement("attachements", "somefile")

        splitter.addWidget(self.editor)
        # splitter.addWidget(self.elements)
        splitter.setStretchFactor(0, 2)
        # splitter.setStretchFactor(1, 0)

        # TODO: should accessibleName be used?
        self.setAccessibleName(docid)

    @classmethod
    def Editor(cls, name, win, project, docid, docname):
        global EDITORS
        editor = EDITORS.get(name)
        if not editor:
            return
        return editor(win, project, docid, docname)

    @classmethod
    def EditorTypesList(cls):
        global EDITORS
        return EDITORS.keys()

    def createEditorWidget(self):
        return None

    def destroy(self, *args):
        self.log.info("Destroy")

        if self.elementsroot:
            self.elementsroot = None
        if self.elements:
            self.elements.destroy()
            del self.elements
            self.elements = None

    def setModified(self, modified):
        return None

    def _findElement(self, docid):
        root = self.elementsroot
        child_count = root.childCount()
        for i in range(child_count):
            item = root.child(i)
            _docid = item.text(1)  # text at first (0) column
            if _docid == docid:
                return item
        return None

    def _addElement(self, _type, name):
        if not _type:
            return None

        parent = self._findElement(_type) or self.elementsroot
        if not parent:
            return None

        item = Qt.QTreeWidgetItem(parent, [name, "something", ])
        item.setIcon(0, getIcon("attachment"))

    def getBody(self):
        return None

    def getImages(self):
        return []

    def insertImage(self, path, image=None):
        return None

    def on_toolbar_editor_action(self, name):
        return None

    def exportToPdf(self):
        return None

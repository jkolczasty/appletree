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
from appletree.backend import getBackend
from appletree.helpers import getIcon, T, genuid
import logging
from weakref import ref


class QATTextDocument(Qt.QTextDocument):
    def __init__(self, docbackend, docid, *args):
        super(QATTextDocument, self).__init__(*args)
        self.docbackend = docbackend
        self.docid = docid

    def loadResource(self, p_int, _qurl):
        url = _qurl.toString()

        backend = getBackend(self.docbackend)
        # print("loadResource():", self.docid, url)
        return backend.getImage(self.docid, url)


class TabEditorText(Qt.QWidget):
    prevModified = False

    def __init__(self, win, docbackend, docid, docname):
        backend = getBackend(docbackend)
        if not backend:
            raise RuntimeError("Missing backend")

        Qt.QWidget.__init__(self)
        self.log = logging.getLogger("at.texteditor")
        self.win = ref(win)

        self.docid = docid
        self.docname = docname
        self.docbackend = docbackend
        h1 = Qt.QVBoxLayout()
        splitter = Qt.QSplitter()

        self.setLayout(h1)
        h1.addWidget(splitter)

        self.editor = Qt.QTextEdit()
        self.editor.setAcceptRichText(1)
        # self.editor = Qt.QTextDocument()
        self.doc = QATTextDocument(docbackend, docid)

        docbody = backend.getDocumentBody(docid)
        images = backend.getImages(docid)

        for img in images:
            image = backend.getImage(docid, img)
            if image:
                self.log.info("document(): add image: %s: %s", docid, img)
                self.addImage(img, image)

        self.doc.setHtml(docbody)
        self.editor.setDocument(self.doc)

        fontdb = Qt.QFontDatabase()
        fontdb.addApplicationFont("fonts/fontawesome-webfont.ttf")

        font = Qt.QFont("Courier")
        font.setPointSize(24)
        self.editor.setFont(font)

        elements = Qt.QTreeWidget()
        # elements.setMaximumWidth(200)
        # elements.setFixedWidth(200)
        # elements.setMinimumWidth(100)
        elements.setBaseSize(100, 100)
        elements.adjustSize()
        # elements.setSizePolicy(Qt.QSizePolicy.MinimumExpanding,Qt.QSizePolicy.MinimumExpanding)

        # elements.setFixedWidth(200)
        elements.setHeaderHidden(True)
        elementsroot = elements.invisibleRootItem()
        # self.connect(tree, Qt.SIGNAL("itemSelectionChanged(QTreeWidgetItem*, int)"), self.on_tree_clicked)
        # elements.itemSelectionChanged.connect(self.on_tree_item_selection)

        elementstype = Qt.QTreeWidgetItem(elementsroot, [T("Attachements"), "attachements"])
        elementstype.setIcon(0, getIcon("attachments"))
        elementstype.setExpanded(True)

        elementstype = Qt.QTreeWidgetItem(elementsroot, [T("Images"), "images"])
        elementstype.setIcon(0, getIcon("attachments"))
        elementstype.setExpanded(True)

        self.elements = elements
        self.elementsroot = elementsroot

        # self._addElement("attachements", "somefile")

        splitter.addWidget(self.editor)
        splitter.addWidget(self.elements)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 0)

        # TODO: should accessibleName be used?
        self.setAccessibleName(docid)

        self.doc.setModified(False)

        self.connect(self.editor, Qt.SIGNAL("textChanged()"), self.on_text_changed)

    def setModified(self, modified):
        self.doc.setModified(modified)
        # NOTE: change also self.prevModified?
        self.prevModified = None
        self.on_text_changed()

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
        return self.doc.toHtml(encoding='UTF-8')

    def getImages(self):
        images = []
        block = self.doc.begin()
        while block.isValid():
            item = block.begin()
            while 1:
                if item.atEnd():
                    break

                fragment = item.fragment()
                # shitty C++ iterators ];-S
                item += 1
                if not fragment.isValid():
                    continue

                charformat = fragment.charFormat()

                if charformat.isImageFormat():
                    imageformat = charformat.toImageFormat()
                    name = imageformat.name()
                    images.append(name)

            block = block.next()
        return images

    def loadImageFromFile(self, path):
        pass

    def addImage(self, name, image=None, path=None):
        url = name
        qurl = Qt.QUrl()
        qurl.setUrl(url)

        if not image:
            image = Qt.QImage(path)

        self.log.info("addImage(): %s: %s", name, url)
        imagef = Qt.QTextImageFormat()
        imagef.setName(url)

        self.doc.addResource(Qt.QTextDocument.ImageResource, qurl, image)
        return qurl

    def insertImage(self, name, path):
        if name is None:
            name = genuid()

        self.log.info("insertImage(): %s: %s", name, path)
        qurl = self.addImage(name, path=path)
        url = qurl.toString()

        image = Qt.QTextImageFormat()
        image.setName(url)
        # image.setName()

        cursor = self.editor.textCursor()
        cursor.insertImage(image)

    def on_text_changed(self, *args):
        modified = self.doc.isModified()
        if modified == self.prevModified:
            return
        self.prevModified = modified

        win = self.win()
        if not win:
            return

        name = self.docname if not modified else self.docname + " *"
        win.tabSetLabel(self.docid, name)

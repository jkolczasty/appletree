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

from appletree.gui.qt import Qt, QtCore, QtGui, FontDB, loadQImageFix
from appletree.helpers import getIcon, T, genuid, messageDialog
import logging
from weakref import ref
from hashlib import sha1
from .texteditor import QTextEdit, QATTextDocument, ImageResizeDialog


class TabEditorText(Qt.QWidget):
    prevModified = False

    def __init__(self, win, project, docid, docname):
        Qt.QWidget.__init__(self)
        self.project = project
        self.log = logging.getLogger("at.texteditor")
        self.win = ref(win)
        self.ignorechanges = False
        # keep cursorpos for some deffered events
        self.cursorpos = None

        self.docid = docid
        self.docname = docname
        h1 = Qt.QVBoxLayout()
        splitter = Qt.QSplitter()

        self.setLayout(h1)
        h1.addWidget(splitter)

        self.editor = QTextEdit(parent=self)
        self.editor.cursorPositionChanged.connect(self.on_cursor_possition_changed)
        self.doc = QATTextDocument(self, docid, parent=self.editor)

        docbody = self.project.doc.getDocumentBody(docid)
        images = self.project.doc.getImages(docid)

        for img in images:
            image = self.project.doc.getImage(docid, img)
            if image:
                self.log.info("document(): add image: %s: %s", docid, img)
                self.addImage(img, image)

        self.doc.setHtml(docbody)
        self.editor.setDocument(self.doc)

        font = Qt.QFont("Courier")
        font.setPointSize(14)
        self.editor.setFont(font)

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

        self.doc.setModified(False)

        # self.connect(self.editor, Qt.SIGNAL("textChanged()"), self.on_text_changed)
        self.editor.textChanged.connect(self.on_text_changed)
        self.editor.contextMenuEventSingal.connect(self.on_contextmenu_event)

    def destroy(self, *args):
        self.log.info("Destroy")

        if self.editor:
            self.editor.close()
            self.editor.destroy()
            del self.editor
            self.editor = None

        if self.doc:
            self.doc.clear()
            del self.doc
            self.doc = None

        if self.elementsroot:
            self.elementsroot = None
        if self.elements:
            self.elements.destroy()
            del self.elements
            self.elements = None

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
        return self.doc.toHtml()

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
                    scheme = name.split("://", 1)[0]
                    if scheme and scheme in ('http', 'https', 'file'):
                        # change image name to local one (e.g. image loaded/pasted from url)
                        # image = self.doc.resource(Qt.QTextDocument.ImageResource, Qt.QUrl(name))
                        # newname = "resources/images/" + sha1(name.encode('utf-8')).hexdigest() + ".png"
                        # self.doc.addResource(Qt.QTextDocument.ImageResource, Qt.QUrl(newname), image)
                        # imageformat.setName(newname)
                        images.append(name)
                    else:
                        images.append(name)

            block = block.next()
        return images

    def loadImageFromFile(self, path):
        pass

    def addImage(self, url, image=None, path=None):
        if not image:
            image = loadQImageFix(path)
            if not image:
                return

        self.log.info("addImage(): %s: %s", path, url)

        qurl = Qt.QUrl()
        qurl.setUrl(url)
        self.doc.addResource(Qt.QTextDocument.ImageResource, qurl, image)
        del qurl
        del image
        return url

    def insertImage(self, path):
        url = "file://" + path
        self.log.info("insertImage(): %s", url)
        self.addImage(url, path)

        image = Qt.QTextImageFormat()
        image.setName(url)

        cursor = self.editor.textCursor()
        cursor.insertImage(image)
        del image

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

    def on_contextmenu_event(self, event):
        pos = event.pos()
        if not pos:
            return
        cursor = self.editor.cursorForPosition(pos)
        if not cursor:
            return

        self.cursorpos = pos
        menu = self.editor.createStandardContextMenu()

        charformat = cursor.charFormat()
        if charformat.isImageFormat():
            menu.addSeparator()

            # TODO: allow plugins to modify context menus
            action = Qt.QAction(T("Resize image"), menu)
            action.triggered.connect(self.on_contextmenu_imageresize)
            menu.addAction(action)

            action = Qt.QAction(T("Copy image"), menu)
            action.triggered.connect(self.on_contextmenu_imagecopy)
            menu.addAction(action)

        menu.exec_(event.globalPos())
        del menu
        self.cursorpos = None

    def on_contextmenu_imageresize(self, *args):
        cursor = self.editor.cursorForPosition(self.cursorpos)
        if not cursor:
            return

        charformat = cursor.charFormat()
        if not charformat or not charformat.isImageFormat():
            return

        _format = charformat.toImageFormat()
        w, h = _format.width(), _format.height()

        if not w or not h:
            image = self.doc.resource(Qt.QTextDocument.ImageResource, Qt.QUrl(_format.name()))
            if not image:
                return
            w, h = image.width(), image.height()
            if not w or not h:
                return

        resizedialog = ImageResizeDialog(self.win(), "Resize image", "Resize image", w, h)

        if not resizedialog.exec_():
            return

        w = resizedialog.w
        h = resizedialog.h

        _format.setWidth(w)
        _format.setHeight(h)

        # now we need to find that block -> fragment in document now
        block = cursor.block()
        if not block:
            return
        it = block.begin()
        fragment = it.fragment()
        if not fragment:
            return

        cursor2 = self.editor.textCursor()
        cursor2.setPosition(fragment.position())
        cursor2.setPosition(fragment.position() + fragment.length(), Qt.QTextCursor.KeepAnchor)
        cursor2.setCharFormat(_format)

    def on_contextmenu_imagecopy(self, *args):
        cursor = self.editor.cursorForPosition(self.cursorpos)
        if not cursor:
            return

        charformat = cursor.charFormat()
        if not charformat or not charformat.isImageFormat():
            return

        _format = charformat.toImageFormat()
        w, h = _format.width(), _format.height()

        if not w or not h:
            image = self.doc.resource(Qt.QTextDocument.ImageResource, Qt.QUrl(_format.name()))
            if not image:
                return
            w, h = image.width(), image.height()
            if not w or not h:
                return
        clipboard = Qt.QApplication.clipboard()
        clipboard.setImage(image.toImage())

    def on_fontselection_change(self, font):
        if self.ignorechanges:
            return
        cfont = self.editor.currentFont()
        font.setPointSize(cfont.pointSize())
        self.editor.setCurrentFont(font)
        self.editor.setFont(font)

    def on_fontsizeselection_change(self, size):
        if self.ignorechanges:
            return

        cursor = self.editor.textCursor()
        _format = cursor.charFormat()
        _format.setFontPointSize(size)
        cursor.setCharFormat(_format)
        self.editor.setFontPointSize(size)

    def on_cursor_possition_changed(self):
        win = self.win()
        if not win:
            return

        self.ignorechanges = True
        try:
            font = self.editor.currentFont()
            win.fontsizeselection.setValue(font.pointSize())
            win.fontselection.setCurrentFont(font)
        finally:
            self.ignorechanges = False

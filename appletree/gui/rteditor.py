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
from appletree.helpers import T, genuid, messageDialog, getIcon
from .rteditorbase import QTextEdit, RTDocument, ImageResizeDialog
from .editor import Editor, EDITORS


class RTEditor(Editor):
    prevModified = False
    doc = None
    has_images = True
    fontselection = None
    fontsizeselection = None

    def __init__(self, win, project, docid, docname):
        super(RTEditor, self).__init__(win, project, docid, docname)
        self.cursorpos = None

    def createEditorWidget(self):
        self.editor = QTextEdit(parent=self)
        self.editor.cursorPositionChanged.connect(self.on_cursor_possition_changed)
        self.doc = RTDocument(self, self.docid, parent=self.editor)

        docbody = self.project.doc.getDocumentBody(self.docid)
        self.doc.setHtml(docbody)
        self.editor.setDocument(self.doc)

        font = Qt.QFont("Courier")
        font.setPointSize(14)
        self.editor.setFont(font)
        self.doc.setModified(False)

        # self.connect(self.editor, Qt.SIGNAL("textChanged()"), self.on_text_changed)
        self.editor.textChanged.connect(self.on_text_changed)
        self.editor.contextMenuEventSingal.connect(self.on_contextmenu_event)

        return self.editor

    def buildToolbarLocal(self):
        self.fontselection = Qt.QFontComboBox(self.toolbar)
        self.fontselection.currentFontChanged.connect(self.on_fontselection_change)

        self.fontsizeselection = Qt.QSpinBox(self.toolbar)
        self.fontsizeselection.setMinimum(4)
        self.fontsizeselection.setMaximum(32)
        self.fontsizeselection.setValue(14)
        self.fontsizeselection.valueChanged.connect(self.on_fontsizeselection_change)

        self.toolbar.addWidget(self.fontselection)
        self.toolbar.addWidget(self.fontsizeselection)
        self.toolbar.addButtonObjectAction(self, "format-justify-left", getIcon('format-justify-left'))
        self.toolbar.addButtonObjectAction(self, "format-justify-center", getIcon('format-justify-center'))
        self.toolbar.addButtonObjectAction(self, "format-justify-right", getIcon('format-justify-right'))

        self.toolbar.addSeparator()
        self.toolbar.addButtonObjectAction(self, 'insert-image', getIcon('image-insert'), desc='Insert image',
                                           shortcut='CTRL+SHIFT+I')

    def destroy(self, *args):
        super(RTEditor, self).destroy(*args)
        self.log.info("Destroy")

        if self.doc:
            self.doc.clear()
            del self.doc
            self.doc = None

    def save(self, *args):
        self.log.info("save()")

        # first getimages, couse this method can change body settings
        images = self.getImages()
        imageslocal = []
        body = self.getBody()
        # save images
        for res in images:
            if res.startswith('data:image/'):
                # ignore inline encoded images
                continue
            url = Qt.QUrl()
            url.setUrl(res)
            resobj = self.doc.resource(Qt.QTextDocument.ImageResource, url)

            localname = self.project.doc.putImage(self.docid, res, resobj)
            if localname:
                imageslocal.append(localname)

        if self.project.doc.putDocumentBody(self.docid, body):
            self.setModified(False)

        self.project.doc.clearImagesOld(self.docid, imageslocal)

    def setModified(self, modified):
        self.doc.setModified(modified)
        # NOTE: change also self.prevModified?
        self.prevModified = None
        self.on_text_changed()

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
                    images.append(name)

            block = block.next()
        return images

    def insertImage(self, path, image=None):
        qurl = Qt.QUrl.fromLocalFile(path)
        url = qurl.toString()
        self.log.info("insertImage(): %s: %s", path, url)

        if not image:
            image = loadQImageFix(path)
            if not image:
                return

        qbaimage = Qt.QByteArray()
        qb = Qt.QBuffer(qbaimage)
        qb.open(Qt.QIODevice.WriteOnly)
        image.save(qb, 'PNG')
        del image
        qb.close()

        data = Qt.QByteArray()
        data.append(b'data:image/png;base64,')
        data.append(qbaimage.toBase64())
        qbaimage.clear()
        del qbaimage

        strdata = str(data, 'ascii')
        data.clear()
        del data

        imagef = Qt.QTextImageFormat()
        imagef.setName(strdata)

        cursor = self.editor.textCursor()
        cursor.insertImage(imagef)
        del imagef

    def on_toolbar_action(self, name, *args):
        if super(RTEditor, self).on_toolbar_action(name, *args):
            return

        if name == 'format-justify-center':
            self.editor.setAlignment(QtCore.Qt.AlignCenter)
            return

        if name == 'format-justify-right':
            self.editor.setAlignment(QtCore.Qt.AlignRight)
            return

        if name == 'format-justify-left':
            self.editor.setAlignment(QtCore.Qt.AlignLeft)
            return

    def exportToPdf(self):
        result = Qt.QFileDialog.getSaveFileName(self, "Export document to pdf", "", "PDF document (*.pdf)")
        if QTVERSION == 4:
            filename = result
        else:
            filename, selectedfilter = result

        if not filename:
            return

        try:
            if os.path.isfile(filename):
                os.unlink(filename)
        except Exception as e:
            self.log.error("exportToPdf(): failed to unlink destination file: %s: %s", e.__class__.__name__, e)
            messageDialog("PDF Export", "Failed to export as pdf.")
            return

        self.log.info("Export to PDF: %s", filename)
        printer = Qt.QPrinter(Qt.QPrinter.PrinterResolution)
        printer.setOutputFormat(Qt.QPrinter.PdfFormat)
        printer.setPaperSize(Qt.QPrinter.A4)
        printer.setOutputFileName(filename)
        printer.setCreator("AppleTree")
        printer.setPrintProgram("AppleTree")
        printer.setFontEmbeddingEnabled(True)
        printer.setDocName(self.docname)
        self.doc.print(printer)
        messageDialog("PDF Export", "PDF saved as: " + Qt.QDir.toNativeSeparators(filename))
        del printer

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

        menu.addSeparator()
        charformat = cursor.charFormat()
        if charformat.isImageFormat():
            # TODO: allow plugins to modify context menus
            action = Qt.QAction(T("Resize image"), menu)
            action.triggered.connect(self.on_contextmenu_imageresize)
            menu.addAction(action)

            action = Qt.QAction(T("Copy image"), menu)
            action.triggered.connect(self.on_contextmenu_imagecopy)
            menu.addAction(action)

        clipboard = Qt.QApplication.clipboard()
        image = clipboard.image()
        if image and not image.isNull():
            del image
            action = Qt.QAction(T("Paste image"), menu)
            action.triggered.connect(self.on_contextmenu_imagepaste)
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
        image = self.doc.resource(Qt.QTextDocument.ImageResource, Qt.QUrl(_format.name()))
        if not image:
            return
        w, h = image.width(), image.height()
        if not w or not h:
            return
        clipboard = Qt.QApplication.clipboard()
        clipboard.setImage(image.toImage())

    def on_contextmenu_imagepaste(self, *args):
        self.log.info("imagepaste")
        cursor = self.editor.cursorForPosition(self.cursorpos)
        if not cursor:
            return

        clipboard = Qt.QApplication.clipboard()
        image = clipboard.pixmap()

        if not image or image.isNull():
            image = clipboard.image()

        if not image or image.isNull():
            self.log.info("imagepaste(): no image in clipboard/2")
            # NOTE: should it be deleted?
            del image
            return

        self.insertImage(genuid(), image=image)

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

        _format = Qt.QTextCharFormat()
        _format.setFontPointSize(size)
        self.editor.mergeCurrentCharFormat(_format)
        self.editor.setFontPointSize(size)

    def on_cursor_possition_changed(self):
        self.ignorechanges = True
        try:
            font = self.editor.currentFont()
            self.fontsizeselection.setValue(font.pointSize())
            self.fontselection.setCurrentFont(font)
        finally:
            self.ignorechanges = False


EDITORS['richtext'] = RTEditor

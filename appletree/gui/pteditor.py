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


class PTEditor(Editor):
    prevModified = False
    doc = None
    has_images = False

    def __init__(self, win, project, docid, docname):
        super(PTEditor, self).__init__(win, project, docid, docname)
        self.cursorpos = None

    def createEditorWidget(self):
        self.editor = Qt.QPlainTextEdit(parent=self)
        # self.editor.cursorPositionChanged.connect(self.on_cursor_possition_changed)
        # self.doc = Qt.QTextDocument(self)

        docbody = self.project.doc.getDocumentBody(self.docid)
        self.doc = self.editor.document()
        self.doc.setPlainText(docbody)

        font = Qt.QFont("Courier")
        font.setPointSize(14)
        self.editor.setFont(font)
        self.doc.setModified(False)

        # self.connect(self.editor, Qt.SIGNAL("textChanged()"), self.on_text_changed)
        self.editor.textChanged.connect(self.on_text_changed)
        # self.editor.contextMenuEventSingal.connect(self.on_contextmenu_event)

        return self.editor

    def destroy(self, *args):
        super(PTEditor, self).destroy(*args)
        self.log.info("Destroy")

        if self.doc:
            self.doc.clear()
            del self.doc
            self.doc = None

    def setModified(self, modified):
        self.doc.setModified(modified)
        # NOTE: change also self.prevModified?
        self.prevModified = None
        self.on_text_changed()

    def getBody(self):
        return self.editor.toPlainText()

    def on_toolbar_editor_action(self, name):
        return None

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
        print("Modified!!!!", self.doc.isModified())
        modified = self.doc.isModified()
        if modified == self.prevModified:
            return
        self.prevModified = modified

        win = self.win()
        if not win:
            return

        name = self.docname if not modified else self.docname + " *"
        win.tabSetLabel(self.docid, name)


EDITORS['plaintext'] = PTEditor

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
from appletree.helpers import T, messageDialog, getIconImage
import requests
import html
import re
import logging
from weakref import ref
import base64

RE_URL = re.compile(r'((file|http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?)')


class ImageResizeDialog(Qt.QDialog):
    def __init__(self, win, title, name, w, h):
        super(ImageResizeDialog, self).__init__(win)
        self.w = w
        self.h = h
        self.keepaspect = True
        self.aspect = float(w) / float(h)
        self.result = False

        self.setWindowTitle(title)
        self.vbox = Qt.QVBoxLayout(self)
        self.vbox.addWidget(Qt.QLabel(T(name)))

        self.box = Qt.QGroupBox(self)
        self.form = Qt.QFormLayout(self.box)

        buttonbox = Qt.QDialogButtonBox()
        buttonbox.setGeometry(Qt.QRect(150, 250, 341, 32))
        buttonbox.setOrientation(QtCore.Qt.Horizontal)
        buttonbox.setStandardButtons(Qt.QDialogButtonBox.Cancel | Qt.QDialogButtonBox.Ok)
        buttonbox.setWindowTitle(title)

        self.vbox.addWidget(self.box)
        self.vbox.addWidget(buttonbox)
        self.vbox.setStretch(2, 0)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        # self.setWindowModality(QtCore.QCoreApplication)
        self.setModal(True)

        self.ww = Qt.QSpinBox()
        self.ww.setMinimum(16)
        self.ww.setMaximum(0xffff)
        self.ww.setValue(self.w)
        self.ww.valueChanged.connect(self.on_changed_width)
        self.form.addRow(T("Width"), self.ww)

        self.ww.setFocus()

        self.wh = Qt.QSpinBox()
        self.ww.setMinimum(16)
        self.wh.setMaximum(0xffff)
        self.wh.setValue(self.h)
        self.wh.valueChanged.connect(self.on_changed_height)
        self.form.addRow(T("Height"), self.wh)

        widget = Qt.QCheckBox()
        widget.setChecked(True)
        widget.stateChanged.connect(self.on_changed_aspect)
        self.form.addRow(T("Keep aspect"), widget)

        buttonbox.accepted.connect(self.on_accept)
        buttonbox.rejected.connect(self.on_reject)
        # QtCore.QMetaObject.connectSlotsByName(Dialog)
        self.adjustSize()
        self.setMinimumWidth(600)
        self.setSizePolicy(Qt.QSizePolicy.MinimumExpanding, Qt.QSizePolicy.MinimumExpanding)

    def exec_(self):
        super(ImageResizeDialog, self).exec_()
        # del self.fields
        return self.result

    def on_accept(self):
        self.result = True
        self.close()

    def on_reject(self):
        self.result = False
        self.close()

    def on_changed_width(self, w):
        self.w = w
        if not self.keepaspect:
            return

        self.keepaspect = False
        h = float(w) / self.aspect
        self.wh.setValue(int(h))
        self.keepaspect = True

    def on_changed_height(self, h):
        self.h = h
        if not self.keepaspect:
            return
        self.keepaspect = False
        w = float(h) * self.aspect
        self.ww.setValue(int(w))
        self.keepaspect = True

    def on_changed_aspect(self, newvalue):
        self.keepaspect = newvalue


class QTextEdit(Qt.QTextEdit):
    contextMenuEventSingal = Qt.pyqtSignal(object)
    linkClicked = Qt.pyqtSignal(object)
    clickedAnchor = None

    def __init__(self, *args, **kwargs):
        super(QTextEdit, self).__init__()
        self.win = ref(kwargs.get('parent'))
        # self.contextMenuEventSingal = Qt.pyqtSignal(object)
        flags = self.textInteractionFlags()
        flags = QtCore.Qt.TextInteractionFlags(flags)
        flags |= QtCore.Qt.LinksAccessibleByMouse
        flags |= QtCore.Qt.LinksAccessibleByKeyboard
        self.setTextInteractionFlags(flags)
        self.setAcceptRichText(True)
        self.setAutoFormatting(QTextEdit.AutoAll)
        self.addShortcut('CTRL+B', self.on_bold)
        self.addShortcut('CTRL+I', self.on_italic)
        self.addShortcut('CTRL+U', self.on_underline)
        self.addShortcut('CTRL+T', self.on_test)

    def addShortcut(self, shortcut, callback):
        action = Qt.QAction(self)
        action.setShortcut(shortcut)
        action.triggered.connect(callback)
        self.addAction(action)

    def mousePressEvent(self, event):
        pos = event.pos()
        self.clickedAnchor = self.anchorAt(pos)
        return super(QTextEdit, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.clickedAnchor and (event.button() & QtCore.Qt.LeftButton) and (
                    event.modifiers() & QtCore.Qt.ControlModifier):
            pos = event.pos()
            clickedAnchor = self.anchorAt(pos)

            messageDialog("Link clicked", "Link you clicked: {0}".format(clickedAnchor), details=clickedAnchor)
            self.linkClicked.emit(event)

            self.clickedAnchor = None
            return
        return super(QTextEdit, self).mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        self.contextMenuEventSingal.emit(event)

    def insertLink(self, url, cursor=None, addSpace=True):
        if not cursor:
            cursor = self.textCursor()
        cursor = Qt.QTextCursor(cursor)
        _cformat = cursor.charFormat()
        font = _cformat.font()
        _format = Qt.QTextCharFormat()
        _format.setFont(font)
        _format.setUnderlineStyle(1)
        _format.setForeground(QtCore.Qt.blue)
        _format.setAnchor(True)
        _format.setAnchorHref(url)

        cursor.insertText(url, _format)
        if addSpace:
            _format = Qt.QTextCharFormat()
            _format.setFont(font)
            cursor.insertText(" ", _format)

    def insertText(self, s, cursor=None):
        if not cursor:
            cursor = self.textCursor()
        cursor = Qt.QTextCursor(cursor)
        _cformat = cursor.charFormat()
        font = _cformat.font()
        _format = Qt.QTextCharFormat()
        _format.setFont(font)
        cursor.insertText(s, _format)

    def insertFromMimeData(self, mime):
        if mime.hasText() and not mime.hasHtml():
            global RE_URL
            s = mime.text()
            # replace links
            s = html.escape(s, quote=False)
            index = 0
            c = 0
            while c < 1000:
                m = RE_URL.search(s, index)
                if not m:
                    s2 = s[index:]
                    if c and s2.startswith(" "):
                        s2 = s2[1:]
                    self.insertText(s2)
                    break

                pos = m.start()
                s2 = s[index:pos]
                if c and s2.startswith(" "):
                    s2 = s2[1:]
                self.insertText(s2)
                index2 = m.end()
                self.insertLink(m.group(1))
                c += 1
                index = index2
            return

        return super(QTextEdit, self).insertFromMimeData(mime)

    def on_bold(self):
        if self.fontWeight() == QtGui.QFont.Bold:
            self.setFontWeight(QtGui.QFont.Normal)
        else:
            self.setFontWeight(QtGui.QFont.Bold)

    def on_italic(self):
        self.setFontItalic(not self.fontItalic())

    def on_underline(self):
        self.setFontUnderline(not self.fontUnderline())

    def on_strikeout(self):
        # not implemented
        font = self.currentFont()
        font.setStrikeOut(not font.strikeOut())
        self.setCurrentFont(font)
        self.setFont(font)

    def on_test(self):
        pass


class QATTextDocument(Qt.QTextDocument):
    def __init__(self, editor, docid, *args, **kwargs):
        super(QATTextDocument, self).__init__(*args, **kwargs)
        self.log = logging.getLogger("at.document." + docid)
        self.editor = editor
        self.docid = docid

    def loadResourceRemote(self, url):
        # TODO: show wait/progress dialog/info
        try:
            ret = requests.get(url)
            if ret.status_code not in (200,):
                return None

            data = Qt.QByteArray(ret.content)
            image = Qt.QPixmap()
            image.loadFromData(data)
            data.clear()
            return image
        except Exception as e:
            self.log.error("Failed to retrive remote image: %s: %s", e.__class__.__name__, e)

    def loadResourceMissing(self, _qurl):
        image = getIconImage("noimage")
        self.editor.doc.addResource(Qt.QTextDocument.ImageResource, _qurl, image)
        return image

    def loadResource(self, p_int, _qurl):
        url = _qurl.toString()
        if url.startswith('data:image/'):
            return super(QATTextDocument, self).loadResource(p_int, _qurl)

        self.editor.log.info("loadResource(): %s", url)
        scheme = _qurl.scheme()
        image = self.editor.project.doc.getImage(self.docid, url)
        if image:
            self.editor.doc.addResource(Qt.QTextDocument.ImageResource, _qurl, image)
            return image

        if scheme:
            if scheme in ('http', 'https'):
                self.editor.log.info("Trying retrive remote image: %s", url)
                # remote image get it from network
                image = self.loadResourceRemote(url)
                if image:
                    self.editor.doc.addResource(Qt.QTextDocument.ImageResource, _qurl, image)
                return image

            if scheme == 'file':
                try:

                    filename = Qt.QDir.toNativeSeparators(_qurl.toLocalFile())
                    self.editor.log.info("Trying retrive local image: %s", filename)
                    f = Qt.QFile(filename)
                    if not f.open(Qt.QFile.ReadOnly):
                        self.log.error("loadResource(): could not open file: %s", url)
                        return self.loadResourceMissing(_qurl)

                    data = f.readAll()
                    f.close()
                    del f

                    image = Qt.QPixmap()
                    image.loadFromData(data)
                    data.clear()
                    del data
                    if image:
                        self.editor.doc.addResource(Qt.QTextDocument.ImageResource, _qurl, image)
                    return image
                except Exception as e:
                    self.log.error("Failed to load image: %s: %s", e.__class__.__name__, e)

        res = super(QATTextDocument, self).loadResource(p_int, _qurl)
        if res:
            return res

        return self.loadResourceMissing(_qurl)

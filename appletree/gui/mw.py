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

from __future__ import absolute_import
from __future__ import print_function

import logging
from appletree.backend import getBackend, listBackends
from appletree.gui.qt import Qt, QtGui, QtCore
from appletree.helpers import genuid, getIcon
from appletree.gui.texteditor import TabEditorText
from appletree.gui.mwtoolbar import MainWindowToolbar
from appletree.gui.treeview import QATTreeWidget
from appletree.plugins.base import ATPlugins

TREE_ITEM_FLAGS = QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled


class AppleTreeMainWindow(QtGui.QMainWindow):
    editors = None
    ready = False
    treeready = False
    plugins = None

    def __init__(self):
        QtGui.QMainWindow.__init__(self, None)
        self.log = logging.getLogger("at")

        self.setWindowTitle("AppleTree")
        self.editors = dict()

        self.menubar = Qt.QMenuBar()
        self.toolbar = MainWindowToolbar(self)

        self.menuplugins = self.menubar.addMenu("Plugins")

        self.plugins = ATPlugins(self)
        self.plugins.discovery()

        wid = Qt.QWidget()
        splitter = Qt.QSplitter()
        box = Qt.QVBoxLayout()
        tree = QATTreeWidget(self)

        tabs = Qt.QTabWidget()
        tabs.setTabsClosable(True)
        tabs.tabCloseRequested.connect(self.on_tab_close_req)
        tabs.currentChanged.connect(self.on_tab_current_changed)

        # TODO: remove static code, move to dynamic build of toolbars and menus
        self.toolbar.add(
            [dict(name='Save', icon='save', shortcut='CTRL+S', callback=self.on_toolbar_save),
             dict(name='Add document', icon='document-add', shortcut='CTRL+SHIFT++',
                  callback=self.on_toolbar_document_add),
             ])

        self.toolbar.addWithSeparatorLeft(
            [dict(name='Bold', icon='bold', shortcut='CTRL+B', callback=self.on_toolbar_bold),
             ])

        self.toolbar.addWithSeparatorLeft(
            [
                dict(name='Insert image', icon='image-insert', shortcut='CTRL+SHIFT+I',
                     callback=self.on_toolbar_insert_image),
            ])

        splitter.addWidget(tree)
        splitter.addWidget(tabs)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)

        # self.splitter.show()
        # self.tree.show()
        tree.setColumnCount(3)
        tree.setColumnHidden(1, True)
        tree.setColumnHidden(2, True)

        wid.setLayout(box)
        box.addWidget(self.toolbar)
        box.addWidget(splitter)
        box.setMenuBar(self.menubar)

        tree.setHeaderHidden(True)
        # tree.setSelectionModel(Qt.QItemSelectionModel.)
        tree.setDragDropMode(Qt.QAbstractItemView.InternalMove)
        tree.setAcceptDrops(True)
        tree.setAutoScroll(True)

        root = tree.invisibleRootItem()
        # self.connect(tree, Qt.SIGNAL("itemSelectionChanged(QTreeWidgetItem*, int)"), self.on_tree_clicked)
        tree.itemSelectionChanged.connect(self.on_tree_item_selection)
        tree.itemChanged.connect(self.on_tree_item_changed)

        self.setGeometry(50, 50, 1440, 800)
        self.setCentralWidget(wid)

        self.tabs = tabs
        self.root = root
        self.tree = tree
        # self.tree.setSortingEnabled(True)
        # self.tree.sortByColumn(0, QtCore.Qt.Qt_)

        self.plugins.initialize()
        self.ready = True
        self.treeready = False

    def _processDocumentsTree(self, docbackend, docid, docname, items, parent):
        self.addDocumentTree(docbackend, docid, docname, parent)

        for childdocid, childdocname, childitems in items:
            self._processDocumentsTree(docbackend, childdocid, childdocname, childitems, docid)

    def loadDocumentsTree(self):
        self.treeready = False
        for docbackend in listBackends():
            self.addDocumentBackend(docbackend)
            backend = getBackend(docbackend)
            doctree = backend.getDocumentsTree()

            for docid, docname, items in doctree:
                self._processDocumentsTree(docbackend, docid, docname, items, docbackend)

        self.treeready = True

    def _getDocumentTree(self, root):
        tree = []
        for i in range(0, root.childCount()):
            child = root.child(i)
            # name, docbackend, docid
            docname = child.text(0)
            docid = child.text(2)
            tree.append((docid, docname, self._getDocumentTree(child)))

        return tree

    def saveDocumentsTree(self):
        if not self.treeready:
            return

        for docbackend in listBackends():
            backend = getBackend(docbackend)
            if not backend:
                continue

            print("BACKEND:", docbackend)

            root = self._treeFindDocument("at:backend:" + docbackend)
            tree = self._getDocumentTree(root)

            backend.setDocumentsTree(tree)

    def on_tree_item_selection(self):
        items = self.tree.selectedItems()
        if not items:
            return
        item = items[0]

        _type = item.text(3)
        if _type != 'D':
            return

        docid = item.text(2)
        if not docid:
            return
        docname = item.text(0)
        docbackend = item.text(1)

        self.open(docbackend, docid, docname)

    def on_tree_item_changed(self, item):
        if not self.treeready:
            return
        self.log.info("on_tree_item_changed()")
        self.saveDocumentsTree()

    def on_tree_drop_event(self, event):
        dropaction = event.dropAction()
        if dropaction != QtCore.Qt.MoveAction:
            event.ignore()
            return True

        source = self.tree.currentItem()
        destination = self.tree.itemAt(event.pos())
        srcdocbackend = source.text(1)
        dstdocbackend = destination.text(1)
        if srcdocbackend != dstdocbackend:
            event.ignore()
            return True

        return False

    def on_tree_drop_after_event(self):
        if not self.treeready:
            return
        self.log.info("on_tree_drop_after_event()")
        self.saveDocumentsTree()

    def on_tab_close_req(self, index):
        widget = self.tabs.widget(index)
        docid = widget.accessibleName()
        # noinspection PyBroadException
        try:
            del self.editors[docid]
        except:
            pass
        widget.destroy()
        self.tabs.removeTab(index)

        if self.tabs.count() == 0:
            self.tabs.hide()

    def on_tab_current_changed(self, index):
        widget = self.tabs.widget(index)
        docid = widget.accessibleName()
        treeitem = self._treeFindDocument(docid)
        if treeitem:
            self.tree.setCurrentItem(treeitem)

    def on_toolbar_bold(self):
        docid, editor = self.getCurrentEditor()

        if not editor:
            return
        if editor.editor.fontWeight() == QtGui.QFont.Bold:
            editor.editor.setFontWeight(QtGui.QFont.Normal)
        else:
            editor.editor.setFontWeight(QtGui.QFont.Bold)

    def on_toolbar_save(self):
        self.save()

    def _treeFindDocument(self, docid):
        items = self.tree.findItems(docid, QtCore.Qt.MatchFixedString | QtCore.Qt.MatchRecursive,
                                    2)  # 0  - Qt.MatchExactly
        if items:
            return items[0]

        return None

    def addDocumentBackend(self, docbackend):
        uid = "at:backend:" + docbackend
        item = self._treeFindDocument(uid)
        if not item:
            item = Qt.QTreeWidgetItem(self.root, [docbackend, docbackend, uid, "B"])
            item.setIcon(0, getIcon("backend"))
            item.setExpanded(True)
        return item

    def addDocumentTree(self, docbackend, docid, name, parent):
        uid = "at:backend:" + docbackend
        root = self._treeFindDocument(uid)
        if parent:
            # TODO: find parent in tree
            parent = self._treeFindDocument(parent) or root
        else:
            parent = root

        item = Qt.QTreeWidgetItem(parent, [name, docbackend, docid, "D"])
        item.setIcon(0, getIcon("doc"))
        item.setExpanded(True)
        item.setFlags(TREE_ITEM_FLAGS)
        return item

    def getCurrentEditor(self):
        index = self.tabs.currentIndex()
        tab = self.tabs.widget(index)
        if not tab:
            return None, None
        docid = tab.accessibleName()
        editor = self.editors.get(docid)
        return docid, editor

    def tabFind(self, uid):
        for i in range(0, self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab.accessibleName() == uid:
                return i

    def open(self, docbackend, docid, name):
        idx = self.tabFind(docid)
        if idx is not None:
            self.tabs.setCurrentIndex(idx)
            return

        tabeditor = TabEditorText(self, docbackend, docid, name)
        self.editors[docid] = tabeditor
        self.tabs.addTab(tabeditor, name)
        c = self.tabs.count()
        if self.tabs.count() == 1:
            self.tabs.show()

        self.tabs.setCurrentIndex(c - 1)

    def tabSetLabel(self, uid, label):
        idx = self.tabFind(uid)
        if idx is None:
            return

        self.tabs.setTabText(idx, label)

    def save(self, *args):
        docid, editor = self.getCurrentEditor()

        print("SAVE:", docid)

        if not editor:
            # TODO: notify about desync/fail?
            return None

        print("=" * 100)
        body = editor.getBody()
        print(body)
        print("=" * 100)

        images = editor.getImages()

        backend = getBackend(editor.docbackend)
        # save images
        imagesnames = []
        for res in images:
            name = res.split("://", 1)[-1]
            imagesnames.append(name)
            url = Qt.QUrl(res)
            resobj = editor.doc.resource(Qt.QTextDocument.ImageResource, url)
            backend.putImage(docid, name, resobj)

        backend.putDocumentBody(docid, body)
        backend.clearImagesOld(docid, imagesnames)
        editor.setModified(False)
        # TODO: clear flag modified in editor

    def on_toolbar_insert_image(self, *args):
        docid, editor = self.getCurrentEditor()

        dialog = Qt.QFileDialog()
        dialog.setFileMode(Qt.QFileDialog.AnyFile)
        dialog.setFilter("Images JPEG/PNG/TIFF (*.png *.jpg *.jpeg *.tiff)")

        if not dialog.exec_():
            return

        filenames = dialog.selectedFiles()

        for fn in filenames:
            uid = genuid()
            editor.insertImage(uid, fn)

    def on_toolbar_test(self, *args):
        pass

    def on_toolbar_document_add(self, *args):
        currentitem = self.tree.currentItem()
        if not currentitem:
            return
        docbackend = currentitem.text(1)
        parent = currentitem.text(2)
        name, ok = Qt.QInputDialog.getText(self, 'New document', 'Enter new document name:')
        if not ok:
            return
        backend = getBackend(docbackend)
        # parent = self._treeFindDocument(parent)
        docid = genuid()
        if not backend.putDocumentBody(docid, ""):
            # TODO: show error dialog
            return
        self.addDocumentTree(docbackend, docid, name, parent)

        self.saveDocumentsTree()
